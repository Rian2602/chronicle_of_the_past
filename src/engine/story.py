"""Echo memori (GDD §15.3 grant_memory) — konten naratif data-driven.

Isi memori (judul + teks) dipisah dari engine: event cukup menyimpan
``memory_id``, teks lengkap dibaca dari ``data/story/`` (§14.2).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.core.state import GameState

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
STORY_DIR = DATA_DIR / "story"


def load_memories(data_dir: Path = STORY_DIR) -> dict[str, dict[str, str]]:
    """Muat semua echo memori dari data/story/ keyed by id.

    Args:
        data_dir: Direktori berisi JSON memori (default data/story/).

    Returns:
        Mapping memory_id -> dict dengan kunci ``id``, ``title``, ``text``.

    Raises:
        KeyError: Jika sebuah file JSON tidak punya kunci ``id``.
    """
    memories: dict[str, dict[str, str]] = {}
    for path in sorted(data_dir.glob("*.json")):
        raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        memories[raw["id"]] = {"title": raw["title"], "text": raw["text"]}
    return memories


def calculate_ending(state: GameState) -> str:
    """Hitung jalur ending dengan poin tertinggi dari state.ending_points.

    Sesuai GDD §21.1, ending utama ditentukan oleh jalur dengan poin
    tertinggi di ``state.ending_points`` ('defy', 'seal', 'reconcile').
    Jika terjadi seri (tie), prioritas default adalah 'defy' >= 'seal' >=
    'reconcile'.

    Args:
        state: GameState permainan saat ini.

    Returns:
        Nama jalur ending yang menang: 'defy', 'seal', atau 'reconcile'.
    """
    points = state.ending_points
    defy_pts = points.get("defy", 0)
    seal_pts = points.get("seal", 0)
    reconcile_pts = points.get("reconcile", 0)

    if defy_pts >= seal_pts and defy_pts >= reconcile_pts:
        return "defy"
    if seal_pts >= reconcile_pts:
        return "seal"
    return "reconcile"


def build_epilogue(state: GameState) -> list[str]:
    """Susun epilog dari reputasi 5 faksi (GDD §21.2).

    Status per faksi: >= 70 "berkuasa", >= 30 "kuat", > -30 "lemah",
    lainnya "hancur". Dipanggil game_loop saat flag ending memicu.

    Args:
        state: GameState permainan saat ini.

    Returns:
        Daftar baris epilog, satu baris per faksi.
    """
    lines: list[str] = []
    for faction, score in state.reputation.items():
        if score >= 70:
            status = "berkuasa"
        elif score >= 30:
            status = "kuat"
        elif score > -30:
            status = "lemah"
        else:
            status = "hancur"
        lines.append(f"{faction}: {status} ({score})")
    return lines
