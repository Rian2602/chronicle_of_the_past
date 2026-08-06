"""Validasi data toko & harga item (GDD §7, §14.2, AGENTS §2.1)."""

import json
from pathlib import Path

from src.engine.items import load_items
from src.engine.shop import load_shops

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
SHOP_DIR = DATA_DIR / "shops"
NPC_DIR = DATA_DIR / "npc"


def test_semua_toko_memenuhi_skema():
    """Toko punya id == nama file, name, dan stock berisi item+count."""
    for path in SHOP_DIR.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["id"] == path.stem
        assert isinstance(data["name"], str) and data["name"]
        assert isinstance(data["stock"], list) and data["stock"]
        for entry in data["stock"]:
            assert isinstance(entry["item"], str) and entry["item"]
            count = entry.get("count")
            assert isinstance(count, int) and count >= 1, (
                f"{path.name}: count stok {entry['item']} tidak valid"
            )


def test_stok_toko_merujuk_item_yang_ada_dan_berharga():
    """Setiap item di stok toko wajib ada di data/items dan punya harga."""
    items = load_items()
    for path in SHOP_DIR.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        for entry in data["stock"]:
            item_id = entry["item"]
            assert item_id in items, (
                f"{path.name}: stok -> item {item_id} tidak ada"
            )
            price = items[item_id].get("price")
            assert isinstance(price, int) and price >= 1, (
                f"{path.name}: stok -> {item_id} tanpa harga beli valid"
            )


def test_npc_field_shop_merujuk_toko():
    """NPC dengan field shop wajib merujuk toko yang ada di data/shops."""
    shops = load_shops()
    for path in NPC_DIR.glob("*.json"):
        npc = json.loads(path.read_text(encoding="utf-8"))
        shop_id = npc.get("shop")
        if shop_id is not None:
            assert shop_id in shops, (
                f"{path.name}: shop {shop_id} tidak ada di data/shops"
            )


def test_data_item_berharga_valid():
    """Semua field price di data/items berupa bilangan bulat positif."""
    for path in (DATA_DIR / "items").glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        price = data.get("price")
        if price is not None:
            assert isinstance(price, int) and price >= 1, (
                f"{path.name}: price tidak valid"
            )


def test_toko_pedagang_kelana_ada_dan_lengkap():
    """Toko pedagang kelana ada dengan stok sesuai dialog NPC."""
    path = SHOP_DIR / "pedagang_kelana.json"
    assert path.is_file()
    data = json.loads(path.read_text(encoding="utf-8"))
    stocked = {entry["item"] for entry in data["stock"]}
    assert {
        "esensi_api",
        "esensi_air",
        "esensi_kayu",
        "esensi_tanah",
        "pil_pemulih",
        "pil_qi",
        "batu_qi",
    } <= stocked


def test_item_dagangan_pedagang_memiliki_harga():
    """Semua item dagangan pedagang kelana punya harga beli (50/esensi)."""
    items = load_items()
    for item_id in (
        "esensi_api",
        "esensi_air",
        "esensi_kayu",
        "esensi_tanah",
        "pil_pemulih",
        "pil_qi",
        "batu_qi",
    ):
        price = items[item_id].get("price")
        assert isinstance(price, int) and price >= 1, (
            f"{item_id} belum punya harga"
        )
