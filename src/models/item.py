from dataclasses import dataclass, field


@dataclass
class Item:
    id: str
    name: str
    type: str
    slot: str | None = None
    modifiers: dict = field(default_factory=dict)
    price: int = 0
    description: str = ""
    heal: int = 0
    heal_mp: int = 0
    heal_full: bool = False
    escape: bool = False
    quest_flag: str | None = None
