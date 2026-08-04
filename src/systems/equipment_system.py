from src.core.constants import STATS
from src.models.player import effective_stat


def total_stats(player) -> dict:
    """Hitung seluruh stat efektif pemain (base + bonus perlengkapan)."""
    return {stat: effective_stat(player, stat) for stat in STATS}


def unequip(player, slot, items=None) -> str:
    """Lepas item dari slot; kembalikan pesan hasil ke pemain.

    Args:
        player: Pemain yang perlengkapannya diubah.
        slot: Nama slot (weapon/armor/helmet).
        items: Katalog item untuk menghitung modifier (opsional).

    Returns:
        Pesan konfirmasi/peringatan dalam Bahasa Indonesia.
    """
    item_id = player.equipped.get(slot)
    if item_id is None:
        return f"Tidak ada item di slot {slot}."
    item_def = items.get(item_id) if items is not None else None
    if item_def is None:
        del player.equipped[slot]
        return (
            f"Peringatan: tidak bisa menghitung modifier {item_id}; "
            f"slot {slot} dikosongkan."
        )
    for stat, value in (item_def.modifiers or {}).items():
        player.attribute_bonuses[stat] = (
            player.attribute_bonuses.get(stat, 0) - value
        )
        if player.attribute_bonuses[stat] == 0:
            del player.attribute_bonuses[stat]
    del player.equipped[slot]
    return f"{item_def.name} dilepas dari slot {slot}."


def equip(player, item, items=None) -> str:
    """Pasang item ke slot-nya; item lama di slot sama dilepas dulu.

    Args:
        player: Pemain yang perlengkapannya diubah.
        item: Item yang akan dipasang.
        items: Katalog item untuk menghitung modifier (opsional).

    Returns:
        Pesan konfirmasi dalam Bahasa Indonesia.
    """
    if item.slot is None:
        return "Item ini tidak bisa dipasang."
    if player.equipped.get(item.slot) is not None:
        unequip(player, item.slot, items)
    for stat, value in (item.modifiers or {}).items():
        player.attribute_bonuses[stat] = (
            player.attribute_bonuses.get(stat, 0) + value
        )
    player.equipped[item.slot] = item.id
    return f"{item.name} dipasang di slot {item.slot}."
