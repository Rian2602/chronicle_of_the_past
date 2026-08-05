"""Test engine kultivasi: loader, insight, dan breakthrough (GDD §4.1)."""

import pytest

from src.engine.cultivation import (
    BASE_SUCCESS_RATE,
    INJURY_DAYS,
    RATE_CAP,
    attempt_breakthrough,
    breakthrough_rate,
    can_breakthrough,
    load_tiers,
    next_tier,
)
from src.models.player import BASE_STATS, Player


class _FixedRng:
    """RNG deterministik dengan nilai tetap."""

    def __init__(self, value: float) -> None:
        self.value = value

    def random(self) -> float:
        """Kembalikan nilai tetap."""
        return self.value


class _SeqRng:
    """RNG deterministik dengan deret nilai."""

    def __init__(self, values: list[float]) -> None:
        self._values = iter(values)

    def random(self) -> float:
        """Kembalikan nilai berikutnya dari deret."""
        return next(self._values)


@pytest.fixture(scope="module")
def tiers():
    """Muat data tingkatan sekali untuk seluruh modul."""
    return load_tiers()


def test_loader_memuat_enam_tingkatan_terurut(tiers):
    """Loader memuat 6 tingkatan sesuai urutan order §4.1."""
    ids = [tier.id for tier in tiers]
    assert ids == [
        "qi_condensation",
        "foundation_establishment",
        "golden_core",
        "soul_separation",
        "void_breaker",
        "heaven_challenger",
    ]
    thresholds = [tier.insight_required for tier in tiers]
    assert thresholds == [100, 300, 800, 2000, 5000, 12000]


def test_next_tier_mortal_adalah_qi_condensation(tiers):
    """Pemain mortal menuju tingkatan pertama."""
    player = Player(name="Akar")
    assert next_tier(player, tiers).id == "qi_condensation"


def test_can_breakthrough_butuh_insight_cukup(tiers):
    """Breakthrough butuh insight mencapai ambang tingkatan berikutnya."""
    below = Player(name="Akar", insight=99)
    assert not can_breakthrough(below, tiers)
    at = Player(name="Akar", insight=100)
    assert can_breakthrough(at, tiers)


def test_can_breakthrough_puncak_tidak_bisa(tiers):
    """Pemain di puncak tidak bisa breakthrough lagi."""
    player = Player(name="Akar", tier_order=6, insight=99999)
    assert not can_breakthrough(player, tiers)


def test_rate_dasar_55_dan_cap_90():
    """Tingkat sukses: 55% dasar, +5%/poin stat, cap 90% (§4.1)."""
    assert breakthrough_rate() == BASE_SUCCESS_RATE
    assert breakthrough_rate(support_stat=10) == RATE_CAP
    assert breakthrough_rate(pill_bonus=20) <= RATE_CAP
    assert breakthrough_rate(support_stat=20, pill_bonus=20) == RATE_CAP


def test_pill_bonus_di_luar_rentang_ditolak():
    """Pil breakthrough hanya 10–20%; nilai lain ditolak (§4.1)."""
    with pytest.raises(ValueError):
        breakthrough_rate(pill_bonus=50)
    with pytest.raises(ValueError):
        breakthrough_rate(pill_bonus=10.5)
    assert breakthrough_rate(pill_bonus=15) == BASE_SUCCESS_RATE + 15


def test_attempt_menolak_pill_bonus_invalid(tiers):
    """attempt_breakthrough menolak pill_bonus di luar rentang 10–20."""
    player = Player(name="Akar", insight=100)
    with pytest.raises(ValueError):
        attempt_breakthrough(player, tiers, pill_bonus=50)
    with pytest.raises(ValueError):
        attempt_breakthrough(player, tiers, pill_bonus=10.5)


def test_sukses_menerapkan_bonus_dan_naik_tier(tiers):
    """Sukses: stat_bonus diterapkan dan pemain naik ke tingkatan berikutnya."""
    player = Player(name="Akar", insight=100)
    result = attempt_breakthrough(player, tiers, rng=_FixedRng(0.0))
    assert result.success
    assert result.tier_id == "qi_condensation"
    assert player.tier_id == "qi_condensation"
    assert player.tier_order == 1
    tier = tiers[0]
    assert (
        player.stats["attack"]
        == BASE_STATS["attack"] + tier.stat_bonus["attack"]
    )
    assert player.tier_bonus["hp_max"] == tier.stat_bonus["hp_max"]
    assert player.tier_bonus["qi_max"] == tier.stat_bonus["qi_max"]
    assert result.unlocks == tuple(tier.unlocks)


def test_sukses_tidak_mengurangi_insight(tiers):
    """Insight bersifat kumulatif, tidak terkonsumsi saat breakthrough."""
    player = Player(name="Akar", insight=100)
    attempt_breakthrough(player, tiers, rng=_FixedRng(0.0))
    assert player.insight == 100


def test_gagal_menyebabkan_cedera_dua_hari(tiers):
    """Gagal: cedera sementara 2 hari game (§4.1)."""
    player = Player(name="Akar", insight=100)
    result = attempt_breakthrough(player, tiers, rng=_FixedRng(0.99))
    assert not result.success
    assert result.injury_days == INJURY_DAYS
    assert player.injury_days_remaining == INJURY_DAYS


def test_gagal_30_persen_inner_demon(tiers):
    """Gagal: 30% peluang memicu pertarungan inner demon (§4.1)."""
    player = Player(name="Akar", insight=100)
    result = attempt_breakthrough(player, tiers, rng=_SeqRng([0.99, 0.10]))
    assert not result.success
    assert result.inner_demon


def test_gagal_tanpa_inner_demon(tiers):
    """Gagal tanpa inner demon bila lemparan demon >= 0.30."""
    player = Player(name="Akar", insight=100)
    result = attempt_breakthrough(player, tiers, rng=_SeqRng([0.99, 0.50]))
    assert not result.success
    assert not result.inner_demon


def test_attempt_menolak_saat_insight_kurang(tiers):
    """attempt_breakthrough menolak ketika insight belum cukup."""
    player = Player(name="Akar", insight=50)
    with pytest.raises(ValueError):
        attempt_breakthrough(player, tiers)


def test_attempt_menolak_saat_puncak(tiers):
    """attempt_breakthrough menolak saat pemain sudah di puncak."""
    player = Player(name="Akar", tier_order=6, insight=99999)
    with pytest.raises(ValueError):
        attempt_breakthrough(player, tiers)


def test_progresi_hingga_tingkat_kedua(tiers):
    """Pemain bisa breakthrough berurutan hingga tingkatan berikutnya."""
    player = Player(name="Akar", insight=300)
    attempt_breakthrough(player, tiers, rng=_FixedRng(0.0))
    assert player.tier_order == 1
    attempt_breakthrough(player, tiers, rng=_FixedRng(0.0))
    assert player.tier_order == 2
    assert player.tier_id == "foundation_establishment"
