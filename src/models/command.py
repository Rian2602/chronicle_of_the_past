from dataclasses import dataclass, field


@dataclass
class Command:
    action: str
    args: list = field(default_factory=list)
    index: int | None = None
