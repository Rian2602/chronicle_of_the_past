from dataclasses import dataclass, field


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
    xp_bonus: float = 1.0


def effective_stat(player, stat: str) -> int:
    """Menghitung stat efektif dengan menambahkan base_stats dan attribute_bonuses."""
    return player.base_stats.get(stat, 0) + player.attribute_bonuses.get(stat, 0)


def max_hp(player: Player) -> int:
    return effective_stat(player, "hp")


def max_mp(player: Player) -> int:
    return effective_stat(player, "mp")
