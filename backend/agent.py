"""Campus Customs shopping agent: model setup, prompt loading, tool wiring, output validation and audit trail."""

import json
import logging
import os
import re
import threading
import time
import uuid
from datetime import datetime, timezone

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic_ai import Agent, ModelRetry, NativeOutput, RunContext, UsageLimits, capture_run_messages
from pydantic_ai.exceptions import ModelHTTPError, UnexpectedModelBehavior, UsageLimitExceeded
from pydantic_ai.messages import (
    ModelMessage, ModelRequest, ModelResponse, RetryPromptPart, TextPart, ToolCallPart, ToolReturnPart, UserPromptPart,
)
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

import tools
from models import AuditEntry, AuditStep, ChatTurn, CustomerProfile, PageContext, ProductCard, ProductInfo, SearchResults, ShopReply, StockReport

BACKEND_DIR = Path(__file__).resolve().parent
PROMPT_PATH = BACKEND_DIR / "prompts" / "prompt.md"

# Nearest .env wins: hw4/.env, then the course-root .env (load_dotenv never overrides).
for folder in [BACKEND_DIR.parent, *BACKEND_DIR.parents]:
    if (folder / ".env").is_file():
        load_dotenv(folder / ".env", override=False)

MODEL_NAME = os.getenv("MODEL_NAME", "gpt-5.6-luna")
PORTKEY_BASE_URL = os.getenv("PORTKEY_BASE_URL", "https://api.portkey.ai/v1")
# Search, maybe a detail lookup or two, then the answer.
USAGE_LIMITS = UsageLimits(request_limit=6)
# Shown when the provider's safety filter blocks a message (e.g. jailbreak attempts).
FILTERED_REPLY = ShopReply(
    reply="Sorry, I can't help with that request. I'm here to help you shop Campus Customs: "
          "ask me about hoodies, tees, sizes, stock or prices!",
)
PRICE_RE = re.compile(r"\$\s?(\d+(?:\.\d{1,2})?)")

log = logging.getLogger("campus_customs.agent")


@dataclass
class ShopDeps:
    customer: CustomerProfile | None = None
    page: PageContext | None = None


def make_model() -> OpenAIChatModel:
    """OpenAI model accessed through the Portkey gateway."""
    key = os.environ.get("PORTKEY_API_KEY")
    if not key:
        raise RuntimeError("PORTKEY_API_KEY is not set; add it to HW4/.env or the course-root .env")
    client = AsyncOpenAI(api_key=key, base_url=PORTKEY_BASE_URL, default_headers={"x-portkey-api-key": key})
    return OpenAIChatModel(MODEL_NAME, provider=OpenAIProvider(openai_client=client))


agent = Agent(
    make_model(),
    deps_type=ShopDeps,
    system_prompt=PROMPT_PATH.read_text(),
    output_type=NativeOutput(ShopReply),
    name="campus-customs-assistant",
    retries=2,
)


@agent.instructions
def customer_context(ctx: RunContext[ShopDeps]) -> str:
    c = ctx.deps.customer
    if c:
        return (f"The customer is logged in as {c.name} (first name: {c.first_name or c.name}, email: {c.email}). "
                "Their earlier conversations with you are included in the message history.")
    return "The customer is browsing as a guest (not logged in); nothing is remembered between visits."


@agent.instructions
def page_context(ctx: RunContext[ShopDeps]) -> str:
    page = ctx.deps.page
    if page is None:
        return ""
    if page.product_id:
        card = tools.get_product_info(page.product_id)
        if card:
            return (f"The customer is currently viewing the product page for **{card.name}** "
                    f"(product_id `{card.product_id}`, colors: {', '.join(card.colors)}). "
                    "'This', 'it' or 'this one' with no other referent means this product.")
    return f"The customer is currently on the page `{page.path}` (not a single product page)."


@agent.tool_plain
def search_products(
    query: str = "",
    garment_type: str | None = None,
    color: str | None = None,
    max_price: float | None = None,
    size: str | None = None,
    limit: int = 8,
) -> SearchResults:
    """Search the catalogue. `query` holds keywords (e.g. "hockey hoodie", "Harvard game").
    Optional filters: garment_type (e.g. "hoodie", "crewneck", "t-shirt", "quarter-zip"),
    color, max_price in USD, size (XS-XXL, only items with that size in stock), limit (max 30).
    `total_matches` is the true number of matching products, even if fewer are returned."""
    return tools.search_products(query, garment_type, color, max_price, size, limit)


