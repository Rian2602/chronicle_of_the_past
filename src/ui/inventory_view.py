def render(player, items=None):
    """Render inventaris: perlengkapan terpasang dan barang bawaan."""
    items = items or {}
    lines = ["Perlengkapan:"]
    for slot, item_id in player.equipped.items():
        name = items[item_id].name if item_id in items else item_id
        lines.append(f"  {slot}: {name}")
    lines.append("Inventaris:")
    for entry in player.inventory:
        item = items.get(entry["id"])
        name = item.name if item else entry["id"]
        lines.append(f"  {name} x{entry['qty']}")
    return "\n".join(lines)
