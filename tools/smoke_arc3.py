"""Smoke test end-to-end Phase 2 (Arc 3) via Game asli.

Alur: simulasi Arc 2 selesai -> event_arc3_gate -> quest012 (talk tom + go
forest_deep) -> quest013 (talk sister_iris + ultimatum) -> HUD countdown ->
rest -> quest014-019 -> boss quest020 sister_iris -> event_arc3_complete ->
memory005 -> quest021 (Arc 4).

Talk quest diselesaikan lewat dialog nyata bila dialog penting (iris, lyra,
marcus) atau lewat complete_requirement untuk talk biasa (tom, kade, sera,
kael) — sama dengan pola test_arc3_content.py.
"""

from src.core.game import Game
from src.core.game_context import GameContext
from src.engine import event_engine, quest_engine
from src.engine.combat_engine import start_combat
from src.models.combat_interfaces import CombatResult
from src.systems import loot_system

ctx = GameContext(data_dir="data")
g = Game(ctx, rng_seed=7)
g.new_game("Rian", "warrior")
state = g.state


def clear_levels():
    while g._pending_levels > 0:
        g.run_turn("select 1")


def force_victory(enemy_id):
    enemy = state.enemies[enemy_id]
    combat = start_combat(
        state.player,
        enemy,
        g.randomizer,
        skills=ctx.skills,
        loot_resolver=loot_system.roll_loot,
        items=state.items,
    )
    combat.enemy.stats["hp"] = 1
    combat.result = CombatResult.VICTORY
    combat.over = True
    combat.loot = []
    g._finish_combat(combat)
    clear_levels()


def end_talk(npc_id):
    """Selesaikan requirement talk quest seperti _end_dialog."""
    msg = quest_engine.complete_requirement(state, "talk", npc_id)
    if msg and msg != "Tidak ada syarat yang sesuai.":
        print(f"    (talk {npc_id} -> {msg})")


ok = []


def check(label, cond):
    assert cond, f"FAIL: {label}"
    ok.append(label)
    print(f"  OK {label}")


# ===== STEP 1: Simulasikan Arc 2 selesai =====
state.flags["boss_arc2_defeated"] = True
state.flags["quest011_done"] = True
print("[1] Simulasi Arc 2 selesai (boss_arc2_defeated)")

# ===== STEP 2: event_arc3_gate -> quest012 =====
lines = event_engine.process_events(state, g.randomizer)
joined = "\n".join(lines)
check(
    "event_arc3_gate memicu quest012",
    "quest012" in state.player.quests_active,
)
check("arc3_started diset", state.flags.get("arc3_started") is True)

check(
    "map_forest_deep_unlocked diset",
    state.flags.get("map_forest_deep_unlocked") is True,
)
print("    banner:", [ln for ln in lines if "ARC 3" in ln])

# ===== STEP 3: quest012 =====
print("[2] quest012 (Api di Tepi Hutan)")
state.current_map = state.world["village"]
g.run_turn("talk tom")
end_talk("tom")
clear_levels()
g.run_turn("go forest")
g.run_turn("go forest_deep")
clear_levels()
check("quest012 selesai", "quest012" in state.player.quests_done)
check("quest013 aktif", "quest013" in state.player.quests_active)

# ===== STEP 4: quest013 - dialog iris nyata =====
print("[3] quest013 (Gereja yang Menghakimi)")
state.current_map = state.world["village"]
g.run_turn("talk sister_iris")  # dialog_iris_intro
g.run_turn("1")  # -> dialog_iris_ultimatum
g.run_turn("1")  # pilih ultimatum -> dialog berakhir -> talk selesai
clear_levels()
check("ultimatum_received diset", state.flags.get("ultimatum_received") is True)
check("ultimatum_5_days diset", state.flags.get("ultimatum_5_days") is True)
check("quest013 selesai", "quest013" in state.player.quests_done)
check("quest014 aktif", "quest014" in state.player.quests_active)
check("map_crime_den_unlocked", state.flags.get("map_crime_den_unlocked"))

