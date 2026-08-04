from src.core.game_state import GameState
from src.engine.time_engine import advance_time, rest
from src.models.player import Player


def test_time_cycle():
    gs = GameState()
    gs.time = "evening"
    advance_time(gs)
    assert gs.time == "night"


def test_day_wraps():
    gs = GameState()
    gs.time = "night"
    gs.day = 1
    advance_time(gs)
    assert gs.time == "morning"
    assert gs.day == 2


def test_full_cycle_in_four_ticks():
    gs = GameState()
    gs.time = "morning"
    gs.day = 1
    advance_time(gs, ticks=4)
    assert gs.time == "morning"
    assert gs.day == 2


def test_multiple_ticks_wrap_past_midnight():
    gs = GameState()
    gs.time = "night"
    gs.day = 1
    advance_time(gs, ticks=2)
    assert gs.time == "afternoon"
    assert gs.day == 2


def test_multiple_ticks_stay_within_day():
    gs = GameState()
    gs.time = "afternoon"
    gs.day = 3
    advance_time(gs, ticks=3)
    assert gs.time == "morning"
    assert gs.day == 4


def test_rest_sets_morning_next_day():
    gs = GameState()
    gs.time = "night"
    gs.day = 5
    gs.player = Player(
        name="Rin",
        class_id="warrior",
        hp=1,
        mp=0,
        base_stats={"hp": 100, "mp": 50},
    )
    rest(gs)
    assert gs.time == "morning"
    assert gs.day == 6


def test_rest_heals_player_to_full():
    gs = GameState()
    gs.time = "evening"
    gs.day = 1
    gs.player = Player(
        name="Rin",
        class_id="warrior",
        hp=30,
        mp=10,
        base_stats={"hp": 100, "mp": 50},
    )
    rest(gs)
    assert gs.player.hp == 100
    assert gs.player.mp == 50
