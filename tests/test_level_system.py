from src.core.randomizer import Randomizer
from src.models.player import Player
from src.systems.level_system import award_xp, gain_xp, xp_to_next


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


def test_gain_xp_no_level():
    p = make_player(level=1, xp=10)
    assert gain_xp(p, 20) == []
    assert p.level == 1
    assert p.xp == 30


def test_gain_xp_single_level():
    p = make_player(level=1, xp=40)
    assert gain_xp(p, 20) == [2]
    assert p.level == 2
    assert p.xp == 10


def test_gain_xp_single_level_with_randomizer():
    p = make_player(level=1, xp=40)
    r = Randomizer(seed=1)
    assert gain_xp(p, 20, r) == [2]
    assert p.level == 2
    assert p.xp == 10


def test_gain_xp_multi_level():
    p = make_player(level=1, xp=40)
    assert gain_xp(p, 120) == [2, 3]
    assert p.level == 3
    assert p.xp == 10


def test_gain_xp_exact_threshold():
    p = make_player(level=1, xp=50)
    assert gain_xp(p, 0) == [2]
    assert p.level == 2
    assert p.xp == 0


def test_award_xp_applies_xp_bonus():
    assert award_xp(make_player(xp_bonus=1.2), 30) == 36
    assert award_xp(make_player(), 30) == 30
    assert award_xp(make_player(xp_bonus=0), 30) == 0
