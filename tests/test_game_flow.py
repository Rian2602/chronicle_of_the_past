from src.core.game_context import GameContext
from src.core.game import Game
from src.engine.combat_engine import start_combat
from src.systems import loot_system


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


def test_failed_escape_enemy_attacks_once(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    g.state.player.hp = 1000
    g.state.player.attribute_bonuses["agility"] = -100
    wolf = g.state.enemies["wild_wolf"]
    wolf.behavior = "aggressive"
    wolf.stats["hp"] = 1000
    wolf.stats["max_hp"] = 1000
    g._combat = start_combat(
        g.state.player,
        wolf,
        g.randomizer,
        skills=ctx.skills,
        loot_resolver=loot_system.roll_loot,
        items=g.state.items,
    )
    g.run_turn("escape")
    assert g._combat is not None
    attacks = sum(
        1
        for line in g._combat.log
        if "menyerang" in line or "meleset" in line or "Kritikal!" in line
    )
    assert attacks == 1


def test_dialog_gated_choice_maps_correct_branch(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    g.run_turn("talk old_man")
    g.run_turn("2")  # "Pergi." (gated-out choice not shown, so #2 is "Pergi.")
    assert g.state.flags.get("met_old_man") is None
    assert g._current_dialog is None


def test_dialog_followup_shows_npc_name_not_id(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    g.run_turn("talk old_man")
    out = g.run_turn("1")  # lanjut ke dialog berikutnya
    assert "Old Man:" in out
    assert "old_man:" not in out


def test_victory_levels_up_exactly_once(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    g.state.player.xp = 30  # 30 + 40 (wolf) = 70 -> 1 level
    wolf = g.state.enemies["wild_wolf"]
    g._combat = start_combat(
        g.state.player,
        wolf,
        g.randomizer,
        skills=ctx.skills,
        loot_resolver=loot_system.roll_loot,
        items=g.state.items,
    )
    g._combat.enemy.stats["hp"] = 1
    out = g.run_turn("attack")
    assert g.state.player.level == 2
    assert "Naik level! Kamu kini level 2." in out
