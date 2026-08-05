"""Kompatibilitas save lama Arc 1 (spec §15/§18).

Save yang menyelesaikan quest001+quest002 sebelum update harus tetap
lanjut ke quest003 via event_arc2_gate tanpa reset. Save lama belum
punya field `progress` di quests_active maupun `quests_failed`.
"""

from src.core.game import Game
from src.core.game_context import GameContext
from src.core.game_state import GameState
from src.core.save_manager import save_game


def _write_legacy_save(path, player, flags=None):
    gs = GameState()
    gs.player = player
    gs.flags = {"quest001_done": True, "quest002_done": True, **(flags or {})}
    save_game(gs, str(path))


def test_legacy_arc1_save_continues_to_quest003(tmp_path):
    ctx = GameContext(data_dir="data")
    player = ctx.create_player("Rian", "warrior")
    player.quests_done = ["quest001", "quest002"]
    player.quests_active = {}
    path = tmp_path / "legacy.json"
    _write_legacy_save(path, player)

    g = Game(ctx)
    g.continue_game(str(path))
    assert "quest003" in g.state.player.quests_active
    assert g.state.flags.get("arc2_started") is True


def test_legacy_save_without_quests_failed_loads(tmp_path):
    ctx = GameContext(data_dir="data")
    player = ctx.create_player("Rian", "warrior")
    player.quests_done = ["quest001", "quest002"]
    path = tmp_path / "legacy.json"
    _write_legacy_save(path, player)

    g = Game(ctx)
    g.continue_game(str(path))
    assert g.state.player.quests_failed == []


def test_legacy_active_quest_without_progress_loads(tmp_path):
    """Save lama dengan quest aktif tanpa field `progress` tetap valid."""
    ctx = GameContext(data_dir="data")
    player = ctx.create_player("Rian", "warrior")
    player.quests_done = ["quest001", "quest002"]
    player.quests_active = {"quest003": {"met": []}}
    path = tmp_path / "legacy.json"
    _write_legacy_save(path, player)

    g = Game(ctx)
    g.continue_game(str(path))
    info = g.state.player.quests_active["quest003"]
    assert info.get("met") == []
    assert "progress" not in info
