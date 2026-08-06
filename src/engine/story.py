"""Echo memori (GDD §15.3 grant_memory) — konten naratif data-driven.

Isi memori (judul + teks) dipisah dari engine: event cukup menyimpan
``memory_id``, teks lengkap dibaca dari ``data/story/`` (§14.2).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

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
