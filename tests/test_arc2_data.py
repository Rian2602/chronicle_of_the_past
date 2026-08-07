"""Validasi data Arc 2: NPC kunci, dialog, teknik, resep, artefak.

Konten mengikuti GDD §10/§12.5/§14.3 dan AGENTS.md §8 (TASK 3).
"""

import json
from pathlib import Path

from src.engine.items import load_items

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def test_npc_kunci_arc2_ada_di_guild_city():
    """NPC kunci Arc 2 (blacksmith_tie & kestrel) ada di guild_city."""
    npc_dir = DATA_DIR / "npc"
    data = {
        path.stem: json.loads(path.read_text(encoding="utf-8"))
        for path in npc_dir.glob("*.json")
    }
    assert "blacksmith_tie" in data
    assert data["blacksmith_tie"]["location"] == "guild_city"
    assert "kestrel" in data
    assert data["kestrel"]["location"] == "guild_city"


def test_dialog_arc2_merujuk_npc_yang_ada():
    """Dialog *_1 di data/dialogues wajib merujuk NPC yang benar-benar ada."""
    npc_dir = DATA_DIR / "npc"
    npc_ids = {path.stem for path in npc_dir.glob("*.json")}
    for path in (DATA_DIR / "dialogues").glob("dialog_*_1.json"):
        raw = json.loads(path.read_text(encoding="utf-8"))
        assert raw["npc"] in npc_ids, f"{path.name}: NPC {raw['npc']} tak ada"


def test_teknik_alchemy_dan_soul_arc2_bertambah():
    """Kuota Arc 2: minimal 5 teknik alchemy dan 5 teknik soul (GDD §22)."""
    tech = {
        path.stem: json.loads(path.read_text(encoding="utf-8"))
        for path in (DATA_DIR / "techniques").glob("*.json")
    }
    alchemy = [t for t in tech.values() if t.get("path") == "alchemy"]
    soul = [t for t in tech.values() if t.get("path") == "soul"]
    assert len(alchemy) >= 5
    assert len(soul) >= 5


def test_resep_arc2_melengkapi_pil_yang_ada():
    """Resep Arc 2 mengajarkan pil-pil yang sudah ada di data/items."""
    resep = {
        path.stem: json.loads(path.read_text(encoding="utf-8"))
        for path in (DATA_DIR / "items").glob("resep_*.json")
    }
    targets = {r["effect"]["learn_recipe"] for r in resep.values()}
    for pil in ["pil_besi_hitam", "pil_qi_tenang", "pil_peneguh_fondasi"]:
        assert pil in targets, f"resep untuk {pil} belum ada"


def test_artefak_arc2_punya_growth_stat_dan_max_level():
    """Semua artefak punya growth_stat & max_level; kuota Arc 2 terpenuhi."""
    items = load_items()
    artifacts = [
        item for item in items.values() if item.get("type") == "artifact"
    ]
    assert len(artifacts) >= 6
    for item in artifacts:
        assert item.get("growth_stat"), f"{item['id']}: tanpa growth_stat"
        assert item.get("max_level"), f"{item['id']}: tanpa max_level"
