from src.models.player import Player
from src.systems.level_system import (
    award_xp,
    gain_xp,
    process_level_ups,
    xp_to_next,
)


def make_player(**overrides):
    defaults = {
        "name": "Rian",
        "class_id": "warrior",
        "hp": 100,
        "mp": 10,
        "base_stats": {},
    }
    defaults.update(overrides)
    return Player(**defaults)


def test_xp_curve():
    assert xp_to_next(1) == 50
    assert xp_to_next(2) == 100
    assert xp_to_next(3) == 150


def test_gain_xp_adds_amount():
    p = make_player(level=1, xp=10)
    assert gain_xp(p, 20) == 20
    assert p.level == 1
    assert p.xp == 30


def test_gain_xp_applies_xp_bonus():
    assert gain_xp(make_player(xp_bonus=1.2), 30) == 36
    assert gain_xp(make_player(), 30) == 30


def test_gain_xp_applies_multiplier():
    p = make_player(xp_bonus=1.2)
    assert gain_xp(p, 30, multiplier=2.0) == 72
    assert p.xp == 72


def test_process_level_ups_no_level():
    p = make_player(level=1, xp=30)
    assert process_level_ups(p) == []
    assert p.level == 1
    assert p.xp == 30


def test_process_level_ups_single_level():
    p = make_player(level=1, xp=40)
    gain_xp(p, 20)
    assert process_level_ups(p) == [2]
    assert p.level == 2
    assert p.xp == 10


def test_process_level_ups_multi_level():
    p = make_player(level=1, xp=40)
    gain_xp(p, 120)
    assert process_level_ups(p) == [2, 3]
    assert p.level == 3
    assert p.xp == 10


def test_process_level_ups_exact_threshold():
    p = make_player(level=1, xp=50)
    assert process_level_ups(p) == [2]
    assert p.level == 2
    assert p.xp == 0


def test_award_xp_applies_xp_bonus():
    assert award_xp(make_player(xp_bonus=1.2), 30) == 36
    assert award_xp(make_player(), 30) == 30
    assert award_xp(make_player(xp_bonus=0), 30) == 0
