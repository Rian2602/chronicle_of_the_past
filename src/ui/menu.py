from src.ui.renderer import bar

MAIN_ITEMS = ["Permainan Baru", "Lanjutkan", "Pengaturan", "Kredit", "Keluar"]


def render_main(selection=0):
    """Render menu utama dengan penanda item terpilih."""
    lines = ["CHRONICLE OF THE PAST", "=" * 26, ""]
    for idx, item in enumerate(MAIN_ITEMS):
        marker = "> " if idx == selection else "  "
        lines.append(marker + item)
    return "\n".join(lines)


def render_class_card(class_data):
    """Render kartu ringkas kelas beserta bar stat."""
    lines = [f"{class_data['name']}"]
    for stat, value in class_data.get("stat_bars", {}).items():
        lines.append(f"{stat.title():<14}{bar(value * 2, 10, width=10)}")
    return "\n".join(lines)
