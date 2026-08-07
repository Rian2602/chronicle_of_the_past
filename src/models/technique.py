"""Model teknik kultivasi (GDD §14.3)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Technique:
    """Teknik yang dipakai dalam pertarungan (skema §14.3)."""

    id: str
    name: str
    path: str
    element: str
    type: str
    qi_cost: int
    power: int
    effects: list[dict] = field(default_factory=list)
    requires: dict[str, str] = field(default_factory=dict)

    @property
    def is_physical(self) -> bool:
        """Kembalikan True bila teknik bertipe fisik (stat inti = attack)."""
        return self.type == "physical"
