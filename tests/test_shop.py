"""Test sistem toko: loader data + perilaku jual-beli (GDD §7, §18)."""

import json
import random

from src.core.game_loop import GameSession
from src.core.input import Command
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


# ----------------------------------------------------------------------
# Perilaku command shop / buy / sell (GDD §18.2)
# ----------------------------------------------------------------------


def _session(tmp_path, seed: int = 7) -> GameSession:
    """Sesi dengan rng deterministik dan folder save sementara."""
    return GameSession(save_dir=tmp_path, rng=random.Random(seed))


def _dispatch(session: GameSession, raw: str) -> list[str]:
    """Parse + kirim perintah; kembalikan pesan."""
    parts = raw.split()
    command = Command(name=parts[0], args=tuple(parts[1:]), raw=raw)
    return session.dispatch(command)


def _di_toko(session: GameSession) -> None:
    """Bawa pemain ke lokasi pedagang (sekarang di village_emberfall)."""
    session.new_game("Akar")


def test_shop_tanpa_pedagang_di_lokasi(tmp_path):
    """Shop di hutan: tidak ada pedagang, pesan jelas."""
    session = _session(tmp_path)
    session.new_game("Akar")
    _dispatch(session, "go ashfall_forest")
    lines = _dispatch(session, "shop")
    assert any("Tidak ada pedagang" in line for line in lines)


def test_shop_menampilkan_stok_dan_harga(tmp_path):
    """Shop menampilkan nama dagangan, harga beli, dan sisa stok."""
    session = _session(tmp_path)
    _di_toko(session)
    lines = _dispatch(session, "shop")
    joined = "\n".join(lines)
    assert "Dagangan Pedagang Kelana" in joined
    assert "Esensi Api" in joined
    assert "50 emas" in joined
    assert "sisa 3" in joined
    # Setelah membeli 1, sisa stok yang ditampilkan ikut diperbarui.
    session.state.player.gold = 200
    _dispatch(session, "buy esensi_api 1")
    joined = "\n".join(_dispatch(session, "shop"))
    assert "sisa 2" in joined


def test_buy_mengurangi_emas_menambah_item_dan_stok(tmp_path):
    """Buy: emas berkurang, item masuk tas, stok terjual tercatat."""
    session = _session(tmp_path)
    _di_toko(session)
    session.state.player.gold = 200
    lines = _dispatch(session, "buy esensi_api")
    assert session.state.player.gold == 150
    assert session.state.inventory["items"]["esensi_api"] == 1
    assert session.state.shop_sold == {"pedagang_kelana": {"esensi_api": 1}}
    assert any("Kamu membeli Esensi Api" in line for line in lines)


def test_buy_emas_tidak_cukup_ditolak(tmp_path):
    """Buy tanpa emas cukup: ditolak, emas dan tas tidak berubah."""
    session = _session(tmp_path)
    _di_toko(session)
    session.state.player.gold = 30
    lines = _dispatch(session, "buy esensi_api")
    assert any("kurang" in line for line in lines)
    assert session.state.player.gold == 30
    assert session.state.inventory["items"] == {}
    assert session.state.shop_sold == {}


def test_buy_stok_habis_ditolak(tmp_path):
    """Buy saat stok habis: ditolak sampai restock."""
    session = _session(tmp_path)
    _di_toko(session)
    session.state.player.gold = 500
    _dispatch(session, "buy esensi_api 3")
    lines = _dispatch(session, "buy esensi_api 1")
    assert any("habis" in line for line in lines)


def test_buy_count_lebih_dari_stok_ditolak(tmp_path):
    """Buy melebihi sisa stok: ditolak dengan jumlah tersisa."""
    session = _session(tmp_path)
    _di_toko(session)
    session.state.player.gold = 500
    lines = _dispatch(session, "buy esensi_api 5")
    assert any("tinggal 3" in line for line in lines)


def test_buy_jumlah_tidak_valid(tmp_path):
    """Buy dengan jumlah non-angka: pesan jelas, tanpa crash."""
    session = _session(tmp_path)
    _di_toko(session)
    session.state.player.gold = 500
    lines = _dispatch(session, "buy esensi_api abc")
    assert any("tidak valid" in line for line in lines)
    assert session.state.inventory["items"] == {}


def test_buy_di_lokasi_tanpa_pedagang_ditolak(tmp_path):
    """Buy di lokasi tanpa toko: ditolak."""
    session = _session(tmp_path)
    session.new_game("Akar")
    _dispatch(session, "go ashfall_forest")
    lines = _dispatch(session, "buy esensi_api")
    assert any("Tidak ada pedagang" in line for line in lines)


def test_sell_menambah_emas_empat_puluh_persen(tmp_path):
    """Sell: emas +40% harga beli per item, item keluar dari tas."""
    session = _session(tmp_path)
    _di_toko(session)
    session.state.player.gold = 0
    session.state.inventory.setdefault("items", {})["esensi_api"] = 2
    lines = _dispatch(session, "sell esensi_api 2")
    assert session.state.player.gold == 40  # 2 x 20 (40% dari 50)
    assert session.state.inventory["items"].get("esensi_api", 0) == 0
    assert any("Kamu menjual Esensi Api" in line for line in lines)


def test_sell_item_tanpa_harga_ditolak(tmp_path):
    """Item tanpa price tidak bisa dijual, tetap di tas."""
    session = _session(tmp_path)
    _di_toko(session)
    session.state.inventory.setdefault("items", {})["pil_uji_heal"] = 1
    lines = _dispatch(session, "sell pil_uji_heal")
    assert any("tak bernilai jual" in line for line in lines)
    assert session.state.inventory["items"]["pil_uji_heal"] == 1
    assert session.state.player.gold == 0


def test_sell_tanpa_item_ditolak(tmp_path):
    """Sell item yang tidak dimiliki: pesan jelas."""
    session = _session(tmp_path)
    _di_toko(session)
    lines = _dispatch(session, "sell esensi_api")
    assert any("tidak punya" in line for line in lines)


def test_pesan_buy_satu_baris(tmp_path):
    """Pesan buy utuh dalam satu baris (regresi polish review).

    Sebelumnya pesan terbelah dua baris ("Kamu membeli ..." lalu
    "seharga ... emas."); harus kembali sebagai satu kalimat utuh.
    """
    session = _session(tmp_path)
    _di_toko(session)
    session.state.player.gold = 200
    lines = _dispatch(session, "buy esensi_api 2")
    buy_lines = [line for line in lines if "Kamu membeli" in line]
    assert len(buy_lines) == 1
    assert "Esensi Api x2 seharga 100 emas." in buy_lines[0]


def test_pesan_sell_satu_baris(tmp_path):
    """Pesan sell utuh dalam satu baris (regresi polish review)."""
    session = _session(tmp_path)
    _di_toko(session)
    session.state.inventory.setdefault("items", {})["esensi_api"] = 2
    lines = _dispatch(session, "sell esensi_api 2")
    sell_lines = [line for line in lines if "Kamu menjual" in line]
    assert len(sell_lines) == 1
    assert "Esensi Api x2 seharga 40 emas." in sell_lines[0]


def test_rest_merestock_toko(tmp_path):
    """Rest mengisi ulang stok toko (shop_sold dibersihkan)."""
    session = _session(tmp_path)
    _di_toko(session)
    session.state.player.gold = 500
    _dispatch(session, "buy esensi_api 3")  # stok esensi_api habis
    _dispatch(session, "rest")
    assert session.state.shop_sold == {}
    lines = _dispatch(session, "buy esensi_api 1")
    assert any("Kamu membeli Esensi Api" in line for line in lines)
