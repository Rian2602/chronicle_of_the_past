def derived_stats(player, randomizer=None):
    def effective(stat):
        return player.base_stats.get(stat, 0) + player.attribute_bonuses.get(stat, 0)

    agility = effective("agility")
    intelligence = effective("intelligence")
    defense = effective("defense")
    level = player.level

    return {
        "critical": agility * 0.4,
        "dodge": agility * 0.3,
        "accuracy": 90 + agility * 0.3,
        "magic_resistance": intelligence * 0.6,
        "physical_resistance": defense * 0.4,
        "mana_regen": intelligence * 0.2,
        "hp_regen": 1 + level,
        "casting_speed": intelligence * 0.3,
        "initiative": agility + (randomizer.roll(0, 5) if randomizer else 0),
        "carry_capacity": 30 + level * 2,
    }


def evaluate(condition: dict, game_state) -> bool:
    kind = condition.get("kind")
    if kind == "flag":
        return game_state.flags.get(condition.get("flag")) is True
    if kind == "map":
        return game_state.current_map == condition.get("map")
    if kind == "time":
        return game_state.time == condition.get("time")
    if kind == "level":
        if game_state.player is None:
            return False
        return game_state.player.level >= condition.get("gte", 0)
    if kind == "quest_done":
        player = game_state.player
        return condition.get("quest") in (player.quests_done if player else [])
    return False


def damage_roll(attacker_stats: dict, defender_stats: dict, randomizer) -> dict:
    attack = attacker_stats.get("attack", 0)
    defense = defender_stats.get("defense", 0)
    agility = attacker_stats.get("agility", 0)

    base = max(1, attack - defense // 2)
    variance = randomizer.roll(0, 5)
    total = base + variance

    accuracy = 90 + agility * 0.3
    missed = randomizer.roll(0, 100) > accuracy
    critical = randomizer.roll(0, 100) < agility * 0.4
    if critical:
        total = round(total * 1.5)
    if missed:
        total = 0

    return {
        "damage": max(0, int(total)),
        "critical": critical,
        "missed": missed,
    }
