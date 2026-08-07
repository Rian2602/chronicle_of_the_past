"""Data peta (GDD §9) — lokasi, nama, deskripsi, tier.

Gating akses tetap lewat flag ``map_<id>_unlocked`` dari event engine;
modul ini hanya menyediakan konten tampilan (nama + deskripsi).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.core.utils import load_json_dir

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
MAP_DIR = DATA_DIR / "maps"


def load_maps(data_dir: Path = MAP_DIR) -> dict[str, dict[str, Any]]:
    """Muat semua peta dari data/maps/ keyed by id.

    Args:
        data_dir: Direktori berisi JSON peta (default data/maps/).

    Returns:
        Mapping map_id -> dict dengan kunci ``id``, ``name``,
        ``description``, ``tier``.
    """
    return load_json_dir(data_dir)
