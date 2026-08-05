from src.models.player import max_hp, max_mp


class InventoryFullError(Exception):
    """Exception raised when inventory is full and cannot add more items."""

    pass


def carry_capacity(player) -> int:
    """Kapasitas total inventaris pemain (30 + 2 per level)."""
    return 30 + player.level * 2


def count_items(player) -> int:
    """Jumlah total item yang dibawa pemain (termasuk stack qty)."""
    return sum(entry.get("qty", 0) for entry in player.inventory)


def add_item(player, item_id, qty=1, game_state=None) -> bool:
    """Tambahkan item ke inventaris bila kapasitas masih cukup.

    Args:
        player: Pemilik inventaris.
        item_id: ID item yang ditambahkan.
        qty: Jumlah yang ditambahkan (harus positif).
        game_state: Opsional. Bila diberikan, kemajuan syarat quest kind
            'collect' untuk item ini diperbarui (§12.1 story-season1-spec).

    Returns:
        True bila item ditambahkan, False bila qty invalid atau penuh.

    Raises:
        InventoryFullError: Bila inventaris penuh dan tidak bisa menambah item.
    """
    # Validasi: qty harus positif
    if qty <= 0:
        return False
    # Cek kapasitas sebelum menambahkan
    if count_items(player) + qty > carry_capacity(player):
        raise InventoryFullError(
            f"Inventaris penuh! Kapasitas: {carry_capacity(player)}, "
            f"terisi: {count_items(player)}, butuh: {qty}"
        )
    for entry in player.inventory:
        if entry["id"] == item_id:
            entry["qty"] = entry.get("qty", 0) + qty
            _progress_collect(game_state, item_id, entry["qty"])
            _progress_quest_flag(game_state, item_id)
            return True
    player.inventory.append({"id": item_id, "qty": qty})
    _progress_collect(game_state, item_id, qty)
    _progress_quest_flag(game_state, item_id)
    return True


def _progress_collect(game_state, item_id, owned_qty):
    """Perbarui syarat quest kind 'collect' bila game_state tersedia."""
    if game_state is None:
        return
    from src.engine import quest_engine

    quest_engine.progress_requirement(
        game_state, "collect", item_id, amount=owned_qty
    )


def _progress_quest_flag(game_state, item_id):
    """Set quest_flag item saat dimiliki (beli; loot via _track_loot_flags)."""
    if game_state is None:
        return
    item_def = game_state.items.get(item_id)
    flag = getattr(item_def, "quest_flag", None) if item_def else None
    if flag and flag not in game_state.flags:
        from src.engine import quest_engine

        game_state.flags[flag] = True
        quest_engine.complete_requirement(game_state, "flag", flag)


def remove_item(player, item_id, qty=1) -> None:
    """Kurangi qty item; entri dihapus saat qty mencapai nol.

    Raises:
        ValueError: Bila item tidak dimiliki atau qty melebihi stok.
    """
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
    """Gunakan item konsumabel: pulihkan HP/MP lalu hapus dari inventaris.

    Mendukung efek HP (`heal`), MP (`heal_mp`, mis. time_tincture), dan
    kabur dalam combat (`escape`, mis. smoke_bomb — di luar combat tidak
    bisa dipakai). §9.2/§21 Phase 0.

    Returns:
        Pesan hasil penggunaan dalam Bahasa Indonesia.
    """
    item_id = item_entry["id"]
    item_def = game_state.items.get(item_id)
    if item_def is None:
        return "Item ini tidak bisa dipakai."
    if getattr(item_def, "escape", False):
        return f"{item_def.name} hanya bisa dipakai saat bertarung."
    heal = item_def.heal
    heal_mp = getattr(item_def, "heal_mp", 0)
    if heal == 0 and heal_mp == 0:
        return "Item ini tidak bisa dipakai."
    if heal:
        player.hp = min(max_hp(player), player.hp + heal)
    if heal_mp:
        player.mp = min(max_mp(player), player.mp + heal_mp)
    remove_item(player, item_id, 1)
    parts = []
    if heal:
        parts.append(f"memulihkan {heal} HP")
    if heal_mp:
        parts.append(f"memulihkan {heal_mp} MP")
    return f"Kamu memakai {item_def.name}, " + " dan ".join(parts) + "."
