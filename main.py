from fastapi import FastAPI
from pydantic import BaseModel

from agent.buyer_graph import buyer_graph
from config import settings

app = FastAPI(title="buyer-agent")


class RunRequest(BaseModel):
    task_text: str
    search_query: str = ""
    strategy: str = "any"          # asap | fast | week | flexible | any
    deadline_days: int | None = None
    current_location: str = ""
    home_location: str = ""


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/run")
async def run(body: RunRequest):
    home = body.home_location or settings.home_location
    current = body.current_location or home

    state = await buyer_graph.ainvoke({
        "task_text": body.task_text,
        "search_query": body.search_query or body.task_text,
        "strategy": body.strategy,
        "deadline_days": body.deadline_days,
        "current_location": current,
        "home_location": home,
        "offers": [],
    })

    offers = state.get("offers", [])
    return {
        "offers": [
            {
                "title": o.title,
                "price": o.price,
                "store": o.store,
                "url": o.url,
                "snippet": o.snippet,
                "delivery_days": o.delivery_days,
            }
            for o in offers
        ]
    }
