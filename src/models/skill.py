from dataclasses import dataclass, field


@dataclass
class Skill:
    id: str
    name: str
    type: str
    cost: int
    target: str
    power: int = 0
    effects: list = field(default_factory=list)
    requires: dict = field(default_factory=dict)
    description: str = ""
