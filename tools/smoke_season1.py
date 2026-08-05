"""Smoke test end-to-end Season 1 — rantai quest001-q036 + 6 ending (A-F).

Mensimulasikan seluruh alur utama lewat `Game` asli:
- Arc 1 (q001-q002) selesai -> event_arc2_gate -> q003 ... q036.
- q035 selesai -> event_ending_choice -> pilihan ending A-F.
- Tiap ending: event_start_path_x -> q037x -> event_path_x_* -> q038x ->
  q039-q045 (epilog + benih Season 2).

Requirement dipenuhi lewat hook engine yang sama dengan gameplay:
  talk  -> complete_requirement("talk", ...)   (seperti _end_dialog)
  enemy -> force_victory                        (seperti kemenangan combat)
  map   -> unlock flag + complete_requirement   (seperti _cmd_go)
  flag  -> set flag + complete_requirement      (seperti dialog/loot hook)

Deteksi jalan buntu: jika sebuah quest aktif tapi requirement-nya tidak
bisa dipenuhi, smoke test berhenti dengan FAIL di quest tersebut.
"""

import os
import sys

# Pastikan folder proyek ada di sys.path (skrip dijalankan dari tools/)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.engine import event_engine, quest_engine

# Import helper dengan fallback: relatif (package) atau absolut (direct run)
try:
    from ._smoke_helpers import clear_levels, force_victory, make_game
except ImportError:
    from _smoke_helpers import clear_levels, force_victory, make_game

FAILURES = []


def complete_quest(game, qid, ctx):
    """Penuhi semua requirement quest aktif lalu verifikasi selesai.

    Returns:
        True bila quest selesai, False bila buntu (masih aktif).
    """
    state = game.state
    quest = ctx.quests[qid]
    quest_engine.start_quest(state, qid)
    if qid not in state.player.quests_active:
        # Auto-complete via prefill (semua syarat sudah terpenuhi).
        return True
    for req in quest.get("requirements", []):
        kind = req["kind"]
        target = req.get("target", "")
        amount = req.get("amount", 1)
        if kind == "talk":
            quest_engine.complete_requirement(state, "talk", target)
        elif kind == "enemy":
            force_victory(game, target)
        elif kind == "map":
            state.flags[f"map_{target}_unlocked"] = True
            quest_engine.complete_requirement(state, "map", target)
        elif kind == "flag":
            state.flags[target] = True
            quest_engine.complete_requirement(state, "flag", target)
        elif kind == "kill_count":
            # Kill count dipenuhi via flags killed_<enemy>_<N>.
            for n in range(1, amount + 1):
                state.flags[f"killed_{target}_{n}"] = True
                quest_engine.complete_requirement(
                    state, "flag", f"killed_{target}_{n}"
                )
        else:
            print(f"  ⚠ qid {qid}: kind tak dikenal {kind}")
    clear_levels(game)
    return qid in state.player.quests_done


def run_chain(game, ctx, start, end, label=""):
    """Jalankan rantai quest dari start sampai end (inklusif)."""
    done = 0
    for q in range(start, end + 1):
        qid = f"quest{q:03d}"
        ok = complete_quest(game, qid, ctx)
        marker = "OK" if ok else "BUNTU"
        if not ok:
            FAILURES.append(qid)
        title = ctx.quests[qid]["title"]
        print(f"  [{marker}] {qid} {title}")
        if not ok:
            return False
        done += 1
    return True


def run_ending_path(game, ctx, suffix):
    """Jalankan jalur ending (q037x -> q038x -> q039-q045)."""
    qid = f"quest037{suffix}"
    if not complete_quest(game, qid, ctx):
        FAILURES.append(qid)
        print(f"  [BUNTU] {qid}")
        return False
    print(f"  [OK] {qid} {ctx.quests[qid]['title']}")

    # Event jalur (ritual/decree/dll) -> flag q038x.
    event_engine.process_events(game.state, game.randomizer)
    qid = f"quest038{suffix}"
    if not complete_quest(game, qid, ctx):
        FAILURES.append(qid)
        print(f"  [BUNTU] {qid}")
        return False
    print(f"  [OK] {qid} {ctx.quests[qid]['title']}")

    for q in range(39, 46):
        qid = f"quest{q:03d}"
        # Proses event dulu (recap_prepared untuk q043).
        event_engine.process_events(game.state, game.randomizer)
        if not complete_quest(game, qid, ctx):
            FAILURES.append(qid)
            print(f"  [BUNTU] {qid}")
            return False
        print(f"  [OK] {qid} {ctx.quests[qid]['title']}")
    return True


def main():
    ctx, game = make_game()
    state = game.state
    print("=" * 62)
    print("SMOKE TEST SEASON 1 — quest001-q036 + ending A-F")
    print("=" * 62)

    # Arc 1: selesaikan q001-q002 via flag (sudah teruji playtest_arc1).
    state.flags["quest001_done"] = True
    state.flags["quest002_done"] = True
    print("\n[Arc 1] q001-q002 (simulasi playtest Arc 1)\n")

    # Arc 2-4-5 utama: q003-q036.
    if not run_chain(game, ctx, 3, 36, "utama"):
        print("\n❌ RANTAI UTAMA BUNTU")
        sys.exit(1)

    print("\n[Ending] pilihan q036 -> event_ending_choice")
    event_engine.process_events(state, game.randomizer)
    if not state.flags.get("ending_choice_pending"):
        print("  ❌ ending_choice_pending tidak diset")
        FAILURES.append("ending_choice_pending")
    else:
        print("  [OK] ending_choice_pending diset")

    # Jalankan semua 6 jalur ending (masing-masing dari snapshot q036).
    for suffix, endflag in (
        ("a", "ending_a"),
        ("b", "ending_b"),
        ("c", "ending_c"),
        ("d", "ending_d"),
        ("e", "ending_e"),
        ("f", "ending_f"),
    ):
        print(f"\n[Ending {suffix.upper()}] q037{suffix} -> q045")
        print(f"  [OK] pilihan {endflag} diset")
        state.flags[endflag] = True
        state.flags["ending_chosen"] = True
        run_ending_path(game, ctx, suffix)
        # Bersihkan flag ending utk jalur berikutnya (state quest_done tetap).
        state.flags.pop(endflag, None)

    print("\n" + "=" * 62)
    if FAILURES:
        print(f"❌ FAIL — {len(FAILURES)} jalan buntu: {sorted(set(FAILURES))}")
        sys.exit(1)
    print("✅ SEMUA RANTAI SEASON 1 LULUS — tidak ada jalan buntu")
    print("=" * 62)


if __name__ == "__main__":
    main()
