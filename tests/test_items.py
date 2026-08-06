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


def test_load_items_membaca_field_recipe(tmp_path):
    """Loader item wajib membawa field recipe (GDD §14.3)."""
    item_dir = tmp_path / "items"
    item_dir.mkdir()
    (item_dir / "pil_uji.json").write_text(
        json.dumps(
            {
                "id": "pil_uji",
                "name": "Pil Uji",
                "recipe": [{"item": "esensi_api", "qty": 2}],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    items = load_items(item_dir)
    assert items["pil_uji"]["recipe"] == [{"item": "esensi_api", "qty": 2}]


def test_load_items_membaca_field_price(tmp_path):
    """Loader item membawa field price (harga beli dasar, GDD §7)."""
    item_dir = tmp_path / "items"
    item_dir.mkdir()
    (item_dir / "pil_uji.json").write_text(
        json.dumps(
            {
                "id": "pil_uji",
                "name": "Pil Uji",
                "price": 50,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    items = load_items(item_dir)
    assert items["pil_uji"]["price"] == 50


def test_load_items_item_tanpa_price_tetap_lolos(tmp_path):
    """Item tanpa price (tidak diperjualbelikan) bernilai None."""
    item_dir = tmp_path / "items"
    item_dir.mkdir()
    (item_dir / "pil_lama.json").write_text(
        json.dumps({"id": "pil_lama", "name": "Pil Lama"}, ensure_ascii=False),
        encoding="utf-8",
    )
    items = load_items(item_dir)
    assert items["pil_lama"].get("price") is None


def test_item_alkimia_alat_dan_resep_ada():
    """Kuali roh + 3 item resep Arc 1 wajib ada di data (GDD §22)."""
    data_dir = Path(__file__).resolve().parents[1] / "data" / "items"
    files = {path.stem for path in data_dir.glob("*.json")}
    expected = {"kuali_roh", "resep_pemulih", "resep_qi", "resep_pemahaman"}
    assert expected <= files, f"kurang: {expected - files}"


def test_resep_pil_merujuk_bahan_yang_valid():
    """Recipe tiap pil: ingredient ada di data dan bertype material."""
    data_dir = Path(__file__).resolve().parents[1] / "data" / "items"
    items = {}
    for path in data_dir.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        items[data["id"]] = data
    ber_resep = 0
    for item_id, data in items.items():
        recipe = data.get("recipe")
        if recipe is None:
            continue
        ber_resep += 1
        for req in recipe:
            ingredient = items.get(req["item"])
            assert ingredient is not None, (
                f"{item_id}: ingredient {req['item']} tidak ada di data"
            )
            assert ingredient.get("type") == "material", (
                f"{item_id}: {req['item']} harus bertype material"
            )
            assert isinstance(req.get("qty"), int) and req["qty"] >= 1, (
                f"{item_id}: qty resep {req['item']} tidak valid"
            )
    assert ber_resep >= 3, "target Arc 1: minimal 3 resep (GDD §22)"
