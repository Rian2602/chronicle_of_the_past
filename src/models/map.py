from dataclasses import dataclass, field


@dataclass
class Map:
    id: str
    name: str
    region: str
    threat_level: int
    description: str
    ascii_art: str
    exits: list
    npcs: list
    enemy_pool: list
    time_effects: dict = field(default_factory=dict)
