"""Validasi skema data teknik (GDD §14.3, AGENTS.md §2.1)."""

import json
from pathlib import Path

from src.engine.combat import STATUS_IDS
from src.engine.cultivation import load_tiers

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "techniques"
REQUIRED_KEYS = {
    "id",
    "name",
    "path",
    "element",
    "type",
    "qi_cost",
    "power",
    "effects",
    "requires",
}
ELEMENTS = {"metal", "wood", "earth", "water", "fire"}
PATHS = {"sword", "alchemy", "formation", "spirit", "soul"}
TYPES = {"physical", "technique"}
EXPECTED_TECHNIQUES = {
    "qi_slash",
    "flame_strike",
    "frost_bind",
    "vine_grasp",
    "pukulan_beruntun",
    "serapan_akar",
    "dinding_tanah",
    "pandangan_jiwa",
    "penyerapan_jiwa",
    "tebasan_cahaya",
    "pelindung_suci",
    "panah_bayangan",
    "aura_penekan",
    "langkah_hantu",
    "ledakan_qi",
    "earth_charge",
    "serbuan_akar",
    "perisai_tanah",
    "iblis_pedang",
    "benteng_meridian",
    "senjata_roh",
    "tebasan_bayangan",
    "jaring_jiwa",
    "jarum_racun",
    "perisai_cahaya",
    "racun_meridian_lanjut",
    "tangan_emas",
    "pil_pembakar",
    "seruan_jiwa",
    "ikatan_roh",
    "pandangan_jiwa",
    "penyerapan_jiwa",
}


def test_terdapat_file_teknik_yang_diharapkan():
    """Harus ada file teknik sesuai rencana Fase 0 combat."""
    files = sorted(path.name for path in DATA_DIR.glob("*.json"))
    expected = sorted(f"{tech_id}.json" for tech_id in EXPECTED_TECHNIQUES)
    assert files == expected


def test_semua_teknik_memenuhi_skema():
    """Setiap teknik memenuhi skema §14.3 dan konvensi AGENTS.md §5."""
    tier_ids = {tier.id for tier in load_tiers()}
    for path in DATA_DIR.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        assert set(data) == REQUIRED_KEYS, f"{path.name}: kunci tidak sesuai"
        assert isinstance(data["id"], str) and data["id"] == path.stem
        assert isinstance(data["name"], str) and data["name"]
        assert data["path"] in PATHS
        assert data["element"] in ELEMENTS
        assert data["type"] in TYPES
        assert isinstance(data["qi_cost"], int) and data["qi_cost"] >= 0
        assert isinstance(data["power"], int) and data["power"] >= 0
        assert isinstance(data["effects"], list)
        assert isinstance(data["requires"], dict)
        assert data["requires"]["tier"] in tier_ids


def test_efek_status_valid():
    """Efek status pada teknik memakai id dan durasi yang valid (§16)."""
    for path in DATA_DIR.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        for effect in data["effects"]:
            assert effect["status"] in STATUS_IDS
            duration = effect.get("duration", 1)
            assert isinstance(duration, int) and duration >= 1
            power = effect.get("power", 0)
            assert isinstance(power, int) and power >= 0
