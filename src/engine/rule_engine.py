from src.models.player import effective_stat


def accuracy(agility: int) -> float:
    """Persentase akurasi serangan berdasarkan kelincahan."""
    return 90 + agility * 0.3


def crit_chance(agility: int) -> float:
    """Persentase peluang serangan kritis berdasarkan kelincahan."""
    return agility * 0.4


def magic_resistance(intelligence: int) -> float:
    """Nilai resistensi sihir berdasarkan kecerdasan."""
    return intelligence * 0.6


def derived_stats(player, randomizer=None):
    """Hitung stat turunan (kritis, dodge, regen, inisiatif, dll).

    Args:
        player: Pemain sumber stat efektif.
        randomizer: Sumber acak untuk inisiatif (opsional).

    Returns:
        Dict berisi semua stat turunan untuk pertarungan.
    """
    agility = effective_stat(player, "agility")
    intelligence = effective_stat(player, "intelligence")
    defense = effective_stat(player, "defense")
    level = player.level

    return {
        "critical": crit_chance(agility),
        "dodge": agility * 0.3,
        "accuracy": accuracy(agility),
        "magic_resistance": magic_resistance(intelligence),
        "physical_resistance": defense * 0.4,
        "mana_regen": intelligence * 0.2,
        "hp_regen": 1 + level,
        "casting_speed": intelligence * 0.3,
        "initiative": agility + (randomizer.roll(0, 5) if randomizer else 0),
    }


def evaluate(condition: dict, game_state) -> bool:
    """Evaluasi satu kondisi rule-engine terhadap state permainan.

    Mendukung kind: flag, map, time, level, quest_done — dengan
    operator EQ/NE/EXISTS/MISSING/GT/LT/GTE/LTE sesuai jenisnya.

    Returns:
        True bila kondisi terpenuhi.
    """
    kind = condition.get("kind")
    operator = condition.get("operator", "EQ")
    if kind == "flag":
        flag_name = condition.get("name", condition.get("flag"))
        value = condition.get("value", True)
        if operator == "EQ":
            return game_state.flags.get(flag_name) is value
        if operator == "NE":
            return game_state.flags.get(flag_name) is not value
        if operator == "EXISTS":
            return flag_name in game_state.flags
        if operator == "MISSING":
            return flag_name not in game_state.flags
        return False
    if kind == "map":
        target = condition.get("name", condition.get("map"))
        current = getattr(game_state.current_map, "id", game_state.current_map)
        if operator == "EQ":
            return current == target
        if operator == "NE":
            return current != target
        return False
    if kind == "time":
        target = condition.get("name", condition.get("time"))
        if operator == "EQ":
            return game_state.time == target
        if operator == "NE":
            return game_state.time != target
        return False
    if kind == "level":
        if game_state.player is None:
            return False
        operator = condition.get("operator", "EQ")
        value = condition.get("value", True)
        player_level = game_state.player.level
        if operator == "EQ":
            return player_level == value
        if operator == "NE":
            return player_level != value
        if operator == "GT":
            return player_level > value
        if operator == "LT":
            return player_level < value
        if operator == "GTE":
            return player_level >= value
        if operator == "LTE":
            return player_level <= value
        return False
    if kind == "quest_done":
        if game_state.player is None:
            return False
        quest_id = condition.get("name", condition.get("quest"))
        value = condition.get("value", True)
        done = quest_id in game_state.player.quests_done
        if operator == "EQ":
            return done is value
        if operator == "NE":
            return done is not value
        if operator == "EXISTS":
            return done
        if operator == "MISSING":
            return not done
        return False
    return False


def damage_roll(attacker_stats: dict, defender_stats: dict, randomizer) -> dict:
    """Lempar damage satu serangan: base, varians, miss, dan kritis.

    Args:
        attacker_stats: Dict stat penyerang (attack, agility).
        defender_stats: Dict stat bertahan (defense).
        randomizer: Sumber acak untuk varians/miss/kritis.

    Returns:
        Dict {damage, critical, missed} hasil lemparan.
    """
    attack = attacker_stats.get("attack", 0)
    defense = defender_stats.get("defense", 0)
    agility = attacker_stats.get("agility", 0)

    # Mencegah damage negatif: defense hanya mengurangi maksimal 50% dari attack
    base_damage = max(1, attack - defense // 2)
    variance = randomizer.roll(0, 5)
    total = base_damage + variance

    missed = randomizer.roll(0, 100) > accuracy(agility)
    critical = randomizer.roll(0, 100) < crit_chance(agility)
    if critical:
        total = round(total * 1.5)
    if missed:
        total = 0

    return {
        "damage": max(0, int(total)),
        "critical": critical,
        "missed": missed,
    }
