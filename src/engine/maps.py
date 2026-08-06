"""Data peta (GDD §9) — lokasi, nama, deskripsi, tier.

Gating akses tetap lewat flag ``map_<id>_unlocked`` dari event engine;
modul ini hanya menyediakan konten tampilan (nama + deskripsi).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
MAP_DIR = DATA_DIR / "maps"


def load_maps(data_dir: Path = MAP_DIR) -> dict[str, dict[str, Any]]:
    """Muat semua peta dari data/maps/ keyed by id.

    Args:
        data_dir: Direktori berisi JSON peta (default data/maps/).

    Returns:
        Mapping map_id -> dict dengan kunci ``id``, ``name``,
        ``description``, ``tier``.

    Raises:
        KeyError: Jika sebuah file JSON tidak punya kunci ``id``.
    """
    maps: dict[str, dict[str, Any]] = {}
    for path in sorted(data_dir.glob("*.json")):
        raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        maps[raw["id"]] = raw
    return maps
