"""Sistem Rekan Tim (GDD §20) — evolusi & penetasan binatang roh.

Logika evolusi/penetasan dipindah dari ``src/core/game_loop.py``
(P1 refactor): game_loop tetap menyusun pesan UI; sistem ini satu-satunya
jalur yang memutasi ``state.party`` / ``state.party_active``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.models.party import load_companion

if TYPE_CHECKING:
    from src.core.state import GameState


def hatch_companion(state: GameState, companion_id: str) -> str | None:
    """Tetaskan binatang roh ke tim; None bila rekan sudah bergabung.

    Menambahkan rekan ke ``state.party`` (data dari data/companions/)
    dan, bila slot aktif tersedia (< 3), langsung mengaktifkannya.

    Args:
        state: GameState yang party-nya dimutasi.
        companion_id: ID rekan (snake_case).

    Returns:
        Pesan narasi bila menetas; None bila rekan sudah di tim
        (pemanggil menangani pesannya sendiri).
    """
    ids = [raw["id"] for raw in state.party]
    if companion_id in ids:
        return None
    companion = load_companion(companion_id)
    state.party.append(companion.to_dict())
    if len(state.party_active) < 3:
        state.party_active.append(companion_id)
    return f"Telur menetas: {companion.name} bergabung!"


def evolve_companions(state: GameState, tier_id: str) -> list[str]:
    """Evolusi binatang roh saat tier terpicu (GDD §20.3, sekali).

    Rekan dengan ``evolution.trigger_tier == tier_id`` diganti datanya
    dari companion ``evolved_id``, mempertahankan bond_xp/rank serta
    hp/qi saat ini. Rekan hasil evolusi tak punya field evolution ->
    tidak berevolusi lagi. ``party_active`` ikut dipetakan ke id baru.

    Args:
        state: GameState yang party-nya dimutasi.
        tier_id: Tier pemain setelah breakthrough.

    Returns:
        Daftar pesan evolusi untuk ditampilkan (kosong bila tak ada).
    """
    messages: list[str] = []
    replaced: dict[str, str] = {}
    for raw in state.party:
        evolution = raw.get("evolution")
        if not evolution or evolution.get("trigger_tier") != tier_id:
            continue
        evolved_id = evolution["evolved_id"]
        evolved = load_companion(evolved_id)
        evolved.bond_xp = int(raw.get("bond_xp", 0))
        evolved.rank = int(raw.get("rank", 1))
        evolved.hp = raw.get("hp")
        evolved.qi = raw.get("qi")
        replaced[raw["id"]] = evolved_id
        raw.clear()
        raw.update(evolved.to_dict())
        messages.append(
            f"{evolved.name} berevolusi! Bentuk barunya "
            "berdenyut dengan kekuatan baru."
        )
    if replaced:
        party_ids = {raw["id"] for raw in state.party}
        state.party_active = [
            replaced.get(cid, cid)
            for cid in state.party_active
            if replaced.get(cid, cid) in party_ids
        ]
    return messages
