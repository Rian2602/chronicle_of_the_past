from src.ui.renderer import box


def render(dialog, game_state, npc_id=None, npc_name=None):
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
    return "\n".join(lines)
