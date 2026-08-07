"""Rekan tim: Companion & peringkat bond (GDD §20.3)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

COMPANION_DIR = Path(__file__).resolve().parents[2] / "data" / "companions"


@dataclass
class Companion:
    """Satu rekan tim (cerita atau binatang roh, GDD §20).

    Progresi memakai bond XP terpisah; naik peringkat rekan (bukan
    breakthrough seperti protagonis, §20.3). HP/qi persisten di dunia
    seperti Player (§17.2).

    Attributes:
        id: ID unik rekan, snake_case (mis. "lin_wei").
        name: Nama tampilan dalam Bahasa Indonesia.
        tier: Tier rekan saat rekrut.
        element: Elemen rekan (siklus §6.2).
        stats: Stat dasar (attack/defense/agility/intelligence/
            vitality/spirit + hp/qi).
        skills: Teknik yang dikuasai (data/techniques/).
        bond_xp: XP ikatan terpisah dari insight protagonis (§20.3).
        rank: Peringkat rekan saat ini (1-3 per arc), diset konten.
        hp: HP saat ini di dunia (dibawa ke pertarungan).
        qi: Qi saat ini di dunia.
        evolution: Evolusi sekali (GDD §20.3): dict trigger_tier ->
            evolved_id. Rekan hasil evolusi tidak punya field ini.
    """

    id: str
    name: str
    tier: str
    element: str
    stats: dict[str, int]
    skills: list[str] = field(default_factory=list)
    bond_xp: int = 0
    rank: int = 1
    hp: int | None = None
    qi: int | None = None
    evolution: dict[str, Any] | None = None

    @property
    def hp_max(self) -> int:
        """HP maksimum dari stat (skema §14.3, sama dengan enemy)."""
        return int(self.stats.get("hp", 1))

    @property
    def qi_max(self) -> int:
        """Qi maksimum dari stat."""
        return int(self.stats.get("qi", 0))

    def to_dict(self) -> dict[str, Any]:
        """Serialize untuk save (schema §19.2, field party)."""
        result = {
            "id": self.id,
            "name": self.name,
            "tier": self.tier,
            "element": self.element,
            "stats": dict(self.stats),
            "skills": list(self.skills),
            "bond_xp": self.bond_xp,
            "rank": self.rank,
            "hp": self.hp,
            "qi": self.qi,
        }
        if self.evolution:
            result["evolution"] = dict(self.evolution)
        return result

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> Companion:
        """Bangun Companion dari dict save; backfill field baru."""
        return cls(
            id=raw["id"],
            name=raw.get("name", raw["id"]),
            tier=raw.get("tier", "qi_condensation"),
            element=raw.get("element", "netral"),
            stats=dict(raw.get("stats", {})),
            skills=list(raw.get("skills", [])),
            bond_xp=int(raw.get("bond_xp", 0)),
            rank=int(raw.get("rank", 1)),
            hp=raw.get("hp"),
            qi=raw.get("qi"),
            evolution=raw.get("evolution"),
        )


def load_companions(data_dir: Path = COMPANION_DIR) -> list[Companion]:
    """Muat semua rekan dari data/companions/, urut berdasarkan id.

    Args:
        data_dir: Direktori berisi JSON rekan (default data/companions/).

    Returns:
        Daftar Companion dari seluruh file JSON di direktori.

    Raises:
        KeyError: Jika sebuah file JSON tidak punya kunci ``id``.
    """
    companions: list[Companion] = []
    for path in sorted(data_dir.glob("*.json")):
        raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        companions.append(Companion.from_dict(raw))
    return companions


def load_companion(
    companion_id: str, data_dir: Path = COMPANION_DIR
) -> Companion:
    """Muat satu rekan berdasarkan id.

    Args:
        companion_id: ID rekan (snake_case).
        data_dir: Direktori berisi JSON rekan.

    Returns:
        Companion yang cocok dengan id.

    Raises:
        ValueError: Jika tidak ada rekan dengan id tersebut.
    """
    for companion in load_companions(data_dir):
        if companion.id == companion_id:
            return companion
    raise ValueError(f"rekan tidak dikenal: {companion_id}")
