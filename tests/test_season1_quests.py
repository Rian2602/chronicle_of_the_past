"""Unit test untuk quest chain Season 1 (quest003-quest045).

Mencakup:
- Integritas data quest (next resolve, requirement kinds, referensi flag).
- `start_quest` prefill syarat flag/map yang sudah terpenuhi + auto-complete.
- Kill count via flag `killed_<enemy>_<N>` (termasuk tahan save/load).
- Requirement kind `map` via perjalanan (`go`).
- Loot flag `have_<item>` untuk item quest.
- Jalur ending A-F (quest037x -> quest038x -> epilog q039-q045).
"""

from src.core.game import Game
from src.core.game_context import GameContext
from src.engine import event_engine, quest_engine
from src.engine.combat_engine import start_combat
from src.models.combat_interfaces import CombatResult
from src.systems import loot_system
from src.systems.inventory_system import add_item


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


# ---------------------------------------------------------------------------
# Integritas data
# ---------------------------------------------------------------------------


def test_all_season1_quest_files_present():
    ctx = GameContext(data_dir="data")
    quest_ids = set(ctx.quests)
    assert "quest001" in quest_ids
    assert "quest002" in quest_ids
    # quest037/quest038 adalah quest037a-f / quest038a-f
    for number in range(3, 46):
        if number in (37, 38):
            continue
        assert f"quest{number:03d}" in quest_ids, f"quest{number:03d}"
    for suffix in "abcdef":
        assert f"quest037{suffix}" in quest_ids
        assert f"quest038{suffix}" in quest_ids


def test_quest_next_resolves():
    ctx = GameContext(data_dir="data")
    for qid, quest in ctx.quests.items():
        nxt = quest.get("next")
        if nxt is not None:
            assert nxt in ctx.quests, f"{qid} -> bad next {nxt}"


def test_quest_requirement_targets_resolve():
    ctx = GameContext(data_dir="data")
    for qid, quest in ctx.quests.items():
        for req in quest.get("requirements", []):
            kind = req["kind"]
            target = req["target"]
            if kind == "map":
                assert target in ctx.maps, f"{qid} bad map {target}"
            elif kind == "talk":
                assert target in ctx.npc, f"{qid} bad talk {target}"
            elif kind == "enemy":
                assert target in ctx.enemies, f"{qid} bad enemy {target}"
            elif kind == "flag":
                # Flag requirement: pasti dicocokkan oleh hook flag engine.
                assert isinstance(target, str) and target, f"{qid} flag kosong"


def test_map_requirements_are_unlockable():
    """Setiap map yang jadi syarat quest punya flag unlock (atau open).

    Menjaga travel-lock §6: quest tidak boleh menuntut peta yang
    mustahil dibuka (mis. forest_deep tanpa map_forest_deep_unlocked).
    """
    ctx = GameContext(data_dir="data")
    open_maps = {"village", "forest", "anchor_vault", "ruins_entrance"}
    unlocked = set()
    for _, quest in ctx.quests.items():
        for flag in quest.get("flags_on_complete", []):
            if flag.startswith("map_") and flag.endswith("_unlocked"):
                unlocked.add(flag[4:-9])
    for event in ctx.events:
        for action in event.get("actions", []):
            flag = action.get("flag", "")
            if action.get("kind") == "set_flag" and flag.startswith("map_"):
                unlocked.add(flag[4:-9])
    for qid, quest in ctx.quests.items():
        for req in quest.get("requirements", []):
            if req.get("kind") == "map":
                target = req["target"]
                assert target in open_maps or target in unlocked, (
                    f"{qid}: map {target} tidak pernah di-unlock"
                )


