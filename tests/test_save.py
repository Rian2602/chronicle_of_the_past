"""Test engine simpan/muat: slot, atomic write, backup, migrasi (GDD §19)."""

import json

import pytest

from src.core.save import (
    SaveError,
    autosave_load,
    autosave_save,
    load_game,
    save_game,
    slot_exists,
)
from src.core.state import GameState
from src.models.player import Player


def _state(name="Akar", gold=0) -> GameState:
    """State dasar untuk test save."""
    return GameState(player=Player(name=name, gold=gold))


def test_save_dan_load_roundtrip(tmp_path):
    """Simpan lalu muat mengembalikan state identik."""
    state = _state(gold=50)
    save_game(state, "save1", tmp_path)
    loaded = load_game("save1", tmp_path)
    assert loaded.to_dict() == state.to_dict()


def test_save_atomik_tanpa_tmp_tersisa(tmp_path):
    """Tidak ada file .tmp tersisa setelah simpan sukses (§19.3)."""
    save_game(_state(), "save1", tmp_path)
    assert not list(tmp_path.glob("*.tmp"))


def test_save_membuat_backup_versi_sebelumnya(tmp_path):
    """File lama disalin ke .bak sebelum ditimpa (§19.3)."""
    first = _state(gold=10)
    second = _state(gold=20)
    save_game(first, "save1", tmp_path)
    save_game(second, "save1", tmp_path)
    backup = json.loads((tmp_path / "save1.json.bak").read_text("utf-8"))
    assert backup["player"]["gold"] == 10


def test_load_slot_kosong_saveerror(tmp_path):
    """Slot kosong memunculkan SaveError dengan pesan jelas."""
    with pytest.raises(SaveError):
        load_game("save2", tmp_path)


def test_load_korup_fallback_ke_bak(tmp_path):
    """File utama korup -> muat dari .bak (§19.3)."""
    save_game(_state(gold=15), "save1", tmp_path)
    save_game(_state(gold=30), "save1", tmp_path)  # .bak = versi gold 15
    (tmp_path / "save1.json").write_text("{rusak", encoding="utf-8")
    loaded = load_game("save1", tmp_path)
    assert loaded.player.gold == 15


def test_load_korup_keduanya_saveerror(tmp_path):
    """Utama dan .bak korup -> SaveError (tanpa crash) (§19.3)."""
    save_game(_state(gold=1), "save1", tmp_path)
    save_game(_state(gold=2), "save1", tmp_path)
    (tmp_path / "save1.json").write_text("{rusak", encoding="utf-8")
    (tmp_path / "save1.json.bak").write_text("bukan json", encoding="utf-8")
    with pytest.raises(SaveError):
        load_game("save1", tmp_path)


def test_autosave_slot(tmp_path):
    """Autosave menyimpan/memuat ke slot terpisah (§19.1)."""
    autosave_save(_state(gold=7), tmp_path)
    assert autosave_load(tmp_path).player.gold == 7


def test_backfill_flag_quest_done(tmp_path):
    """Backfill: quest selesai tanpa flag quest<id>_done di-set (§19.3)."""
    state = _state()
    state.quests.done = ["quest101"]
    save_game(state, "save1", tmp_path)
    loaded = load_game("save1", tmp_path)
    assert loaded.flags["quest101_done"] is True


def test_backfill_tidak_menimpa_flag_ada(tmp_path):
    """Backfill tidak menimpa flag yang sudah ada di save."""
    state = _state()
    state.quests.done = ["quest102"]
    state.flags["quest102_done"] = False
    save_game(state, "save1", tmp_path)
    loaded = load_game("save1", tmp_path)
    assert loaded.flags["quest102_done"] is False


def test_migrasi_rantai_dijalankan(tmp_path, monkeypatch):
    """Rantai migrasi diterapkan sebelum state dibangun (§19.3)."""
    import src.core.save as save_module

    monkeypatch.setattr(save_module, "CURRENT_VERSION", 3)
    monkeypatch.setattr(
        save_module,
        "MIGRATIONS",
        {
            1: lambda raw: {
                **raw,
                "flags": {**raw.get("flags", {}), "migrated_1": True},
            },
            2: lambda raw: {
                **raw,
                "flags": {**raw.get("flags", {}), "migrated_2": True},
            },
        },
    )
    raw = {"schema_version": 1, "player": {"name": "Akar", "gold": 5}}
    (tmp_path / "save1.json").write_text(json.dumps(raw), encoding="utf-8")
    loaded = save_module.load_game("save1", tmp_path)
    assert loaded.flags["migrated_1"] is True
    assert loaded.flags["migrated_2"] is True
    assert loaded.player.gold == 5


def test_save_versi_lebih_baru_ditolak(tmp_path):
    """Save dari versi game lebih baru ditolak dengan pesan jelas."""
    raw = {"schema_version": 99, "player": {"name": "Akar"}}
    (tmp_path / "save1.json").write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(SaveError, match="99"):
        load_game("save1", tmp_path)


def test_meridian_tidak_valid_ditolak(tmp_path):
    """Meridian di luar 0-8 di save -> SaveError (bukan crash)."""
    raw = {"schema_version": 1, "player": {"name": "Akar", "meridian_buka": 9}}
    (tmp_path / "save1.json").write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(SaveError):
        load_game("save1", tmp_path)


def test_stats_player_parsial_ditolak(tmp_path):
    """Save dengan stats parsial ditolak saat load (§19.3)."""
    raw = {
        "schema_version": 1,
        "player": {"name": "Akar", "stats": {"attack": 99}},
    }
    (tmp_path / "save1.json").write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(SaveError):
        load_game("save1", tmp_path)


def test_quest_list_bukan_string_ditolak(tmp_path):
    """Daftar quest dengan tipe salah ditolak saat load (§19.3)."""
    raw = {
        "schema_version": 1,
        "player": {"name": "Akar"},
        "quests": {"started": "quest101", "done": [], "failed": []},
    }
    (tmp_path / "save1.json").write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(SaveError):
        load_game("save1", tmp_path)


def test_field_quest_reputasi_waktu_bukan_objek_ditolak(tmp_path):
    """quests/reputation/time non-objek ditolak saat load (tanpa crash)."""
    raw = {
        "schema_version": 1,
        "player": {"name": "Akar"},
        "quests": "hello",
        "reputation": "x",
        "time": "x",
    }
    (tmp_path / "save1.json").write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(SaveError):
        load_game("save1", tmp_path)


def test_slot_tidak_dikenal_ditolak(tmp_path):
    """Nama slot di luar daftar valid ditolak."""
    with pytest.raises(ValueError):
        save_game(_state(), "save4", tmp_path)
    with pytest.raises(ValueError):
        load_game("save4", tmp_path)


def test_slot_exists(tmp_path):
    """slot_exists mendeteksi keberadaan slot."""
    assert not slot_exists("save1", tmp_path)
    save_game(_state(), "save1", tmp_path)
    assert slot_exists("save1", tmp_path)
