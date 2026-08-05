"""Unit test untuk Phase 2 — Arc 3 (quest012-020) sesuai §22.4 spec.

Mencakup:
- Integritas data: event_arc3_gate, event_arc3_complete, memory005,
  dialog_marcus_betrayal, loot sister_iris.
- Quest chain wiring: q012 -> q013 -> q014, kill count q019, boss q020.
- Hitung mundur ultimatum 5 hari terhubung ke gameplay (rest).
- Reputasi/alignment: aligned_any, ultimatum_received.
- Gate map forest_deep.
"""

from src.core.game import Game
from src.core.game_context import GameContext
from src.engine import event_engine, quest_engine
from src.engine.combat_engine import start_combat
from src.models.combat_interfaces import CombatResult
from src.systems import loot_system, travel_system
from src.ui import hud


def make_game(name="Rian", class_id="warrior", seed=7):
    ctx = GameContext(data_dir="data")
    game = Game(ctx, rng_seed=seed)
    game.new_game(name, class_id)
    return ctx, game


def force_victory(game, enemy_id):
    """Jalankan `_finish_combat` dengan kemenangan paksa atas satu musuh."""
    enemy = game.state.enemies[enemy_id]
    combat = start_combat(
        game.state.player,
        enemy,
        game.randomizer,
        skills=game.ctx.skills,
        loot_resolver=loot_system.roll_loot,
        items=game.state.items,
    )
    combat.enemy.stats["hp"] = 1
    combat.result = CombatResult.VICTORY
    combat.over = True
    combat.loot = []
    return game._finish_combat(combat)


def clear_level_ups(game):
    while game._pending_levels > 0:
        game.run_turn("select 1")


def _arc3_event(ctx, event_id):
    return next(e for e in ctx.events if e["id"] == event_id)


# ---------------------------------------------------------------------------
# Data integrity
# ---------------------------------------------------------------------------


def test_arc3_gate_event_exists_and_triggers_quest012():
    ctx = GameContext(data_dir="data")
    ev = _arc3_event(ctx, "event_arc3_gate")
    assert ev["trigger"][0]["flag"] == "boss_arc2_defeated"
    assert ev["trigger"][1]["flag"] == "arc3_started"
    assert ev["trigger"][1]["operator"] == "MISSING"
    assert {"kind": "start_quest", "id": "quest012"} in ev["actions"]
    assert any(
        a.get("kind") == "set_flag" and a.get("flag") == "arc3_started"
        for a in ev["actions"]
    )


def test_arc3_complete_event_grants_memory005():
    ctx = GameContext(data_dir="data")
    ev = _arc3_event(ctx, "event_arc3_complete")
    assert ev["trigger"][0]["flag"] == "boss_arc3_defeated"
    assert {"kind": "grant_memory", "id": "memory005"} in ev["actions"]
    assert ev["trigger"][1]["flag"] == "arc3_complete_shown"
    assert ev["trigger"][1]["operator"] == "MISSING"


def test_memory005_exists_with_correct_fields():
    ctx = GameContext(data_dir="data")
    memory = next(m for m in ctx.memories if m["id"] == "memory005")
    assert memory["title"], "title tidak boleh kosong"
    assert "Varek" in memory["text"] or "Iris" in memory["text"]
    assert "iris_revealed" in memory["flags_set"]


def test_marcus_betrayal_dialog_exists_and_gated():
    ctx = GameContext(data_dir="data")
    dialog = ctx.dialogues["dialog_marcus_betrayal"]
    assert dialog["require_flags"] == ["arc3_started"]
    assert dialog["require_not_flags"] == ["marcus_betrayal_found"]
    for choice in dialog["choices"]:
        assert "marcus_betrayal_found" in choice["set_flags"]
    assert "dialog_marcus_betrayal" in ctx.npc["marcus"]["dialogs"]


def test_sister_iris_loot_50_percent_each():
    ctx = GameContext(data_dir="data")
    for entry in ctx.enemies["sister_iris"]["loot"]:
        if entry["item"] in ("rune_blade", "rune_plate"):
            assert entry["chance"] == 50


# ---------------------------------------------------------------------------
# Quest chain wiring
# ---------------------------------------------------------------------------


def test_quest012_completes_via_talk_and_map():
    _, game = make_game()
    game.state.flags["arc3_started"] = True
    game.state.flags["map_forest_deep_unlocked"] = True
    quest_engine.start_quest(game.state, "quest012")
    quest_engine.complete_requirement(game.state, "talk", "tom")
    game.run_turn("go forest")
    game.run_turn("go forest_deep")
    assert "quest012" in game.state.player.quests_done
    assert "quest013" in game.state.player.quests_active


def test_quest013_completes_via_iris_talk_and_ultimatum_flag():
    _, game = make_game()
    game.state.flags["arc3_started"] = True
    quest_engine.start_quest(game.state, "quest013")
    game.run_turn("talk sister_iris")  # membuka dialog_iris_intro
    game.run_turn("1")  # choice 0 intro -> dialog_iris_ultimatum
    game.run_turn("1")  # choice 0 ultimatum -> dialog berakhir -> talk selesai
    assert "ultimatum_received" in game.state.flags
    assert "quest013" in game.state.player.quests_done