@agent.tool_plain
def get_product_details(product_id: str) -> ProductCard | str:
    """Full description, colors, price and stock per size for one product_id."""
    return tools.get_product_details(product_id) or f"No product with id '{product_id}'."


@agent.tool_plain
def get_product_info(product_id: str) -> ProductInfo | str:
    """Description, colors and exact price for one product_id. Use for 'how much is…' / 'tell me about…'."""
    return tools.get_product_info(product_id) or f"No product with id '{product_id}'."


@agent.tool_plain
def check_stock(product_id: str, size: str | None = None) -> StockReport | str:
    """Stock quantity per size for one product_id. Pass `size` (XS, S, M, L, XL, XXL) when the
    customer asks about a specific size; check `requested_in_stock` and `requested_quantity`."""
    return tools.check_stock(product_id, size) or f"No product with id '{product_id}'."


@agent.tool
def get_customer_profile(ctx: RunContext[ShopDeps]) -> CustomerProfile | str:
    """Name and email of the logged-in customer (only their own). Returns a note for guests."""
    return ctx.deps.customer or "The customer is a guest and is not logged in."


@agent.tool_plain
def list_garment_types() -> dict[str, int]:
    """Overview of the catalogue: product count per garment type and the overall price range."""
    return tools.list_garment_types()


@agent.output_validator
def check_reply_facts(ctx: RunContext[ShopDeps], reply: ShopReply) -> ShopReply:
    """Reject replies that cite unknown products or prices not in the database; the model retries."""
    unknown = [pid for pid in reply.product_ids if tools.get_product_info(pid) is None]
    if unknown:
        raise ModelRetry(f"These product_ids do not exist: {unknown}. Use only ids returned by tools.")

    quoted = {round(float(m), 2) for m in PRICE_RE.findall(reply.reply)}
    if not quoted:
        return reply
    ids = list(reply.product_ids)
    if ctx.deps.page and ctx.deps.page.product_id:
        ids.append(ctx.deps.page.product_id)
    allowed = {round(info.price, 2) for pid in ids if (info := tools.get_product_info(pid))}
    allowed |= tools.catalogue_price_bounds()
    wrong = sorted(quoted - allowed)
    if wrong:
        raise ModelRetry(
            f"Your reply quotes price(s) {', '.join(f'${p:.2f}' for p in wrong)} that do not match the database price "
            "of any product in product_ids. Look the price up with get_product_info, add every product whose "
            "price you mention to product_ids, and quote prices exactly."
        )
    return reply


def to_history(turns: list[ChatTurn]) -> list[ModelMessage]:
    history: list[ModelMessage] = []
    for t in turns:
        if t.role == "user":
            history.append(ModelRequest(parts=[UserPromptPart(content=t.content)]))
        else:
            text = t.content
            if t.product_ids:
                text += f"\n\n[Products shown on the page with this reply: {', '.join(t.product_ids)}]"
            history.append(ModelResponse(parts=[TextPart(content=text)]))
    return history

# ------------------------------------------------------------ audit trail

# Append-only audit trail of agent-loop activity (output/audit_trail.json).
# Each chat turn adds one entry: when it ran, who (user id or guest, never email or
# password data), the page, every tool call with short arguments and results,
# output-validator retries, usage, and why the loop stopped. Existing entries are
# never modified or removed; the file is rewritten atomically with the new entry appended.

AUDIT_PATH = Path(__file__).resolve().parent.parent / "output" / "audit_trail.json"
MAX_TEXT = 160
# 13–19 digit runs (with optional spaces/dashes) look like payment card numbers.
CARD_RE = re.compile(r"\b(?:\d[ -]?){12,18}\d\b")


def redact(text: str) -> str:
    return CARD_RE.sub("[redacted number]", text)
_lock = threading.Lock()


def short(value: object, limit: int = MAX_TEXT) -> str:
    text = value if isinstance(value, str) else json.dumps(value, default=lambda o: getattr(o, "model_dump", lambda: str(o))())
    text = redact(" ".join(text.split()))
    return text if len(text) <= limit else text[: limit - 1] + "…"


