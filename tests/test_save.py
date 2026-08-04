import json

import pytest

from src.core.game_state import GameState
from src.core.save_manager import SaveError, load_game, save_game
from src.models.player import Player


def test_save_roundtrip(tmp_path):
    gs = GameState()
    gs.day = 3
    gs.flags["x"] = True
    p = tmp_path / "s.json"
    save_game(gs, str(p))
    gs2 = load_game(str(p), None)
    assert gs2.day == 3
    assert gs2.flags.get("x") is True


def test_save_player_roundtrip(tmp_path):
    gs = GameState()
    gs.player = Player(
        name="Rian",
        class_id="warrior",
        hp=80,
        mp=10,
        base_stats={"hp": 100, "mp": 10},
        level=2,
        gold=50,
        inventory=[{"id": "potion", "qty": 3}],
        reputation={"merchant_guild": 10},
    )
    p = tmp_path / "s.json"
    save_game(gs, str(p))
    gs2 = load_game(str(p), None)
    assert gs2.player.name == "Rian"
    assert gs2.player.level == 2
    assert gs2.player.inventory == [{"id": "potion", "qty": 3}]
    assert gs2.player.reputation["merchant_guild"] == 10


def test_save_restores_rng_seed(tmp_path):
    gs = GameState()
    gs.rng_seed = 12345
    p = tmp_path / "s.json"
    save_game(gs, str(p))
    gs2 = load_game(str(p), None)
    assert gs2.rng_seed == 12345


def test_load_missing_keys_use_defaults(tmp_path):
    p = tmp_path / "s.json"
    p.write_text(json.dumps({"version": 1}), encoding="utf-8")
    gs = load_game(str(p), None)
    assert gs.day == 1
    assert gs.time == "morning"
    assert gs.flags == {}
    assert gs.player is None


def test_load_wrong_version_raises(tmp_path):
    p = tmp_path / "s.json"
    p.write_text(json.dumps({"version": 99}), encoding="utf-8")
    with pytest.raises(SaveError):
        load_game(str(p), None)


def test_load_corrupt_file_raises(tmp_path):
    p = tmp_path / "s.json"
    p.write_text("{not json", encoding="utf-8")
    with pytest.raises(SaveError):
        load_game(str(p), None)


def test_load_missing_file_raises(tmp_path):
    with pytest.raises(SaveError):
        load_game(str(tmp_path / "nope.json"), None)


def test_save_creates_missing_directory(tmp_path):
    gs = GameState()
    path = str(tmp_path / "new_dir" / "slot1.json")
    save_game(gs, path)
    gs2 = load_game(path, None)
    assert gs2.day == 1
