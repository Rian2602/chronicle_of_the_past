"""Validasi skema data NPC awal (AGENTS.md §5.1; format data existing)."""

import json
from pathlib import Path

from src.engine.maps import load_maps

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "npc"
EXPECTED_NPCS = {
    "elder_mao",
    "lin_wei",
    "fang_yue",
    "alchemist_xiu",
    "diakon_soren",
    "guntur",
    "jati",
    "mira",
    "penunggu_hutan",
    "kultisi_merah",
    "penjaga_abyss",
    "pedagang_kelana",
    "penjaga_makam",
    "blacksmith_tie",
    "kestrel",
}
REQUIRED_KEYS = {"id", "name", "location", "greeting", "dialog"}


def test_terdapat_file_npc_yang_diharapkan():
    """Harus ada NPC awal Arc 1 sesuai rencana (elder_mao, lin_wei)."""
    files = sorted(path.name for path in DATA_DIR.glob("*.json"))
    expected = sorted(f"{npc_id}.json" for npc_id in EXPECTED_NPCS)
    assert files == expected


def test_semua_npc_memenuhi_skema():
    """Setiap NPC memenuhi skema minimal: id/name/location/greeting/dialog.

    Field opsional diizinkan (mis. ``shop`` untuk NPC pedagang, GDD §7);
    asersi memakai subset, bukan kesetaraan kunci.
    """
    known_locations = set(load_maps())
    for path in DATA_DIR.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        assert REQUIRED_KEYS <= set(data), f"{path.name}: kunci tidak sesuai"
        assert isinstance(data["id"], str) and data["id"] == path.stem
        assert isinstance(data["name"], str) and data["name"]
        assert data["location"] in known_locations, (
            f"{path.name}: lokasi {data['location']} tidak dikenal"
        )
        assert isinstance(data["greeting"], str) and data["greeting"]
        assert isinstance(data["dialog"], list) and data["dialog"], (
            f"{path.name}: dialog wajib non-kosong"
        )
        assert all(isinstance(line, str) and line for line in data["dialog"]), (
            f"{path.name}: isi dialog wajib string non-kosong"
        )
