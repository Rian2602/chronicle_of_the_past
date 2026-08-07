"""Validasi skema data peta (GDD §9, AGENTS.md §2.1)."""

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "maps"
EXPECTED_MAPS = {
    "village_emberfall",
    "ashfall_forest",
    "ruin_shrine",
    "sect_azure",
    "guild_city",
    "hutan_kelabu",
    "gua_abyss",
    "holy_cathedral",
    "rebel_hideout",
}
REQUIRED_KEYS = {"id", "name", "description", "tier"}  # + opsional "enemies"


def test_terdapat_file_peta_yang_diharapkan():
    """Harus ada peta Arc 1 sesuai GDD §9 (desa, hutan, kuil)."""
    files = sorted(path.name for path in DATA_DIR.glob("*.json"))
    expected = sorted(f"{map_id}.json" for map_id in EXPECTED_MAPS)
    assert files == expected


def test_semua_peta_memenuhi_skema():
    """Setiap peta memenuhi skema id/name/description/tier (§9)."""
    for path in DATA_DIR.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        assert set(data) >= REQUIRED_KEYS, f"{path.name}: kunci tidak sesuai"
        assert isinstance(data["id"], str) and data["id"] == path.stem
        assert isinstance(data["name"], str) and data["name"]
        assert isinstance(data["description"], str) and data["description"]
        assert isinstance(data["tier"], int) and data["tier"] >= 1


def test_peta_arc1_menyebut_musuh_yang_valid():
    """Ref enemies di peta wajib ter-resolve (GDD §9, §11)."""
    from src.engine.combat import load_enemies

    enemy_ids = {enemy.id for enemy in load_enemies()}
    for path in DATA_DIR.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        for entry in data.get("enemies", []):
            assert entry["enemy"] in enemy_ids, (
                f"{path.name}: musuh {entry['enemy']} tidak dikenal"
            )
            requires_flag = entry.get("requires_flag", None)
            assert isinstance(requires_flag, (str, type(None)))
