from dataclasses import dataclass, field


@dataclass
class Event:
    id: str
    trigger: list
    conditions: list = field(default_factory=list)
    actions: list = field(default_factory=list)
