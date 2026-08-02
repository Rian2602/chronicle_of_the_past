def xp_to_next(level: int) -> int:
    return 50 * level


def gain_xp(player, amount: int, randomizer=None) -> list:
    player.xp += amount
    levels = []
    while player.xp >= xp_to_next(player.level):
        player.xp -= xp_to_next(player.level)
        player.level += 1
        levels.append(player.level)
    return levels


LEVEL_CHOICES = [
    ("attack", 2),
    ("defense", 2),
    ("agility", 2),
    ("intelligence", 2),
    ("hp", 15),
    ("mp", 10),
    ("skill_point", 1),
]

_VALID_KEYS = {choice[0] for choice in LEVEL_CHOICES}


def apply_choice(player, choice_key: str) -> None:
    if choice_key not in _VALID_KEYS:
        pilihan = ", ".join(sorted(_VALID_KEYS))
        raise ValueError(
            f"Pilihan tidak valid: '{choice_key}'. Pilihan yang tersedia: {pilihan}."
        )
    if choice_key == "skill_point":
        player.skill_points += 1
    else:
        player.attribute_bonuses[choice_key] = (
            player.attribute_bonuses.get(choice_key, 0) + dict(LEVEL_CHOICES)[choice_key]
        )


def on_level_up(player) -> list:
    from src.models.player import max_hp as _max_hp
    from src.models.player import max_mp as _max_mp

    player.level += 1
    player.hp += 10
    player.mp += 5
    player.hp = min(player.hp, _max_hp(player))
    player.mp = min(player.mp, _max_mp(player))
    return LEVEL_CHOICES
