"""Engine simpan/muat: slot, atomic write, backup, migrasi (GDD §19)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Callable

from src.core.state import SCHEMA_VERSION, GameState
from src.engine.combat import load_techniques
from src.engine.items import load_items
from src.engine.quest import load_quests
from src.models.party import load_companions
from src.models.player import BASE_STATS
from src.systems.formation import load_formations

SAVE_DIR = Path(__file__).resolve().parents[2] / "saves"
SLOTS = ("save1", "save2", "save3")
AUTOSAVE = "autosave"
VALID_SLOTS = frozenset((*SLOTS, AUTOSAVE))
CURRENT_VERSION = SCHEMA_VERSION

# Migrasi versi lama: MIGRATIONS[versi_lama] -> fungsi yang menaikkan ke
# versi_lama + 1. Diisi saat struktur save berubah (§19.3).
MIGRATIONS: dict[int, Callable[[dict[str, Any]], dict[str, Any]]] = {
    # v1 -> v2: field stok toko terjual (shop_sold) diperkenalkan (GDD
    # §19.2). Default kosong = seluruh toko stok penuh (belum terjual).
    1: lambda raw: {**raw, "shop_sold": {}},
}


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


# ponytail: _validate_references memuat 4 direktori data penuh per load;
# cache id-set di modul bila frekuensi load naik atau jumlah data besar
# (rujukan DataCache GDD §25).
def _validate_references(state: GameState) -> None:
    """Validasi referensi lintas data (GDD §19.3, BUG-5).

    Save yang memuat id tak dikenal (item, quest, party, skill) ditolak
    keras saat load — mencegah error samar/crash di tengah permainan
    (mis. item hantu di inventory, rekan tanpa stats, teknik hilang).
    """
    if not isinstance(state.location, str) or not state.location:
        raise ValueError("lokasi pemain tidak valid")
    missing = set(BASE_STATS) - set(state.player.stats)
    if missing:
        raise ValueError(f"stats pemain tidak lengkap: {sorted(missing)}")
    if (
        state.formation_active is not None
        and state.formation_active not in load_formations()
    ):
        raise ValueError(
            f"formasi aktif tidak dikenal: {state.formation_active}"
        )
    item_ids = set(load_items())
    for item_id in state.inventory.get("items", {}):
        if item_id not in item_ids:
            raise ValueError(f"item tak dikenal di inventory: {item_id}")
    for item_id in state.inventory.get("equipped", {}):
        if item_id not in item_ids:
            raise ValueError(f"item tak dikenal di equipped: {item_id}")
    for item_id, artifact in state.inventory.get("artifacts", {}).items():
        # BUG-24: artefak tanpa level/xp (atau id tak dikenal) memicu
        # KeyError saat battle dimulai (effective_stats_with_gear).
        if item_id not in item_ids:
            raise ValueError(f"artefak tak dikenal: {item_id}")
        if not isinstance(artifact, dict):
            raise ValueError(f"data artefak rusak: {item_id}")
        level = artifact.get("level")
        xp = artifact.get("xp")
        if not isinstance(level, int) or level < 1:
            raise ValueError(f"level artefak tidak valid: {item_id}")
        if not isinstance(xp, int) or xp < 0:
            raise ValueError(f"xp artefak tidak valid: {item_id}")
    quest_ids = {quest.id for quest in load_quests()}
    for group in (state.quests.started, state.quests.done, state.quests.failed):
        for quest_id in group:
            if quest_id not in quest_ids:
                raise ValueError(f"quest tak dikenal: {quest_id}")
    companion_ids = {companion.id for companion in load_companions()}
    technique_ids = {technique.id for technique in load_techniques()}
    for member in state.party:
        if member.get("id") not in companion_ids:
            raise ValueError(f"rekan tak dikenal: {member.get('id')}")
        for skill in member.get("skills", []):
            if skill not in technique_ids:
                raise ValueError(f"skill rekan tak dikenal: {skill}")
        bond_xp = member.get("bond_xp", 0)
        if not isinstance(bond_xp, int):
            # BUG-24: bond_xp non-int crash int() di Companion.from_dict
            # saat panel tim/tampilan dibuka.
            raise ValueError(f"bond_xp rekan tidak valid: {member.get('id')}")
    member_ids = [member.get("id") for member in state.party]
    if not isinstance(state.party_active, list):
        raise ValueError("party_active tidak valid")
    for member_id in state.party_active:
        # BUG-24: anggota aktif harus bagian dari party yang direkrut.
        if member_id not in member_ids:
            raise ValueError(f"anggota aktif tak dikenal: {member_id}")
