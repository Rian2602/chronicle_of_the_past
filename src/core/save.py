"""Engine simpan/muat: slot, atomic write, backup, migrasi (GDD §19)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Callable

from src.core.state import SCHEMA_VERSION, GameState
from src.models.player import BASE_STATS

SAVE_DIR = Path(__file__).resolve().parents[2] / "saves"
SLOTS = ("save1", "save2", "save3")
AUTOSAVE = "autosave"
VALID_SLOTS = frozenset((*SLOTS, AUTOSAVE))
CURRENT_VERSION = SCHEMA_VERSION

# Migrasi versi lama: MIGRATIONS[versi_lama] -> fungsi yang menaikkan ke
# versi_lama + 1. Kosong untuk v1; diisi saat struktur save berubah (§19.3).
MIGRATIONS: dict[int, Callable[[dict[str, Any]], dict[str, Any]]] = {}


class SaveError(Exception):
    """Save rusak atau tidak bisa dimuat; pesan untuk ditampilkan ke pemain."""


def save_game(
    state: GameState,
    slot: str,
    save_dir: Path = SAVE_DIR,
) -> Path:
    """Simpan state ke slot secara atomik; file lama disalin ke .bak.

    Urutan aman (GDD §19.3): backup lama -> tulis .tmp -> os.replace.
    """
    _validate_slot(slot)
    save_dir.mkdir(parents=True, exist_ok=True)
    target = save_dir / f"{slot}.json"
    backup = save_dir / f"{slot}.json.bak"
    if target.exists():
        os.replace(target, backup)
    tmp = save_dir / f"{slot}.json.tmp"
    tmp.write_text(
        json.dumps(state.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    os.replace(tmp, target)
    return target


def load_game(slot: str, save_dir: Path = SAVE_DIR) -> GameState:
    """Muat state dari slot; coba .bak bila utama rusak (GDD §19.3).

    Memunculkan SaveError dengan pesan jelas bila tidak bisa dimuat.
    """
    _validate_slot(slot)
    candidates = [save_dir / f"{slot}.json", save_dir / f"{slot}.json.bak"]
    primary_error: Exception | None = None
    for path in candidates:
        if not path.exists():
            if primary_error is None:
                primary_error = FileNotFoundError(f"slot kosong: {slot}")
            continue
        try:
            return _build_state(path)
        except (ValueError, KeyError, TypeError) as exc:
            if primary_error is None:
                primary_error = exc
    raise SaveError(
        f"save tidak bisa dimuat ({slot}): {primary_error}"
    ) from primary_error


def autosave_save(state: GameState, save_dir: Path = SAVE_DIR) -> Path:
    """Simpan ke slot autosave (§19.1)."""
    return save_game(state, AUTOSAVE, save_dir)


def autosave_load(save_dir: Path = SAVE_DIR) -> GameState:
    """Muat dari slot autosave (§19.1)."""
    return load_game(AUTOSAVE, save_dir)


def slot_exists(slot: str, save_dir: Path = SAVE_DIR) -> bool:
    """Kembalikan True bila slot memiliki file save atau backup."""
    _validate_slot(slot)
    return (save_dir / f"{slot}.json").exists() or (
        save_dir / f"{slot}.json.bak"
    ).exists()


def _validate_slot(slot: str) -> None:
    """Tolak nama slot di luar daftar valid (save1-3, autosave)."""
    if slot not in VALID_SLOTS:
        raise ValueError(f"slot tidak dikenal: {slot}")


def _build_state(path: Path) -> GameState:
    """Baca, migrasi, bangun, backfill, dan validasi state dari file."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError, OSError) as exc:
        raise ValueError(f"file rusak: {path.name}") from exc
    if not isinstance(raw, dict):
        raise ValueError(f"save bukan objek JSON: {path.name}")
    version = raw.get("schema_version", 1)
    if not isinstance(version, int) or version < 1:
        raise ValueError("schema_version tidak valid")
    if version > CURRENT_VERSION:
        raise ValueError(
            f"save dibuat versi {version} (engine hanya mendukung "
            f"sampai {CURRENT_VERSION})"
        )
    data = _apply_migrations(raw, version)
    state = GameState.from_dict(data)
    _backfill_quest_flags(state)
    _validate_references(state)
    return state


def _apply_migrations(raw: dict[str, Any], version: int) -> dict[str, Any]:
    """Terapkan rantai migrasi dari versi save ke versi sekarang (§19.3)."""
    data = dict(raw)
    current = version
    while current < CURRENT_VERSION:
        migration = MIGRATIONS.get(current)
        if migration is None:
            raise ValueError(f"tidak ada migrasi dari versi {current}")
        data = migration(data)
        current += 1
    return data


def _backfill_quest_flags(state: GameState) -> None:
    """Backfill wajib: quest selesai tanpa flag quest<id>_done di-set."""
    for quest_id in state.quests.done:
        flag = f"{quest_id}_done"
        if flag not in state.flags:
            state.flags[flag] = True


def _validate_references(state: GameState) -> None:
    """Validasi referensi lintas data (GDD §19.3).

    Perluasan: resolusi id item/quest/peta/teknik terhadap data/ akan
    diisi di sini saat folder data terkait terisi (Fase 1).
    """
    if not isinstance(state.location, str) or not state.location:
        raise ValueError("lokasi pemain tidak valid")
    missing = set(BASE_STATS) - set(state.player.stats)
    if missing:
        raise ValueError(f"stats pemain tidak lengkap: {sorted(missing)}")
