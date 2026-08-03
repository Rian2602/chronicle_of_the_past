"""Benchmark performa game (stdlib only).

Mengukur 7 dimensi, tiap dimensi 50 iterasi, melaporkan median + p95.
Penanda OVER THRESHOLD bila median > 50 ms. Report-only (exit 0).

Usage: python tools/bench.py
"""

import statistics
import sys
import tempfile
import time
import tracemalloc
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core import save_manager
from src.core.game import Game
from src.core.game_context import GameContext
from src.engine import combat_engine
from src.engine.combat_interfaces import CombatAction
from src.engine.combat_engine import enemy_turn, next_turn, player_action, start_combat
from src.systems import loot_system
from src.ui import combat_view

THRESHOLD_MS = 50.0
N = 50


def _median_p95(samples_ms):
    return statistics.median(samples_ms), statistics.quantiles(samples_ms, n=20)[18]


def _new_game():
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    return ctx, g


def _start_combat(ctx, g):
    wolf = g.state.enemies["wild_wolf"]
    return start_combat(
        g.state.player,
        wolf,
        g.randomizer,
        skills=ctx.skills,
        loot_resolver=loot_system.roll_loot,
        items=g.state.items,
    )


def bench_game_context():
    samples = []
    for _ in range(N):
        t0 = time.perf_counter()
        GameContext(data_dir="data")
        samples.append((time.perf_counter() - t0) * 1000)
    return _median_p95(samples)


def bench_memory_peak():
    tracemalloc.start()
    GameContext(data_dir="data")
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak / (1024 * 1024)


def bench_save_game():
    ctx, g = _new_game()
    g._combat = _start_combat(ctx, g)
    samples = []
    with tempfile.TemporaryDirectory() as tmp:
        path = str(Path(tmp) / "slot.json")
        for _ in range(N):
            t0 = time.perf_counter()
            save_manager.save_game(g.state, path, combat=g._combat)
            samples.append((time.perf_counter() - t0) * 1000)
    return _median_p95(samples)


def bench_load_game():
    ctx, g = _new_game()
    g._combat = _start_combat(ctx, g)
    with tempfile.TemporaryDirectory() as tmp:
        path = str(Path(tmp) / "slot.json")
        save_manager.save_game(g.state, path, combat=g._combat)
        samples = []
        for _ in range(N):
            t0 = time.perf_counter()
            save_manager.load_game(path, ctx)
            samples.append((time.perf_counter() - t0) * 1000)
    return _median_p95(samples)


def bench_run_turn_non_combat():
    ctx, g = _new_game()
    samples = []
    for _ in range(N):
        t0 = time.perf_counter()
        g.run_turn("look")
        samples.append((time.perf_counter() - t0) * 1000)
    return _median_p95(samples)


def bench_run_turn_combat():
    ctx, g = _new_game()
    samples = []
    for _ in range(N):
        state = _start_combat(ctx, g)
        t0 = time.perf_counter()
        while not state.over:
            player_action(state, CombatAction.ATTACK)
            if state.over:
                break
            enemy_turn(state)
            next_turn(state)
        samples.append((time.perf_counter() - t0) * 1000)
    return _median_p95(samples)


def bench_render():
    ctx, g = _new_game()
    state = _start_combat(ctx, g)
    samples = []
    for _ in range(N):
        t0 = time.perf_counter()
        combat_view.render(state)
        samples.append((time.perf_counter() - t0) * 1000)
    return _median_p95(samples)


def main():
    results = [
        ("GameContext startup", bench_game_context()),
        ("save_game", bench_save_game()),
        ("load_game", bench_load_game()),
        ("run_turn (look)", bench_run_turn_non_combat()),
        ("run_turn (full fight)", bench_run_turn_combat()),
        ("combat_view.render", bench_render()),
    ]
    peak_mb = bench_memory_peak()

    over = []
    print(f"\nBenchmark ({N} iterasi, ambang {THRESHOLD_MS:.0f} ms)\n")
    print(f"{'Dimensi':<26}{'median (ms)':>12}{'p95 (ms)':>12}  status")
    print("-" * 60)
    for name, (median, p95) in results:
        flag = "OVER THRESHOLD" if median > THRESHOLD_MS else "ok"
        if median > THRESHOLD_MS:
            over.append(name)
        print(f"{name:<26}{median:>12.2f}{p95:>12.2f}  {flag}")
    print(f"{'GameContext peak memori':<26}{peak_mb:>12.2f} MB")
    print()

    if over:
        print("Dimensi MELEBIHI ambang (perlu optimasi):")
        for name in over:
            print(f"  - {name}")
    else:
        print("Semua dimensi di bawah ambang. Tidak ada optimasi yang diperlukan.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
