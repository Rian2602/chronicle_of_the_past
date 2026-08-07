"""Toko (GDD §7) — stok jual-beli item data-driven.

Engine hanya menyimpan stok yang terjual di ``state.shop_sold``; sisa
stok dihitung dari data/shops/ dikurangi angka terjual (keputusan desain
stok terbatas + restock saat rest).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
SHOP_DIR = DATA_DIR / "shops"

# Rasio jual kembali: 40% dari harga beli (keputusan desain; GDD §24.2 —
# angka halus disetel saat playtest Fase 5).
SELL_RATE_PERCENT = 40


def load_shops(data_dir: Path = SHOP_DIR) -> dict[str, dict[str, Any]]:
    """Muat semua toko dari data/shops/ keyed by id.

    Args:
        data_dir: Direktori berisi JSON toko (default data/shops/).

    Returns:
        Mapping shop_id -> dict mentah dengan kunci ``id``, ``name``,
        dan ``stock`` (daftar {"item", "count"}).

    Raises:
        KeyError: Jika sebuah file JSON tidak punya kunci ``id``.
    """
    shops: dict[str, dict[str, Any]] = {}
    for path in sorted(data_dir.glob("*.json")):
        raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        shops[raw["id"]] = raw
    return shops


def sell_price(price: int) -> int:
    """Hitung harga jual kembali item dari harga beli.

    Args:
        price: Harga beli dasar item (field ``price`` di data/items).

    Returns:
        Harga jual = SELL_RATE_PERCENT dari harga beli, dibulatkan ke
        bawah (bilangan bulat).
    """
    return price * SELL_RATE_PERCENT // 100
