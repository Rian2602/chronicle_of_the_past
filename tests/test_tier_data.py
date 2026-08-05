"""Validasi skema data tingkatan kultivasi (GDD §14.3, AGENTS.md §2.1)."""

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "cultivation"
REQUIRED_KEYS = {
    "id",
    "name",
    "order",
    "insight_required",
    "stat_bonus",
    "unlocks",
}
VALID_STAT_KEYS = {
    "attack",
    "defense",
    "agility",
    "intelligence",
    "vitality",
    "spirit",
    "hp_max",
    "qi_max",
}
EXPECTED_TIERS = {
    "qi_condensation": (1, 100),
    "foundation_establishment": (2, 300),
    "golden_core": (3, 800),
    "soul_separation": (4, 2000),
    "void_breaker": (5, 5000),
    "heaven_challenger": (6, 12000),
}


def test_terdapat_enam_file_tingkatan():
    """Harus ada 6 file JSON tingkatan sesuai GDD §4.1."""
    files = sorted(path.name for path in DATA_DIR.glob("*.json"))
    expected = sorted(f"{tier_id}.json" for tier_id in EXPECTED_TIERS)
    assert files == expected


def test_semua_tier_memenuhi_skema():
    """Setiap file memenuhi skema §14.3 dan konvensi AGENTS.md §5."""
    for path in DATA_DIR.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        assert set(data) == REQUIRED_KEYS, (
            f"{path.name}: kunci tidak sesuai skema"
        )
        assert isinstance(data["id"], str) and data["id"] == path.stem
        assert isinstance(data["name"], str) and data["name"]
        assert isinstance(data["order"], int) and data["order"] >= 1
        assert isinstance(data["insight_required"], int)
        assert data["insight_required"] > 0
        assert isinstance(data["stat_bonus"], dict)
        assert set(data["stat_bonus"]) <= VALID_STAT_KEYS
        assert all(
            isinstance(value, int) and value > 0
            for value in data["stat_bonus"].values()
        )
        assert isinstance(data["unlocks"], list)
        assert all(isinstance(item, str) and item for item in data["unlocks"])


def test_urutan_dan_ambang_insight():
    """Order unik & insight_required menaik sesuai tabel §4.1."""
    by_id = {}
    for path in DATA_DIR.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        by_id[data["id"]] = (data["order"], data["insight_required"])
    assert by_id == EXPECTED_TIERS
    orders = sorted(order for order, _ in by_id.values())
    assert orders == list(range(1, 7))
