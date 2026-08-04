from src.ui.renderer import box


def render_scene(scene):
    lines = scene.get("lines") or []
    if not lines:
        return ""
    return box("\n".join(lines))
