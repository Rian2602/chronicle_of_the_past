"""Test UI Textual — navigasi panah ↑↓ + Enter + klik tanpa ketik (GDD §14.1).

Layar game tidak lagi memakai Input perintah; semua aksi dipilih dari
OptionList yang kontennya data-driven (menu_actions di GameSession).
Pertarungan & dialog berjalan sebagai mode dalam GameScreen yang sama
(satu layar, konten beralih) agar navigasi tetap satu jalur.
"""

import pytest
from textual.widgets import (
    Button,
    Collapsible,
    Input,
    OptionList,
    RichLog,
    Static,
    TabbedContent,
    TabPane,
)

from src.core.game_loop import GameSession
from src.ui.app import ChronicleApp, GameScreen, MainMenuScreen, NameScreen


def _app(tmp_path) -> ChronicleApp:
    """App dengan sesi dan folder save sementara."""
    return ChronicleApp(session=GameSession(save_dir=tmp_path))


async def _mulai(app, pilot, nama: str = "Akar") -> None:
    """Alur mulai baru: n -> isi nama -> enter -> layar game."""
    await pilot.press("n")
    await pilot.pause()
    app.screen.query_one("#name", Input).value = nama
    await pilot.press("enter")
    await pilot.pause()


def _pilih(actions: OptionList, option_id: str, pilot) -> None:
    """Highlight opsi lalu Enter (API nyata Textual 8.2.8)."""
    actions.highlighted = actions.get_option_index(option_id)


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
        await _mulai(app, pilot)
        assert isinstance(app.screen, GameScreen)
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, MainMenuScreen)


