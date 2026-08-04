def roll_loot(enemy, randomizer) -> list:
    """Lempar loot musuh: tiap entri lolos sesuai persentase chance.

    Returns:
        List dict {id, qty} berisi item yang berhasil didapat.
    """
    drops = []
    for entry in enemy.loot:
        if randomizer.chance(entry["chance"]):
            drops.append({"id": entry["item"], "qty": entry["amount"]})
    return drops
