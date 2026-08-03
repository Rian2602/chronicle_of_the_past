from src.core.game_context import GameContext
from src.core.game import Game


def test_new_game_and_status(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    out = g.run_turn("status")
    assert "Rian" in out
    assert "Ashen Village" in out


def test_travel_to_forest(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    out = g.run_turn("go forest")
    assert "Forest" in out
    assert g.state.current_map.id == "forest"


def test_travel_invalid_destination(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    out = g.run_turn("go capital")
    assert "Tidak ada jalan" in out


def test_save_and_continue(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    path = str(tmp_path / "s.json")
    g.run_turn(f"save {path}")
    g2 = Game(ctx)
    g2.continue_game(path)
    assert g2.state.player.name == "Rian"
    assert g2.state.day == g.state.day


def test_talk_npc_sets_dialog_flag(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    out = g.run_turn("talk old_man")
    assert "Old Man" in out
    g.run_turn("1")  # pick "Siapa Anda?" -> next dialog_old_man_1
    assert g.state.flags.get("met_old_man") is True


def test_rest_heals(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    g.state.player.hp = 10
    out = g.run_turn("rest")
    assert "morning" in out
    assert g.state.player.hp >= 50
