"""Helper bersama untuk smoke test (smoke_arc3.py, smoke_season1.py).

Berisi utilitas yang duplikat antar smoke test:
- `make_game`: buat Game asli dengan seed tetap.
- `clear_levels`: habiskan level-up yang tertunda lewat UI.
- `force_victory`: selesaikan satu encounter dengan kemenangan paksa
  (meniru `_finish_combat` setelah hasil VICTORY — sama dengan
  perilaku combat engine sungguhan).

Dipanggil dengan `python tools/<smoke>.py` (sys.path[0] = tools/) maupun
dengan `PYTHONPATH=.` dari root — gunakan try/except import ganda.
"""

from src.core.game import Game
from src.core.game_context import GameContext
from src.engine.combat_engine import start_combat
from src.models.combat_interfaces import CombatResult
from src.systems import loot_system


def make_game(name="Rian", class_id="warrior", seed=7):
    """Buat Game asli dengan seed tetap; kembalikan (ctx, game)."""
    ctx = GameContext(data_dir="data")
    game = Game(ctx, rng_seed=seed)
    game.new_game(name, class_id)
    return ctx, game


def clear_levels(game):
    """Habiskan semua level-up yang tertunda lewat UI (`select 1`)."""
    while game._pending_levels > 0:
        game.run_turn("select 1")


def force_victory(game, enemy_id):
    """Selesaikan satu encounter dengan kemenangan paksa.

    Memanggil `_finish_combat` dengan CombatResult.VICTORY — jalur yang
    sama dengan kemenangan combat nyata (loot kosong biar deterministik).
    """
    state = game.state
    enemy = state.enemies[enemy_id]
    combat = start_combat(
        state.player,
        enemy,
        game.randomizer,
        skills=game.ctx.skills,
        loot_resolver=loot_system.roll_loot,
        items=state.items,
    )
    combat.enemy.stats["hp"] = 1
    combat.result = CombatResult.VICTORY
    combat.over = True
    combat.loot = []
    game._finish_combat(combat)
    clear_levels(game)
