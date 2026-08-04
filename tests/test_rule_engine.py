import pytest

from src.core.game_state import GameState
from src.core.randomizer import Randomizer
from src.engine.rule_engine import damage_roll, derived_stats, evaluate
from src.models.map import Map
from src.models.player import Player


def make_map(map_id="village"):
    return Map(
        id=map_id,
        name=map_id,
        region="1",
        threat_level=0,
        description="d",
        ascii_art="a",
        exits=[],
        npcs=[],
        enemy_pool=[],
    )


def make_player(**overrides):
    defaults = {
        "name": "R",
        "class_id": "assassin",
        "hp": 65,
        "mp": 12,
        "base_stats": {
            "attack": 15,
            "defense": 6,
            "hp": 65,
            "mp": 12,
            "agility": 15,
            "intelligence": 11,
        },
    }
    defaults.update(overrides)
    return Player(**defaults)


def test_derived_stats_critical():
    p = make_player()
    ds = derived_stats(p)
    assert ds["critical"] == pytest.approx(6.0)  # 15*0.4


def test_derived_stats_all_values():
    p = make_player(level=3)
    ds = derived_stats(p)
    assert ds["critical"] == pytest.approx(6.0)
    assert ds["dodge"] == pytest.approx(4.5)
    assert ds["accuracy"] == pytest.approx(94.5)
    assert ds["magic_resistance"] == pytest.approx(6.6)
    assert ds["physical_resistance"] == pytest.approx(2.4)
    assert ds["mana_regen"] == pytest.approx(2.2)
    assert ds["hp_regen"] == pytest.approx(4)
    assert ds["casting_speed"] == pytest.approx(3.3)
    assert ds["initiative"] == 15


def test_derived_stats_uses_attribute_bonuses():
    p = make_player(
        attribute_bonuses={"agility": 5, "intelligence": 4, "defense": 10}
    )
    ds = derived_stats(p)
    assert ds["critical"] == pytest.approx(8.0)  # (15+5)*0.4
    assert ds["dodge"] == pytest.approx(6.0)  # (15+5)*0.3
    assert ds["magic_resistance"] == pytest.approx(9.0)  # (11+4)*0.6
    assert ds["physical_resistance"] == pytest.approx(6.4)  # (6+10)*0.4


def test_derived_stats_initiative_with_randomizer():
    p = make_player()
    r = Randomizer(seed=7)
    ds = derived_stats(p, randomizer=r)
    assert 15 <= ds["initiative"] <= 20


def test_evaluate_flag_true():
    gs = GameState()
    gs.flags["gate_open"] = True
    assert (
        evaluate({"kind": "flag", "flag": "gate_open", "value": True}, gs)
        is True
    )


def test_evaluate_flag_false():
    gs = GameState()
    assert (
        evaluate({"kind": "flag", "flag": "gate_open", "value": True}, gs)
        is False
    )


def test_evaluate_map():
    gs = GameState()
    gs.current_map = "village"
    assert evaluate({"kind": "map", "map": "village"}, gs) is True
    gs.current_map = "forest"
    assert evaluate({"kind": "map", "map": "village"}, gs) is False


def test_evaluate_map_with_map_object():
    gs = GameState()
    gs.current_map = make_map("village")
    assert evaluate({"kind": "map", "map": "village"}, gs) is True
    gs.current_map = make_map("forest")
    assert evaluate({"kind": "map", "map": "village"}, gs) is False


def test_evaluate_time():
    gs = GameState()
    gs.time = "night"
    assert evaluate({"kind": "time", "time": "night"}, gs) is True
    gs.time = "morning"
    assert evaluate({"kind": "time", "time": "night"}, gs) is False


def test_evaluate_level_gte():
    gs = GameState()
    gs.player = make_player(level=3)
    assert evaluate({"kind": "level", "gte": 3}, gs) is True
    gs.player = make_player(level=2)
    assert evaluate({"kind": "level", "gte": 3}, gs) is False


def test_evaluate_level_no_player():
    gs = GameState()
    assert evaluate({"kind": "level", "gte": 3}, gs) is False


def test_evaluate_quest_done():
    gs = GameState()
    gs.player = make_player(quests_done=["quest001"])
    assert evaluate({"kind": "quest_done", "quest": "quest001"}, gs) is True


def test_evaluate_quest_done_empty():
    gs = GameState()
    gs.player = make_player(quests_done=[])
    assert evaluate({"kind": "quest_done", "quest": "quest001"}, gs) is False


def test_evaluate_quest_done_no_player():
    gs = GameState()
    assert evaluate({"kind": "quest_done", "quest": "quest001"}, gs) is False


