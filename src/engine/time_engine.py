from src.models.player import max_hp, max_mp

_TIME_CYCLE = ["morning", "afternoon", "evening", "night"]


def advance_time(game_state, ticks=1):
    """Maju kan waktu beberapa langkah; hari bertambah saat melewati malam."""
    for _ in range(ticks):
        idx = _TIME_CYCLE.index(game_state.time)
        if idx == len(_TIME_CYCLE) - 1:
            game_state.time = "morning"
            game_state.day += 1
        else:
            game_state.time = _TIME_CYCLE[idx + 1]


def rest(game_state):
    """Istirahat semalaman: kembali pagi, hari +1, HP/MP pulih penuh."""
    game_state.time = "morning"
    game_state.day += 1
    game_state.player.hp = max_hp(game_state.player)
    game_state.player.mp = max_mp(game_state.player)
