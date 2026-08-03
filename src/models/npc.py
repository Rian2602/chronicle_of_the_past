from dataclasses import dataclass, field


@dataclass
class Npc:
    id: str
    name: str
    location: str
    role: str
    faction: str
    dialogs: list
    relationship: dict = field(default_factory=dict)
