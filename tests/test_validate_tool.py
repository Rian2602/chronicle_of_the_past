"""Test tools/validate.py — validator aset data (GDD §25.3).

Menjalankan ``collect_errors`` pada pohon data minimal untuk membuktikan
perilaku: referensi gantung tertangkap, pohon valid lolos.
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.validate import collect_errors  # noqa: E402

QUEST = {
    "id": "q_test",
    "title": "Quest Uji",
    "type": "main",
    "description": "Quest untuk menguji validator.",
    "objectives": [{"kind": "talk", "target": "npc_hantu"}],
    "rewards": {"insight": 10, "gold": 0},
    "flags_on_complete": ["q_test_done"],
    "next": None,
    "category": "main",
    "requires_flag": None,
}


def _pohon_data(tmp_path: Path) -> Path:
    """Bangun pohon data minimal (subfolder kosong kecuali quest)."""
    data = tmp_path / "data"
    for sub in (
        "quests",
        "events",
        "story",
        "maps",
        "npc",
        "cultivation",
        "techniques",
        "enemies",
    ):
        (data / sub).mkdir(parents=True)
    (data / "quests" / "q_test.json").write_text(
        json.dumps(QUEST, ensure_ascii=False),
        encoding="utf-8",
    )
    return data


def test_validator_menangkap_referensi_gantung(tmp_path):
    """Referensi talk -> NPC yang tidak ada harus dilaporkan."""
    errors = collect_errors(_pohon_data(tmp_path))
    assert any("npc_hantu" in error for error in errors)


def test_validator_pohon_valid_lolos(tmp_path):
    """Pohon data yang referensinya lengkap tidak menghasilkan temuan."""
    data = _pohon_data(tmp_path)
    (data / "npc" / "npc_hantu.json").write_text(
        json.dumps(
            {
                "id": "npc_hantu",
                "name": "Hantu",
                "location": "map_test",
                "greeting": "Halo.",
                "dialog": ["Satu kalimat."],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (data / "maps" / "map_test.json").write_text(
        json.dumps(
            {
                "id": "map_test",
                "name": "Peta Uji",
                "description": "Tempat uji.",
                "tier": 1,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    assert collect_errors(data) == []


def test_validator_data_lulus(tmp_path):
    """Validator berjalan tanpa temuan dan keluar kode 0 (AGENTS.md §1)."""
    result = subprocess.run(
        [sys.executable, "tools/validate.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "OK" in result.stdout