def test_evaluate_unknown_kind():
    gs = GameState()
    assert evaluate({"kind": "bogus"}, gs) is False


def test_evaluate_flag_name_key():
    gs = GameState()
    gs.flags["gate_open"] = True
    assert (
        evaluate({"kind": "flag", "name": "gate_open", "value": True}, gs)
        is True
    )


def test_evaluate_flag_legacy_key():
    gs = GameState()
    gs.flags["gate_open"] = True
    assert (
        evaluate({"kind": "flag", "flag": "gate_open", "value": True}, gs)
        is True
    )
    gs.flags["gate_open"] = False
    assert (
        evaluate({"kind": "flag", "flag": "gate_open", "value": True}, gs)
        is False
    )


def test_evaluate_flag_eq_false():
    gs = GameState()
    gs.flags["gate_open"] = True
    assert (
        evaluate(
            {
                "kind": "flag",
                "name": "gate_open",
                "operator": "EQ",
                "value": False,
            },
            gs,
        )
        is False
    )
    gs.flags["gate_open"] = False
    assert (
        evaluate(
            {
                "kind": "flag",
                "name": "gate_open",
                "operator": "EQ",
                "value": False,
            },
            gs,
        )
        is True
    )


def test_evaluate_flag_ne():
    gs = GameState()
    gs.flags["gate_open"] = True
    assert (
        evaluate(
            {
                "kind": "flag",
                "name": "gate_open",
                "operator": "NE",
                "value": True,
            },
            gs,
        )
        is False
    )
    assert (
        evaluate(
            {
                "kind": "flag",
                "name": "gate_open",
                "operator": "NE",
                "value": False,
            },
            gs,
        )
        is True
    )


def test_evaluate_flag_exists():
    gs = GameState()
    assert (
        evaluate(
            {"kind": "flag", "name": "gate_open", "operator": "EXISTS"}, gs
        )
        is False
    )
    gs.flags["gate_open"] = False
    assert (
        evaluate(
            {"kind": "flag", "name": "gate_open", "operator": "EXISTS"}, gs
        )
        is True
    )


def test_evaluate_flag_missing():
    gs = GameState()
    gs.flags["gate_open"] = True
    assert (
        evaluate(
            {"kind": "flag", "name": "gate_open", "operator": "MISSING"}, gs
        )
        is False
    )
    gs2 = GameState()
    assert (
        evaluate(
            {"kind": "flag", "name": "gate_open", "operator": "MISSING"}, gs2
        )
        is True
    )


def test_evaluate_flag_default_backward_compat():
    gs = GameState()
    gs.flags["x"] = True
    assert evaluate({"kind": "flag", "name": "x", "value": True}, gs) is True
    gs.flags["x"] = "set"
    assert evaluate({"kind": "flag", "name": "x", "value": True}, gs) is False
    gs.flags["x"] = False
    assert evaluate({"kind": "flag", "name": "x", "value": True}, gs) is False


def test_evaluate_level_gt():
    gs = GameState()
    gs.player = make_player(level=3)
    assert evaluate({"kind": "level", "operator": "GT", "value": 2}, gs) is True
    assert (
        evaluate({"kind": "level", "operator": "GT", "value": 3}, gs) is False
    )


def test_evaluate_level_lt():
    gs = GameState()
    gs.player = make_player(level=3)
    assert evaluate({"kind": "level", "operator": "LT", "value": 4}, gs) is True
    assert (
        evaluate({"kind": "level", "operator": "LT", "value": 3}, gs) is False
    )


def test_evaluate_level_eq_ne():
    gs = GameState()
    gs.player = make_player(level=3)
    assert evaluate({"kind": "level", "operator": "EQ", "value": 3}, gs) is True
    assert (
        evaluate({"kind": "level", "operator": "EQ", "value": 2}, gs) is False
    )
    assert (
        evaluate({"kind": "level", "operator": "NE", "value": 3}, gs) is False
    )
    assert evaluate({"kind": "level", "operator": "NE", "value": 2}, gs) is True


def test_evaluate_level_lte():
    gs = GameState()
    gs.player = make_player(level=3)
    assert (
        evaluate({"kind": "level", "operator": "LTE", "value": 3}, gs) is True
    )
    assert (
        evaluate({"kind": "level", "operator": "LTE", "value": 2}, gs) is False
    )


def test_evaluate_level_no_player_with_operator():
    gs = GameState()
    assert (
        evaluate({"kind": "level", "operator": "GTE", "value": 1}, gs) is False
    )


