from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

from src.core.randomizer import Randomizer
from src.models.enemy import Enemy
from src.models.player import Player


class CombatAction(str, Enum):
    ATTACK = "attack"
    SKILL = "skill"
    MAGIC = "magic"
    ITEM = "item"
    OBSERVE = "observe"
    ESCAPE = "escape"
    DEFEND = "defend"


class CombatResult(str, Enum):
    VICTORY = "victory"
    DEFEAT = "defeat"
    ESCAPED = "escaped"


@dataclass
class StatusEffect:
    kind: str
    duration: int
    power: int


@dataclass
class DamageResult:
    damage: int
    critical: bool
    missed: bool


LootResolver = Callable[[Enemy, Randomizer], list[dict]]


@dataclass
class CombatState:
    round_no: int
    turn_order: list
    current_index: int
    over: bool
    result: CombatResult | None
    log: list[str]
    observe_used: bool
    player_defending: bool
    enemy_defending: bool
    statuses: dict[str, list[StatusEffect]]
    xp: int = 0
    gold: int = 0
    loot: list = field(default_factory=list)
    observe_info: str | None = None
    player: Player | None = None
    enemy: Enemy | None = None
    randomizer: Randomizer | None = None
    skills: dict = field(default_factory=dict)
    loot_resolver: LootResolver | None = None
    max_status_duration: int = 10
    items: dict = field(default_factory=dict)
