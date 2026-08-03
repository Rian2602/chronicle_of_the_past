from src.models.player import effective_stat

TOTAL_STATS = ("hp", "mp", "attack", "defense", "agility", "intelligence")


def total_stats(player) -> dict:
    return {stat: effective_stat(player, stat) for stat in TOTAL_STATS}


def unequip(player, slot, items=None) -> str:
    item_id = player.equipped.get(slot)
    if item_id is None:
        return f"Tidak ada item di slot {slot}."
    item_def = items.get(item_id) if items is not None else None
    if item_def is None:
        del player.equipped[slot]
        return f"Peringatan: tidak bisa menghitung modifier {item_id}; slot {slot} dikosongkan."
    for stat, value in (item_def.modifiers or {}).items():
        player.attribute_bonuses[stat] = player.attribute_bonuses.get(stat, 0) - value
        if player.attribute_bonuses[stat] == 0:
            del player.attribute_bonuses[stat]
    del player.equipped[slot]
    return f"{item_def.name} dilepas dari slot {slot}."


def equip(player, item, items=None) -> str:
    if item.slot is None:
        return "Item ini tidak bisa dipasang."
    if player.equipped.get(item.slot) is not None:
        unequip(player, item.slot, items)
    for stat, value in (item.modifiers or {}).items():
        player.attribute_bonuses[stat] = player.attribute_bonuses.get(stat, 0) + value
    player.equipped[item.slot] = item.id
    return f"{item.name} dipasang di slot {item.slot}."
