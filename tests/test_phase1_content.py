"""Uji Phase 1: wiring konten q036-q045, ultimatum, dan dialog penutup.

Mencakup (sesuai §21 story-season1-spec.md "Belum dibuat (Phase 1+)"):
- Dialog pilihan ending (q036) dengan 6 opsi ber-gerbang reputasi/flag.
- Konsekuensi ultimatum 5 hari: auto-fail quest Arc 3 q014/q016/q018/q019.
- Dialog yang menyetel flag yatim: quest015_resolved, seal_of_wisdom_ok,
  seal_of_time_ok.
- HUD menampilkan hitung mundur "Api dalam N hari" dan hint toko.
- Event rewrite_key (kunci ending F) dari semua echo.
"""

import json

from src.core.game import Game
from src.core.game_context import GameContext
from src.core.game_state import GameState
from src.engine import dialog_engine, event_engine, quest_engine
from src.models.player import Player
from src.ui import hud


def make_player(gold=100):
    return Player(
        name="Rian",
        class_id="warrior",
        hp=100,
        mp=20,
        base_stats={
            "attack": 10,
            "defense": 5,
            "hp": 100,
            "mp": 20,
            "agility": 8,
            "intelligence": 7,
        },
        gold=gold,
    )


def _game(ctx):
    game = Game(ctx, rng_seed=7)
    game.new_game("Rian", "warrior")
    return game


def ctx():
    """Konteks data permainan (dimuat sekali per proses)."""
    return GameContext(data_dir="data")


# --- Dialog pilihan ending (q036) -----------------------------------------


def test_ending_dialog_exists_and_gated():
    data = json.load(open("data/dialogues/dialog_avatar_ending.json"))
    assert data["require_flags"] == ["ending_choice_pending"]
    labels = [c["text"] for c in data["choices"]]
    assert len(labels) == 6
    assert any("Ending A" in t for t in labels)
    assert any("Ending F" in t for t in labels)
    assert "rewrite_key" in data["choices"][5].get("require_flags", [])


def test_ending_dialog_filters_by_reputation():
    gs = GameState()
    gs.player = make_player()
    gs.flags["ending_choice_pending"] = True
    gs.player.reputation = {"ancient_order": 25}
    dialog = json.load(open("data/dialogues/dialog_avatar_ending.json"))
    available = dialog_engine.available_choices(dialog, gs)
    texts = [c["text"] for c in available]
    assert any("Ending A" in t for t in texts)
    # Tanpa reputasi rebels, opsi B tersembunyi.
    assert not any("Ending B" in t for t in texts)
    # Ending E selalu tersedia.
    assert any("Ending E" in t for t in texts)
    # Ending F butuh rewrite_key.
    assert not any("Ending F" in t for t in texts)


def test_ending_choice_sets_ending_flag_and_starts_path():
    ctx_ = ctx()
    game = _game(ctx_)
    gs = game.state
    gs.flags["ending_choice_pending"] = True
    gs.player.reputation = {"rebels": 25}
    dialog = ctx_.dialogues["dialog_avatar_ending"]
    available = dialog_engine.available_choices(dialog, gs)
    chosen = next(c for c in available if "Ending B" in c["text"])
    full_index = dialog["choices"].index(chosen)
    next_id = dialog_engine.choose(gs, dialog, full_index)
    assert next_id is None
    assert gs.flags.get("ending_b") is True
    assert gs.flags.get("ending_chosen") is True
    # Event start path B memulai quest037b.
    event_engine.process_events(gs, game.randomizer)
    assert "quest037b" in gs.player.quests_active


# --- Ultimatum 5 hari: auto-fail quest Arc 3 -----------------------------


def test_ultimatum_expired_event_fails_arc3_quests():
    ctx_ = ctx()
    game = _game(ctx_)
    gs = game.state
    for qid in ("quest014", "quest016", "quest018", "quest019"):
        quest_engine.start_quest(gs, qid)
    gs.flags["ultimatum_expired"] = True
    lines = event_engine.process_events(gs, game.randomizer)
    joined = "\n".join(lines)
    assert "Quest gagal" in joined
    assert "Quest gagal" in joined
    failed = gs.player.quests_failed
    assert "quest014" in failed
    assert "quest016" in failed
    assert "quest018" in failed
    assert "quest019" in failed
    assert gs.flags.get("ultimatum_failures_applied") is True
    # Quest tidak muncul lagi di quests_active.
    assert "quest014" not in gs.player.quests_active


