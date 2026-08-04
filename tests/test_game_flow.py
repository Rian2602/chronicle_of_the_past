import os

import pytest

from src.core import save_manager
from src.core.game import Game, GameQuit
from src.core.game_context import GameContext
from src.engine.combat_engine import start_combat
from src.models.combat_interfaces import StatusEffect
from src.models.player import max_hp, max_mp
from src.systems import loot_system


def test_new_game_and_status(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    out = g.run_turn("status")
    assert "Rian" in out
    assert "Ashen Village" in out


def test_inventory_alias_inv_matches_inventory(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    full = g.run_turn("inventory")
    short = g.run_turn("inv")
    assert full == short
    assert "Inventaris:" in short


def test_hud_shows_objective_when_quest_active(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    g.state.flags["met_old_man"] = True
    g.run_turn("look")  # process_events starts quest001
    out = g.run_turn("status")
    assert "▶ Temui Kepala Desa" in out
    assert "Bicaralah dengan Kepala Desa" in out


def test_hud_no_objective_line_without_quest(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    out = g.run_turn("status")
    assert "▶" not in out


def test_unknown_command_shows_objective_hint(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    g.state.flags["met_old_man"] = True
    g.run_turn("look")
    out = g.run_turn("xyzzy")
    assert "Petunjuk" in out
    assert "Temui Kepala Desa" in out


def test_help_shows_current_objective(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    g.state.flags["met_old_man"] = True
    g.run_turn("look")
    out = g.run_turn("help")
    assert "Tujuan saat ini" in out


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


def test_load_command_swaps_game_state(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    g.state.player.gold = 42
    path = str(tmp_path / "s.json")
    g.run_turn(f"save {path}")
    g2 = Game(ctx)
    g2.new_game("Budi", "mage")
    out = g2.run_turn(f"load {path}")
    assert "dimuat" in out
    assert g2.state.player.name == "Rian"
    assert g2.state.player.gold == 42
    assert g2.state.player.class_id == "warrior"


def test_load_default_slot(tmp_path, monkeypatch):
    data_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "data")
    )
    monkeypatch.chdir(tmp_path)
    ctx = GameContext(data_dir=data_dir)
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    g.run_turn("save saves/slot1.json")
    assert (tmp_path / "saves" / "slot1.json").exists()
    g2 = Game(ctx)
    g2.new_game("Budi", "mage")
    out = g2.run_turn("load")
    assert "dimuat" in out
    assert g2.state.player.name == "Rian"


def test_load_bad_path_message(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    out = g.run_turn("load /tidak/ada/dir/save.json")
    assert "tidak dapat dimuat" in out


def test_load_blocked_during_combat(tmp_path):
    _, g = _mid_combat_game(tmp_path)
    path = str(tmp_path / "combat.json")
    out = g.run_turn(f"load {path}")
    assert "Tidak bisa saat bertarung" in out
    assert g._combat is not None


def test_quit_raises_game_quit(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    with pytest.raises(GameQuit):
        g.run_turn("quit")


def test_talk_npc_sets_dialog_flag(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    out = g.run_turn("talk old_man")
    assert "Aria" in out
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
    assert "Aria:" in out
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


def test_level_up_heals_hp_to_full(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    g.state.player.xp = 30  # cukup untuk naik ke level 2
    g.state.player.hp = 1
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
    assert "Pilih bonus level-up" in out
    g.run_turn("5")  # pilih HP +15
    assert g.state.player.hp == max_hp(g.state.player)
    assert g.state.player.mp == max_mp(g.state.player)


def test_quest_reward_xp_via_dialog_triggers_level_up(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    # quest001 (50 XP) = persis threshold level 2; selesaikan via dialog
    g.run_turn("talk old_man")
    g.run_turn("1")  # Triggers quest001 and quest002, moves to dialog_old_man_1
    g.run_turn("1")  # Ends dialog_old_man_1
    g.run_turn("talk village_chief")
    out = g.run_turn("1")  # Ends dialog_village_chief_met, completing quest001
    assert g.state.player.level == 2
    assert "Pilih bonus level-up" in out
    g.run_turn("1")  # pilih bonus level-up
    assert g.state.player.hp == max_hp(g.state.player)
    assert g.state.player.mp == max_mp(g.state.player)


def test_level_up_choice_applies_selected_bonus(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    g.state.player.xp = 30  # cukup untuk naik ke level 2
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
    g.run_turn("attack")
    before = g.state.player.attribute_bonuses.get("attack", 0)
    g.run_turn("1")  # pilih Serangan +2
    assert g.state.player.attribute_bonuses.get("attack", 0) == before + 2
    assert g._pending_levels == 0


def test_level_up_invalid_choice_reprompts(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    g.state.player.xp = 30
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
    g.run_turn("attack")
    out = g.run_turn("99")  # pilihan di luar jangkauan
    assert "Pilihan tidak valid" in out
    assert "Pilih bonus level-up" in out
    assert g._pending_levels == 1
    g.run_turn("look")  # perintah lain juga re-prompt, tidak mengonsumsi state
    assert g._pending_levels == 1
    g.run_turn("2")  # pilihan valid menyelesaikan level-up
    assert g._pending_levels == 0


def test_multiple_level_ups_require_multiple_choices(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    g.state.player.xp = 120  # +40 (wolf) = 160 -> naik 2 level
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
    assert g.state.player.level == 3
    assert g._pending_levels == 2
    assert "Masih ada 1 bonus level-up lagi" not in out
    out = g.run_turn("1")  # pilihan pertama
    assert "Masih ada 1 bonus level-up lagi" in out
    g.run_turn("2")  # pilihan kedua
    assert g._pending_levels == 0
    assert g.state.player.attribute_bonuses.get("attack", 0) == 2
    assert g.state.player.attribute_bonuses.get("defense", 0) == 2


def _mid_combat_game(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    wolf = g.state.enemies["wild_wolf"]
    wolf.behavior = "defensive"
    wolf.stats["hp"] = 7
    g._combat = start_combat(
        g.state.player,
        wolf,
        g.randomizer,
        skills=ctx.skills,
        loot_resolver=loot_system.roll_loot,
        items=g.state.items,
    )
    return ctx, g


def test_midcombat_save_and_continue_restores_combat(tmp_path):
    ctx, g = _mid_combat_game(tmp_path)
    path = str(tmp_path / "combat.json")
    g.run_turn(f"save {path}")
    g2 = Game(ctx)
    g2.continue_game(path)
    assert g2._combat is not None
    assert g2._combat.enemy.id == "wild_wolf"
    assert g2._combat.enemy.stats["hp"] == 7
    assert g2._combat.round_no == 1
    assert g2._combat.turn_order == g._combat.turn_order
    assert g2._combat.result is None
    assert g2._combat.randomizer.seed == g.randomizer.seed


def test_midcombat_save_restores_statuses(tmp_path):
    ctx, g = _mid_combat_game(tmp_path)
    g._combat.statuses = {
        "enemy": [StatusEffect(kind="burn", duration=3, power=5)]
    }
    path = str(tmp_path / "statuses.json")
    g.run_turn(f"save {path}")
    g2 = Game(ctx)
    g2.continue_game(path)
    effects = g2._combat.statuses.get("enemy", [])
    assert len(effects) == 1
    assert effects[0].kind == "burn"
    assert effects[0].duration == 3
    assert effects[0].power == 5


def test_midcombat_save_restores_enemy_max_hp(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    wolf = g.state.enemies["wild_wolf"]
    g._combat = start_combat(
        g.state.player,
        wolf,
        g.randomizer,
        skills=ctx.skills,
        loot_resolver=loot_system.roll_loot,
        items=g.state.items,
    )
    full_hp = g._combat.enemy.stats["max_hp"]
    assert full_hp > 5
    g._combat.enemy.stats["hp"] = 5
    path = str(tmp_path / "damaged.json")
    g.run_turn(f"save {path}")
    g2 = Game(ctx)
    g2.continue_game(path)
    assert g2._combat.enemy.stats["hp"] == 5
    assert g2._combat.enemy.stats["max_hp"] == full_hp


def test_restore_combat_does_not_mutate_shared_enemy(tmp_path):
    _, g = _mid_combat_game(tmp_path)
    wolf = g.state.enemies["wild_wolf"]
    original_hp = wolf.stats["hp"]
    g._restore_combat({"enemy_id": "wild_wolf", "enemy_hp": 5, "statuses": {}})
    assert wolf.stats["hp"] == original_hp


def test_item_command_in_combat_shows_message_not_crash(tmp_path):
    _, g = _mid_combat_game(tmp_path)
    assert "Item tidak dimiliki" in g.run_turn("item potion")
    # item tanpa argumen sekarang menampilkan pesan yang lebih berguna
    out = g.run_turn("item")
    assert "Gunakan: item" in out or "Item tersedia" in out
    assert g._combat is not None


def test_rest_blocked_during_combat(tmp_path):
    _, g = _mid_combat_game(tmp_path)
    day = g.state.day
    out = g.run_turn("rest")
    assert "Tidak bisa saat bertarung" in out
    assert g._combat is not None
    assert g.state.day == day


def test_save_and_help_allowed_during_combat(tmp_path):
    _, g = _mid_combat_game(tmp_path)
    path = str(tmp_path / "combat.json")
    out = g.run_turn(f"save {path}")
    assert "tersimpan" in out
    assert g._combat is not None
    out = g.run_turn("help")
    assert "Navigasi" in out
    assert g._combat is not None


def test_save_bad_path_shows_message_not_crash(tmp_path):
    _, g = _mid_combat_game(tmp_path)
    out = g.run_turn("save /tidak/ada/dir/save.json")
    assert "Gagal menyimpan" in out
    assert g._combat is not None


def test_continue_with_non_save_file_raises_save_error():
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    with pytest.raises(save_manager.SaveError):
        g.continue_game("data/events/events.json")


def test_continue_with_missing_player_raises_save_error(tmp_path):
    p = tmp_path / "noplayer.json"
    p.write_text('{"schema_version": 1, "flags": {}}')
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    with pytest.raises(save_manager.SaveError):
        g.continue_game(str(p))


def test_restore_combat_corrupt_result_does_not_crash(tmp_path):
    _, g = _mid_combat_game(tmp_path)
    g._combat = None
    g._restore_combat(
        {"enemy_id": "wild_wolf", "result": "bogus", "statuses": {}}
    )
    assert g._combat is not None
    assert g._combat.result is None


def test_restore_combat_unknown_enemy_skipped(tmp_path):
    _, g = _mid_combat_game(tmp_path)
    g._combat = None
    g._restore_combat(
        {"enemy_id": "ghost", "result": "victory", "statuses": {}}
    )
    assert g._combat is None


def test_finish_combat_defeat_message(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    g.state.player.hp = 1
    wolf = g.state.enemies["wild_wolf"]
    wolf.behavior = "aggressive"
    wolf.stats["hp"] = 999
    wolf.stats["max_hp"] = 999
    wolf.stats["attack"] = 99
    g._combat = start_combat(
        g.state.player,
        wolf,
        g.randomizer,
        skills=ctx.skills,
        loot_resolver=loot_system.roll_loot,
        items=g.state.items,
    )
    out = g.run_turn("attack")
    assert "Kamu gugur dalam pertarungan..." in out
    assert g._combat is None


def test_finish_combat_escape_message(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    g.state.player.attribute_bonuses["agility"] = 100
    wolf = g.state.enemies["wild_wolf"]
    wolf.stats["agility"] = 0
    g._combat = start_combat(
        g.state.player,
        wolf,
        g.randomizer,
        skills=ctx.skills,
        loot_resolver=loot_system.roll_loot,
        items=g.state.items,
    )
    out = g.run_turn("escape")
    assert "melarikan diri" in out
    assert g._combat is None


def _combat_log_attacks(state):
    return sum(
        1
        for line in state.log
        if "menyerang" in line or "meleset" in line or "Kritikal!" in line
    )


def test_observe_is_free_turn_no_enemy_action(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    g.state.player.attribute_bonuses["intelligence"] = 100
    wolf = g.state.enemies["wild_wolf"]
    g._combat = start_combat(
        g.state.player,
        wolf,
        g.randomizer,
        skills=ctx.skills,
        loot_resolver=loot_system.roll_loot,
        items=g.state.items,
    )
    out = g.run_turn("observe")
    assert "Kelemahan" in out
    assert _combat_log_attacks(g._combat) == 0


def test_item_use_is_free_turn_no_enemy_action(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    g.state.player.hp = 10
    g.state.player.inventory = [{"id": "herb", "qty": 1}]
    wolf = g.state.enemies["wild_wolf"]
    g._combat = start_combat(
        g.state.player,
        wolf,
        g.randomizer,
        skills=ctx.skills,
        loot_resolver=loot_system.roll_loot,
        items=g.state.items,
    )
    out = g.run_turn("item herb")
    assert "memulihkan 20 HP" in out
    assert _combat_log_attacks(g._combat) == 0
    assert g.state.player.hp >= 30


def test_unknown_command_message(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    out = g.run_turn("bogus_command")
    assert "Perintah tidak dikenal" in out


def test_help_mentions_typed_commands(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    out = g.run_turn("help")
    assert "load" in out
    assert "quit" in out


def test_empty_input_shows_help_hint(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    out = g.run_turn("")
    assert "Ketik 'help' untuk daftar perintah" in out


def test_use_unowned_item_message(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    out = g.run_turn("use herb")
    assert "Kamu tidak memiliki herb" in out


def test_equip_unknown_item_message(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    out = g.run_turn("equip bogus_item")
    assert "Item tidak dikenal" in out


def test_talk_unknown_npc_message(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    out = g.run_turn("talk nobody")
    assert "NPC tidak dikenal" in out


def test_save_without_path_message(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    out = g.run_turn("save")
    assert "Gunakan: save <path>" in out


def test_select_without_dialog_message(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    out = g.run_turn("1")
    assert "Tidak ada dialog aktif" in out


def test_select_without_number_does_not_crash(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    g.run_turn("talk old_man")
    out = g.run_turn("select")
    assert "Pilihan tidak valid." in out


def test_memories_empty_and_after_grant(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    out = g.run_turn("memories")
    assert "belum memiliki kenangan" in out
    g.state.flags["met_old_man"] = True
    out = g.run_turn("talk old_man")  # trigger event_first_memory
    g.run_turn("1")
    out = g.run_turn("memories")
    assert "Kenangan:" in out
    assert "Desa Terbakar" in out


def test_victory_displays_loot(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
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
    g._combat.loot_resolver = lambda enemy, rng: [{"id": "herb", "qty": 1}]
    out = g.run_turn("attack")
    assert "Loot: 1x Herb" in out
