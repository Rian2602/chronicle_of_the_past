from src.engine.dialog_engine import available_choices, choose
from src.core.game_context import GameContext
from src.core.game_state import GameState
from src.models.player import Player


def test_choice_flag_gating():
    gs = GameState()
    dialog = {"id": "d", "lines": [], "choices": [
        {"text": "A", "require_flags": ["knows_village_burns"], "set_flags": [], "next": None},
        {"text": "B", "require_flags": [], "set_flags": ["told"], "next": None}]}
    opts = available_choices(dialog, gs)
    assert len(opts) == 1 and opts[0]["text"] == "B"


def test_choice_require_not_flags_blocks():
    gs = GameState()
    gs.flags["already_spoken"] = True
    dialog = {"id": "d", "lines": [], "choices": [
        {"text": "A", "require_not_flags": ["already_spoken"], "set_flags": [], "next": None},
        {"text": "B", "require_flags": [], "set_flags": [], "next": None}]}
    opts = available_choices(dialog, gs)
    assert len(opts) == 1 and opts[0]["text"] == "B"


def test_choice_reputation_gate():
    gs = GameState()
    gs.player = Player(name="R", class_id="warrior", hp=10, mp=10,
                       base_stats={}, reputation={"merchant_guild": 15})
    dialog = {"id": "d", "lines": [], "choices": [
        {"text": "A", "require_reputation": {"merchant_guild": 20}, "set_flags": [], "next": None},
        {"text": "B", "require_reputation": {"merchant_guild": 10}, "set_flags": [], "next": None}]}
    opts = available_choices(dialog, gs)
    assert len(opts) == 1 and opts[0]["text"] == "B"


def test_choose_applies_flags_and_returns_next():
    gs = GameState()
    dialog = {"id": "d", "lines": [], "choices": [
        {"text": "A", "require_flags": [], "set_flags": ["met_old_man"], "next": "dialog_old_man_1"}]}
    assert choose(gs, dialog, 0) == "dialog_old_man_1"
    assert gs.flags.get("met_old_man") is True


def test_choose_invalid_index_returns_none():
    gs = GameState()
    dialog = {"id": "d", "lines": [], "choices": []}
    assert choose(gs, dialog, 0) is None


def test_factions_json_uses_frozen_ids():
    from src.core.constants import FACTIONS
    ctx = GameContext(data_dir="data")
    assert set(ctx.factions) == set(FACTIONS)