@pytest.mark.asyncio
async def test_alur_mulai_baru_sampai_layar_game(tmp_path):
    """Isi nama -> Enter -> layar game menampilkan HUD pemain."""
    app = _app(tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        await _mulai(app, pilot)
        assert isinstance(app.screen, GameScreen)
        hud = app.screen.query_one("#hud", Static).content
        assert "Akar" in str(hud)


@pytest.mark.asyncio
async def test_layar_game_tidak_memiliki_input_perintah(tmp_path):
    """Input #cmd dihapus total — navigasi lewat OptionList #actions."""
    app = _app(tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        await _mulai(app, pilot)
        assert app.screen.query_one("#actions", OptionList) is not None
        assert len(app.screen.query("#cmd")) == 0


@pytest.mark.asyncio
async def test_sidebar_kiri_memiliki_ikon_navigasi(tmp_path):
    """Left icon sidebar memuat tombol navigasi (Tas/Quest/Tim/dll)."""
    app = _app(tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        await _mulai(app, pilot)
        assert app.screen.query_one("#nav-tas", Button) is not None
        assert app.screen.query_one("#nav-quest", Button) is not None
        assert app.screen.query_one("#nav-tim", Button) is not None


@pytest.mark.asyncio
async def test_tab_konten_memuat_story_memory_map(tmp_path):
    """Tab konten dalam memuat Story/Memory/Map (TASK.md)."""
    app = _app(tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        await _mulai(app, pilot)
        tabs = app.screen.query_one(TabbedContent)
        pane_ids = [pane.id for pane in tabs.query(TabPane)]
        assert "tab-story" in pane_ids
        assert "tab-memory" in pane_ids
        assert "tab-map" in pane_ids


@pytest.mark.asyncio
async def test_layout_memiliki_panel_quest_dan_party(tmp_path):
    """Sidebar kanan memuat panel quest & party (Collapsible)."""
    app = _app(tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        await _mulai(app, pilot)
        assert app.screen.query_one("#col-quest", Collapsible) is not None
        assert app.screen.query_one("#col-party", Collapsible) is not None
        quest = app.screen.query_one("#panel-quest", Static).content
        assert "Quest" in str(quest)


@pytest.mark.asyncio
async def test_hud_menampilkan_progress_bar_hp_qi(tmp_path):
    """HUD memakai ProgressBar untuk HP/Qi (bukan ASCII saja)."""
    app = _app(tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        await _mulai(app, pilot)
        assert app.screen.query_one("#hp-bar") is not None
        assert app.screen.query_one("#qi-bar") is not None


@pytest.mark.asyncio
async def test_pilih_option_status_menampilkan_log(tmp_path):
    """Pilih Status di OptionList -> log menampilkan Insight."""
    app = _app(tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        await _mulai(app, pilot)
        actions = app.screen.query_one("#actions", OptionList)
        _pilih(actions, "status", pilot)
        await pilot.press("enter")
        await pilot.pause()
        log = app.screen.query_one("#game-log", RichLog).lines
        joined = "\n".join(str(line) for line in log)
        assert "Insight" in joined


@pytest.mark.asyncio
async def test_pilih_option_pergi_ke_hutan_memulai_battle(tmp_path):
    """Pilih Pergi -> sub-menu -> ashfall_forest -> Lihat -> battle aktif."""
    app = _app(tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        await _mulai(app, pilot)
        actions = app.screen.query_one("#actions", OptionList)
        _pilih(actions, "pergi", pilot)
        await pilot.press("enter")
        await pilot.pause()
        _pilih(actions, "ashfall_forest", pilot)
        await pilot.press("enter")
        await pilot.pause()
        assert app.session.state.location == "ashfall_forest"
        # Lihat memicu pertarungan melawan Bandit Perbatasan.
        _pilih(actions, "lihat", pilot)
        await pilot.press("enter")
        await pilot.pause()
        assert app.session.in_battle
        # Mode battle: OptionList kini berisi aksi giliran.
        ids = {
            actions.get_option_at_index(i).id
            for i in range(actions.option_count)
        }
        assert "serang" in ids


@pytest.mark.asyncio
async def test_pilih_option_serang_melakukan_battle_step(tmp_path):
    """Di battle, pilih Serang -> log bertambah (battle_step jalan)."""
    app = _app(tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        await _mulai(app, pilot)
        actions = app.screen.query_one("#actions", OptionList)
        _pilih(actions, "pergi", pilot)
        await pilot.press("enter")
        await pilot.pause()
        _pilih(actions, "ashfall_forest", pilot)
        await pilot.press("enter")
        await pilot.pause()
        _pilih(actions, "lihat", pilot)
        await pilot.press("enter")
        await pilot.pause()
        assert app.session.in_battle
        _pilih(actions, "serang", pilot)
        await pilot.press("enter")
        await pilot.pause()
        log = app.screen.query_one("#game-log", RichLog).lines
        joined = "\n".join(str(line) for line in log)
        assert "menyerang" in joined


@pytest.mark.asyncio
async def test_panel_musuh_memuat_bar_hp(tmp_path):
    """Panel musuh saat bertarung menampilkan bar HP visual (GDD §6)."""
    app = _app(tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        await _mulai(app, pilot)
        actions = app.screen.query_one("#actions", OptionList)
        _pilih(actions, "pergi", pilot)
        await pilot.press("enter")
        await pilot.pause()
        _pilih(actions, "ashfall_forest", pilot)
        await pilot.press("enter")
        await pilot.pause()
        _pilih(actions, "lihat", pilot)
        await pilot.press("enter")
        await pilot.pause()
        enemy = app.screen.query_one("#enemy", Static).content
        assert "█" in str(enemy)


@pytest.mark.asyncio
async def test_hud_menampilkan_stat_saat_battle(tmp_path):
    """HUD tetap menampilkan HP/Qi selama pertarungan (bukan guard)."""
    app = _app(tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        await _mulai(app, pilot)
        actions = app.screen.query_one("#actions", OptionList)
        _pilih(actions, "pergi", pilot)
        await pilot.press("enter")
        await pilot.pause()
        _pilih(actions, "ashfall_forest", pilot)
        await pilot.press("enter")
        await pilot.pause()
        _pilih(actions, "lihat", pilot)
        await pilot.press("enter")
        await pilot.pause()
        hud = app.screen.query_one("#hud", Static).content
        assert "HP" in str(hud)
        assert "bertarung" not in str(hud)


@pytest.mark.asyncio
async def test_dialog_screen_menampilkan_pilihan_bernomor(tmp_path):
    """Talk NPC -> pilihan dialog tampil di OptionList #dlg-choices."""
    app = _app(tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        await _mulai(app, pilot)
        actions = app.screen.query_one("#actions", OptionList)
        _pilih(actions, "bicara", pilot)
        await pilot.press("enter")
        await pilot.pause()
        _pilih(actions, "elder_mao", pilot)
        await pilot.press("enter")
        await pilot.pause()
        choices = app.screen.query_one("#dlg-choices", OptionList)
        assert choices.option_count >= 1
