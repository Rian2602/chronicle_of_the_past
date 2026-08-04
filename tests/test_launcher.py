import builtins

import launcher
from launcher import _game_loop, _menu_selection, main
from src.core import save_manager
from src.utils.json_loader import ContentError


def test_main_returns_1_on_content_error(monkeypatch):
    class Boom:
        def __init__(self, *args, **kwargs):
            raise ContentError("bad data")

    monkeypatch.setattr(launcher, "GameContext", Boom)
    assert main() == 1


def test_menu_selection_arrow_down_then_enter(monkeypatch):
    keys = iter(["s", ""])
    monkeypatch.setattr(builtins, "input", lambda _: next(keys))
    assert _menu_selection() == 1


def test_menu_selection_up_wraps(monkeypatch):
    total = len(launcher.menu.MAIN_ITEMS)
    keys = iter(["w", ""])
    monkeypatch.setattr(builtins, "input", lambda _: next(keys))
    assert _menu_selection() == total - 1


def test_menu_loop_clears_screen_for_every_redraw(monkeypatch):
    keys = iter(["s", ""])
    clears = []
    monkeypatch.setattr(builtins, "input", lambda _: next(keys))
    monkeypatch.setattr(launcher, "_clear_screen", lambda: clears.append(True))

    assert launcher._menu_loop(lambda selection: f"Menu {selection}", 2, "Petunjuk") == 1
    assert len(clears) == 2


def test_settings_menu_cycles_then_resets_and_saves(monkeypatch, tmp_path):
    selections = iter([0, 1, 2, 3])
    monkeypatch.setattr(launcher, "_menu_loop", lambda *args, **kwargs: next(selections))
    path = tmp_path / "settings.json"

    result, _ = launcher._settings_menu(launcher.settings.Settings(), path)

    assert result == launcher.settings.Settings()
    assert launcher.settings.load_settings(path) == launcher.settings.Settings()


def test_save_picker_excludes_global_settings(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "saves").mkdir()
    (tmp_path / "saves" / "slot1.json").write_text("{}", encoding="utf-8")
    (tmp_path / launcher.settings.SETTINGS_PATH).write_text("{}", encoding="utf-8")

    assert launcher._save_paths() == ["saves/slot1.json"]


def test_main_skips_startup_animation_when_disabled(monkeypatch):
    calls = []
    monkeypatch.setattr(launcher.settings, "load_settings", lambda: launcher.settings.Settings(animation_mode="off"))
    monkeypatch.setattr(launcher.animation, "animate", lambda *args, **kwargs: calls.append(True))
    monkeypatch.setattr(launcher, "_menu_selection", lambda screen: 4)

    assert main() == 0
    assert calls == []


class FakeGame:
    def __init__(self):
        self.calls = 0

    def run_turn(self, text):
        self.calls += 1
        raise save_manager.SaveError("disk penuh")


def test_game_loop_catches_save_error(monkeypatch, capsys):
    game = FakeGame()
    keys = iter(["", "q"])
    monkeypatch.setattr(builtins, "input", lambda _: next(keys))
    _game_loop(game)
    assert game.calls == 1
    assert "Gagal menyimpan: disk penuh" in capsys.readouterr().out


class BoomGame:
    def run_turn(self, text):
        raise RuntimeError("boom")


def test_game_loop_catches_generic_exception(monkeypatch, capsys):
    game = BoomGame()
    keys = iter(["", "q"])
    monkeypatch.setattr(builtins, "input", lambda _: next(keys))
    _game_loop(game)
    out = capsys.readouterr().out
    assert "Terjadi kesalahan: boom" in out
    assert "Traceback" not in out


def test_game_loop_quit_confirms_during_combat(monkeypatch, capsys):
    class CombatGame:
        _combat = object()

        def run_turn(self, text):
            return "ok"

    game = CombatGame()
    keys = iter(["q", "s", "", "q", ""])

    def fake_input(prompt=""):
        print(prompt, end="")
        return next(keys)

    monkeypatch.setattr(builtins, "input", fake_input)
    _game_loop(game)
    out = capsys.readouterr().out
    assert "bertarung" in out
    assert "Sampai jumpa!" in out
