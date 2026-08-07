"""Tests for story engine functions including calculate_ending and build_epilogue."""

from src.core.state import GameState
from src.engine.story import build_epilogue, calculate_ending
from src.models.player import Player


def create_test_state() -> GameState:
    player = Player(name="Hero")
    return GameState(player=player)


def test_calculate_ending_highest_score() -> None:
    state = create_test_state()
    state.ending_points = {"defy": 10, "seal": 5, "reconcile": 2}
    assert calculate_ending(state) == "defy"

    state.ending_points = {"defy": 3, "seal": 8, "reconcile": 4}
    assert calculate_ending(state) == "seal"

    state.ending_points = {"defy": 1, "seal": 2, "reconcile": 5}
    assert calculate_ending(state) == "reconcile"


def test_calculate_ending_tie_breaking() -> None:
    state = create_test_state()
    # Tie all 0
    state.ending_points = {}
    assert calculate_ending(state) == "defy"

    # Tie defy and seal (5, 5, 0) -> defy wins
    state.ending_points = {"defy": 5, "seal": 5, "reconcile": 0}
    assert calculate_ending(state) == "defy"

    # Tie seal and reconcile (2, 7, 7) -> seal wins
    state.ending_points = {"defy": 2, "seal": 7, "reconcile": 7}
    assert calculate_ending(state) == "seal"

    # Tie defy and reconcile (4, 1, 4) -> defy wins
    state.ending_points = {"defy": 4, "seal": 1, "reconcile": 4}
    assert calculate_ending(state) == "defy"


def test_build_epilogue() -> None:
    state = create_test_state()
    state.reputation = {
        "court": 75,
        "holy_order": 50,
        "rebels": 0,
        "guilds": -50,
    }
    epilogue = build_epilogue(state)
    assert len(epilogue) == 4
    assert "Istana Kerajaan: berkuasa (75)" in epilogue
    assert "Orde Suci: kuat (50)" in epilogue
    assert "Pemberontak: lemah (0)" in epilogue
    assert "Gilda-gilda: hancur (-50)" in epilogue
