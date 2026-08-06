"""Validasi loader item & skema effect (GDD §14.2, AGENTS.md §2.1)."""

import json
from pathlib import Path

from src.engine.items import load_items


def test_data_item_semua_memenuhi_skema():
    """Item data memiliki minimal id+name; type/description/effect opsional."""
    data_dir = Path(__file__).resolve().parents[1] / "data" / "items"
    required = {"id", "name"}
    for path in data_dir.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        assert set(data) >= required, f"{path.name}: kunci tidak sesuai"
        assert isinstance(data["id"], str) and data["id"] == path.stem
        assert isinstance(data["name"], str) and data["name"]


def test_load_items_membaca_field_effect(tmp_path):
    """Loader item wajib membawa field type/description/effect."""
    item_dir = tmp_path / "items"
    item_dir.mkdir()
    (item_dir / "pil_uji.json").write_text(
        json.dumps(
            {
                "id": "pil_uji",
                "name": "Pil Uji",
                "type": "consumable",
                "description": "Uji.",
                "effect": {"heal_hp": 20},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    items = load_items(item_dir)
    assert items["pil_uji"]["name"] == "Pil Uji"
    assert items["pil_uji"]["type"] == "consumable"
    assert items["pil_uji"]["description"] == "Uji."
    assert items["pil_uji"]["effect"] == {"heal_hp": 20}


def test_load_items_item_tanpa_effect_tetap_lolos(tmp_path):
    """Item lama (id+name saja) tidak boleh rusak (kompatibilitas)."""
    item_dir = tmp_path / "items"
    item_dir.mkdir()
    (item_dir / "pil_lama.json").write_text(
        json.dumps({"id": "pil_lama", "name": "Pil Lama"}, ensure_ascii=False),
        encoding="utf-8",
    )
    items = load_items(item_dir)
    assert items["pil_lama"]["name"] == "Pil Lama"
    assert items["pil_lama"].get("effect") is None
