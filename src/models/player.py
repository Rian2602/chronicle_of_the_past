"""Model pemain kultivator (GDD §17, §19.2)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

BASE_STATS: dict[str, int] = {
    "attack": 5,
    "defense": 5,
    "agility": 5,
    "intelligence": 5,
    "vitality": 5,
    "spirit": 5,
}
INJURY_STAT_PENALTY = 0.25


@dataclass
class Player:
    """Pemain dengan stat primer, tingkatan, insight, dan meridian."""

    name: str
    tier_id: str | None = None
    tier_order: int = 0
    insight: int = 0
    gold: int = 0
    meridian_buka: int = 0
    injury_days_remaining: int = 0
    background: str | None = None
    path: str | None = None
    stats: dict[str, int] = field(default_factory=lambda: dict(BASE_STATS))
    tier_bonus: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validasi rentang meridian 0–8 (GDD §17.3)."""
        if not 0 <= self.meridian_buka <= 8:
            raise ValueError("meridian_buka harus antara 0–8")

    @property
    def is_injured(self) -> bool:
        """Kembalikan True bila masih dalam masa cedera (GDD §4.1)."""
        return self.injury_days_remaining > 0

    @property
    def hp_max(self) -> int:
        """Hitung HP maksimum: 40 + vitality x 8 + bonus tingkatan."""
        return (
            40 + self.stats["vitality"] * 8 + self.tier_bonus.get("hp_max", 0)
        )

    @property
    def qi_max(self) -> int:
        """Hitung qi maksimum: basis 10 + meridian x 3 + bonus tingkatan.

        Kontribusi tingkatan diwujudkan lewat stat_bonus.qi_max di data
        (GDD §4.1: angka final hidup di data/cultivation/).
        """
        return 10 + self.meridian_buka * 3 + self.tier_bonus.get("qi_max", 0)

    @property
    def qi_regen(self) -> int:
        """Hitung regenerasi qi per giliran: 2 + meridian."""
        return 2 + self.meridian_buka

    @property
    def effective_stats(self) -> dict[str, int]:
        """Hitung stat efektif; seluruh stat turun 25% saat cedera."""
        if not self.is_injured:
            return dict(self.stats)
        return {
            key: int(value * (1 - INJURY_STAT_PENALTY))
            for key, value in self.stats.items()
        }

    def add_insight(self, amount: int) -> None:
        """Tambahkan pemahaman (XP kultivasi, §4.3)."""
        if amount < 0:
            raise ValueError("insight tidak boleh negatif")
        self.insight += amount

    def advance_day(self) -> None:
        """Kurangi sisa hari cedera; dipanggil sistem waktu game."""
        if self.injury_days_remaining > 0:
            self.injury_days_remaining -= 1

    def to_dict(self) -> dict[str, Any]:
        """Serialize ke dict save (skema §19.2 + ekstensi state cedera)."""
        return {
            "name": self.name,
            "background": self.background,
            "path": self.path,
            "tier": self.tier_id,
            "stats": dict(self.stats),
            "insight": self.insight,
            "gold": self.gold,
            "meridian_buka": self.meridian_buka,
            "injury_days_remaining": self.injury_days_remaining,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Player:
        """Buat Player dari dict save (tanpa rekonstruksi tier).

        tier_order dan tier_bonus dibangun ulang oleh GameState melalui
        cultivation.restore_tier (data-driven, GDD §4.1).
        """
        name = data.get("name")
        if not isinstance(name, str) or not name:
            raise ValueError("nama pemain tidak ada")
        return cls(
            name=name,
            background=data.get("background"),
            path=data.get("path"),
            tier_id=data.get("tier"),
            stats=dict(data.get("stats", BASE_STATS)),
            insight=data.get("insight", 0),
            gold=data.get("gold", 0),
            meridian_buka=data.get("meridian_buka", 0),
            injury_days_remaining=data.get("injury_days_remaining", 0),
        )
