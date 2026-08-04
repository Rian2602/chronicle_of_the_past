from src.ui.renderer import bar


def render(state):
    lines = []
    enemy = state.enemy
    max_hp = enemy.stats.get("max_hp", enemy.stats.get("hp", 1))
    lines.append(f"{enemy.name} — Lv {enemy.level}")
    lines.append(f"HP {enemy.stats['hp']}/{max_hp} {bar(enemy.stats['hp'], max_hp, width=10)}")
    if state.observe_info:
        lines.append(state.observe_info)
    lines.append("")
    p = state.player
    lines.append(f"{p.name} — HP {p.hp}  MP {p.mp}")
    lines.append("")
    lines.extend(state.log[-5:])
    return "\n".join(lines)
