from src.engine import quest_engine
from src.models.player import max_hp, max_mp
from src.ui.renderer import bar


def render(player, game_state):
    location = game_state.current_map.name if game_state.current_map else "—"
    hp_bar = bar(player.hp, max_hp(player))
    mp_bar = bar(player.mp, max_mp(player))
    lines = [
        f"{player.name} — {player.class_id.title()} (Lv {player.level})",
        f"HP {player.hp}/{max_hp(player)} {hp_bar}",
        f"MP {player.mp}/{max_mp(player)} {mp_bar}",
        f"Emas: {player.gold}   XP: {player.xp}",
        f"Lokasi: {location}   Waktu: {game_state.time}",
    ]
    objective = quest_engine.next_objective(game_state)
    if objective:
        lines.append(f"▶ {objective}")
    return "\n".join(lines)
