"""Smoke test untuk entry point launcher (GDD §14.1)."""

from unittest import mock

import launcher
from src.ui.app import ChronicleApp


def test_app_textual_tersedia():
    """App Textual tersedia dengan judul yang benar."""
    app = ChronicleApp()
    assert app.TITLE == "Chronicle of the Past"


def test_main_returns_zero():
    """main() menjalankan App (dimock) dan mengembalikan 0."""
    with mock.patch.object(ChronicleApp, "run") as run:
        assert launcher.main() == 0
        run.assert_called_once()
