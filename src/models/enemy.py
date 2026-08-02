from dataclasses import dataclass


@dataclass
class Enemy:
    id: str
    name: str
    level: int
    stats: dict
    loot: list
    skills: list
    lore: str = ""
