from src.ui.renderer import box


def render(dialog, game_state, npc_id=None, npc_name=None, has_shop=False):
    """Render isi dialog: baris pembicara + teks dalam kotak.

    Args:
        dialog: Data dialog berisi lines.
        game_state: State (tidak dipakai di render; untuk API konsisten).
        npc_id: ID speaker yang ditampilkan sebagai nama NPC.
        npc_name: Nama tampilan NPC (fallback ke speaker ID).
        has_shop: True bila NPC ini punya toko (§12.2 story-season1-spec) —
            menambahkan baris ajakan berbelanja sebagai aksi paralel di
            luar daftar pilihan dialog bernomor.

    Returns:
        Teks dialog yang siap dicetak.
    """
    lines = []
    # Gunakan nama NPC jika tersedia, fallback ke speaker ID
    display_name = npc_name
    for line in dialog["lines"]:
        speaker = line.get("speaker", "")
        # Jika speaker adalah ID dan kita punya npc_name, gunakan nama NPC
        if speaker == npc_id and display_name:
            lines.append(f"{display_name}:")
        elif speaker:
            # Speaker lain (pemain/NPC lain): tampilkan ID-nya apa adanya
            lines.append(f"{speaker}:")
        lines.append(box(line["text"]))
    if has_shop:
        who = display_name or npc_id or "pedagang ini"
        lines.append(f"(Ketik 'shop' untuk berbelanja di toko {who}.)")
    return "\n".join(lines)
