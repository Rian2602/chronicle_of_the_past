"""Unit test perbaikan unlock crime_den untuk quest008 (Arc 2).

Latar belakang: quest008 (Punggung Pisau) butuh `talk kade` di crime_den,
tapi `map_crime_den_unlocked` sebelumnya hanya diset quest013 (Arc 3) —
pemain terkunci. Sesuai spec §10.2 (unlock via dialog Aria/Lyra),
`dialog_lyra_main` pilihan 0 kini menyetel `map_crime_den_unlocked`.

Mencakup:
- Data: dialog_lyra_main menyetel map_crime_den_unlocked.
- Travel: crime_den bisa dituju di Arc 2 setelah dialog Lyra.
- Quest: q008 selesai via rantai dialog Kade (intro -> offer -> paid).
"""

from src.core.game import Game
from src.core.game_context import GameContext
from src.engine import quest_engine
from src.systems import travel_system


def make_game(name="Rian", class_id="warrior", seed=7):
    ctx = GameContext(data_dir="data")
    game = Game(ctx, rng_seed=seed)
    game.new_game(name, class_id)
    return ctx, game


def clear_level_ups(game):
    while game._pending_levels > 0:
        game.run_turn("select 1")


def _setup_arc2_to_quest008(game, ctx):
    """Siapkan state Arc 2 sampai quest008 aktif (shortcut setup, bukan

    simulasi penyelesaian sesungguhnya: requirement dipenuhi langsung dan
    `next` chain tidak dijalankan engine).
    """
    state = game.state
    state.flags["arc2_started"] = True
    for qid in ("quest003", "quest004", "quest005", "quest006", "quest007"):
        quest_engine.start_quest(state, qid)
        for req in ctx.quests[qid]["requirements"]:
            kind, target = req["kind"], req.get("target", "")
            if kind == "talk":
                quest_engine.complete_requirement(state, "talk", target)
            elif kind == "flag":
                state.flags.setdefault(target, True)
                quest_engine.complete_requirement(state, "flag", target)
            elif kind == "enemy":
                quest_engine.complete_requirement(state, "enemy", target)
            elif kind == "map":
                state.flags[f"map_{target}_unlocked"] = True
        for flag in ctx.quests[qid].get("flags_on_complete", []):
            state.flags[flag] = True
    quest_engine.start_quest(state, "quest008")
    game._apply_pending_levels([])
    clear_level_ups(game)


# ---------------------------------------------------------------------------
# Data: unlock via dialog Lyra
# ---------------------------------------------------------------------------


def test_lyra_main_dialog_sets_crime_den_unlock():
    ctx, _ = make_game()
    dialog = ctx.dialogues["dialog_lyra_main"]
    choice = dialog["choices"][0]
    assert "map_crime_den_unlocked" in choice["set_flags"]
    # Quest013 tetap sumber unlock kedua (idempoten, tidak konflik).
    assert "map_crime_den_unlocked" in ctx.quests["quest013"][
        "flags_on_complete"
    ]


# ---------------------------------------------------------------------------
# Travel: crime_den bisa dituju di Arc 2 setelah dialog Lyra
# ---------------------------------------------------------------------------


def test_crime_den_locked_before_lyra_dialog():
    _, game = make_game()
    game.state.current_map = game.state.world["village"]
    assert travel_system.can_travel(game.state, "crime_den") is False


def test_crime_den_travel_available_after_lyra_dialog():
    _, game = make_game()
    game.state.flags["arc2_started"] = True
    game.state.current_map = game.state.world["village"]
    game.run_turn("talk lyra")
    game.run_turn("1")  # "Ceritakan tentang batu yang berdenyut"
    clear_level_ups(game)
    assert game.state.flags.get("map_crime_den_unlocked") is True
    assert travel_system.can_travel(game.state, "crime_den") is True


def test_other_lyra_choices_do_not_unlock_crime_den():
    _, game = make_game()
    game.state.flags["arc2_started"] = True
    game.state.current_map = game.state.world["village"]
    game.run_turn("talk lyra")
    game.run_turn("2")  # "Bagaimana aku bisa masuk ke reruntuhan?"
    clear_level_ups(game)
    assert game.state.flags.get("map_crime_den_unlocked") is None
    assert travel_system.can_travel(game.state, "crime_den") is False


# ---------------------------------------------------------------------------
# Quest: q008 selesai via dialog Kade
# ---------------------------------------------------------------------------


def test_quest008_completes_via_kade_dialog():
    ctx, game = make_game()
    _setup_arc2_to_quest008(game, ctx)
    state = game.state
    assert "quest008" in state.player.quests_active

    # Buka crime_den lewat dialog Lyra (jalur Arc 2 yang benar).
    state.current_map = state.world["village"]
    game.run_turn("talk lyra")
    game.run_turn("1")
    clear_level_ups(game)
    assert travel_system.can_travel(state, "crime_den") is True

    # Travel ke crime_den lalu bicara Kade.
    state.current_map = state.world["village"]
    game.run_turn("go crime_den")
    assert state.current_map.id == "crime_den"

    # Rantai dialog Kade: intro -> offer (bayar) -> paid (dialog berakhir).
    game.run_turn("talk kade")  # dialog_kade_intro
    game.run_turn("1")  # "Aku mencari informasi" -> kade_met -> offer
    game.run_turn("1")  # "Aku bayar" -> kade_deal_done -> paid
    game.run_turn("1")  # "Varek..." -> next null -> dialog berakhir
    clear_level_ups(game)

    assert state.flags.get("kade_met") is True
    assert state.flags.get("kade_deal_done") is True
    assert state.flags.get("knows_varek_name") is True
    assert "quest008" in state.player.quests_done
    assert "quest009" in state.player.quests_active


def test_quest008_requires_kade_deal_flag():
    ctx, game = make_game()
    _setup_arc2_to_quest008(game, ctx)
    state = game.state
    state.flags["map_crime_den_unlocked"] = True
    # Talk saja tidak cukup — harus ada flag kade_deal_done dari dialog.
    quest_engine.complete_requirement(state, "talk", "kade")
    assert "quest008" not in state.player.quests_done
    state.flags["kade_deal_done"] = True
    quest_engine.complete_requirement(state, "flag", "kade_deal_done")
    assert "quest008" in state.player.quests_done
