# buyer-agent — CLAUDE.md

## ToDo System — Repository Map

This repo is part of the **ToDo** personal productivity system. All repositories:

| Repo | Type | Status | Description |
|------|------|--------|-------------|
| [paulalexeevich/todo-bot](https://github.com/paulalexeevich/todo-bot) | UI + Core | active | Telegram bot, Next.js dashboard, data-api — live system |
| [paulalexeevich/todo-api](https://github.com/paulalexeevich/todo-api) | Core | planned | Future standalone core (not yet live) |
| [paulalexeevich/discovery-agent](https://github.com/paulalexeevich/discovery-agent) | Agent | active | Standalone idea validation pipeline |
| [paulalexeevich/buyer-agent](https://github.com/paulalexeevich/buyer-agent) | Agent | current repo | Standalone product search pipeline |

---

## What this agent does

Searches for products to buy given a task description. Location-aware and deadline-aware — adjusts search queries and filters results based on where the user is and how urgently they need the item.

**Input**: task text, search query, strategy, deadline, current location, home location
**Output**: ranked list of offers with price, store, URL, and estimated delivery days

Called by `todo-api` when a `shopping`-type task is ready to process.

---

## Architecture

```
POST /run
    │
    ▼
BuyerGraph (LangGraph)
    └── buyer_node
            │
        DuckDuckGo search (ddgs)
        1–2 queries based on strategy
            │
        Deduplicate by URL
        Filter by deadline vs delivery estimate
        Sort by delivery_days ASC, priced first
            │
        list[Offer]
```

---

## Project Structure

```
buyer-agent/
├── CLAUDE.md
├── .env.example
├── .env                   # gitignored
├── Dockerfile
├── requirements.txt
├── main.py                # FastAPI app — POST /run, GET /health
├── config.py              # pydantic-settings → settings singleton
├── db/
│   └── models.py          # Offer dataclass
└── agent/
    ├── buyer_graph.py     # BuyerState TypedDict + compiled LangGraph
    ├── deadline.py        # LLM deadline parser → DeadlineInfo
    └── nodes/
        └── buyer.py       # DuckDuckGo search, delivery estimation, offer ranking
```

---

## API

### `GET /health`
Returns `{"status": "ok"}`.

### `POST /run`
```json
// Request
{
  "task_text": "Buy a mechanical keyboard",
  "search_query": "mechanical keyboard",
  "strategy": "week",
  "deadline_days": 5,
  "current_location": "Budapest, Hungary",
  "home_location": "Budapest, Hungary"
}

// Response
{
  "offers": [
    {
      "title": "...",
      "price": "€89.99",
      "store": "alza.hu",
      "url": "https://...",
      "snippet": "...",
      "delivery_days": 2
    }
  ]
}
```

`strategy` values and their meaning:
| Strategy | When | Search behaviour |
|----------|------|-----------------|
| `asap` | deadline = today | Prioritises local stores + in-stock |
| `fast` | deadline ≤ 3 days | Local + fast EU delivery |
| `week` | deadline ≤ 7 days | Local + EU online |
| `flexible` | deadline > 7 days | Wide search, best price |
| `any` | no deadline | Global search |

---

## Data Models

```python
@dataclass
class Offer:
    title: str
    url: str
    store: str
    price: str | None       # extracted price string e.g. "€49.99"
    snippet: str | None
    delivery_days: int | None  # 0=pickup, 2=local, 5=EU, 10=global

class BuyerState(TypedDict):
    task_text: str
    search_query: str
    strategy: str
    deadline_days: int | None
    current_location: str
    home_location: str
    offers: list[Offer]
```

---

## Deadline Parsing (`agent/deadline.py`)

Exposed internally — `todo-api` can also call `POST /parse-deadline` if needed (not yet implemented as an endpoint, logic lives in `agent/deadline.py`).

```python
@dataclass
class DeadlineInfo:
    date: date | None
    days_until: int | None
    label: str          # human-readable: "today", "Fri Apr 4", "no rush"
    strategy: str       # asap | fast | week | flexible | any
```

---

## LLM Providers

Used only for deadline parsing (`agent/deadline.py`).

| Provider | Model | Env var |
|----------|-------|---------|
| `gemini` (default) | `gemini-3.1-flash-lite-preview` | `GOOGLE_GEMINI_API_KEY` |
| `claude` | `claude-sonnet-4-6` | `ANTHROPIC_API_KEY` |
| `openai` | `gpt-4o` | `OPENAI_API_KEY` |

---

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `LLM_PROVIDER` | `gemini` (default) \| `claude` \| `openai` |
| `GOOGLE_GEMINI_API_KEY` | Required if `LLM_PROVIDER=gemini` |
| `ANTHROPIC_API_KEY` | Required if `LLM_PROVIDER=claude` |
| `OPENAI_API_KEY` | Required if `LLM_PROVIDER=openai` |
| `HOME_LOCATION` | Fallback location if not provided in request |

---

## Running Locally

```bash
cp .env.example .env
# fill in .env

python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

uvicorn main:app --reload --port 8003
```

## Running with Docker

```bash
docker build -t buyer-agent .
docker run --env-file .env -p 8003:8003 buyer-agent
```

---

## Code Conventions

- All async — blocking DuckDuckGo calls wrapped in `asyncio.to_thread`
- `config.py` imported as `from config import settings` — instantiated once
- LangGraph graph compiled once at import time in `agent/buyer_graph.py`
- Secrets never logged
