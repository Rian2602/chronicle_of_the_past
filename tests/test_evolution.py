"""Test evolusi binatang roh (GDD §20.3, sekali per rekan)."""

from src.models.party import Companion, load_companions


def _raw_companion() -> dict:
    return {
        "id": "serigala_bayangan",
        "name": "Serigala Bayangan",
        "tier": "foundation_establishment",
        "element": "water",
        "stats": {"attack": 15, "defense": 10, "agility": 30},
        "skills": ["qi_slash"],
        "evolution": {
            "trigger_tier": "golden_core",
            "evolved_id": "serigala_bayangan_evolved",
        },
    }


def test_from_dict_memuat_evolution():
    """from_dict membaca field evolution pada rekan."""
    companion = Companion.from_dict(_raw_companion())
    assert companion.evolution == {
        "trigger_tier": "golden_core",
        "evolved_id": "serigala_bayangan_evolved",
    }


def test_to_dict_menyimpan_evolution():
    """to_dict menyertakan evolution bila rekan memilikinya."""
    companion = Companion.from_dict(_raw_companion())
    assert companion.to_dict()["evolution"] == companion.evolution


def test_from_dict_backfill_tanpa_evolution():
    """Rekan tanpa field evolution di-backfill jadi None (save lama)."""
    raw = _raw_companion()
    del raw["evolution"]
    assert Companion.from_dict(raw).evolution is None


def test_data_companion_mempunyai_evolution_valid():
    """Data serigala_bayangan punya evolution yang ter-resolve."""
    companions = load_companions()
    by_id = {c.id: c for c in companions}
    assert by_id["serigala_bayangan"].evolution is not None
    evolved_id = by_id["serigala_bayangan"].evolution["evolved_id"]
    assert evolved_id in by_id


def _game_session_with_companion(tmp_path):
    from tests.test_game_loop import _session

    session = _session(tmp_path)
    session.new_game("Akar")
    session.state.party = [_raw_companion()]
    session.state.party_active = ["serigala_bayangan"]
    return session


def test_evolve_mengganti_rekan_saat_tier_tercapai(tmp_path):
    """Evolusi mengganti data rekan dan memperbarui party_active."""
    session = _game_session_with_companion(tmp_path)
    session.state.player.tier_id = "golden_core"
    messages = session._evolve_companions("golden_core")
    ids = [raw["id"] for raw in session.state.party]
    assert "serigala_bayangan_evolved" in ids
    assert "serigala_bayangan" not in ids
    assert any("Serigala Malam Belati" in m for m in messages)
    assert "serigala_bayangan_evolved" in session.state.party_active
