from dataclasses import dataclass, field


@dataclass
class Enemy:
    id: str
    name: str
    level: int
    stats: dict
    loot: list
    skills: list
    lore: str = ""
    reward: dict = field(default_factory=dict)
    behavior: str = "aggressive"
    weight: int = 1
    tags: list = field(default_factory=list)
