from src.systems import shop_system


def render(game_state, npc):
    """Render tampilan toko NPC: daftar beli, daftar jual, dan emas pemain.

    Args:
        game_state: State permainan (untuk katalog item & data pemain).
        npc: Data NPC (dict) yang memiliki field `shop`.

    Returns:
        Teks tampilan toko yang siap dicetak.
    """
    lines = [f"Toko {npc['name']}:"]

    buy_list = shop_system.list_buy(game_state, npc)
    if buy_list:
        lines.append("Beli (ketik: buy <item> [jumlah]):")
        for item_id, name, price in buy_list:
            lines.append(f"  {name} ({item_id}) — {price} emas")
    else:
        lines.append("Tidak ada barang yang dijual di sini.")

    sell_list = shop_system.list_sell(game_state, npc)
    if sell_list:
        lines.append("Jual (ketik: sell <item> [jumlah]):")
        for item_id, name, price, qty in sell_list:
            lines.append(f"  {name} ({item_id}) x{qty} — {price} emas/unit")

    lines.append(f"Emas kamu: {game_state.player.gold}")
    lines.append("Ketik 'go', 'talk', atau perintah lain untuk keluar toko.")
    return "\n".join(lines)
