from src.ui.renderer import box
from src.engine.dialog_engine import available_choices


def render(dialog, game_state):
    lines = []
    for line in dialog["lines"]:
        lines.append(f"{line['speaker']}:")
        lines.append(box(line["text"]))
    lines.append("Pilihan:")
    for idx, choice in enumerate(available_choices(dialog, game_state), start=1):
        lines.append(f"  {idx}. {choice['text']}")
    return "\n".join(lines)
