"""Pembungkus unit pertarungan: pemain, rekan & musuh (GDD §6)."""

from __future__ import annotations

from dataclasses import dataclass, field

from src.models.enemy import Enemy
from src.models.party import Companion
from src.models.player import Player

ENEMY_QI_REGEN = 2
COMPANION_QI_REGEN = 2


@dataclass(eq=False)
class Combatant:
    """Unit dalam pertarungan dengan hp/qi saat ini dan status (§6)."""

    name: str
    element: str
    stats: dict[str, int]
    hp_max: int
    qi_max: int
    qi_regen: int
    skills: list[str] = field(default_factory=list)
    behavior: str = "aggressive"
    is_boss: bool = False
    hp: int = field(init=False)
    qi: int = field(init=False)
    statuses: dict[str, dict[str, int]] = field(default_factory=dict)
    defending: bool = False

    def __post_init__(self) -> None:
        """Inisialisasi hp/qi penuh di awal pertarungan."""
        self.hp = self.hp_max
        self.qi = self.qi_max

    @property
    def is_alive(self) -> bool:
        """Kembalikan True bila unit belum KO."""
        return self.hp > 0

    def take_damage(self, amount: int, *, defend_reduces: bool = True) -> int:
        """Kurangi hp (min 0); damage langsung berkurang 50% saat defend."""
        if amount < 0:
            amount = 0
        if self.defending and defend_reduces:
            amount //= 2
        self.hp = max(0, self.hp - amount)
        return amount


def combatant_from_player(
    player: Player,
    skills: list[str] | None = None,
    element: str = "netral",
) -> Combatant:
    """Buat Combatant dari Player; stat efektif memperhitungkan cedera.

    hp/qi saat ini diwarisi dari Player (None berarti penuh), sehingga
    luka di dunia ikut terbawa ke pertarungan (GDD §17.2, §20.4).
    """
    combatant = Combatant(
        name=player.name,
        element=element,
        stats=dict(player.effective_stats),
        hp_max=player.hp_max,
        qi_max=player.qi_max,
        qi_regen=player.qi_regen,
        skills=list(skills or []),
    )
    combatant.hp = player.hp if player.hp is not None else combatant.hp_max
    combatant.qi = player.qi if player.qi is not None else combatant.qi_max
    return combatant


def combatant_from_companion(companion: Companion) -> Combatant:
    """Buat Combatant dari Companion; luka di dunia ikut terbawa (§20.4).

    HP/qi saat ini diwarisi dari Companion (None berarti penuh).
    """
    combatant = Combatant(
        name=companion.name,
        element=companion.element,
        stats={
            key: value
            for key, value in companion.stats.items()
            if key not in ("hp", "qi")
        },
        hp_max=companion.hp_max,
        qi_max=companion.qi_max,
        qi_regen=COMPANION_QI_REGEN,
        skills=list(companion.skills),
    )
    if companion.hp is not None:
        combatant.hp = companion.hp
    if companion.qi is not None:
        combatant.qi = companion.qi
    return combatant


def combatant_from_enemy(enemy: Enemy) -> Combatant:
    """Buat Combatant dari data Enemy (skema §14.3)."""
    stats = {
        key: value
        for key, value in enemy.stats.items()
        if key not in ("hp", "qi")
    }
    return Combatant(
        name=enemy.name,
        element=enemy.element,
        stats=stats,
        hp_max=enemy.stats["hp"],
        qi_max=enemy.stats["qi"],
        # Regen qi musuh: default 2 (skema §14.3 tidak memuat qi_regen).
        qi_regen=ENEMY_QI_REGEN,
        skills=list(enemy.skills),
        behavior=enemy.behavior,
        is_boss=enemy.is_boss,
    )
