"""Sistem Artefak (GDD §7) — pertumbuhan XP & level artefak.

Logika growth dipindah dari ``src/engine/items.py`` (P1 refactor):
items.py tetap memuat katalog, sistem ini mengelola progres.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.engine.items import load_items

if TYPE_CHECKING:
    from src.core.state import GameState

# Level maksimal default bila data item tidak menyebutkan max_level.
DEFAULT_MAX_LEVEL = 5


def add_artifact_xp(
    state: GameState,
    artifact_id: str,
    amount: int,
    catalog: dict[str, Any] | None = None,
) -> bool:
    """Tambahkan XP ke artefak; kembalikan True jika naik level.

    Konsumsi XP sesuai kurva level (level * 100 per naik), artefak
    berhenti di ``max_level`` dari katalog data (default 5).

    Args:
        state: GameState yang inventory-artefaknya dimutasi.
        artifact_id: ID artefak di inventory.
        amount: Jumlah XP yang ditambahkan.
        catalog: Cache hasil load_items (optional).

    Returns:
        True jika artefak naik level; False jika tidak (atau artefak
        tidak ada di inventory).
    """
    if artifact_id not in state.inventory["artifacts"]:
        return False
    artifact = state.inventory["artifacts"][artifact_id]
    artifact["xp"] += amount
    leveled_up = False

    if catalog is None:
        catalog = load_items()

    max_level = catalog.get(artifact_id, {}).get("max_level")
    if max_level is None:
        max_level = DEFAULT_MAX_LEVEL

    while (
        artifact["level"] < max_level
        and artifact["xp"] >= artifact["level"] * 100
    ):
        artifact["xp"] -= artifact["level"] * 100
        artifact["level"] += 1
        leveled_up = True
    return leveled_up
