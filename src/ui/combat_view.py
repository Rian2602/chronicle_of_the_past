from src.engine.combat_engine import BUFF_LABELS
from src.ui.renderer import bar


def _buff_line(state) -> str | None:
    """Baris buff aktif pemain (self-buff skill §9.4), atau None."""
    buffs = state.buffs.get("player", [])
    if not buffs:
        return None
    parts = []
    for buff in buffs:
        label = BUFF_LABELS.get(buff.stat, buff.stat)
        parts.append(f"{label}+{buff.power} ({buff.duration})")
    return "Buff: " + ", ".join(parts)


def render(state):
    """Render tampilan combat: musuh, HP bar, info Amati, dan log."""
    lines = []
    enemy = state.enemy
    max_hp = enemy.stats.get("max_hp", enemy.stats.get("hp", 1))
    lines.append(f"{enemy.name} — Lv {enemy.level}")
    lines.append(
        f"HP {enemy.stats['hp']}/{max_hp} "
        f"{bar(enemy.stats['hp'], max_hp, width=10)}"
    )
    if state.observe_info:
        lines.append(state.observe_info)
    lines.append("")
    p = state.player
    lines.append(f"{p.name} — HP {p.hp}  MP {p.mp}")
    buff_line = _buff_line(state)
    if buff_line:
        lines.append(buff_line)
    lines.append("")
    lines.extend(state.log[-5:])
    return "\n".join(lines)
