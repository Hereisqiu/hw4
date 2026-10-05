"""Campus Customs API: catalogue, images, accounts, chat history, rate limiting and the shopping-assistant chat.

Run from this folder: uvicorn main:app --reload --port 8000
"""

import base64
import hashlib
import hmac
import json
import logging
import os
import re
import secrets
import sqlite3
import time
from collections import defaultdict, deque

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import agent
from agent import redact
from models import ChatRequest, ChatResponse, ChatTurn, CustomerProfile, ProductCard, StoredMessage
from tools import DATA_DIR, get_db, load_inventory, product_dict

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
log = logging.getLogger("campus_customs")

# ------------------------------------------------------------ accounts (registration, login, sessions)
#
# Account registration, login and sessions for Campus Customs.
#
# Passwords are stored as `pbkdf2_sha256$<salt>$<hex digest>` (120,000 iterations),
# matching the format already used by the seeded test account. Password hashes never
# leave this module: every query that returns user data selects only PUBLIC_COLUMNS.

PBKDF2_ITERATIONS = 120_000
SESSION_COOKIE = "cc_session"
SESSION_TTL = 7 * 24 * 3600
# Signing key for session cookies. Set SESSION_SECRET in .env to keep sessions across restarts.
SESSION_SECRET = os.environ.get("SESSION_SECRET") or secrets.token_hex(32)
PUBLIC_COLUMNS = "id, name, email, first_name, last_name, created_at"
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

auth_router = APIRouter(prefix="/api/auth", tags=["auth"])


# --- password hashing -------------------------------------------------------

def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(8)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), PBKDF2_ITERATIONS).hex()
    return f"pbkdf2_sha256${salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, salt, _ = stored.split("$", 2)
    except ValueError:
        return False
    if algo != "pbkdf2_sha256":
        return False
    return hmac.compare_digest(hash_password(password, salt), stored)


# --- signed session cookie --------------------------------------------------

def _sign(payload: bytes) -> str:
    return hmac.new(SESSION_SECRET.encode(), payload, hashlib.sha256).hexdigest()


def make_session(user_id: int) -> str:
    payload = base64.urlsafe_b64encode(json.dumps({"uid": user_id, "exp": int(time.time()) + SESSION_TTL}).encode())
    return f"{payload.decode()}.{_sign(payload)}"


def read_session(token: str | None) -> int | None:
    if not token or "." not in token:
        return None
    payload, sig = token.rsplit(".", 1)
    if not hmac.compare_digest(_sign(payload.encode()), sig):
        return None
    data = json.loads(base64.urlsafe_b64decode(payload))
    return data["uid"] if data["exp"] > time.time() else None


def _set_cookie(response: Response, user_id: int) -> None:
    response.set_cookie(
        SESSION_COOKIE, make_session(user_id), max_age=SESSION_TTL, httponly=True, samesite="lax"
    )


def _public_user(conn: sqlite3.Connection, user_id: int) -> dict | None:
    row = conn.execute(f"SELECT {PUBLIC_COLUMNS} FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


def current_user(request: Request) -> dict | None:
    user_id = read_session(request.cookies.get(SESSION_COOKIE))
    if user_id is None:
        return None
    with get_db() as conn:
        return _public_user(conn, user_id)


def require_user(user: dict | None = Depends(current_user)) -> dict:
    if user is None:
        raise HTTPException(status_code=401, detail="Please log in")
    return user


# --- endpoints --------------------------------------------------------------

class RegisterIn(BaseModel):
    first_name: str = Field(min_length=1, max_length=60)
    last_name: str = Field(min_length=1, max_length=60)
    email: str = Field(max_length=254)
    password: str = Field(min_length=8, max_length=128)


class LoginIn(BaseModel):
    email: str
    password: str


@auth_router.post("/register", status_code=201)
def register(body: RegisterIn, response: Response) -> dict:
    email = body.email.strip().lower()
    if not EMAIL_RE.match(email):
        raise HTTPException(status_code=422, detail="Please enter a valid email address")
    first, last = body.first_name.strip(), body.last_name.strip()
    with get_db() as conn:
        try:
            cur = conn.execute(
                "INSERT INTO users (name, email, password_hash, first_name, last_name) VALUES (?, ?, ?, ?, ?)",
                (f"{first} {last}", email, hash_password(body.password), first, last),
            )
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=409, detail="An account with this email already exists")
        user = _public_user(conn, cur.lastrowid)
    _set_cookie(response, user["id"])
    return user


@auth_router.post("/login")
def login(body: LoginIn, response: Response) -> dict:
    with get_db() as conn:
        row = conn.execute(
            "SELECT id, password_hash FROM users WHERE email = ?", (body.email.strip().lower(),)
        ).fetchone()
        if row is None or not verify_password(body.password, row["password_hash"]):
            raise HTTPException(status_code=401, detail="Incorrect email or password")
        user = _public_user(conn, row["id"])
    _set_cookie(response, user["id"])
    return user


