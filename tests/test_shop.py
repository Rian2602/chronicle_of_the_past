"""Test sistem toko: loader data + perilaku jual-beli (GDD §7, §18)."""

import json

from src.engine.shop import load_shops, sell_price


def _toko(tmp_path, name="toko_uji", stock=None) -> object:
    """Bangun satu file toko di direktori sementara."""
    shop_dir = tmp_path / "shops"
    shop_dir.mkdir(exist_ok=True)
    raw = {"id": name, "name": "Toko Uji", "stock": stock or []}
    (shop_dir / f"{name}.json").write_text(
        json.dumps(raw, ensure_ascii=False), encoding="utf-8"
    )
    return shop_dir


def test_load_shops_membaca_stok(tmp_path):
    """Loader toko mengembalikan id, name, dan daftar stock."""
    shop_dir = _toko(
        tmp_path,
        stock=[{"item": "esensi_api", "count": 3}],
    )
    shops = load_shops(shop_dir)
    assert "toko_uji" in shops
    assert shops["toko_uji"]["name"] == "Toko Uji"
    assert shops["toko_uji"]["stock"] == [{"item": "esensi_api", "count": 3}]


def test_load_shops_direktori_kosong(tmp_path):
    """Tanpa file toko, loader mengembalikan dict kosong."""
    shop_dir = tmp_path / "shops"
    shop_dir.mkdir()
    assert load_shops(shop_dir) == {}


def test_sell_price_empat_puluh_persen():
    """Harga jual kembali = 40% harga beli, dibulatkan ke bawah."""
    assert sell_price(50) == 20
    assert sell_price(30) == 12
    assert sell_price(25) == 10
    assert sell_price(10) == 4
