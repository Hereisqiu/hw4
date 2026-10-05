"""Read-only catalogue tools the shopping agent can call.

The agent never writes SQL. Every query here is parameterised, touches only
`catalogue` and `inventory`, and never reads the `users` table.
The shared SQLite helpers used by the API live here too.
"""

import json
import sqlite3
from pathlib import Path

from models import ProductCard, ProductInfo, ProductSummary, SearchResults, SizeStatus, StockReport

# ------------------------------------------------------------ database helpers

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DATA_DIR / "campus_customs.db"
SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def product_dict(row: sqlite3.Row, inventory: list[dict] | None = None) -> dict:
    p = dict(row)
    p["colors"] = json.loads(p["colors"])
    p["search_tags"] = json.loads(p["search_tags"])
    p["image_url"] = "/media/" + p["image_file_path"]
    if inventory is not None:
        p["inventory"] = inventory
        p["total_stock"] = sum(i["quantity"] for i in inventory)
    return p


def load_inventory(conn: sqlite3.Connection, product_id: str) -> list[dict]:
    rows = conn.execute(
        "SELECT size, quantity FROM inventory WHERE product_id = ?", (product_id,)
    ).fetchall()
    inv = [dict(r) for r in rows]
    inv.sort(key=lambda i: SIZE_ORDER.index(i["size"]) if i["size"] in SIZE_ORDER else 99)
    return inv

# ------------------------------------------------------------ agent tools

MAX_RESULTS = 30
# Catalogue garment types are free text ("hoodie", "full-zip hooded sweatshirt", "short-sleeve T-shirt"),
# so customer wording is mapped to a stem that appears in all variants.
TYPE_STEMS = {"hoodie": "hood", "hooded": "hood", "tee": "t-shirt", "tshirt": "t-shirt", "t shirt": "t-shirt",
              "shirt": "shirt", "quarter zip": "quarter-zip", "quarterzip": "quarter-zip", "1/4 zip": "quarter-zip",
              "crew": "crewneck", "crew neck": "crewneck", "sweater": "sweatshirt", "fleece": "fleece"}


def type_stem(garment_type: str) -> str:
    t = garment_type.lower().strip().rstrip("s")
    return TYPE_STEMS.get(t, t)


def search_products(
    query: str = "",
    garment_type: str | None = None,
    color: str | None = None,
    max_price: float | None = None,
    size: str | None = None,
    limit: int = 8,
) -> SearchResults:
    """Search the catalogue by keywords and optional filters.

    Words in `query` are matched (case-insensitive) against name, garment type,
    description, colors and search tags; products matching more words rank higher.
    `size` keeps only products with that size in stock (XS, S, M, L, XL, XXL).
    """
    words = [w for w in query.lower().split() if len(w) > 1]
    hits: list[tuple[int, ProductSummary]] = []
    with get_db() as conn:
        for row in conn.execute("SELECT * FROM catalogue"):
            p = product_dict(row)
            text = " ".join([p["name"], p["garment_type"], p["description"], *p["colors"], *p["search_tags"]]).lower()
            score = sum(w.rstrip("s") in text for w in words)
            if words and score == 0:
                continue
            if garment_type and type_stem(garment_type) not in (p["garment_type"] + " " + p["name"]).lower():
                continue
            if color and not any(color.lower() in c.lower() for c in p["colors"]):
                continue
            if max_price is not None and p["price"] > max_price:
                continue
            inv = load_inventory(conn, p["product_id"])
            in_stock = [i["size"] for i in inv if i["quantity"] > 0]
            if size and size.upper() not in in_stock:
                continue
            hits.append((score, ProductSummary(
                product_id=p["product_id"], name=p["name"], garment_type=p["garment_type"],
                price=p["price"], colors=p["colors"], sizes_in_stock=in_stock,
                total_stock=sum(i["quantity"] for i in inv),
            )))
    hits.sort(key=lambda h: -h[0])
    shown = [h[1] for h in hits[: max(1, min(limit, MAX_RESULTS))]]
    return SearchResults(total_matches=len(hits), returned=len(shown), products=shown)


