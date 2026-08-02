from dataclasses import dataclass


@dataclass
class Npc:
    id: str
    name: str
    location: str
    role: str
    faction: str
    dialogs: list
