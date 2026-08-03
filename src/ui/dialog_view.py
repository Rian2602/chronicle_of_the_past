from src.ui.renderer import box
from src.engine.dialog_engine import available_choices


def render(dialog, game_state, npc_id=None, npc_name=None):
    lines = []
    # Gunakan nama NPC jika tersedia, fallback ke speaker ID
    display_name = npc_name
    for line in dialog["lines"]:
        speaker = line.get("speaker", "")
        # Jika speaker adalah ID dan kita punya npc_name, gunakan nama NPC
        if speaker == npc_id and display_name:
            lines.append(f"{display_name}:")
        elif not display_name and speaker:
            # Fallback: tampilkan speaker apa adanya (biasanya ID)
            lines.append(f"{speaker}:")
        elif display_name:
            lines.append(f"{display_name}:")
        lines.append(box(line["text"]))
    lines.append("Pilihan:")
    for idx, choice in enumerate(available_choices(dialog, game_state), start=1):
        lines.append(f"  {idx}. {choice['text']}")
    return "\n".join(lines)
