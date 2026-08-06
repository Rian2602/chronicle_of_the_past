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


def load_items(data_dir: Path = ITEM_DIR) -> dict[str, dict[str, Any]]:
    """Muat semua item dari data/items/ keyed by id.

    Skema item: ``id`` dan ``name`` wajib; ``type`` (default
    "consumable"), ``description``, ``effect``, ``price`` (harga beli
    dasar, default None), dan ``recipe`` (daftar bahan untuk refine,
    GDD §14.3) opsional. ``effect`` siap dipakai combat nanti tanpa
    menyentuh combat.py (stabil); ``price`` dipakai toko.

    Args:
        data_dir: Direktori berisi JSON item (default data/items/).

    Returns:
        Mapping item_id -> dict berisi ``id``, ``name``, ``type``,
        ``description`` (default ""), ``effect`` (default None),
        ``price`` (default None), dan ``recipe`` (default None).

    Raises:
        KeyError: Jika sebuah file JSON tidak punya kunci ``id``.
    """
    items: dict[str, dict[str, Any]] = {}
    for path in sorted(data_dir.glob("*.json")):
        raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        items[raw["id"]] = {
            "id": raw["id"],
            "name": raw["name"],
            "type": raw.get("type", "consumable"),
            "description": raw.get("description", ""),
            "effect": raw.get("effect"),
            "price": raw.get("price"),
            "recipe": raw.get("recipe"),
        }
    return items
