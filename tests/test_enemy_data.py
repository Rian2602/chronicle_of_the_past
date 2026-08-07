"""Validasi skema data musuh (GDD §14.3, AGENTS.md §2.1)."""

import json
from pathlib import Path

from src.engine.combat import load_techniques
from src.engine.cultivation import load_tiers

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "enemies"
REQUIRED_KEYS = {
    "id",
    "name",
    "tier",
    "element",
    "behavior",
    "stats",
    "skills",
    "tags",
    "rewards",
}
OPTIONAL_KEYS = {"requires_flag"}
REWARD_KEYS = {"insight", "gold"}
STAT_KEYS = {
    "attack",
    "defense",
    "agility",
    "intelligence",
    "vitality",
    "spirit",
    "hp",
    "qi",
}
ELEMENTS = {"metal", "wood", "earth", "water", "fire"}
EXPECTED_ENEMIES = {
    "serigala_qi",
    "bandit_perbatasan",
    "zombie_temple",
    "penjaga_makam",
    "penjaga_arsip",
    "babi_hutan_qi",
    "pembelot_pemberontak",
    "penebus_orde_suci",
    "golem_terbakar",
    "abyssal_worm",
    "penunggu_hutan",
    "hantu_laut",
    "serigala_ember",
    "kultisi_merah",
    "golem_latihan",
    "pembunuh_gilda",
    "kultis_bayangan",
    "bos_sekte_bayangan",
}


def test_terdapat_file_musuh_yang_diharapkan():
    """Harus ada file musuh Arc 1 sesuai GDD §11."""
    files = sorted(path.name for path in DATA_DIR.glob("*.json"))
    expected = sorted(f"{enemy_id}.json" for enemy_id in EXPECTED_ENEMIES)
    assert files == expected


def test_semua_musuh_memenuhi_skema():
    """Setiap musuh memenuhi skema §14.3 dan konvensi AGENTS.md §5."""
    tier_ids = {tier.id for tier in load_tiers()}
    for path in DATA_DIR.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        assert REQUIRED_KEYS <= set(data) <= (REQUIRED_KEYS | OPTIONAL_KEYS), (
            f"{path.name}: kunci tidak sesuai"
        )
        assert isinstance(data["id"], str) and data["id"] == path.stem
        assert isinstance(data["name"], str) and data["name"]
        assert data["tier"] in tier_ids
        assert data["element"] in ELEMENTS
        assert isinstance(data["behavior"], str) and data["behavior"]
        assert set(data["stats"]) == STAT_KEYS
        assert all(
            isinstance(value, int) and value > 0
            for value in data["stats"].values()
        )
        assert isinstance(data["skills"], list)
        assert isinstance(data["tags"], list)
        assert all(isinstance(item, str) and item for item in data["skills"])
        assert all(isinstance(item, str) for item in data["tags"])
        # rewards: optional field, kunci subset {insight, gold}, nilai >= 0.
        assert isinstance(data["rewards"], dict)
        assert set(data["rewards"]) <= REWARD_KEYS
        assert all(
            isinstance(value, int) and value >= 0
            for value in data["rewards"].values()
        )


def test_musuh_arc1_memiliki_reward():
    """Musuh Arc 1 punya reward insight/gold untuk MVP (§4.3)."""
    for path in DATA_DIR.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["rewards"], f"{path.name}: rewards kosong"


def test_skill_musuh_terresolve_ke_teknik():
    """Semua referensi skill musuh wajib valid (AGENTS.md §5.1)."""
    technique_ids = {technique.id for technique in load_techniques()}
    for path in DATA_DIR.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        for skill in data["skills"]:
            assert skill in technique_ids, (
                f"{path.name}: skill {skill} tidak dikenal"
            )