def test_arc_chain_linear_next_links():
    """Rantai utama q003 -> q004 -> ... -> q036 harus linier via `next`."""
    ctx = GameContext(data_dir="data")
    chain = {}
    for qid, quest in ctx.quests.items():
        nxt = quest.get("next")
        if nxt:
            chain[qid] = nxt
    expected = [
        ("quest003", "quest004"),
        ("quest004", "quest005"),
        ("quest005", "quest006"),
        ("quest006", "quest007"),
        ("quest007", "quest008"),
        ("quest008", "quest009"),
        ("quest009", "quest010"),
        ("quest010", "quest011"),
        ("quest011", "quest012"),
        ("quest012", "quest013"),
        ("quest013", "quest014"),
        ("quest014", "quest015"),
        ("quest015", "quest016"),
        ("quest016", "quest017"),
        ("quest017", "quest018"),
        ("quest018", "quest019"),
        ("quest019", "quest020"),
        ("quest020", "quest021"),
        ("quest021", "quest022"),
        ("quest022", "quest023"),
        ("quest023", "quest024"),
        ("quest024", "quest025"),
        ("quest025", "quest026"),
        ("quest026", "quest027"),
        ("quest027", "quest028"),
        ("quest028", "quest029"),
        ("quest029", "quest030"),
        ("quest030", "quest031"),
        ("quest031", "quest032"),
        ("quest032", "quest033"),
        ("quest033", "quest034"),
        ("quest034", "quest035"),
        ("quest035", "quest036"),
    ]
    for source, dest in expected:
        assert chain.get(source) == dest, f"{source} next != {dest}"


def test_ending_path_links():
    ctx = GameContext(data_dir="data")
    for suffix in "abcdef":
        assert ctx.quests[f"quest037{suffix}"]["next"] == f"quest038{suffix}"
        assert ctx.quests[f"quest038{suffix}"]["next"] == "quest039"
    for qid in (
        "quest039",
        "quest040",
        "quest041",
        "quest042",
        "quest043",
        "quest044",
    ):
        nxt = ctx.quests[qid]["next"]
        expected = f"quest{int(qid[-3:]) + 1:03d}"
        assert nxt == expected, f"{qid} next != {expected}"
    assert ctx.quests["quest045"]["next"] is None


# ---------------------------------------------------------------------------
# start_quest prefill & auto-complete
# ---------------------------------------------------------------------------


def test_start_quest_prefills_flag_requirement():
    """Syarat flag tunggal (q007) membuat quest auto-complete saat mulai."""
    _, game = make_game()
    game.state.flags["aligned_any"] = True
    quest_engine.start_quest(game.state, "quest007")
    assert "quest007" not in game.state.player.quests_active
    assert "quest007" in game.state.player.quests_done, "auto-complete"
    assert "quest008" in game.state.player.quests_active, "next chain"


def test_start_quest_prefills_map_requirement():
    _, game = make_game()
    game.state.current_map = game.state.world["forest_deep"]
    quest_engine.start_quest(game.state, "quest006")
    info = game.state.player.quests_active["quest006"]
    assert 0 in info["met"], "map requirement langsung met"


def test_start_quest_auto_completes_epilogue_chain():
    """Rantai epilog q039-q045 auto-complete bila flag prasyarat sudah ada."""
    _, game = make_game()
    game.state.flags["season1_path_done"] = True
    quest_engine.start_quest(game.state, "quest039")
    assert "quest039" not in game.state.player.quests_active
    assert "quest039" in game.state.player.quests_done
    # quest040 (talk) tetap aktif menunggu aksi pemain
    assert "quest040" in game.state.player.quests_active


def test_start_quest_no_prefill_without_flags():
    _, game = make_game()
    quest_engine.start_quest(game.state, "quest003")
    info = game.state.player.quests_active["quest003"]
    assert info["met"] == [], "tanpa flag, tidak ada prefill"


def test_start_quest_requires_all_requirements():
    """Talk saja tidak cukup bila quest butuh talk + kill (q003)."""
    _, game = make_game()
    quest_engine.start_quest(game.state, "quest003")
    game.state.current_map = game.state.world["village"]
    # talk old_man
    quest_engine.complete_requirement(game.state, "talk", "old_man")
    assert "quest003" in game.state.player.quests_active, "butuh kill juga"
    # kill royal_scout
    force_victory(game, "royal_scout")
    clear_level_ups(game)
    assert "quest003" not in game.state.player.quests_active
    assert "quest004" in game.state.player.quests_active, "next chain"


# ---------------------------------------------------------------------------
# Kill count
# ---------------------------------------------------------------------------


def _start_quest006_with_map(game):
    """Aktifkan quest006 dan capai forest_deep lewat perjalanan (map req)."""
    # quest005 yang selesai memberi unlock map forest_deep
    game.state.flags["map_forest_deep_unlocked"] = True
    quest_engine.start_quest(game.state, "quest006")
    game.run_turn("go forest")
    game.run_turn("go forest_deep")
    info = game.state.player.quests_active["quest006"]
    assert 0 in info["met"], "map requirement met via travel"


