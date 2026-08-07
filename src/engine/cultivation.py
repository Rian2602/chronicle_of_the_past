"""Engine kultivasi: data tingkatan, insight, dan breakthrough.

Acuan desain: GDD §4.1 (tingkatan & breakthrough), §4.3 (insight),
§14.3 (skema data), §17.2 (stat turunan).
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.models.player import Player

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "cultivation"
BASE_SUCCESS_RATE = 55
RATE_CAP = 90
SUPPORT_STAT_BONUS = 5
PILL_BONUS_MIN = 10
PILL_BONUS_MAX = 20
INJURY_DAYS = 2
INNER_DEMON_CHANCE = 0.30


@dataclass(frozen=True)
class CultivationTier:
    """Tingkatan kultivasi (GDD §14.3)."""

    id: str
    name: str
    order: int
    insight_required: int
    stat_bonus: dict[str, int]
    unlocks: list[str]


@dataclass(frozen=True)
class BreakthroughResult:
    """Hasil percobaan breakthrough (GDD §4.1)."""

    success: bool
    tier_id: str | None = None
    unlocks: tuple[str, ...] = ()
    injury_days: int = 0
    inner_demon: bool = False
    rate: int = 0


def load_tiers(data_dir: Path = DATA_DIR) -> list[CultivationTier]:
    """Muat semua tingkatan dari data/cultivation/, urut berdasarkan order."""
    tiers: list[CultivationTier] = []
    for path in sorted(data_dir.glob("*.json")):
        raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        tiers.append(CultivationTier(**raw))
    return sorted(tiers, key=lambda tier: tier.order)


def next_tier(
    player: Player, tiers: list[CultivationTier]
) -> CultivationTier | None:
    """Kembalikan tingkatan berikutnya yang dituju, atau None di puncak."""
    target_order = player.tier_order + 1
    for tier in tiers:
        if tier.order == target_order:
            return tier
    return None


def can_breakthrough(player: Player, tiers: list[CultivationTier]) -> bool:
    """Kembalikan True bila insight mencapai ambang tingkatan berikutnya."""
    tier = next_tier(player, tiers)
    return tier is not None and player.insight >= tier.insight_required


def breakthrough_rate(support_stat: int = 0, pill_bonus: int = 0) -> int:
    """Hitung tingkat sukses: 55% + 5%/poin stat jalur + pil, cap 90%.

    Memunculkan ValueError bila argumen bukan bilangan bulat atau
    pill_bonus bukan 0 / di luar rentang 10–20.
    """
    if not isinstance(support_stat, int) or not isinstance(pill_bonus, int):
        raise ValueError("support_stat dan pill_bonus harus bilangan bulat")
    if pill_bonus and not PILL_BONUS_MIN <= pill_bonus <= PILL_BONUS_MAX:
        raise ValueError("pill_bonus harus 0 atau antara 10–20")
    bonus = support_stat * SUPPORT_STAT_BONUS + pill_bonus
    return min(RATE_CAP, BASE_SUCCESS_RATE + bonus)


def _apply_stat_bonus(player: Player, tier: CultivationTier) -> None:
    """Terapkan stat_bonus tingkatan ke stat primer dan bonus turunan."""
    for key, value in tier.stat_bonus.items():
        if key in ("hp_max", "qi_max"):
            player.tier_bonus[key] = player.tier_bonus.get(key, 0) + value
        else:
            player.stats[key] = player.stats.get(key, 0) + value


def restore_tier(player: Player, tiers: list[CultivationTier]) -> None:
    """Rekonstruksi tier_order & tier_bonus dari data (dipanggil saat load).

    Stats disimpan apa adanya di save; hanya urutan dan bonus turunan
    (hp_max/qi_max) yang dihitung ulang dari data/cultivation (GDD §4.1:
    angka final hidup di data). Bila data tier di-rebalance, bonus baru
    berlaku untuk save lama.
    """
    ordered = sorted(tiers, key=lambda tier: tier.order)
    player.tier_order = 0
    player.tier_bonus = {}
    if player.tier_id is None:
        return
    target = next((tier for tier in ordered if tier.id == player.tier_id), None)
    if target is None:
        raise ValueError(f"tier tidak dikenal di data: {player.tier_id}")
    for tier in ordered:
        if tier.order > target.order:
            break
        for key, value in tier.stat_bonus.items():
            if key in ("hp_max", "qi_max"):
                player.tier_bonus[key] = player.tier_bonus.get(key, 0) + value
    player.tier_order = target.order


def attempt_breakthrough(
    player: Player,
    tiers: list[CultivationTier],
    *,
    rng: Any = None,
    support_stat: int = 0,
    pill_bonus: int = 0,
) -> BreakthroughResult:
    """Coba breakthrough: sukses naik tier, gagal cedera + 30% inner demon.

    Memunculkan ValueError bila syarat insight belum terpenuhi, pemain
    sudah di puncak kultivasi, atau pill_bonus di luar rentang 10–20.
    """
    tier = next_tier(player, tiers)
    if tier is None:
        raise ValueError("sudah mencapai puncak kultivasi")
    if player.insight < tier.insight_required:
        raise ValueError("insight belum mencapai ambang tingkatan berikutnya")
    generator = rng if rng is not None else random
    rate = breakthrough_rate(support_stat, pill_bonus)
    if generator.random() * 100 < rate:
        _apply_stat_bonus(player, tier)
        player.tier_id = tier.id
        player.tier_order = tier.order
        return BreakthroughResult(
            success=True,
            tier_id=tier.id,
            unlocks=tuple(tier.unlocks),
            rate=rate,
        )
    player.injury_days_remaining = INJURY_DAYS
    inner_demon = generator.random() < INNER_DEMON_CHANCE
    return BreakthroughResult(
        success=False,
        injury_days=INJURY_DAYS,
        inner_demon=inner_demon,
        rate=rate,
    )
