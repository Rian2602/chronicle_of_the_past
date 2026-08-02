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
