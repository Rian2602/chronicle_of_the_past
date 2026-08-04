FOREST_REGIONS = ("2", 2)


def check_encounter(game_state, randomizer):
    """Cek kemungkinan pertemuan musuh di peta saat ini.

    Peluang naik seiring threat level dan saat malam di kawasan hutan.

    Args:
        game_state: State permainan berisi peta dan daftar musuh.
        randomizer: Sumber acak (chance + weighted_choice).

    Returns:
        Enemy yang ditemui, atau None bila tidak ada pertemuan.
    """
    m = game_state.current_map
    percent = 20 + m.threat_level * 10
    if game_state.time == "night" and m.region in FOREST_REGIONS:
        percent += 10
    if not randomizer.chance(percent):
        return None
    entries = []
    for entry in m.enemy_pool:
        if isinstance(entry, str):
            enemy_id, weight = entry, 1
        elif isinstance(entry, dict):
            enemy_id = entry.get("id")
            weight = entry.get("weight", 1)
        else:
            continue
        if enemy_id is None:
            continue
        enemy = game_state.enemies.get(enemy_id)
        if enemy is not None and weight > 0:
            entries.append((enemy, weight))
    if not entries:
        return None
    return randomizer.weighted_choice(entries)