def test_evaluate_map_ne():
    gs = GameState()
    gs.current_map = "village"
    assert (
        evaluate({"kind": "map", "name": "village", "operator": "NE"}, gs)
        is False
    )
    assert (
        evaluate({"kind": "map", "name": "forest", "operator": "NE"}, gs)
        is True
    )
    assert (
        evaluate({"kind": "map", "map": "forest", "operator": "NE"}, gs) is True
    )


def test_evaluate_time_ne():
    gs = GameState()
    gs.time = "night"
    assert (
        evaluate({"kind": "time", "name": "night", "operator": "NE"}, gs)
        is False
    )
    assert (
        evaluate({"kind": "time", "time": "morning", "operator": "NE"}, gs)
        is True
    )


def test_evaluate_quest_done_exists_missing():
    gs = GameState()
    gs.player = make_player(quests_done=["quest001"])
    assert (
        evaluate(
            {"kind": "quest_done", "name": "quest001", "operator": "EXISTS"}, gs
        )
        is True
    )
    assert (
        evaluate(
            {"kind": "quest_done", "name": "quest002", "operator": "EXISTS"}, gs
        )
        is False
    )
    assert (
        evaluate(
            {"kind": "quest_done", "name": "quest001", "operator": "MISSING"},
            gs,
        )
        is False
    )
    assert (
        evaluate(
            {"kind": "quest_done", "name": "quest002", "operator": "MISSING"},
            gs,
        )
        is True
    )


def test_evaluate_quest_done_eq_ne():
    gs = GameState()
    gs.player = make_player(quests_done=["quest001"])
    assert (
        evaluate(
            {
                "kind": "quest_done",
                "name": "quest001",
                "operator": "EQ",
                "value": True,
            },
            gs,
        )
        is True
    )
    assert (
        evaluate(
            {
                "kind": "quest_done",
                "name": "quest001",
                "operator": "NE",
                "value": True,
            },
            gs,
        )
        is False
    )
    assert (
        evaluate(
            {
                "kind": "quest_done",
                "name": "quest001",
                "operator": "EQ",
                "value": False,
            },
            gs,
        )
        is False
    )


def test_evaluate_unknown_operator():
    gs = GameState()
    gs.flags["x"] = True
    assert (
        evaluate({"kind": "flag", "name": "x", "operator": "FOO"}, gs) is False
    )
    gs.player = make_player(level=3)
    assert (
        evaluate({"kind": "level", "operator": "FOO", "value": 3}, gs) is False
    )


class ScriptedRandomizer:
    def __init__(self, rolls):
        self._rolls = list(rolls)

    def roll(self, low, high):
        return self._rolls.pop(0)


def test_damage_roll_bounds():
    a = {"attack": 10, "defense": 5, "agility": 8, "intelligence": 7}
    d = {"defense": 5, "agility": 5}
    r = Randomizer(seed=7)
    res = damage_roll(a, d, r)
    assert res["missed"] in (True, False)
    assert res["critical"] in (True, False)
    assert isinstance(res["damage"], int)
    assert res["damage"] >= 0
    assert res["damage"] <= 20  # (10 - 2) + 0..5, crit x1.5 → 20 cap


def test_damage_roll_formula():
    a = {"attack": 10, "defense": 5, "agility": 8, "intelligence": 7}
    d = {"defense": 5, "agility": 5}
    r = ScriptedRandomizer([0, 0, 0])  # variance, miss_roll, crit_roll
    res = damage_roll(a, d, r)
    # base = max(1, 10 - 5//2) = 8; + variance 0 = 8;
    # crit (0 < 3.2) → round(8*1.5) = 12
    assert res == {"damage": 12, "critical": True, "missed": False}


def test_damage_roll_miss_zeroes_damage():
    a = {"attack": 10, "defense": 5, "agility": 8, "intelligence": 7}
    d = {"defense": 5, "agility": 5}
    r = ScriptedRandomizer(
        [0, 100, 100]
    )  # variance 0, miss (100 > 92.4), no crit
    res = damage_roll(a, d, r)
    assert res["missed"] is True
    assert res["critical"] is False
    assert res["damage"] == 0


def test_damage_roll_base_minimum():
    a = {"attack": 0, "defense": 0, "agility": 0, "intelligence": 0}
    d = {"defense": 50, "agility": 5}
    r = ScriptedRandomizer([0, 0, 100])  # variance 0, not missed, no crit
    res = damage_roll(a, d, r)
    # base = max(1, 0 - 25) = 1
    assert res == {"damage": 1, "critical": False, "missed": False}
