"""Test engine cerita dan penentuan ending (GDD §21)."""

from src.core.state import GameState
from src.engine.event import EventResult, apply_action
from src.engine.story import build_epilogue, calculate_ending
from src.models.player import Player


def _state() -> GameState:
    """Buat instance GameState dasar untuk pengujian."""
    return GameState(player=Player(name="Akar"))


def test_calculate_ending_defy_highest():
    """Jalur defy memiliki poin tertinggi harus mengembalikan 'defy'."""
    state = _state()
    state.ending_points = {"defy": 10, "seal": 5, "reconcile": 2}
    assert calculate_ending(state) == "defy"


def test_calculate_ending_seal_highest():
    """Jalur seal memiliki poin tertinggi harus mengembalikan 'seal'."""
    state = _state()
    state.ending_points = {"defy": 3, "seal": 8, "reconcile": 5}
    assert calculate_ending(state) == "seal"


def test_calculate_ending_reconcile_highest():
    """Jalur reconcile poin tertinggi harus mengembalikan 'reconcile'."""
    state = _state()
    state.ending_points = {"defy": 1, "seal": 4, "reconcile": 9}
    assert calculate_ending(state) == "reconcile"


def test_calculate_ending_tie_breaking_defy_over_seal():
    """Poin defy dan seal seri harus memprioritaskan 'defy'."""
    state = _state()
    state.ending_points = {"defy": 5, "seal": 5, "reconcile": 2}
    assert calculate_ending(state) == "defy"


def test_calculate_ending_tie_breaking_seal_over_reconcile():
    """Poin seal dan reconcile seri harus memprioritaskan 'seal'."""
    state = _state()
    state.ending_points = {"defy": 2, "seal": 5, "reconcile": 5}
    assert calculate_ending(state) == "seal"


def test_calculate_ending_tie_breaking_all_tied():
    """Semua poin 0 atau seri bertiga harus memprioritaskan 'defy'."""
    state = _state()
    state.ending_points = {"defy": 0, "seal": 0, "reconcile": 0}
    assert calculate_ending(state) == "defy"


def test_apply_action_calculate_ending():
    """Aksi calculate_ending harus menghitung ending dan men-set flag menang."""
    state = _state()
    state.ending_points = {"defy": 2, "seal": 7, "reconcile": 3}
    result = EventResult()
    action = {"kind": "calculate_ending"}

    apply_action(action, state, result, "evt_ending")

    assert state.flags.get("ending_seal_win") is True
    assert state.flags.get("ending_defy_win") is None
    assert state.flags.get("ending_reconcile_win") is None


def test_build_epilogue_menyebut_status_faksi():
    """Epilog menyebut tiap faksi dengan status dari reputasi (GDD §21.2)."""
    state = _state()
    state.reputation = {
        "court": 40,
        "holy_order": -60,
        "rebels": 10,
        "guilds": 0,
        "ancient_order": 70,
    }
    lines = build_epilogue(state)
    joined = "\n".join(lines)
    assert "ancient_order" in joined and "berkuasa" in joined
    assert "holy_order" in joined and "hancur" in joined
    assert len(lines) == 5
