"""Smoke test untuk entry point launcher (Fase 0 belum dimulai)."""

import launcher


def test_main_returns_zero(capsys):
    """main() sukses, mengembalikan 0, dan mencetak judul game."""
    assert launcher.main() == 0
    output = capsys.readouterr().out
    assert "Chronicle of the Past" in output
