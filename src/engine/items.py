"""Item (GDD §14.2) — konten nama item data-driven.

Engine hanya menyimpan item_id di state.inventory; nama tampilan dibaca
dari ``data/items/`` (pola sama dengan story.py).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
ITEM_DIR = DATA_DIR / "items"


def load_items(data_dir: Path = ITEM_DIR) -> dict[str, dict[str, str]]:
    """Muat semua item dari data/items/ keyed by id.

    Args:
        data_dir: Direktori berisi JSON item (default data/items/).

    Returns:
        Mapping item_id -> dict dengan kunci ``id`` dan ``name``.

    Raises:
        KeyError: Jika sebuah file JSON tidak punya kunci ``id``.
    """
    items: dict[str, dict[str, str]] = {}
    for path in sorted(data_dir.glob("*.json")):
        raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        items[raw["id"]] = {"id": raw["id"], "name": raw["name"]}
    return items
