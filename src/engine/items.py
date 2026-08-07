"""Item (GDD §14.2) — konten nama item data-driven.

Engine hanya menyimpan item_id di state.inventory; nama tampilan dibaca
dari ``data/items/`` (pola sama dengan story.py).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.core.utils import load_json_dir

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
ITEM_DIR = DATA_DIR / "items"


def load_items(data_dir: Path = ITEM_DIR) -> dict[str, dict[str, Any]]:
    """Muat semua item dari data/items/ keyed by id.

    Args:
        data_dir: Direktori berisi JSON item (default data/items/).

    Returns:
        Mapping item_id -> dict berisi data item mentah.
    """
    return load_json_dir(data_dir)