def test_fail_quest_advances_next_chain():
    ctx_ = ctx()
    game = _game(ctx_)
    gs = game.state
    quest_engine.start_quest(gs, "quest014")
    out = quest_engine.fail_quest(gs, "quest014")
    assert "gagal" in out
    assert "quest014" in gs.player.quests_failed
    # Rantai next (quest015) tetap dimulai agar alur utama tidak terblokir.
    assert "quest015" in gs.player.quests_active


def test_ultimatum_resolved_skips_auto_fail():
    ctx_ = ctx()
    game = _game(ctx_)
    gs = game.state
    quest_engine.start_quest(gs, "quest014")
    gs.flags["ultimatum_expired"] = True
    gs.flags["ultimatum_resolved"] = True
    event_engine.process_events(gs, game.randomizer)
    assert "quest014" not in gs.player.quests_failed
    assert "quest014" in gs.player.quests_active


# --- Dialog flag yatim -----------------------------------------------------


def test_lyra_quest015_dialog_sets_resolved():
    ctx_ = ctx()
    gs = GameState()
    gs.player = make_player()
    gs.flags["arc3_started"] = True
    dialog = ctx_.dialogues["dialog_lyra_quest015"]
    available = dialog_engine.available_choices(dialog, gs)
    chosen = next(c for c in available if "Bocorkan" in c["text"])
    full_index = dialog["choices"].index(chosen)
    dialog_engine.choose(gs, dialog, full_index)
    assert gs.flags.get("quest015_resolved") is True
    assert gs.flags.get("quest015_leaked") is True


def test_spirit_seal_wisdom_dialog_sets_ok():
    ctx_ = ctx()
    gs = GameState()
    gs.player = make_player()
    gs.flags["arc4_started"] = True
    dialog = ctx_.dialogues["dialog_spirit_seal_wisdom"]
    correct = next(c for c in dialog["choices"] if "lebih takut" in c["text"])
    full_index = dialog["choices"].index(correct)
    dialog_engine.choose(gs, dialog, full_index)
    assert gs.flags.get("seal_of_wisdom_ok") is True


def test_spirit_seal_time_dialog_sets_ok():
    ctx_ = ctx()
    gs = GameState()
    gs.player = make_player()
    gs.flags["seal_of_wisdom_ok"] = True
    dialog = ctx_.dialogues["dialog_spirit_seal_time"]
    available = dialog_engine.available_choices(dialog, gs)
    assert available, "Semua opsi selaras harus tersedia"
    full_index = dialog["choices"].index(available[0])
    dialog_engine.choose(gs, dialog, full_index)
    assert gs.flags.get("seal_of_time_ok") is True


def test_spirit_failed_offers_retry_back_to_test():
    """Regresi: dialog_spirit_failed dulu jalan buntu permanen — begitu
    flag `spirit_failed` ter-set, setiap `talk ancient_spirit` baru akan
    selalu jatuh ke dialog ini lagi (tak ada require_not_flags), sehingga
    dialog_spirit_seal_wisdom/seal_time (syarat quest024/quest025) tidak
    akan pernah tercapai lagi. Diperbaiki dengan flag `spirit_failure_
    resolved` + opsi retry yang mengarah balik ke dialog_spirit_test.
    """
    ctx_ = ctx()
    gs = GameState()
    gs.player = make_player()
    intro = ctx_.dialogues["dialog_spirit_intro"]
    dialog_engine.choose(gs, intro, 0)  # "Aku mencari Jangkar Waktu."
    test_dialog = ctx_.dialogues["dialog_spirit_test"]
    wrong = next(
        c for c in test_dialog["choices"] if "menguasai dunia" in c["text"]
    )
    dialog_engine.choose(gs, test_dialog, test_dialog["choices"].index(wrong))
    assert gs.flags.get("spirit_failed") is True

    failed = ctx_.dialogues["dialog_spirit_failed"]
    available = dialog_engine.available_choices(failed, gs)
    retry = next(c for c in available if "coba lagi" in c["text"].lower())
    next_id = dialog_engine.choose(gs, failed, failed["choices"].index(retry))
    assert next_id == "dialog_spirit_test"
    assert gs.flags.get("spirit_failure_resolved") is True


