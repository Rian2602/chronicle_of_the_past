"""Validasi skema data peta (GDD §9, AGENTS.md §2.1)."""

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "maps"
EXPECTED_MAPS = {"village_emberfall", "ashfall_forest", "ruin_shrine"}
REQUIRED_KEYS = {"id", "name", "description", "tier"}


def test_terdapat_file_peta_yang_diharapkan():
    """Harus ada peta Arc 1 sesuai GDD §9 (desa, hutan, kuil)."""
    files = sorted(path.name for path in DATA_DIR.glob("*.json"))
    expected = sorted(f"{map_id}.json" for map_id in EXPECTED_MAPS)
    assert files == expected


def test_semua_peta_memenuhi_skema():
    """Setiap peta memenuhi skema id/name/description/tier (§9)."""
    for path in DATA_DIR.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        assert set(data) == REQUIRED_KEYS, f"{path.name}: kunci tidak sesuai"
        assert isinstance(data["id"], str) and data["id"] == path.stem
        assert isinstance(data["name"], str) and data["name"]
        assert isinstance(data["description"], str) and data["description"]
        assert isinstance(data["tier"], int) and data["tier"] >= 1
