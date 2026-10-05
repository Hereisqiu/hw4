"""Pydantic types shared by the chat API, the agent and its tools."""

from typing import Literal

from pydantic import BaseModel, Field


class SizeStock(BaseModel):
    size: str
    quantity: int


class ProductCard(BaseModel):
    """A product as shown on a card in the chat or on the page."""

    product_id: str
    name: str
    garment_type: str
    price: float
    colors: list[str]
    image_url: str
    description: str
    inventory: list[SizeStock] = []
    total_stock: int = 0


class ProductSummary(BaseModel):
    """Compact search hit returned to the agent by `search_products`."""

    product_id: str
    name: str
    garment_type: str
    price: float
    colors: list[str]
    sizes_in_stock: list[str]
    total_stock: int


class SearchResults(BaseModel):
    """Returned by `search_products`: the hits shown, plus how many matched in total."""

    total_matches: int
    returned: int
    products: list[ProductSummary]


class ShopReply(BaseModel):
    """Structured output the agent must produce for every turn."""

    reply: str = Field(description="Friendly answer to the customer in Markdown. Prices and stock must come from tools.")
    product_ids: list[str] = Field(
        default_factory=list,
        description="product_id values (from tool results) of items to display as cards on the page; empty if none are relevant.",
    )
    results_title: str | None = Field(
        default=None,
        description='Short heading for the cards shown on the page, e.g. "Hoodies" or "Navy crewnecks under $60". Null when product_ids is empty.',
    )


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)
    product_ids: list[str] = Field(default_factory=list, max_length=30)


class PageContext(BaseModel):
    """What the shopper is looking at when they send a message."""

    path: str = Field(default="/", max_length=200)
    product_id: str | None = Field(default=None, max_length=120)


class CustomerProfile(BaseModel):
    """The only customer fields the agent ever sees (never the password hash)."""

    name: str
    first_name: str | None
    email: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    # Used for guests only; logged-in history is loaded from the database.
    history: list[ChatTurn] = Field(default_factory=list, max_length=20)
    page: PageContext = Field(default_factory=PageContext)


class ChatResponse(BaseModel):
    reply: str
    results_title: str | None = None
    products: list[ProductCard]


class ProductInfo(BaseModel):
    """Description and price for one product (no stock), returned by `get_product_info`."""

    product_id: str
    name: str
    garment_type: str
    description: str
    colors: list[str]
    price: float


class SizeStatus(BaseModel):
    size: str
    quantity: int
    in_stock: bool


class StockReport(BaseModel):
    """Stock for one product, returned by `check_stock`.

    When a size is requested, `requested_size`, `requested_quantity` and
    `requested_in_stock` answer it directly so the model cannot misread the table.
    """

    product_id: str
    name: str
    price: float
    sizes: list[SizeStatus]
    sizes_in_stock: list[str]
    sizes_sold_out: list[str]
    total_stock: int
    requested_size: str | None = None
    requested_quantity: int | None = None
    requested_in_stock: bool | None = None
    note: str | None = None


class StoredMessage(BaseModel):
    """A saved chat message as returned by GET /api/chat/history."""

    id: int
    role: Literal["user", "assistant"]
    content: str
    products: list[ProductCard] = []
    created_at: str


class AuditStep(BaseModel):
    """One step inside an agent run: a tool call, its result, or a validator retry."""

    time: str
    kind: Literal["tool_call", "tool_result", "retry"]
    tool: str | None = None
    detail: str


class AuditEntry(BaseModel):
    """One chat turn in output/audit_trail.json."""

    run_id: str
    started_at: str
    finished_at: str
    duration_s: float
    model: str
    user: str  # "user:<id>" or "guest" (no email, no password data)
    page: str | None
    message: str
    history_turns: int
    steps: list[AuditStep]
    tools_used: list[str]
    model_requests: int
    input_tokens: int
    output_tokens: int
    stop_reason: Literal["final_result", "content_filter", "request_limit", "output_retries_exhausted", "error"]
    error: str | None = None
    reply: str | None = None
    product_ids: list[str] = []