def get_product_details(product_id: str) -> ProductCard | None:
    """Full details for one product, including stock per size. None if the id does not exist."""
    with get_db() as conn:
        row = conn.execute("SELECT * FROM catalogue WHERE product_id = ?", (product_id,)).fetchone()
        if row is None:
            return None
        return ProductCard.model_validate(product_dict(row, load_inventory(conn, product_id)))


def get_product_info(product_id: str) -> ProductInfo | None:
    """Description, colors and exact price for one product. None if the id does not exist."""
    with get_db() as conn:
        row = conn.execute("SELECT * FROM catalogue WHERE product_id = ?", (product_id,)).fetchone()
    return ProductInfo.model_validate(product_dict(row)) if row else None


def normalize_size(size: str) -> str:
    s = size.strip().upper().replace(" ", "").replace("-", "")
    aliases = {"XSMALL": "XS", "EXTRASMALL": "XS", "SMALL": "S", "MEDIUM": "M", "MED": "M", "LARGE": "L",
               "XLARGE": "XL", "EXTRALARGE": "XL", "XXLARGE": "XXL", "2XL": "XXL", "2X": "XXL"}
    return aliases.get(s, s)


def check_stock(product_id: str, size: str | None = None) -> StockReport | None:
    """Stock per size for one product, optionally answering for one requested size."""
    with get_db() as conn:
        row = conn.execute("SELECT product_id, name, price FROM catalogue WHERE product_id = ?", (product_id,)).fetchone()
        if row is None:
            return None
        inv = load_inventory(conn, product_id)
    sizes = [SizeStatus(size=i["size"], quantity=i["quantity"], in_stock=i["quantity"] > 0) for i in inv]
    report = StockReport(
        product_id=row["product_id"], name=row["name"], price=row["price"], sizes=sizes,
        sizes_in_stock=[s.size for s in sizes if s.in_stock],
        sizes_sold_out=[s.size for s in sizes if not s.in_stock],
        total_stock=sum(s.quantity for s in sizes),
    )
    if size:
        wanted = normalize_size(size)
        match = next((s for s in sizes if s.size == wanted), None)
        report.requested_size = wanted
        if match is None:
            report.requested_quantity, report.requested_in_stock = 0, False
            report.note = f"Size '{size}' is not offered. Available sizes: {', '.join(SIZE_ORDER)}."
        else:
            report.requested_quantity, report.requested_in_stock = match.quantity, match.in_stock
            if not match.in_stock:
                report.note = f"{wanted} is OUT OF STOCK for this product."
    return report


def list_garment_types() -> dict[str, int]:
    """Every garment type in the catalogue with its product count, plus the price range."""
    with get_db() as conn:
        rows = conn.execute("SELECT lower(garment_type) t, count(*) n FROM catalogue GROUP BY t ORDER BY n DESC").fetchall()
        lo, hi = conn.execute("SELECT min(price), max(price) FROM catalogue").fetchone()
    return {**{r["t"]: r["n"] for r in rows}, "_price_range": json.dumps([lo, hi])}


def catalogue_price_bounds() -> set[float]:
    """Lowest and highest catalogue prices, so 'from $32.00 to $98.00' style answers are allowed."""
    with get_db() as conn:
        lo, hi = conn.execute("SELECT min(price), max(price) FROM catalogue").fetchone()
    return {round(lo, 2), round(hi, 2)}


def get_cards(product_ids: list[str]) -> list[ProductCard]:
    """Look up cards for the ids the agent chose, silently dropping unknown ids."""
    cards = []
    for pid in dict.fromkeys(product_ids):
        card = get_product_details(pid)
        if card:
            cards.append(card)
    return cards[:MAX_RESULTS]
