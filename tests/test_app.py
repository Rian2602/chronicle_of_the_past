"""Test tipis UI Textual: menu utama dan alur mulai baru (GDD §14.1)."""

import pytest
from textual.widgets import Input, RichLog, Static

from src.core.game_loop import GameSession
from src.ui.app import ChronicleApp, GameScreen, MainMenuScreen, NameScreen


def _app(tmp_path) -> ChronicleApp:
    """App dengan sesi dan folder save sementara."""
    return ChronicleApp(session=GameSession(save_dir=tmp_path))


@pytest.mark.asyncio
async def test_game_screen_menggunakan_richlog(tmp_path):
    """Layar game memakai RichLog agar narasi bisa diberi markup warna."""
    app = _app(tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("n")
        await pilot.pause()
        app.screen.query_one("#name", Input).value = "Akar"
        await pilot.press("enter")
        await pilot.pause()
        # RichLog ada di layout panel (§14.1); Log klasik tidak dipakai.
        assert isinstance(app.screen.query_one("#game-log"), RichLog)


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
async def test_layout_memiliki_panel_quest_dan_party(tmp_path):
    """Layar game memuat panel quest & party di sidebar."""
    app = _app(tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("n")
        await pilot.pause()
        app.screen.query_one("#name", Input).value = "Akar"
        await pilot.press("enter")
        await pilot.pause()
        assert app.screen.query_one("#panel-quest") is not None
        assert app.screen.query_one("#panel-party") is not None
        # Sidebar terisi data quest aktif (quest101 via event intro).
        quest = app.screen.query_one("#panel-quest", Static).content
        assert "Quest" in str(quest)


@pytest.mark.asyncio
async def test_escape_dari_layar_nama_kembali_ke_menu(tmp_path):
    """Escape dari layar nama kembali ke menu tanpa memulai permainan."""
    app = _app(tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("n")
        await pilot.pause()
        assert isinstance(app.screen, NameScreen)
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, MainMenuScreen)
        assert app.session.state is None


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
async def test_hud_menampilkan_stat_saat_battle(tmp_path):
    """HUD tetap menampilkan HP/Qi selama pertarungan (bukan pesan guard)."""
    app = _app(tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("n")
        await pilot.pause()
        app.screen.query_one("#name", Input).value = "Akar"
        await pilot.press("enter")
        await pilot.pause()
        cmd = app.screen.query_one("#cmd", Input)
        cmd.value = "go ashfall_forest"
        await pilot.press("enter")
        await pilot.pause()
        cmd.value = "look"
        await pilot.press("enter")
        await pilot.pause()
        hud = app.screen.query_one("#hud", Static).content
        assert "HP" in str(hud)
        assert "bertarung" not in str(hud)


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
        log = app.screen.query_one("#game-log", RichLog).lines
        joined = "\n".join(str(line) for line in log)
        assert "Insight" in joined
