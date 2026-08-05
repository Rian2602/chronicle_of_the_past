"""Sistem toko: beli/jual item lewat NPC yang punya konfigurasi `shop`.

Mengikuti §12.2 story-season1-spec.md. NPC toko didefinisikan di
data/npc/<id>.json dengan field:

    "shop": {
        "buy": [{"item": "potion", "price": 25}, ...],
        "sell_multiplier": 0.5
    }

Modul ini murni fungsi (tanpa state tersembunyi) — sejalan dengan gaya
dialog_engine.py: NPC dict diberikan langsung oleh pemanggil (game.py),
bukan dicari lewat game_state (game_state tidak menyimpan katalog NPC).
"""

from src.systems import inventory_system

_MERCHANT_GUILD_DISCOUNT_THRESHOLD = 15
_MERCHANT_GUILD_DISCOUNT_RATE = 0.85  # -15% harga


def has_shop(npc) -> bool:
    """True bila data NPC memiliki konfigurasi toko yang valid."""
    return bool(npc and npc.get("shop") and npc["shop"].get("buy") is not None)


def _buy_entry(npc, item_id):
    """Cari entri {item, price} di daftar jual NPC, atau None."""
    for entry in npc.get("shop", {}).get("buy", []):
        if entry.get("item") == item_id:
            return entry
    return None


def _sell_multiplier(npc) -> float:
    """Pengali harga jual pemain ke NPC (default 0.5)."""
    return npc.get("shop", {}).get("sell_multiplier", 0.5)


def _reputation_discount(game_state, npc) -> float:
    """Diskon harga beli berdasar reputasi faksi NPC.

    Sesuai §12.2/§12.4: merchant_guild >= 15 -> -15% harga beli.
    """
    player = game_state.player
    if player is None:
        return 1.0
    if npc.get("faction") != "merchant_guild":
        return 1.0
    if (
        player.reputation.get("merchant_guild", 0)
        < _MERCHANT_GUILD_DISCOUNT_THRESHOLD
    ):
        return 1.0
    return _MERCHANT_GUILD_DISCOUNT_RATE


def _item_name(game_state, item_id) -> str:
    """Nama tampilan item, fallback ke ID bila tak ada di katalog."""
    item_def = game_state.items.get(item_id)
    return item_def.name if item_def else item_id


def list_buy(game_state, npc):
    """Daftar item yang bisa dibeli dari NPC.

    Returns:
        List tuple (item_id, nama, harga_efektif) — harga sudah
        memperhitungkan diskon reputasi.
    """
    discount = _reputation_discount(game_state, npc)
    result = []
    for entry in npc.get("shop", {}).get("buy", []):
        item_id = entry["item"]
        price = round(entry["price"] * discount)
        result.append((item_id, _item_name(game_state, item_id), price))
    return result


def list_sell(game_state, npc):
    """Daftar item milik pemain yang bisa dijual ke NPC ini.

    Returns:
        List tuple (item_id, nama, harga_jual_per_unit, qty_dimiliki).
        Item tanpa entri di katalog (game_state.items) dilewati.
    """
    multiplier = _sell_multiplier(npc)
    result = []
    for entry in game_state.player.inventory:
        if entry["id"] in game_state.player.equipped.values():
            continue
        item_def = game_state.items.get(entry["id"])
        if item_def is None:
            continue
        price = round(item_def.price * multiplier)
        result.append((entry["id"], item_def.name, price, entry.get("qty", 0)))
    return result


def buy(game_state, npc, item_id, qty=1) -> str:
    """Beli `qty` item dari toko NPC; potong emas & tambah ke inventaris.

    Returns:
        Pesan hasil transaksi dalam Bahasa Indonesia.
    """
    if qty <= 0:
        return "Jumlah pembelian harus lebih dari nol."
    if not has_shop(npc):
        return f"{npc.get('name', 'NPC ini')} tidak berjualan."
    entry = _buy_entry(npc, item_id)
    if entry is None:
        return "Item itu tidak dijual di sini."
    name = _item_name(game_state, item_id)
    unit_price = round(entry["price"] * _reputation_discount(game_state, npc))
    total = unit_price * qty
    player = game_state.player
    if player.gold < total:
        return f"Emas tidak cukup untuk membeli {name} ({total} emas)."
    if not inventory_system.add_item(
        player, item_id, qty, game_state=game_state
    ):
        return "Tas penuh, tidak bisa membawa item lagi."
    player.gold -= total
    return f"Kamu membeli {name} x{qty} seharga {total} emas."


def sell(game_state, npc, item_id, qty=1) -> str:
    """Jual `qty` item milik pemain ke NPC; tambah emas & kurangi stok.

    Returns:
        Pesan hasil transaksi dalam Bahasa Indonesia.
    """
    if qty <= 0:
        return "Jumlah penjualan harus lebih dari nol."
    if not has_shop(npc):
        return f"{npc.get('name', 'NPC ini')} tidak berjualan."
    player = game_state.player
    if item_id in player.equipped.values():
        return "Item yang sedang dipasang tidak bisa dijual."
    owned = next((e for e in player.inventory if e["id"] == item_id), None)
    if owned is None or owned.get("qty", 0) < qty:
        return "Kamu tidak memiliki item itu sejumlah itu."
    item_def = game_state.items.get(item_id)
    name = item_def.name if item_def else item_id
    base_price = item_def.price if item_def else 0
    unit_price = round(base_price * _sell_multiplier(npc))
    total = unit_price * qty
    inventory_system.remove_item(player, item_id, qty)
    player.gold += total
    return f"Kamu menjual {name} x{qty} seharga {total} emas."
