from dataclasses import dataclass


@dataclass
class Offer:
    title: str
    url: str
    store: str
    price: str | None = None
    snippet: str | None = None
    delivery_days: int | None = None
