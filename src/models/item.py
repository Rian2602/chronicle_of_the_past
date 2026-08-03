from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Item:
    id: str
    name: str
    type: str
    slot: Optional[str] = None
    modifiers: dict = field(default_factory=dict)
    price: int = 0
    description: str = ""
    heal: int = 0
