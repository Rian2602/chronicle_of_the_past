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
    "capital",
    "ancient_vault",
    "sky_seal",
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


def test_musuh_target_quest_muncul_di_peta():
    """Tiap musuh yang jadi target quest muncul di minimal satu peta.

    Mencegah quest macet: objektif enemy/kill_count menuntut kills musuh,
    tapi musuh tak pernah muncul di peta mana pun (GDD §9).
    """
    quests_dir = Path(__file__).resolve().parents[1] / "data" / "quests"
    targets: set[str] = set()
    for path in quests_dir.glob("*.json"):
        quest = json.loads(path.read_text(encoding="utf-8"))
        for objective in quest.get("objectives", []):
            if objective["kind"] in ("enemy", "kill_count"):
                targets.add(objective["target"])
    placed: set[str] = set()
    for path in DATA_DIR.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        placed.update(entry["enemy"] for entry in data.get("enemies", []))
    missing = targets - placed
    assert not missing, f"musuh target quest tak muncul di peta: {missing}"


def test_bos_tidak_digate_oleh_quest_yang_membunuhnya():
    """Musuh tak boleh digate quest<id>_done dari quest yang menargetkannya.

    Deadlock: kalau bos X muncul hanya saat quest<id>_done (padahal quest
    itu menuntut membunuh X), pemain tak pernah bisa membunuhnya (GDD §9,
    §11). Gate harus quest SEBELUMNYA (yang men-start quest pembunuhan).
    """
    quests_dir = Path(__file__).resolve().parents[1] / "data" / "quests"
    killers: dict[str, set[str]] = {}
    for path in quests_dir.glob("*.json"):
        quest = json.loads(path.read_text(encoding="utf-8"))
        for objective in quest.get("objectives", []):
            if objective["kind"] in ("enemy", "kill_count"):
                killers.setdefault(objective["target"], set()).add(quest["id"])
    for path in DATA_DIR.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        for entry in data.get("enemies", []):
            requires = entry.get("requires_flag")
            if not requires or not requires.endswith("_done"):
                continue
            gate_quest = requires[: -len("_done")]
            assert gate_quest not in killers.get(entry["enemy"], set()), (
                f"{path.name}: musuh {entry['enemy']} digate "
                f"{requires} padahal quest itu yang menargetkannya"
            )
