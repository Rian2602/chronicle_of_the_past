"""Guard regresi: Arc 1 harus tetap bisa dimenangi oleh playtest otomatis.

Menjalankan playthrough deterministik (seed tetap) untuk tiap kelas dan
memastikan quest002 (kalahkan Wild Wolf) dapat diselesaikan. Jika keseimbangan
nerf terlalu jauh (musuh/LEVEL_CHOICES/kelas), test ini akan gagal.
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "tools"))

from playtest_arc1 import CLASSES, play_arc1  # noqa: E402

from src.core.game_context import GameContext  # noqa: E402


def test_arc1_playtest_winnable_for_all_classes():
    ctx = GameContext(data_dir="data")
    for class_id in CLASSES:
        result = play_arc1(ctx, seed=0, class_id=class_id, choice="hp")
        assert result["won"], f"{class_id} gagal menyelesaikan Arc 1: {result}"
