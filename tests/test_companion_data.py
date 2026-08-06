"""Validasi data rekan tim (GDD §20)."""

import json
from pathlib import Path

from src.engine.combat import load_techniques

ELEMENTS = {"metal", "wood", "earth", "water", "fire", "netral"}
REQUIRED_KEYS = {"id", "name", "tier", "element", "stats", "skills"}
REQUIRED_STATS = {
    "attack",
    "defense",
    "agility",
    "intelligence",
    "vitality",
    "spirit",
    "hp",
    "qi",
}


def test_data_rekan_semua_valid():
    """Rekan: skema wajib + ref teknik/element valid (GDD §20)."""
    techniques = {t.id for t in load_techniques()}
    data_dir = Path(__file__).resolve().parents[1] / "data" / "companions"
    assert data_dir.exists(), "data/companions/ belum ada"
    for path in data_dir.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        assert set(data) >= REQUIRED_KEYS, f"{path.name}: kunci kurang"
        assert data["id"] == path.stem
        assert isinstance(data["name"], str) and data["name"]
        assert data["element"] in ELEMENTS, f"{path.name}: elemen tidak valid"
        assert all(skill in techniques for skill in data["skills"]), (
            f"{path.name}: teknik tidak ter-resolve"
        )
        assert REQUIRED_STATS <= set(data["stats"]), (
            f"{path.name}: stat tidak lengkap"
        )