@auth_router.post("/logout")
def logout(response: Response) -> dict:
    response.delete_cookie(SESSION_COOKIE)
    return {"ok": True}


@auth_router.get("/me")
def me(user: dict = Depends(require_user)) -> dict:
    return user

# ------------------------------------------------------------ chat history (chat_messages table, logged-in customers only)

# Turns of saved history replayed to the agent (older ones stay in the DB and the UI).
AGENT_HISTORY_TURNS = 20


def save_message(user_id: int, role: str, content: str, products: list[ProductCard] | None = None) -> None:
    products_json = json.dumps([p.model_dump() for p in products]) if products else None
    with get_db() as conn:
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content, products_json) VALUES (?, ?, ?, ?)",
            (user_id, role, redact(content), products_json),
        )


def load_messages(user_id: int, limit: int = 200) -> list[StoredMessage]:
    """The customer's most recent messages, oldest first."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, role, content, products_json, created_at FROM chat_messages "
            "WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    messages = []
    for r in reversed(rows):
        products = [ProductCard.model_validate(p) for p in json.loads(r["products_json"])] if r["products_json"] else []
        messages.append(StoredMessage(id=r["id"], role=r["role"], content=r["content"], products=products, created_at=r["created_at"]))
    return messages


def agent_history(user_id: int) -> list[ChatTurn]:
    return [
        ChatTurn(role=m.role, content=m.content, product_ids=[p.product_id for p in m.products])
        for m in load_messages(user_id, AGENT_HISTORY_TURNS)
    ]


def clear_messages(user_id: int) -> None:
    with get_db() as conn:
        conn.execute("DELETE FROM chat_messages WHERE user_id = ?", (user_id,))

# ------------------------------------------------------------ rate limiting (in-memory sliding window for /api/chat)

# (max requests, window in seconds)
LIMITS = [(8, 60), (60, 3600)]
_hits: dict[str, deque[float]] = defaultdict(deque)


def check_rate_limit(request: Request, user: dict | None) -> None:
    """Raise 429 if this customer (or guest IP) has sent too many chat messages recently."""
    key = f"user:{user['id']}" if user else f"ip:{request.client.host if request.client else 'unknown'}"
    now = time.monotonic()
    hits = _hits[key]
    longest = max(window for _, window in LIMITS)
    while hits and now - hits[0] > longest:
        hits.popleft()
    for limit, window in LIMITS:
        recent = sum(1 for t in hits if now - t <= window)
        if recent >= limit:
            wait = int(window - (now - next(t for t in hits if now - t <= window))) + 1
            raise HTTPException(
                status_code=429,
                detail=f"You're sending messages quickly. Please wait {wait} seconds and try again.",
                headers={"Retry-After": str(wait)},
            )
    hits.append(now)

# ------------------------------------------------------------ app and routes

app = FastAPI(title="Campus Customs API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.mount("/media/products", StaticFiles(directory=DATA_DIR / "products"), name="products")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/products")
def list_products() -> list[dict]:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM catalogue ORDER BY name").fetchall()
        return [product_dict(r, load_inventory(conn, r["product_id"])) for r in rows]


@app.get("/api/products/{product_id}")
def get_product(product_id: str) -> dict:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM catalogue WHERE product_id = ?", (product_id,)
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Product not found")
        return product_dict(row, load_inventory(conn, product_id))


@app.post("/api/chat")
async def chat(body: ChatRequest, request: Request, user: dict | None = Depends(current_user)) -> ChatResponse:
    """Send one website chat message to the agent; returns its reply and product cards.

    Logged-in customers: history comes from `chat_messages` and both turns are saved.
    Guests: the browser sends recent history and nothing is stored.
    """
    check_rate_limit(request, user)
    customer = CustomerProfile(name=user["name"], first_name=user["first_name"], email=user["email"]) if user else None
    turns = agent_history(user["id"]) if user else body.history
    try:
        reply, cards = await agent.ask(body.message, turns, customer, body.page, user['id'] if user else None)
    except Exception:
        log.exception("agent run failed")
        raise HTTPException(status_code=502, detail="The assistant is unavailable right now. Please try again.")
    if user:
        save_message(user["id"], "user", body.message)
        save_message(user["id"], "assistant", reply.reply, cards)
    return ChatResponse(reply=reply.reply, results_title=reply.results_title if cards else None, products=cards)


@app.get("/api/chat/history")
def chat_history(user: dict = Depends(require_user)) -> list[StoredMessage]:
    """The logged-in customer's saved conversation (only their own)."""
    return load_messages(user["id"])


@app.delete("/api/chat/history")
def clear_chat_history(user: dict = Depends(require_user)) -> dict:
    clear_messages(user["id"])
    return {"ok": True}
