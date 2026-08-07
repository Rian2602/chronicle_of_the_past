"""Sistem Formasi (GDD §7, §18.2) — data-driven buff tim.

Modul ringan: formasi dimuat dari data/formations/, buff-nya diterapkan
ke seluruh anggota tim saat pertarungan dimulai (lihat game_loop).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
FORMATION_DIR = DATA_DIR / "formations"


def load_formations(
    data_dir: Path | None = None,
) -> dict[str, dict[str, Any]]:
    """Muat semua formasi dari data/formations/, keyed by id.

    Args:
        data_dir: Direktori berisi JSON formasi (default data/formations/).

    Returns:
        Mapping formation_id -> dict skema GDD §7: ``id``, ``name``,
        ``element``, ``description``, ``buff`` (dict stat), ``skill``
        (opsional, id teknik).

    Raises:
        KeyError: Jika sebuah file JSON tidak punya kunci ``id``.
    """
    formations: dict[str, dict[str, Any]] = {}
    for path in sorted((data_dir or FORMATION_DIR).glob("*.json")):
        raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        formations[raw["id"]] = raw
    return formations


def formation_buff(
    formation_id: str,
    formations: dict[str, dict[str, Any]] | None = None,
) -> dict[str, int]:
    """Stat bonus dari sebuah formasi.

    Args:
        formation_id: ID formasi (snake_case).
        formations: Cache hasil load_formations (optional).

    Returns:
        Dict stat -> nilai bonus (mis. {"defense": 20}).

    Raises:
        ValueError: Jika formasi dengan id tersebut tidak ada.
    """
    catalog = formations if formations is not None else load_formations()
    formation = catalog.get(formation_id)
    if formation is None:
        raise ValueError(f"formasi tidak dikenal: {formation_id}")
    return dict(formation.get("buff", {}))


def formation_skill(
    formation_id: str,
    formations: dict[str, dict[str, Any]] | None = None,
) -> str | None:
    """Skill aktif dari formasi, bila ada (GDD §18.3 formation_skill).

    Args:
        formation_id: ID formasi (snake_case).
        formations: Cache hasil load_formations (optional).

    Returns:
        ID teknik formasi, atau None bila formasi tak punya skill.

    Raises:
        ValueError: Jika formasi dengan id tersebut tidak ada.
    """
    catalog = formations if formations is not None else load_formations()
    formation = catalog.get(formation_id)
    if formation is None:
        raise ValueError(f"formasi tidak dikenal: {formation_id}")
    return formation.get("skill")