def test_quest014_unlocks_crime_den_via_quest013_flags():
    ctx = GameContext(data_dir="data")
    assert "map_crime_den_unlocked" in ctx.quests["quest013"][
        "flags_on_complete"
    ]
    _, game = make_game()
    game.state.flags["map_crime_den_unlocked"] = True
    game.state.current_map = game.state.world["village"]
    assert travel_system.can_travel(game.state, "crime_den") is True


def test_quest019_kill_count_inquisitor_3_via_flags():
    _, game = make_game()
    game.state.flags["arc3_started"] = True
    quest_engine.start_quest(game.state, "quest019")
    for _ in range(3):
        force_victory(game, "inquisitor_soldier")
        clear_level_ups(game)
    assert "killed_inquisitor_soldier_3" in game.state.flags
    assert "quest019" in game.state.player.quests_done


def test_quest020_boss_iris_completes_arc3():
    _, game = make_game()
    game.state.flags["arc3_started"] = True
    quest_engine.start_quest(game.state, "quest020")
    force_victory(game, "sister_iris")
    clear_level_ups(game)
    assert "boss_arc3_defeated" in game.state.flags
    event_engine.process_events(game.state, game.randomizer)
    assert "arc3_complete_shown" in game.state.flags
    assert any(
        memory["id"] == "memory005" for memory in game.state.player.memories
    )


# ---------------------------------------------------------------------------
# Ultimatum countdown integration
# ---------------------------------------------------------------------------


def test_rest_advances_day_tick_and_decrements_ultimatum():
    _, game = make_game()
    game.state.flags["ultimatum_5_days"] = True
    game.run_turn("rest")
    assert game.state.flags.get("ultimatum_days_passed") == 1
    out = hud.render(game.state.player, game.state)
    assert "Api dalam 4 hari" in out


def test_ultimatum_expires_after_5_rests():
    _, game = make_game()
    game.state.flags["ultimatum_5_days"] = True
    for _ in range(5):
        game.run_turn("rest")
    assert "ultimatum_expired" in game.state.flags


def test_expired_ultimatum_fails_arc3_quests_via_process_events():
    _, game = make_game()
    for qid in ("quest014", "quest016", "quest018", "quest019"):
        quest_engine.start_quest(game.state, qid)
    game.state.flags["ultimatum_expired"] = True
    event_engine.process_events(game.state, game.randomizer)
    for qid in ("quest014", "quest016", "quest018", "quest019"):
        assert qid in game.state.player.quests_failed
    assert game.state.flags.get("ultimatum_failures_applied") is True


def test_ultimatum_resolved_prevents_auto_fail():
    _, game = make_game()
    for qid in ("quest014", "quest016", "quest018", "quest019"):
        quest_engine.start_quest(game.state, qid)
    game.state.flags["ultimatum_expired"] = True
    game.state.flags["ultimatum_resolved"] = True
    event_engine.process_events(game.state, game.randomizer)
    assert game.state.player.quests_failed == []


def test_quest032_completion_sets_ultimatum_resolved():
    """Kemenangan pengepungan (q032) menuntaskan ultimatum secara nyata."""
    _, game = make_game()
    quest_engine.start_quest(game.state, "quest032")
    game.state.flags["killed_inquisitor_soldier_4"] = True
    quest_engine.complete_requirement(
        game.state, "flag", "killed_inquisitor_soldier_4"
    )
    assert "quest032" in game.state.player.quests_done
    assert game.state.flags.get("ultimatum_resolved") is True
    assert game.state.flags.get("siege_won") is True


# ---------------------------------------------------------------------------
# Reputation and alignment
# ---------------------------------------------------------------------------


def test_sera_offer_sets_aligned_any():
    ctx = GameContext(data_dir="data")
    dialog = ctx.dialogues["dialog_sera_offer"]
    choice = next(
        c for c in dialog["choices"]
        if "bekerja sama" in c["text"] or "pemberontak" in c["text"]
    )
    assert "aligned_any" in choice["set_flags"]


def test_iris_intro_all_choices_set_ultimatum_received():
    ctx = GameContext(data_dir="data")
    dialog = ctx.dialogues["dialog_iris_intro"]
    for choice in dialog["choices"]:
        flags = choice.get("set_flags", [])
        assert "ultimatum_received" in flags or "ultimatum_5_days" in flags


# ---------------------------------------------------------------------------
# map_forest_deep gate
# ---------------------------------------------------------------------------


def test_arc3_gate_sets_map_forest_deep_unlocked():
    ctx = GameContext(data_dir="data")
    ev = _arc3_event(ctx, "event_arc3_gate")
    assert any(
        a.get("kind") == "set_flag"
        and a.get("flag") == "map_forest_deep_unlocked"
        for a in ev["actions"]
    )


def test_travel_to_forest_deep_blocked_without_unlock():
    _, game = make_game()
    game.state.current_map = game.state.world["forest"]
    assert travel_system.can_travel(game.state, "forest_deep") is False
    game.state.flags["map_forest_deep_unlocked"] = True
    assert travel_system.can_travel(game.state, "forest_deep") is True
