"""Validasi sistem ritual persiapan (GDD §21.3)."""

from src.core.state import GameState
from src.models.player import Player
from src.systems.ritual import check_ritual_ready


def _state() -> GameState:
    """State dasar untuk test ritual."""
    return GameState(player=Player(name="Akar"))


def test_ritual_belum_siap_tanpa_syarat():
    """State fresh: ritual belum siap dengan alasan yang jelas."""
    ok, reasons = check_ritual_ready(_state())
    assert ok is False
    assert len(reasons) >= 1


def test_ritual_siap_dengan_semua_syarat():
    """Artefak + formasi + tim cukup -> ritual siap."""
    state = _state()
    state.inventory["items"]["pedang_taring_naga"] = 1
    state.formation_active = "jaring_naga"
    state.party_active = ["lin_wei"]
    ok, reasons = check_ritual_ready(state)
    assert ok is True, reasons
    assert reasons == []


def test_ritual_kurang_satu_syarat():
    """Tanpa artefak ritual -> alasan menyebut artefak."""
    state = _state()
    state.formation_active = "jaring_naga"
    state.party_active = ["lin_wei"]
    ok, reasons = check_ritual_ready(state)
    assert ok is False
    assert any("Artefak" in reason for reason in reasons)
