def roll_loot(enemy, randomizer) -> list:
    drops = []
    for entry in enemy.loot:
        if randomizer.chance(entry["chance"]):
            drops.append({"id": entry["item"], "qty": entry["amount"]})
    return drops
