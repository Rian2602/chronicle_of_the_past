"""Test tipis UI Textual: menu utama dan alur mulai baru (GDD §14.1)."""

import pytest
from textual.widgets import Input, Log, Static

from src.core.game_loop import GameSession
from src.ui.app import ChronicleApp, GameScreen, MainMenuScreen, NameScreen


def _app(tmp_path) -> ChronicleApp:
    """App dengan sesi dan folder save sementara."""
    return ChronicleApp(session=GameSession(save_dir=tmp_path))


@pytest.mark.asyncio
async def test_menu_utama_menampilkan_judul(tmp_path):
    """Layar menu menampilkan judul game dan tombol mulai."""
    app = _app(tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        assert isinstance(app.screen, MainMenuScreen)
        title = app.screen.query_one("#title", Static).content
        assert "Chronicle of the Past" in str(title)


@pytest.mark.asyncio
async def test_mulai_baru_mengarah_ke_input_nama(tmp_path):
    """Tombol/tombol n membuka layar input nama."""
    app = _app(tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("n")
        await pilot.pause()
        assert isinstance(app.screen, NameScreen)


@pytest.mark.asyncio
async def test_alur_mulai_baru_sampai_layar_game(tmp_path):
    """Isi nama -> Enter -> layar game menampilkan HUD pemain."""
    app = _app(tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("n")
        await pilot.pause()
        name_input = app.screen.query_one("#name", Input)
        name_input.value = "Akar"
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, GameScreen)
        hud = app.screen.query_one("#hud", Static).content
        assert "Akar" in str(hud)


@pytest.mark.asyncio
async def test_escape_dari_game_kembali_ke_menu(tmp_path):
    """Escape dari layar game kembali ke menu, bukan layar nama basi."""
    app = _app(tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("n")
        await pilot.pause()
        app.screen.query_one("#name", Input).value = "Akar"
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, GameScreen)
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, MainMenuScreen)


@pytest.mark.asyncio
async def test_perintah_status_dari_layar_game(tmp_path):
    """Mengetik status di layar game menampilkan baris log."""
    app = _app(tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("n")
        await pilot.pause()
        app.screen.query_one("#name", Input).value = "Akar"
        await pilot.press("enter")
        await pilot.pause()
        cmd = app.screen.query_one("#cmd", Input)
        cmd.value = "status"
        await pilot.press("enter")
        await pilot.pause()
        log = app.screen.query_one("#game-log", Log).lines
        joined = "\n".join(str(line) for line in log)
        assert "Insight" in joined
