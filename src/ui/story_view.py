from src.ui.renderer import box


def render_scene(scene):
    """Render satu scene cerita: baris teks dalam kotak."""
    lines = scene.get("lines") or []
    if not lines:
        return ""
    return box("\n".join(lines))
