from dataclasses import dataclass
from typing import Optional


@dataclass
class Quest:
    id: str
    title: str
    type: str
    description: str
    requirements: list
    rewards: dict
    flags_on_complete: list
    next: Optional[str] = None
