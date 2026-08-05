"""Test model Player (GDD §17, §19.2)."""

import pytest

from src.models.player import BASE_STATS, Player


def test_hp_max_mengikuti_vitality():
    """hp_max = 40 + vitality x 8 + bonus tingkatan (§17.2)."""
    player = Player(name="Akar")
    assert player.hp_max == 40 + BASE_STATS["vitality"] * 8


def test_qi_max_mortal_tanpa_meridian():
    """Qi maksimum mortal tanpa meridian = 10 (basis §17.2)."""
    player = Player(name="Akar")
    assert player.qi_max == 10


def test_qi_max_mengikuti_meridian_dan_bonus():
    """Qi maksimum = basis 10 + meridian x 3 + bonus tingkatan dari data."""
    player = Player(
        name="Akar",
        tier_order=2,
        meridian_buka=3,
        tier_bonus={"qi_max": 10},
    )
    assert player.qi_max == 10 + 3 * 3 + 10


def test_qi_regen_mengikuti_meridian():
    """qi_regen = 2 + meridian (§17.2)."""
    assert Player(name="Akar", meridian_buka=3).qi_regen == 5


def test_meridian_di_luar_rentang_ditolak():
    """meridian_buka dibatasi 0–8 (GDD §17.3)."""
    with pytest.raises(ValueError):
        Player(name="Akar", meridian_buka=9)


def test_add_insight_menambah_dan_menolak_negatif():
    """add_insight menambah insight dan menolak nilai negatif (§4.3)."""
    player = Player(name="Akar")
    player.add_insight(50)
    assert player.insight == 50
    with pytest.raises(ValueError):
        player.add_insight(-1)


def test_cedera_mengurangi_stat_25_persen():
    """Saat cedera, seluruh stat primer efektif berkurang 25% (§4.1)."""
    player = Player(name="Akar", injury_days_remaining=2)
    assert player.is_injured
    effective = player.effective_stats
    for key in BASE_STATS:
        assert effective[key] == int(BASE_STATS[key] * 0.75)


def test_cedera_tidak_mengubah_pool():
    """Cedera menurunkan stat primer, bukan pool hp/qi (keputusan desain)."""
    player = Player(name="Akar", injury_days_remaining=2)
    assert player.is_injured
    assert player.hp_max == 40 + BASE_STATS["vitality"] * 8
    assert player.qi_max == 10


def test_cedera_sembuh_setelah_dua_hari():
    """Cedera sementara pulih setelah 2 hari game (§4.1)."""
    player = Player(name="Akar", injury_days_remaining=2)
    player.advance_day()
    player.advance_day()
    assert not player.is_injured
    assert player.effective_stats == BASE_STATS


def test_field_ekonomi_dan_latar_default():
    """Player baru punya gold 0, background/path None (§17.3, §19.2)."""
    player = Player(name="Akar")
    assert player.gold == 0
    assert player.background is None
    assert player.path is None


def test_to_dict_memuat_skema_save():
    """to_dict memuat field player sesuai skema §19.2 + state cedera."""
    player = Player(
        name="Akar",
        background="anak_rakyat",
        path="sword",
        tier_id="qi_condensation",
        insight=150,
        gold=25,
        meridian_buka=2,
        injury_days_remaining=1,
        hp=60,
        qi=8,
    )
    assert player.to_dict() == {
        "name": "Akar",
        "background": "anak_rakyat",
        "path": "sword",
        "tier": "qi_condensation",
        "stats": BASE_STATS,
        "insight": 150,
        "gold": 25,
        "meridian_buka": 2,
        "injury_days_remaining": 1,
        "hp": 60,
        "qi": 8,
    }


def test_from_dict_roundtrip_tanpa_rekonstruksi_tier():
    """from_dict mengembalikan field dasar yang sama (§19.2)."""
    player = Player(
        name="Akar",
        background="anak_rakyat",
        path="sword",
        tier_id="qi_condensation",
        insight=150,
        gold=25,
        meridian_buka=2,
        injury_days_remaining=1,
        hp=60,
        qi=8,
    )
    restored = Player.from_dict(player.to_dict())
    assert restored.name == "Akar"
    assert restored.gold == 25
    assert restored.background == "anak_rakyat"
    assert restored.path == "sword"
    assert restored.tier_id == "qi_condensation"
    assert restored.insight == 150
    assert restored.meridian_buka == 2
    assert restored.injury_days_remaining == 1
    assert restored.hp == 60
    assert restored.qi == 8
    assert restored.stats == BASE_STATS
    # Rekonstruksi tier_order/bonus adalah tugas GameState (data-driven).
    assert restored.tier_order == 0
    assert restored.tier_bonus == {}


def test_from_dict_tanpa_nama_ditolak():
    """from_dict menolak data tanpa nama dengan ValueError (bukan KeyError)."""
    with pytest.raises(ValueError):
        Player.from_dict({"tier": "qi_condensation"})


def test_hp_qi_default_none():
    """Player baru belum punya hp/qi saat ini; penuh saat dipakai (§19.2)."""
    player = Player(name="Akar")
    assert player.hp is None
    assert player.qi is None


def test_hp_qi_negatif_ditolak():
    """hp/qi tidak boleh negatif."""
    with pytest.raises(ValueError):
        Player(name="Akar", hp=-1)
    with pytest.raises(ValueError):
        Player(name="Akar", qi=-5)


def test_from_dict_tanpa_hp_qi_ok():
    """Save lama tanpa hp/qi dimuat dengan hp/qi None (bukan error)."""
    player = Player.from_dict({"name": "Akar", "gold": 5})
    assert player.hp is None
    assert player.qi is None
