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
    dasar, default None), ``recipe`` (daftar bahan untuk refine,
    GDD §14.3), ``growth_stat``, dan ``max_level`` opsional. ``effect``
    siap dipakai combat nanti tanpa menyentuh combat.py (stabil);
    ``price`` dipakai toko.

    Args:
        data_dir: Direktori berisi JSON item (default data/items/).

    Returns:
        Mapping item_id -> dict berisi ``id``, ``name``, ``type``,
        ``description`` (default ""), ``effect`` (default None),
        ``price`` (default None), ``recipe`` (default None),
        ``growth_stat`` (default None), dan ``max_level`` (default None).

    Raises:
        KeyError: Jika sebuah file JSON tidak punya kunci ``id``.
    """
    items: dict[str, dict[str, Any]] = {}
    for path in sorted(data_dir.glob("*.json")):
        raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        effect = raw.get("effect")
        growth_stat = raw.get("growth_stat")
        if growth_stat is None and isinstance(effect, dict):
            growth_stat = effect.get("growth_stat")
        max_level = raw.get("max_level")
        if max_level is None and isinstance(effect, dict):
            max_level = effect.get("max_level")

        items[raw["id"]] = {
            "id": raw["id"],
            "name": raw["name"],
            "type": raw.get("type", "consumable"),
            "description": raw.get("description", ""),
            "effect": effect,
            "price": raw.get("price"),
            "recipe": raw.get("recipe"),
            "growth_stat": growth_stat,
            "max_level": max_level,
        }
    return items


def add_artifact_xp(
    state: Any,
    artifact_id: str,
    amount: int,
    catalog: dict[str, Any] | None = None,
) -> bool:
    """Tambahkan XP ke artefak; kembalikan True jika naik level."""
    if artifact_id not in state.inventory["artifacts"]:
        return False
    artifact = state.inventory["artifacts"][artifact_id]
    artifact["xp"] += amount
    leveled_up = False

    if catalog is None:
        catalog = load_items()

    max_level = catalog.get(artifact_id, {}).get("max_level")
    if max_level is None:
        max_level = 5

    while (
        artifact["level"] < max_level
        and artifact["xp"] >= artifact["level"] * 100
    ):
        artifact["xp"] -= artifact["level"] * 100
        artifact["level"] += 1
        leveled_up = True
    return leveled_up
