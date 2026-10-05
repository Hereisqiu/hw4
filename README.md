# Campus Customs: Shopping Site and AI Assistant (HW4)

A customer-facing storefront for **Campus Customs** (officially licensed Yale apparel, 57 Broadway, New Haven) with an integrated shopping assistant, **Dan**.

- **Frontend:** React + Vite + TypeScript (`frontend/`), with a black-and-pink varsity design.
- **Backend:** Python FastAPI (`backend/main.py`) plus a **PydanticAI** agent in four files: `backend/prompts/prompt.md`, `backend/agent.py`, `backend/tools.py`, `backend/models.py`.
- **Model:** `gpt-5.6-luna` via the Portkey gateway.
- **Data:** a local SQLite catalogue, inventory and users (`data/campus_customs.db`). It is not in this repo; see below.

Shoppers can browse and filter products, register and log in, and chat with Dan. Dan quotes live prices and stock, fills the page with matching product cards, knows which product you're viewing, and remembers logged-in shoppers' conversations.

## 1. Add the data pack (not in git)

The database and product images are excluded by `.gitignore`. Put the data pack you were given in a `data/` folder at the project root, **next to `backend/` and `frontend/`**:

```
hw4/
├── backend/
├── frontend/
├── output/
└── data/                      ← create this folder
    ├── campus_customs.db      ← catalogue, inventory, users, chat_messages
    └── products/              ← product images (paths referenced by the catalogue)
        ├── basic-hoodie-big-yale.jpg
        └── …
```

The backend finds it automatically at `../data` relative to `backend/`, so no configuration is needed. If the folder is missing, the backend won't start (it serves images from `data/products/`).

## 2. Configure the API key

```bash
cp .env.example .env
```
Edit `.env` and set `PORTKEY_API_KEY`. The other values are optional:

| Variable | Default | Purpose |
|---|---|---|
| `PORTKEY_API_KEY` | (required) | Key for the Portkey AI gateway |
| `PORTKEY_BASE_URL` | `https://api.portkey.ai/v1` | Gateway URL |
| `MODEL_NAME` | `gpt-5.6-luna` | Model used by the agent |
| `SESSION_SECRET` | random per start | Signs login cookies. Set it to stay logged in across backend restarts. |

The backend also picks up a `.env` in any parent folder.

## 3. Run the backend (port 8000)

Requires Python 3.11+.

```bash
cd hw4
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd backend
uvicorn main:app --reload --port 8000
```

Check it at http://localhost:8000/api/health, which should return `{"status":"ok"}`.

## 4. Run the frontend (port 5173)

Requires Node 20+. Use a second terminal:

```bash
cd hw4/frontend
npm install
npm run dev
```

Open **http://localhost:5173**. The Vite dev server proxies `/api` and `/media` to the backend on port 8000, so start the backend first.

**Test account:** `test@campuscustoms.yale.edu` / `password`. You can also create your own on the **Create account** page.

## 5. Things to try

- **Products:** filter by category or "in stock in [size]", sort by price, and click any card for its detail page.
- **Chat** (bulldog button, bottom right):
  - "What hoodies do you have?" fills the page with hoodie cards.
  - On a product page, "Do you have this in pink?" or "Is this in stock in M?"
  - Logged in: close the tab, come back, and your chat history is restored.

## Project layout

```
hw4/
├── AI_prompts.md          # prompts given to the coding assistant, per problem
├── README.md
├── requirements.txt
├── .env.example           # placeholders only
├── .gitignore             # excludes .env, data/ (DB + images), node_modules, .venv
├── frontend/              # Vite React TypeScript app
├── backend/
│   ├── main.py            # FastAPI app: products, images, accounts, chat, history, rate limit
│   ├── agent.py           # PydanticAI agent: model, prompt, tool wiring, validator, audit trail
│   ├── models.py          # Pydantic types (tool results, chat API, agent output, audit)
│   ├── tools.py           # read-only catalogue/stock tools + SQLite helpers
│   └── prompts/
│       └── prompt.md      # system prompt: voice, tool rules, safety rules
└── output/
    ├── harness.md         # database, models, tools, safety rules, specs
    ├── design.md          # design write-up
    ├── usability.md       # four usability improvements
    ├── app_check.html     # test report (open by double-clicking)
    ├── app_check_images/  # screenshots linked from app_check.html
    └── audit_trail.json   # append-only log of agent runs
```

Full technical documentation is in [`output/harness.md`](output/harness.md).