# ===== STEP 5: HUD countdown =====
print("[4] HUD hitung mundur")
from src.ui import hud  # noqa: E402  (impor lokal setelah state siap)

htxt = hud.render(state.player, state, ctx.npc)
check("HUD: Api dalam 5 hari", "Api dalam 5 hari" in htxt)

# ===== STEP 6: rest -> day tick =====
print("[5] rest -> process_day_tick")
g.run_turn("rest")
clear_levels()
print("    ultimatum_days_passed =", state.flags.get("ultimatum_days_passed"))
htxt2 = hud.render(state.player, state, ctx.npc)
check("HUD: Api dalam 4 hari", "Api dalam 4 hari" in htxt2)

# ===== STEP 7: quest014 (crime_den) =====
print("[6] quest014 (Sarang Serigala Malam)")
state.current_map = state.world["village"]
g.run_turn("go crime_den")
g.run_turn("talk kade")
end_talk("kade")
clear_levels()
check("quest014 selesai", "quest014" in state.player.quests_done)
check("quest015 aktif", "quest015" in state.player.quests_active)
check("have_evidence_letter", state.flags.get("have_evidence_letter") is True)

# ===== STEP 8: quest015 via dialog lyra =====
print("[7] quest015 (Harga Sebuah Nama)")
state.current_map = state.world["village"]
g.run_turn("talk lyra")
g.run_turn("1")
clear_levels()
check("quest015_resolved diset", state.flags.get("quest015_resolved") is True)
check("quest015 selesai", "quest015" in state.player.quests_done)
check("quest016 aktif", "quest016" in state.player.quests_active)

# ===== STEP 9: quest016-019 =====
print("[8] quest016-019")
# rebel_camp hanya bisa diakses via forest_deep (forest_deep.exits)
state.current_map = state.world["village"]
g.run_turn("go forest")
g.run_turn("go forest_deep")
g.run_turn("go rebel_camp")
g.run_turn("talk sera")
end_talk("sera")
clear_levels()
check("quest016 selesai", "quest016" in state.player.quests_done)
if "have_old_scrolls" not in state.flags:
    # Simulasi collect: set flag + panggil hook flag (seperti _track_loot_flags)
    state.flags["have_old_scrolls"] = True
    quest_engine.complete_requirement(state, "flag", "have_old_scrolls")
state.current_map = state.world["village"]
g.run_turn("talk kael")
end_talk("kael")
clear_levels()
check("quest017 selesai", "quest017" in state.player.quests_done)
state.current_map = state.world["village"]
g.run_turn("talk marcus")
g.run_turn("1")
clear_levels()
force_victory("guild_guard")
check("quest018 selesai", "quest018" in state.player.quests_done)
check("marcus_betrayal_found", state.flags.get("marcus_betrayal_found") is True)
for _ in range(3):
    force_victory("inquisitor_soldier")
check("quest019 selesai", "quest019" in state.player.quests_done)
check("quest020 aktif", "quest020" in state.player.quests_active)

# ===== STEP 10: boss quest020 -> arc3_complete =====
print("[9] quest020 (Api Hakim - BOSS Iris)")
force_victory("sister_iris")
check("quest020 selesai", "quest020" in state.player.quests_done)
check("boss_arc3_defeated", state.flags.get("boss_arc3_defeated") is True)
lines2 = event_engine.process_events(state, g.randomizer)
joined2 = "\n".join(lines2)
check("event_arc3_complete memicu", "ARC 3 SELESAI" in joined2)
check(
    "arc3_complete_shown diset",
    state.flags.get("arc3_complete_shown") is True,
)
mem_ids = [m["id"] for m in state.player.memories]
print("    memories:", mem_ids)
check("memory005 diberikan", "memory005" in mem_ids)
check("quest021 aktif (Arc 4)", "quest021" in state.player.quests_active)

print(f"\n=== SEMUA {len(ok)} SMOKE CHECK LULUS ===")