def iso(ts: datetime | None) -> str:
    return (ts or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat(timespec="milliseconds")


def steps_from(messages: list[ModelMessage]) -> list[AuditStep]:
    """Turn the run's new messages into tool-call / tool-result / retry steps."""
    steps: list[AuditStep] = []
    for msg in messages:
        if isinstance(msg, ModelResponse):
            for part in msg.parts:
                if isinstance(part, ToolCallPart):
                    steps.append(AuditStep(time=iso(msg.timestamp), kind="tool_call", tool=part.tool_name, detail=short(part.args_as_dict())))
        elif isinstance(msg, ModelRequest):
            for part in msg.parts:
                if isinstance(part, ToolReturnPart):
                    steps.append(AuditStep(time=iso(part.timestamp), kind="tool_result", tool=part.tool_name, detail=short(part.content)))
                elif isinstance(part, RetryPromptPart):
                    steps.append(AuditStep(time=iso(part.timestamp), kind="retry", tool=part.tool_name, detail=short(part.content)))
    return steps


def append_audit(entry: AuditEntry) -> None:
    with _lock:
        entries = json.loads(AUDIT_PATH.read_text()) if AUDIT_PATH.exists() else []
        entries.append(entry.model_dump(mode="json"))
        AUDIT_PATH.parent.mkdir(exist_ok=True)
        tmp = AUDIT_PATH.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(entries, indent=2, ensure_ascii=False))
        os.replace(tmp, AUDIT_PATH)

# ------------------------------------------------------------ chat turn

async def ask(
    message: str,
    history: list[ChatTurn],
    customer: CustomerProfile | None = None,
    page: PageContext | None = None,
    user_id: int | None = None,
) -> tuple[ShopReply, list[ProductCard]]:
    """Run one chat turn and return the reply plus validated product cards.

    Every run, successful or not, is appended to the audit trail.
    """
    started_at = datetime.now(timezone.utc)
    started = time.perf_counter()
    prior = to_history(history)
    reply: ShopReply | None = None
    usage = None
    stop_reason, error = "final_result", None
    with capture_run_messages() as messages:
        try:
            result = await agent.run(
                message,
                deps=ShopDeps(customer=customer, page=page),
                message_history=prior,
                usage_limits=USAGE_LIMITS,
            )
            reply, usage = result.output, result.usage
        except ModelHTTPError as e:
            if e.status_code == 400 and "filter" in str(e.body).lower():
                stop_reason, error = "content_filter", "Provider content filter blocked the request"
                reply = FILTERED_REPLY
            else:
                stop_reason, error = "error", f"{type(e).__name__}: {e}"
                raise
        except UsageLimitExceeded as e:
            stop_reason, error = "request_limit", str(e)
            raise
        except UnexpectedModelBehavior as e:
            stop_reason, error = "output_retries_exhausted", str(e)
            raise
        except Exception as e:
            stop_reason, error = "error", f"{type(e).__name__}: {e}"
            raise
        finally:
            duration = time.perf_counter() - started
            new_messages = messages[len(prior):]
            steps = steps_from(new_messages)
            requests = usage.requests if usage else sum(isinstance(m, ModelResponse) for m in new_messages)
            append_audit(AuditEntry(
                run_id=uuid.uuid4().hex[:12],
                started_at=iso(started_at),
                finished_at=iso(None),
                duration_s=round(duration, 2),
                model=MODEL_NAME,
                user=f"user:{user_id}" if user_id else "guest",
                page=page.product_id or page.path if page else None,
                message=short(message),
                history_turns=len(history),
                steps=steps,
                tools_used=sorted({st.tool for st in steps if st.kind == "tool_call" and st.tool}),
                model_requests=requests,
                input_tokens=(usage.input_tokens or 0) if usage else 0,
                output_tokens=(usage.output_tokens or 0) if usage else 0,
                stop_reason=stop_reason,
                error=short(error) if error else None,
                reply=short(reply.reply, 300) if reply else None,
                product_ids=reply.product_ids if reply else [],
            ))
            log.info(
                "chat turn: %.1fs, %d model requests, %d tool calls, stop=%s",
                duration, requests, sum(st.kind == "tool_call" for st in steps), stop_reason,
            )
    return reply, tools.get_cards(reply.product_ids)
