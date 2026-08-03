from src.models.player import max_hp


def carry_capacity(player) -> int:
    return 30 + player.level * 2


def count_items(player) -> int:
    return sum(entry.get("qty", 0) for entry in player.inventory)


def add_item(player, item_id, qty=1) -> bool:
    # Validasi: qty harus positif
    if qty <= 0:
        return False
    # Cek kapasitas sebelum menambahkan
    if count_items(player) + qty > carry_capacity(player):
        return False
    for entry in player.inventory:
        if entry["id"] == item_id:
            entry["qty"] = entry.get("qty", 0) + qty
            return True
    player.inventory.append({"id": item_id, "qty": qty})
    return True


def remove_item(player, item_id, qty=1) -> None:
    # Validasi: qty harus positif
    if qty <= 0:
        return
    for entry in player.inventory:
        if entry["id"] == item_id:
            if entry.get("qty", 0) < qty:
                raise ValueError(f"Jumlah item tidak cukup: {item_id}")
            entry["qty"] -= qty
            if entry["qty"] <= 0:
                player.inventory.remove(entry)
            return
    raise ValueError(f"Item tidak dimiliki: {item_id}")


def use_consumable(player, item_entry, game_state) -> str:
    item_id = item_entry["id"]
    item_def = game_state.items.get(item_id)
    if item_def is None or item_def.heal == 0:
        return "Item ini tidak bisa dipakai."
    heal = item_def.heal
    player.hp = min(max_hp(player), player.hp + heal)
    remove_item(player, item_id, 1)
    return f"Kamu memakai {item_def.name}, memulihkan {heal} HP."