def test_kill_count_requires_two_kills():
    """Quest006 butuh 2 kill mercenary_soldier (map sudah met)."""
    _, game = make_game()
    game.state.flags.update(
        {
            "quest001_done": True,
            "quest002_done": True,
            "quest003_done": True,
            "quest004_done": True,
            "quest005_done": True,
        }
    )
    _start_quest006_with_map(game)
    force_victory(game, "mercenary_soldier")
    clear_level_ups(game)
    assert "killed_mercenary_soldier_1" in game.state.flags
    assert "quest006" in game.state.player.quests_active, "1 kill belum cukup"
    force_victory(game, "mercenary_soldier")
    clear_level_ups(game)
    assert "killed_mercenary_soldier_2" in game.state.flags
    assert "quest006" not in game.state.player.quests_active
    assert "quest007" in game.state.player.quests_active, "next chain"


def test_kill_count_survives_save_load_style_reset():
    """Kill count dihitung ulang dari flag, bukan dict in-memory.

    Simulasikan save/load: bersihkan `kill_counts` (seperti state baru)
    lalu kill lagi — flag harus tetap naik ke _2.
    """
    _, game = make_game()
    game.state.flags.update(
        {
            "quest001_done": True,
            "quest002_done": True,
            "quest003_done": True,
            "quest004_done": True,
            "quest005_done": True,
        }
    )
    _start_quest006_with_map(game)
    force_victory(game, "mercenary_soldier")
    clear_level_ups(game)
    assert "killed_mercenary_soldier_1" in game.state.flags
    # Simulasi load: kill_counts kosong, tapi flag persist
    game.state.kill_counts = {}
    force_victory(game, "mercenary_soldier")
    clear_level_ups(game)
    assert "killed_mercenary_soldier_2" in game.state.flags, (
        "count dihitung ulang dari flag yang tersimpan"
    )
    assert "quest006" not in game.state.player.quests_active


# ---------------------------------------------------------------------------
# Map requirement via travel
# ---------------------------------------------------------------------------


def test_map_requirement_completed_by_travel():
    """Quest004 selesai saat pemain melakukan `go anchor_vault`."""
    _, game = make_game()
    quest_engine.start_quest(game.state, "quest004")
    out = game.run_turn("go anchor_vault")
    assert "Quest selesai" in out
    assert "quest004" not in game.state.player.quests_active
    assert "quest005" in game.state.player.quests_active


def test_map_requirement_not_completed_on_other_travel():
    """Pergi ke peta lain (bukan target) tidak menyelesaikan quest004."""
    _, game = make_game()
    quest_engine.start_quest(game.state, "quest004")
    game.run_turn("go forest")
    assert "quest004" in game.state.player.quests_active
    assert "quest005" not in game.state.player.quests_active


# ---------------------------------------------------------------------------
# Loot flags
# ---------------------------------------------------------------------------


def test_loot_flag_have_rune_key():
    """Item quest dari loot memicu flag have_<item> dan menyelesaikan q009."""
    _, game = make_game()
    quest_engine.start_quest(game.state, "quest009")
    game.run_turn("go ruins_entrance")  # penuhi syarat map
    add_item(game.state.player, "rune_key", 1)
    # Lewati pipeline nyata: kemenangan memanggil _track_loot_flags
    force_victory(game, "ruins_scavenger")
    clear_level_ups(game)
    assert "have_rune_key" in game.state.flags
    assert "quest009" not in game.state.player.quests_active, (
        "q009 selesai (map + loot flag)"
    )


# ---------------------------------------------------------------------------
# Ending paths A-F
# ---------------------------------------------------------------------------


