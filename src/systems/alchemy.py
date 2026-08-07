"""Sistem Alkimia (GDD §7) — meracik pil dari bahan (refine).

Logika racik dipindah dari ``src/core/game_loop.py`` (P1 refactor):
game_loop tetap menyusun cascade quest/event; sistem ini murni
memvalidasi syarat dan memutasi inventori (satu jalur mutasi).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.engine.items import load_items

if TYPE_CHECKING:
    from src.core.state import GameState


def refine_item(state: GameState, target_id: str) -> tuple[bool, list[str]]:
    """Racik pil dari bahan sesuai resep (GDD §18.2).

    Syarat: resep sudah dipelajari (flag ``recipe_<item>_known``),
    Kuali Roh ada di tas, dan semua bahan tersedia. Mengonsumsi bahan
    sesuai resep lalu menambah pil hasil.

    Args:
        state: GameState yang inventory-nya dimutasi.
        target_id: ID pil hasil racikan (kunci data/items/).

    Returns:
        Tuple (sukses, pesan). Bila gagal, pesan berisi alasan; bila
        sukses, pesan berisi hasil racikan.
    """
    catalog = load_items()
    item = catalog.get(target_id)
    if item is None:
        return False, [f"Resep '{target_id}' tidak dikenal."]
    recipe = item.get("recipe")
    if not recipe:
        # Beberapa resep menempel di item tipe=recipe yang learn_recipe
        # menunjuk ke hasilnya (data eksisting) — cari di seluruh katalog.
        for cat_item in catalog.values():
            eff = cat_item.get("effect") or {}
            if (
                cat_item.get("type") == "recipe"
                and eff.get("learn_recipe") == target_id
            ):
                recipe = cat_item.get("recipe")
                break
    if not recipe:
        return False, [f"{item['name']} tidak memiliki resep."]
    if not state.flags.get(f"recipe_{target_id}_known"):
        return False, [
            f"Kamu belum mempelajari resep {item['name']}. "
            "Beli dan pakai item resepnya dulu."
        ]
    items = state.inventory.setdefault("items", {})
    if items.get("kuali_roh", 0) <= 0:
        return False, ["Kamu butuh Kuali Roh untuk meracik."]
    for req in recipe:
        if items.get(req["item"], 0) < req["qty"]:
            need = catalog.get(req["item"], {}).get("name", req["item"])
            return False, [f"Bahan tidak cukup: butuh {req['qty']}x {need}."]
    for req in recipe:
        items[req["item"]] -= req["qty"]
        if items[req["item"]] == 0:
            del items[req["item"]]
    items[target_id] = items.get(target_id, 0) + 1
    return True, [f"Kamu meracik {item['name']} x1."]
