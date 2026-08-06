"""Test state game kanonik dan serialisasi (GDD §19.2)."""

import pytest

from src.core.state import (
    DEFAULT_LOCATION,
    FACTIONS,
    SCHEMA_VERSION,
    GameState,
    GameTime,
    QuestProgress,
)
from src.engine.cultivation import (
    attempt_breakthrough,
    load_tiers,
    restore_tier,
)
from src.models.player import Player

REQUIRED_KEYS = {
    "schema_version",
    "player",
    "party",
    "inventory",
    "quests",
    "flags",
    "kills",
    "reputation",
    "memories",
    "map_unlocks",
    "location",
    "time",
    "settings",
    "shop_sold",
}


class _FixedRng:
    """RNG deterministik dengan nilai tetap."""

    def __init__(self, value: float) -> None:
        self.value = value

    def random(self) -> float:
        """Kembalikan nilai tetap."""
        return self.value


def _state() -> GameState:
    """State dasar untuk test serialisasi."""
    return GameState(player=Player(name="Akar"))


def test_shop_sold_default_kosong():
    """State baru: stok terjual toko kosong (seluruh stok penuh)."""
    assert _state().shop_sold == {}


def test_shop_sold_roundtrip():
    """shop_sold ikut round-trip to_dict/from_dict identik."""
    state = _state()
    state.shop_sold = {"pedagang_kelana": {"esensi_api": 2}}
    restored = GameState.from_dict(state.to_dict())
    assert restored.shop_sold == state.shop_sold
    assert restored.to_dict() == state.to_dict()


def test_shop_sold_bentuk_salah_ditolak():
    """shop_sold bukan dict (save korup) ditolak keras, tanpa crash."""
    with pytest.raises(ValueError):
        GameState.from_dict(
            {"player": {"name": "Akar"}, "shop_sold": "rusak"}
        )


def test_to_dict_memiliki_semua_kunci_skema():
    """to_dict memuat semua kunci top-level skema §19.2."""
    assert set(_state().to_dict()) == REQUIRED_KEYS


def test_default_state_sesuai_skema():
    """Default: lokasi desa awal, waktu 1/8, reputasi 5 faksi nol."""
    data = _state().to_dict()
    assert data["schema_version"] == SCHEMA_VERSION
    assert data["location"] == DEFAULT_LOCATION
    assert data["time"] == {"day": 1, "hour": 8}
    assert data["quests"] == {"started": [], "done": [], "failed": []}
    assert data["reputation"] == {faction: 0 for faction in FACTIONS}
    assert data["flags"] == {}
    assert data["settings"] == {}


def test_roundtrip_state_identik():
    """Save -> load mengembalikan state yang identik (round-trip penuh)."""
    state = GameState(
        player=Player(name="Akar", gold=25, meridian_buka=2, insight=100),
        quests=QuestProgress(started=["quest101"], done=["quest102"]),
        flags={"map_guild_city_unlocked": True},
        reputation={
            "rebels": 15
        },  # parsial -> dinormalisasi, round-trip tetap identik
        memories=["memory_001"],
        map_unlocks=["ashfall_forest"],
        location="ashfall_forest",
        time=GameTime(day=3, hour=14),
    )
    restored = GameState.from_dict(state.to_dict())
    assert restored.to_dict() == state.to_dict()


def test_tier_direkonstruksi_dari_data():
    """Tier_order & tier_bonus dibangun ulang dari data saat load (§4.1)."""
    player = Player(name="Akar", insight=300)
    attempt_breakthrough(player, load_tiers(), rng=_FixedRng(0.0))
    attempt_breakthrough(player, load_tiers(), rng=_FixedRng(0.0))
    state = GameState(player=player)
    restored = GameState.from_dict(state.to_dict())
    assert restored.player.tier_id == "foundation_establishment"
    assert restored.player.tier_order == 2
    assert restored.player.tier_bonus == player.tier_bonus
    assert restored.player.stats == player.stats
    assert restored.player.hp_max == player.hp_max
    assert restored.player.qi_max == player.qi_max


def test_reputasi_dinormalisasi_saat_konstruksi():
    """Reputasi selalu kanonik 5 faksi saat konstruksi (GDD §8)."""
    state = GameState(player=Player(name="Akar"), reputation={"rebels": 15})
    assert state.reputation == {
        "court": 0,
        "holy_order": 0,
        "rebels": 15,
        "guilds": 0,
        "ancient_order": 0,
    }


def test_restore_tier_tahan_terhadap_urutan_data():
    """restore_tier tidak bergantung pada urutan daftar tier."""
    tiers = load_tiers()
    player = Player(name="Akar", tier_id="golden_core")
    restore_tier(player, tiers)
    baseline = (player.tier_order, dict(player.tier_bonus))
    shuffled = Player(name="Akar", tier_id="golden_core")
    restore_tier(shuffled, list(reversed(tiers)))
    assert (shuffled.tier_order, shuffled.tier_bonus) == baseline


def test_from_dict_toleran_kunci_ekstra():
    """Kunci tak dikenal diabaikan (toleran untuk save editan tangan)."""
    data = _state().to_dict()
    data["cheat"] = {"gold": 999}
    restored = GameState.from_dict(data)
    assert restored.to_dict() == _state().to_dict()


def test_from_dict_menolak_tanpa_player():
    """Save tanpa field player ditolak dengan ValueError."""
    with pytest.raises(ValueError):
        GameState.from_dict({"schema_version": 1})


def test_save_lama_tanpa_hp_qi_jadi_penuh():
    """Load save tanpa hp/qi (versi lama) mengisi penuh (§19.3 migrasi)."""
    data = {
        "player": {"name": "Akar", "gold": 5},
        "reputation": {
            "court": 0,
            "holy_order": 0,
            "rebels": 0,
            "guilds": 0,
            "ancient_order": 0,
        },
    }
    state = GameState.from_dict(data)
    assert state.player.hp == state.player.hp_max
    assert state.player.qi == state.player.qi_max


def test_time_validasi_rentang():
    """Waktu divalidasi: hour 0-23, day >= 1."""
    with pytest.raises(ValueError):
        GameTime(day=0)
    with pytest.raises(ValueError):
        GameTime(hour=24)
    assert GameTime(day=1, hour=23).to_dict() == {"day": 1, "hour": 23}


def test_add_reputation_di_clamp():
    """add_reputation mengubah reputasi dan di-clamp ke [-100, +100] (§8)."""
    state = _state()
    state.add_reputation("rebels", 30)
    assert state.reputation["rebels"] == 30
    state.add_reputation("rebels", 200)
    assert state.reputation["rebels"] == 100
    state.add_reputation("court", -500)
    assert state.reputation["court"] == -100


def test_add_reputation_menolak_faksi_tak_dikenal():
    """Faksi di luar daftar kanonik ditolak, bukan ditambah diam-diam."""
    state = _state()
    with pytest.raises(ValueError):
        state.add_reputation("bogus_faction", 5)
    assert "bogus_faction" not in state.reputation


def test_kills_roundtrip():
    """Counter kill ikut tersimpan dan terbaca kembali (round-trip)."""
    state = _state()
    state.kills["bandit_perbatasan"] = 3
    restored = GameState.from_dict(state.to_dict())
    assert restored.kills == {"bandit_perbatasan": 3}


def test_save_lama_tanpa_kills_jadi_kosong():
    """Save lama tanpa field kills dimuat sebagai dict kosong (additive)."""
    data = _state().to_dict()
    del data["kills"]
    restored = GameState.from_dict(data)
    assert restored.kills == {}