def test_spirit_failed_does_not_permanently_block_fresh_talk():
    """Setelah gagal & memilih 'Aku siap menghadapinya.', talk baru ke
    ancient_spirit tidak nyangkut selamanya di dialog_spirit_failed —
    entri lain (mis. dialog_spirit_seal_wisdom) harus tetap terjangkau
    lewat urutan seleksi npc.dialogs seperti yang dipakai _cmd_talk.
    """
    ctx_ = ctx()
    gs = GameState()
    gs.player = make_player()
    npc = ctx_.npc["ancient_spirit"]
    gs.flags["arc4_started"] = True

    intro = ctx_.dialogues["dialog_spirit_intro"]
    dialog_engine.choose(gs, intro, 0)
    test_dialog = ctx_.dialogues["dialog_spirit_test"]
    wrong = next(
        c for c in test_dialog["choices"] if "menguasai dunia" in c["text"]
    )
    dialog_engine.choose(gs, test_dialog, test_dialog["choices"].index(wrong))
    failed = ctx_.dialogues["dialog_spirit_failed"]
    accept = next(
        c for c in failed["choices"] if "siap menghadapinya" in c["text"]
    )
    dialog_engine.choose(gs, failed, failed["choices"].index(accept))

    # Replikasi loop seleksi dialog npc di _cmd_talk (game.py).
    selected = None
    for did in npc["dialogs"]:
        d = ctx_.dialogues.get(did)
        if not d:
            continue
        if not all(f in gs.flags for f in d.get("require_flags", [])):
            continue
        if any(f in gs.flags for f in d.get("require_not_flags", [])):
            continue
        selected = d
        break
    assert selected is not None
    assert selected["id"] != "dialog_spirit_failed"
    assert selected["id"] == "dialog_spirit_seal_wisdom"


# --- HUD: ultimatum & toko ------------------------------------------------


def test_hud_shows_ultimatum_countdown():
    ctx_ = ctx()
    game = _game(ctx_)
    gs = game.state
    gs.flags["ultimatum_5_days"] = True
    gs.flags["ultimatum_days_passed"] = 2
    out = hud.render(gs.player, gs, ctx_.npc)
    assert "Api dalam 3 hari" in out


def test_hud_hides_ultimatum_when_resolved():
    ctx_ = ctx()
    game = _game(ctx_)
    gs = game.state
    gs.flags["ultimatum_5_days"] = True
    gs.flags["ultimatum_resolved"] = True
    out = hud.render(gs.player, gs, ctx_.npc)
    assert "Api dalam" not in out


def test_hud_shows_shop_hint_with_catalog():
    ctx_ = ctx()
    game = _game(ctx_)
    gs = game.state
    gs.current_map = gs.world["village"]
    out = hud.render(gs.player, gs, ctx_.npc)
    assert "Toko tersedia" in out
    assert any(name in out for name in ("Marcus", "Kael", "Ben", "Helen"))


def test_hud_no_shop_hint_without_catalog():
    ctx_ = ctx()
    game = _game(ctx_)
    gs = game.state
    gs.current_map = gs.world["village"]
    out = hud.render(gs.player, gs)
    assert "Toko tersedia" not in out


# --- Event rewrite_key -----------------------------------------------------


def test_rewrite_key_event_fires_with_all_echoes():
    ctx_ = ctx()
    game = _game(ctx_)
    gs = game.state
    gs.flags["echo_1_collected"] = True
    gs.flags["echo_2_collected"] = True
    event_engine.process_events(gs, game.randomizer)
    assert gs.flags.get("rewrite_key") is True


def test_rewrite_key_not_set_without_all_echoes():
    ctx_ = ctx()
    game = _game(ctx_)
    gs = game.state
    gs.flags["echo_1_collected"] = True
    event_engine.process_events(gs, game.randomizer)
    assert gs.flags.get("rewrite_key") is None
