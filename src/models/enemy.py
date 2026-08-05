"""Model musuh (GDD §14.3)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Enemy:
    """Musuh dalam pertarungan (skema §14.3)."""

    id: str
    name: str
    tier: str
    element: str
    behavior: str
    stats: dict[str, int]
    skills: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    requires_flag: str | None = None

    @property
    def is_boss(self) -> bool:
        """Kembalikan True bila musuh ber-tag boss (GDD §11)."""
        return "boss" in self.tags
