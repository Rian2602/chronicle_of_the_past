from src.models.player import max_hp
from src.models.player import max_mp

_TIME_CYCLE = ["morning", "afternoon", "evening", "night"]


def advance_time(game_state, ticks=1):
    for _ in range(ticks):
        idx = _TIME_CYCLE.index(game_state.time)
        if idx == len(_TIME_CYCLE) - 1:
            game_state.time = "morning"
            game_state.day += 1
        else:
            game_state.time = _TIME_CYCLE[idx + 1]


def rest(game_state):
    game_state.time = "morning"
    game_state.day += 1
    game_state.player.hp = max_hp(game_state.player)
    game_state.player.mp = max_mp(game_state.player)
