"""Sistem Faksi (GDD §8) — reputasi 5 faksi dengan clamp.

Logika reputasi dipindah dari ``src/core/state.py`` (P1 refactor):
state tetap menyimpan data reputasi, fungsi ini satu-satunya jalur mutasi.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.state import GameState

# Faksi kanonik (GDD §8) — urutan tetap, lima faksi.
FACTIONS = ("court", "holy_order", "rebels", "guilds", "ancient_order")
# Reputasi faksi dibatasi -100 s/d +100 (GDD §8).
REPUTATION_CLAMP = 100


def add_reputation(state: GameState, faction: str, delta: int) -> None:
    """Ubah reputasi faksi dengan batas -100 s/d +100 (GDD §8).

    Satu-satunya jalur mutasi reputasi (dipakai event & quest).
    Faksi di luar daftar kanonik ditolak keras, bukan ditambahkan
    diam-diam (kunci ekstra akan dibuang saat round-trip save).

    Args:
        state: GameState yang reputasinya dimutasi.
        faction: ID faksi (court/holy_order/rebels/guilds/ancient_order).
        delta: Perubahan nilai (bisa negatif).

    Raises:
        ValueError: Jika faksi tidak dikenal.
    """
    if faction not in FACTIONS:
        raise ValueError(f"faksi tidak dikenal: {faction}")
    current = state.reputation.get(faction, 0)
    state.reputation[faction] = max(
        -REPUTATION_CLAMP, min(REPUTATION_CLAMP, current + delta)
    )
