"""Sistem ritual persiapan melawan entitas kuno (GDD §21.3).

Ritual butuh artefak kunci, formasi terpasang, dan tim yang cukup.
Pengecekan murni state; perintah ``ritual`` di game_loop yang
menjalankannya dan men-set ``ritual_ready``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.state import GameState

# Artefak ritual kunci (GDD §21.3) — harus ada di inventory.
RITUAL_ARTIFACT = "pedang_taring_naga"
# Jumlah anggota tim minimal (protagonis + rekan aktif).
RITUAL_MIN_TEAM = 2


def check_ritual_ready(state: GameState) -> tuple[bool, list[str]]:
    """Periksa apakah ritual persiapan sudah lengkap.

    Syarat (GDD §21.3): artefak ritual di inventory, formasi terpasang,
    dan tim minimal 2 anggota.

    Args:
        state: GameState permainan saat ini.

    Returns:
        Tuple (siap, daftar alasan yang belum terpenuhi). ``siap`` True
        bila semua syarat terpenuhi.
    """
    reasons: list[str] = []
    items = state.inventory.get("items", {})
    if items.get(RITUAL_ARTIFACT, 0) < 1:
        reasons.append("Artefak ritual (Pedang Taring Naga) belum dimiliki.")
    if not state.formation_active:
        reasons.append("Formasi belum terpasang.")
    if len(state.party_active) + 1 < RITUAL_MIN_TEAM:
        reasons.append("Tim terlalu kecil untuk ritual.")
    return (not reasons, reasons)
