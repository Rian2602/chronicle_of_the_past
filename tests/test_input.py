"""Test parser perintah game (GDD §18): alias, argumen, dan error."""

import pytest

from src.core.input import (
    Command,
    CommandError,
    parse_command,
)


def test_perintah_kanonik():
    """Perintah bahasa Inggris langsung dikenali."""
    command = parse_command("status")
    assert command == Command(name="status", args=(), raw="status")


def test_alias_indonesia():
    """Alias bahasa Indonesia dipetakan ke perintah kanonik (§18)."""
    assert parse_command("kultivasi").name == "cultivate"
    assert parse_command("istirahat").name == "rest"
    assert parse_command("terobosan").name == "breakthrough"
    assert parse_command("keluar").name == "quit"
    assert parse_command("bicara elder_mao").name == "talk"
    assert parse_command("tas").name == "inventory"
    assert parse_command("misi").name == "quests"
    assert parse_command("memori").name == "memories"
    assert parse_command("tim").name == "party"
    assert parse_command("amat").name == "look"
    assert parse_command("rampas").name == "loot"
    assert parse_command("meditasi").name == "meditate"
    assert parse_command("racik").name == "refine"
    assert parse_command("formasi").name == "formation"
    assert parse_command("pengaturan").name == "settings"


def test_alias_combat():
    """Alias perintah pertarungan (§18.3)."""
    assert parse_command("serang").name == "attack"
    assert parse_command("bertahan").name == "defend"
    assert parse_command("kabur").name == "escape"
    assert parse_command("amati").name == "observe"
    assert parse_command("teknik qi_slash").name == "technique"


def test_argument_dipisah():
    """Argumen dipisah dan dipertahankan urutannya."""
    command = parse_command("go ashfall_forest")
    assert command.name == "go"
    assert command.args == ("ashfall_forest",)

    command = parse_command("save 2")
    assert command.name == "save"
    assert command.args == ("2",)


def test_teknik_ambil_nama_teknik():
    """Perintah teknik membawa nama teknik sebagai argumen."""
    command = parse_command("teknik qi_slash")
    assert command.name == "technique"
    assert command.args == ("qi_slash",)


def test_huruf_besar_dinormalisasi():
    """Input huruf besar/kecil tidak masalah."""
    assert parse_command("STATUS").name == "status"
    assert parse_command("Go Forest").name == "go"


def test_whitespace_berlebih_dirapikan():
    """Spasi berlebih tidak menghasilkan argumen kosong."""
    command = parse_command("  go   ashfall_forest  ")
    assert command.args == ("ashfall_forest",)


def test_baris_kosong_mengembalikan_none():
    """Baris kosong diabaikan (bukan error)."""
    assert parse_command("") is None
    assert parse_command("   ") is None


def test_perintah_tidak_dikenal_melempar_error():
    """Perintah tak dikenal memberi pesan jelas yang memuat perintah itu."""
    with pytest.raises(CommandError) as excinfo:
        parse_command("flying_sword")
    assert "flying_sword" in str(excinfo.value)
