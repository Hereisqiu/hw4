# Usability Improvements: Campus Customs

Four improvements: two on the frontend (easier, more attractive shopping) and two on the agent/backend (accuracy, safety, cost).

---

## Frontend 1: Product filters, sorting and stock badges

**What I added**
- **Category chips** on the Products page (All, Hoodies, Crewnecks, Quarter-zips, T-shirts, Fleece & jackets, Other), each showing its item count. The catalogue's 15+ inconsistent `garment_type` strings ("pullover hoodie", "full-zip hooded sweatshirt", "short-sleeve T-shirt" vs "t-shirt") are grouped into these shopper-friendly categories in `frontend/src/categories.ts`.
- **"In stock in [size]"** filter: only shows products with quantity > 0 in that size.
- **Sort**: name A–Z, price low→high, price high→low, most in stock.
- **Stock badges** on cards: "Only 2 left in L" (pink) when a filtered size has ≤ 5 units, "Sold out in M", and "Limited sizes" / "Sold out" when no size is filtered.
- Filters are stored in the URL (`/products?category=hoodies&size=L&sort=price-desc`), so they survive the Back button from a product page and can be shared or bookmarked. "Reset filters" clears them, and an empty-state message suggests asking the assistant.
- Backend support: `GET /api/products` now includes each product's per-size `inventory` and `total_stock`.

**Why it helps shoppers and the business**
- With 102 products in one grid, shoppers had to scroll or guess search words. Chips get them to "hoodies" in one click.
- Size is the #1 reason a shopper bounces: falling for a hoodie and then finding their size sold out. The size filter hides those dead ends up front, so fewer frustrated visits and abandoned carts.
- "Only 2 left" badges create honest urgency, which tends to raise conversion. They also show the store is accurate about stock, which builds trust.
- Price sorting helps budget shoppers (students, gift buyers) find options fast.

**Check it:** open Products, click **Hoodies**, choose **In stock in → L**, and sort **Price: high to low**. You'll see 20 items (matches the DB), Brooks Brothers $88.00 first, and "Only 5 left in L"-style badges.

---

## Frontend 2: Context-aware suggested questions in the chat

**What I added**
- One-tap suggestion chips above the chat input that send a question immediately. They change with the page:
  - On a **product page**: "Is this in stock in M?", "What colors does this come in?", "Show me similar items". These use Problem 8's page context, so "this" means the product being viewed.
  - **Elsewhere**: "What hoodies do you have?", "Gifts under $40", "Anything for The Game?"
- They hide while the assistant is answering, and the input placeholder changes to "Ask about this product…" on product pages.

**Why it helps shoppers and the business**
- Many visitors don't know what a shop chatbot can do, and staring at an empty box is a barrier. The chips show what's possible (stock, colors, gifts, categories) and get a useful answer in one tap.
- They're especially helpful on mobile, where typing is slow.
- The suggestions steer people to things the assistant does well and accurately, so they see good answers instead of off-topic attempts. "Show me similar items" and "Gifts under $40" encourage further browsing, cross-selling and gift purchases.

**Check it:** open any product (e.g. Fencing Left Chest Hoodie) and open the chat. Tap **What colors does this come in?** → "navy blue". Tap **Is this in stock in M?** → "in stock in M, with 15 available" (matches the DB).

---

## Agent/backend 1: Fact-checking output validator (accuracy)

**What I added**
- A PydanticAI `@agent.output_validator` (`check_reply_facts` in `backend/agent.py`) that inspects every reply **before** it reaches the shopper:
  1. **Unknown products:** if `product_ids` contains an id that isn't in the catalogue, it raises `ModelRetry` ("These product_ids do not exist… use only ids returned by tools").
  2. **Price check:** every `$` amount in the reply text is extracted and compared with the real DB prices of the products in `product_ids` (plus the product on the current page and the catalogue's min/max price, for "from $32.00 to $98.00"-style answers). A price that doesn't match (e.g. "$59.99" for a $68.00 hoodie) triggers `ModelRetry`, telling the model to look up the price with `get_product_info` and quote it exactly.
- The agent gets up to 2 retries (`retries=2`). The model sees the error and fixes its answer in the same request.

**Why it helps shoppers and the business**
- A chatbot that quotes the wrong price is a real business risk: angry customers at checkout, pressure to honor the wrong price, and lost trust. The prompt already says "never invent prices", but a prompt is a request, not a guarantee. This check makes it enforced in code.
- It also catches made-up products that would otherwise show as missing cards.
- It only costs extra model calls in the rare case it fires.

**Check it:** this is a unit-level check (`check_reply_facts` called directly):
- "Basic Hoodie Big Yale is $68.00" → passes.
- "…is $59.99" → retry: "quotes price(s) $59.99 that do not match the database price…".
- `product_ids=["made-up-id"]` → retry.
- "Prices range from $32.00 to $98.00" → passes.

In the running app every reply goes through it, and all prices quoted in testing matched the DB.

---

## Agent/backend 2: Chat rate limiting and per-turn usage logging (safety & cost)

**What I added**
- **Rate limiter** (`check_rate_limit` in `backend/main.py`) on `POST /api/chat`: a sliding window of **8 messages per minute and 60 per hour**.
  - Logged-in shoppers are keyed by user id, guests by IP.
  - Over the limit, the API returns **HTTP 429** with a friendly message ("You're sending messages quickly. Please wait N seconds…") and a `Retry-After` header, and the chat widget shows that message.
  - The check runs **before** the agent is called, so blocked requests cost nothing.
- **Usage logging**: each agent run logs its duration, model requests, tool calls, input/output tokens and history length, e.g.:
  `chat turn: 2.9s, 2 model requests, 1 tool calls, 1628 input + 87 output tokens, history=2 turns`

**Why it helps shoppers and the business**
- Every chat message is a paid LLM call. Without a limit, a script or abusive user could run up the Portkey bill or slow the assistant down for everyone. The limits are generous for a real shopper (8 per minute is faster than anyone types) but stop floods and automated prompt-injection probing.
- The usage log gives the business data on cost per conversation, slow turns and tool-call patterns. That shows where to optimise (e.g. history length drives input tokens) and lets them budget the assistant as traffic grows.

**Check it:** the backend console shows a `chat turn:` line for every message. Calling `check_rate_limit` 10 times from one IP gives 8 OK, then 429 "Please wait 60 seconds" with `Retry-After: 60`, while a different user is still allowed.
