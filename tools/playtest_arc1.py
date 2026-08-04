"""Playtest otomatis Arc 1 — memverifikasi quest utama masih bisa dimenangi.

Strategi pemain sederhana (pola bermain optimal):
- Pilih bonus level-up sesuai --choice (default HP untuk ketahanan).
- Istirahat (rest) bila HP < 60% — pemulihan penuh di luar pertarungan.
- Saat bertarung: serang; pakai item pemulih bila HP rendah; kabur bila kritis.

Menjalankan:  python3 tools/playtest_arc1.py [--count N] [--class CLASS]
              [--choice hp]
              python3 tools/playtest_arc1.py --count 30 --all-classes
"""

import argparse
import os
import sys

# Pastikan folder proyek ada di sys.path (skrip dijalankan dari tools/)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.game import Game
from src.core.game_context import GameContext
from src.models.player import max_hp

LEVEL_CHOICE_INDEX = {
    "attack": "1",
    "defense": "2",
    "agility": "3",
    "intelligence": "4",
    "hp": "5",
    "mp": "6",
    "skill_point": "7",
}
CLASSES = ["assassin", "warrior", "mage", "ranger", "scholar"]
MAX_STEPS = 300
MAX_FIGHT_TURNS = 100


def choose_pending_levels(game, choice_key):
    """Selesaikan semua pilihan level-up yang tertunda."""
    while getattr(game, "_pending_levels", 0) > 0:
        game.run_turn(LEVEL_CHOICE_INDEX[choice_key])


def _heal_items(game):
    player = game.state.player
    return [
        e["id"]
        for e in player.inventory
        if game.state.items.get(e["id"]) is not None
        and game.state.items[e["id"]].heal
    ]


def fight(game, choice_key):
    """Jalankan pertarungan sampai selesai.

    Return hasil: victory/defeat/escaped/timeout.
    """
    guard = 0
    while game._combat is not None and guard < MAX_FIGHT_TURNS:
        guard += 1
        player = game.state.player
        heal_items = _heal_items(game)
        if player.hp <= 12 and heal_items:
            out = game.run_turn(f"item {heal_items[0]}")
        elif player.hp <= 8:
            out = game.run_turn("escape")
            if "Kamu gugur" in out:
                # escape gagal dan serangan balik musuh membunuh pemain
                choose_pending_levels(game, choice_key)
                return "defeat"
            if game._combat is None:
                choose_pending_levels(game, choice_key)
                return "escaped"
            continue
        else:
            out = game.run_turn("attack")
        if game._combat is None:
            choose_pending_levels(game, choice_key)
            if "Kemenangan!" in out:
                return "victory"
            if "Kamu gugur" in out:
                return "defeat"
            return "escaped"
    return "timeout"


def play_arc1(ctx, seed, class_id="assassin", choice="hp"):
    game = Game(ctx, rng_seed=seed)
    game.new_game("Smoke", class_id)

    # Walkthrough dialog Arc 1: Aria → Kepala Desa → quest001 selesai → level 2
    game.run_turn("talk old_man")
    game.run_turn("1")
    game.run_turn("1")
    game.run_turn("talk village_chief")
    game.run_turn("1")
    choose_pending_levels(game, choice)
    game.run_turn("go forest")

    steps = 0
    deaths = 0
    while steps < MAX_STEPS:
        # Arc 1 tuntas = banner percabangan waktu muncul
        # (quest001 + quest002 selesai)
        if "arc1_divergence_shown" in game.state.flags:
            return {
                "won": True,
                "deaths": deaths,
                "steps": steps,
                "level": game.state.player.level,
                "seed": seed,
            }
        choose_pending_levels(game, choice)
        if game.state.player.hp < max_hp(game.state.player) * 0.6:
            game.run_turn("rest")
            continue
        game.run_turn("explore")
        if game._combat is not None:
            result = fight(game, choice)
            if result == "defeat":
                deaths += 1
                game.run_turn("rest")  # HP 0 → pulihkan penuh
            elif result == "timeout":
                return {
                    "won": False,
                    "deaths": deaths,
                    "steps": steps,
                    "level": game.state.player.level,
                    "seed": seed,
                }
        steps += 1
    return {
        "won": False,
        "deaths": deaths,
        "steps": steps,
        "level": game.state.player.level,
        "seed": seed,
    }


def run_batch(ctx, count, class_id, choice):
    results = [
        play_arc1(ctx, seed, class_id=class_id, choice=choice)
        for seed in range(count)
    ]
    wins = sum(1 for r in results if r["won"])
    deaths = sum(r["deaths"] for r in results)
    avg_steps = sum(r["steps"] for r in results) / len(results)
    avg_level = sum(r["level"] for r in results) / len(results)
    return {
        "class": class_id,
        "choice": choice,
        "seeds": count,
        "wins": wins,
        "rate": wins / count * 100,
        "deaths": deaths,
        "avg_steps": avg_steps,
        "avg_level": avg_level,
    }


def main():
    parser = argparse.ArgumentParser(description="Playtest otomatis Arc 1")
    parser.add_argument(
        "--count", type=int, default=10, help="jumlah seed per kelas"
    )
    parser.add_argument(
        "--class",
        dest="class_id",
        default="assassin",
        help="kelas (assassin/warrior/mage/ranger/scholar)",
    )
    parser.add_argument(
        "--choice", default="hp", choices=sorted(LEVEL_CHOICE_INDEX)
    )
    parser.add_argument(
        "--all-classes", action="store_true", help="jalankan untuk semua kelas"
    )
    args = parser.parse_args()

    ctx = GameContext(data_dir="data")
    classes = CLASSES if args.all_classes else [args.class_id]

    print(
        f"{'Kelas':<12}{'Seed':>5}{'Menang':>7}{'Tingkat':>9}"
        f"{'Mati':>6}{'Rata2 langkah':>14}{'Rata2 lvl':>10}"
    )
    print("-" * 63)
    overall_wins = 0
    overall_count = 0
    for cls in classes:
        row = run_batch(ctx, args.count, cls, args.choice)
        overall_wins += row["wins"]
        overall_count += row["seeds"]
        print(
            f"{cls:<12}{row['seeds']:>5}{row['wins']:>7}"
            f"{row['rate']:>8.0f}%{row['deaths']:>6}"
            f"{row['avg_steps']:>14.1f}{row['avg_level']:>10.1f}"
        )
    print("-" * 63)
    print(
        f"Total: {overall_wins}/{overall_count} menang "
        f"({overall_wins / overall_count * 100:.0f}%)"
    )


if __name__ == "__main__":
    main()
