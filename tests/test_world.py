import pytest

from src.core.game_state import GameState
from src.core.randomizer import Randomizer
from src.engine.world_engine import current_map
from src.engine.world_engine import get_map
from src.models.enemy import Enemy
from src.models.map import Map
from src.systems.exploration_system import check_encounter
from src.systems.travel_system import can_travel
from src.systems.travel_system import travel


def make_map(map_id, region="1", threat=1, exits=None, pool=None):
    return Map(
        id=map_id,
        name=map_id.title(),
        region=region,
        threat_level=threat,
        description="desc",
        ascii_art=".",
        exits=exits or [],
        npcs=[],
        enemy_pool=pool or [],
    )


def make_enemy(enemy_id):
    return Enemy(
        id=enemy_id,
        name=enemy_id.title(),
        level=1,
        stats={"hp": 10, "mp": 0, "atk": 3, "def": 1, "spd": 5},
        loot=[],
        skills=[],
    )


def gs_with_world():
    gs = GameState()
    village = make_map("village", exits=["forest"])
    forest = make_map("forest")
    gs.world = {"village": village, "forest": forest}
    gs.current_map = village
    return gs


def test_get_map_returns_map_from_world():
    gs = GameState()
    m = make_map("village")
    gs.world = {"village": m}
    assert get_map(gs, "village") is m


def test_current_map_returns_current_map():
    gs = GameState()
    m = make_map("village")
    gs.current_map = m
    assert current_map(gs) is m


def test_can_travel_true_when_target_in_exits():
    gs = gs_with_world()
    assert can_travel(gs, "forest") is True


def test_can_travel_false_when_target_not_in_exits():
    gs = gs_with_world()
    assert can_travel(gs, "capital") is False


def test_can_travel_false_without_current_map():
    gs = GameState()
    assert can_travel(gs, "forest") is False


def test_travel_moves_map_advances_time_and_returns_message():
    gs = gs_with_world()
    gs.time = "morning"
    msg = travel(gs, "forest")
    assert gs.current_map is gs.world["forest"]
    assert gs.time == "afternoon"
    assert msg == "Kamu tiba di Forest."


def test_travel_raises_value_error_on_non_exit():
    gs = gs_with_world()
    with pytest.raises(ValueError):
        travel(gs, "capital")


def test_no_encounter_at_low_threat():
    gs = GameState()
    gs.time = "morning"
    gs.current_map = make_map("village", threat=0,
                              pool=[{"id": "wolf", "weight": 1}])
    gs.enemies = {"wolf": make_enemy("wolf")}
    r = Randomizer(seed=2)
    assert check_encounter(gs, r) is None


def test_encounter_triggers_at_high_threat():
    gs = GameState()
    gs.time = "morning"
    gs.current_map = make_map("forest", threat=5,
                              pool=[{"id": "wolf", "weight": 1}])
    gs.enemies = {"wolf": make_enemy("wolf")}
    r = Randomizer(seed=1)
    assert check_encounter(gs, r) is gs.enemies["wolf"]


def test_night_in_forest_adds_ten_percent():
    pool = [{"id": "wolf", "weight": 1}]
    day_gs = GameState()
    day_gs.time = "afternoon"
    day_gs.current_map = make_map("forest", region="2", threat=0, pool=pool)
    day_gs.enemies = {"wolf": make_enemy("wolf")}
    night_gs = GameState()
    night_gs.time = "night"
    night_gs.current_map = make_map("forest", region="2", threat=0, pool=pool)
    night_gs.enemies = {"wolf": make_enemy("wolf")}
    assert check_encounter(day_gs, Randomizer(seed=3)) is None
    assert check_encounter(night_gs, Randomizer(seed=3)) is night_gs.enemies["wolf"]


def test_night_bonus_accepts_integer_region():
    gs = GameState()
    gs.time = "night"
    gs.current_map = make_map("forest", region=2, threat=0,
                              pool=[{"id": "wolf", "weight": 1}])
    gs.enemies = {"wolf": make_enemy("wolf")}
    assert check_encounter(gs, Randomizer(seed=3)) is gs.enemies["wolf"]


def test_weighted_pool_prefers_heavier_enemy():
    gs = GameState()
    gs.time = "morning"
    gs.current_map = make_map("forest", threat=8, pool=[
        {"id": "wolf", "weight": 1},
        {"id": "goblin", "weight": 9},
    ])
    gs.enemies = {"wolf": make_enemy("wolf"), "goblin": make_enemy("goblin")}
    counts = {"wolf": 0, "goblin": 0}
    for seed in range(1, 301):
        enemy = check_encounter(gs, Randomizer(seed=seed))
        assert enemy is not None
        counts[enemy.id] += 1
    assert counts["goblin"] > counts["wolf"]


def test_pool_plain_ids_default_weight_one():
    gs = GameState()
    gs.time = "morning"
    gs.current_map = make_map("forest", threat=8, pool=["wolf", "goblin"])
    gs.enemies = {"wolf": make_enemy("wolf"), "goblin": make_enemy("goblin")}
    seen = set()
    for seed in range(1, 121):
        enemy = check_encounter(gs, Randomizer(seed=seed))
        assert enemy is not None
        seen.add(enemy.id)
    assert seen == {"wolf", "goblin"}


def test_unknown_enemy_id_skipped():
    gs = GameState()
    gs.time = "morning"
    gs.current_map = make_map("forest", threat=8, pool=["wolf", "ghost"])
    gs.enemies = {"wolf": make_enemy("wolf")}
    for seed in range(1, 21):
        assert check_encounter(gs, Randomizer(seed=seed)) is gs.enemies["wolf"]


def test_unresolvable_pool_returns_none():
    gs = GameState()
    gs.time = "morning"
    gs.current_map = make_map("forest", threat=8, pool=["ghost"])
    gs.enemies = {}
    for seed in range(1, 11):
        assert check_encounter(gs, Randomizer(seed=seed)) is None


def test_empty_pool_returns_none():
    gs = GameState()
    gs.time = "morning"
    gs.current_map = make_map("forest", threat=8, pool=[])
    gs.enemies = {"wolf": make_enemy("wolf")}
    assert check_encounter(gs, Randomizer(seed=1)) is None