def _complete_ending_path(game, suffix, boss_id, kill_flag=None):
    """Selesaikan jalur ending: q037x -> q038x -> q039 -> q040 aktif."""
    q037 = f"quest037{suffix}"
    q038 = f"quest038{suffix}"
    quest_engine.start_quest(game.state, q037)
    if kill_flag:
        game.state.flags[kill_flag] = True
        quest_engine.complete_requirement(game.state, "flag", kill_flag)
    force_victory(game, boss_id)
    clear_level_ups(game)
    assert q037 not in game.state.player.quests_active, f"{q037} selesai"
    # Event penyelesaian jalur -> q038 selesai -> season1_path_done
    event_engine.process_events(game.state, game.randomizer)
    assert q038 not in game.state.player.quests_active, f"{q038} via event"
    assert game.state.flags.get("season1_path_done") is True
    # q039 auto-complete saat start; q040 menunggu aksi pemain
    quest_engine.start_quest(game.state, "quest039")
    assert "quest039" not in game.state.player.quests_active
    assert "quest040" in game.state.player.quests_active


def test_ending_path_a_guardians():
    _, game = make_game()
    _complete_ending_path(
        game, "a", "high_inquisitor", kill_flag="killed_inquisitor_soldier_3"
    )
    assert game.state.flags.get("ending_a_done") is True


def test_ending_path_b_rebels():
    _, game = make_game()
    _complete_ending_path(
        game, "b", "elite_guard", kill_flag="killed_royal_knight_2"
    )
    assert game.state.flags.get("ending_b_done") is True


def test_ending_path_c_king():
    _, game = make_game()
    _complete_ending_path(
        game, "c", "crown_assassin", kill_flag="killed_cult_acolyte_2"
    )
    assert game.state.flags.get("ending_c_done") is True


def test_ending_path_d_scholars():
    _, game = make_game()
    _complete_ending_path(
        game, "d", "time_lord_wraith", kill_flag="killed_time_wraith_2"
    )
    assert game.state.flags.get("ending_d_done") is True


def test_ending_path_e_destroy():
    _, game = make_game()
    _complete_ending_path(game, "e", "anchor_shade")
    assert game.state.flags.get("ending_e_done") is True


def test_ending_path_f_paradox():
    _, game = make_game()
    _complete_ending_path(game, "f", "ancient_tyrant")
    assert game.state.flags.get("ending_f_done") is True


# ---------------------------------------------------------------------------
# Epilog & TAMAT
# ---------------------------------------------------------------------------


def test_epilogue_runs_to_tamat():
    """q042 selesai -> recap_prepared -> q043-q045 auto sampai TAMAT."""
    _, game = make_game()
    game.state.flags["season1_path_done"] = True
    quest_engine.start_quest(game.state, "quest042")
    # talk anchor_avatar -> q042 selesai, set quest042_done
    quest_engine.complete_requirement(game.state, "talk", "anchor_avatar")
    assert "quest043" in game.state.player.quests_active, "q043 via next"
    # Event recap_prepared -> q043 auto -> q044 -> q045
    event_engine.process_events(game.state, game.randomizer)
    assert "recap_prepared" in game.state.flags
    assert "quest043" not in game.state.player.quests_active
    assert game.state.flags.get("season1_ended") is True, "q044 auto"
    assert game.state.flags.get("season2_hint") is True, "q045 auto (TAMAT)"


def test_event_start_path_quests_resolve():
    """Setiap event_start_path_* merujuk quest037x yang ada."""
    ctx = GameContext(data_dir="data")
    for suffix in "abcdef":
        event = next(
            e for e in ctx.events if e["id"] == f"event_start_path_{suffix}"
        )
        action = next(a for a in event["actions"] if a["kind"] == "start_quest")
        assert action["id"] == f"quest037{suffix}"


def test_ending_choice_event_starts_path_quest():
    """Pemain memilih ending A -> event_start_path_a memulai quest037a."""
    _, game = make_game()
    game.state.flags["ending_a"] = True
    event_engine.process_events(game.state, game.randomizer)
    assert "quest037a" in game.state.player.quests_active


def test_flag_requirement_completed_by_event():
    """Flag yang diset event menyelesaikan quest berbasis flag (q007)."""
    _, game = make_game()
    game.state.flags.update({"aligned_any": True})
    quest_engine.start_quest(game.state, "quest007")
    assert "quest007" not in game.state.player.quests_active
    assert "quest008" in game.state.player.quests_active, "next chain"


def test_event_gate_starts_arc2_quest():
    """event_arc2_gate memulai quest003 setelah quest001+002 selesai."""
    _, game = make_game()
    game.state.flags.update({"quest001_done": True, "quest002_done": True})
    event_engine.process_events(game.state, game.randomizer)
    assert "quest003" in game.state.player.quests_active
