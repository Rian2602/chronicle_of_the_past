from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Player:
    name: str
    class_id: str
    hp: int
    mp: int
    base_stats: dict
    attribute_bonuses: dict = field(default_factory=dict)
    level: int = 1
    xp: int = 0
    gold: int = 0
    skill_points: int = 0
    equipped: dict = field(default_factory=dict)
    inventory: list = field(default_factory=list)
    reputation: dict = field(default_factory=dict)
    relationship: dict = field(default_factory=dict)
    flags: dict = field(default_factory=dict)
    quests_active: dict = field(default_factory=dict)
    quests_done: list = field(default_factory=list)
    memories: list = field(default_factory=list)
    learned_skills: list = field(default_factory=list)


def max_hp(player: Player) -> int:
    return player.base_stats.get("hp", 0) + player.attribute_bonuses.get("hp", 0)


def max_mp(player: Player) -> int:
    return player.base_stats.get("mp", 0) + player.attribute_bonuses.get("mp", 0)
