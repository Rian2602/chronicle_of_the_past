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


class FakeGame:
    def __init__(self):
        self.calls = 0

    def run_turn(self, text):
        self.calls += 1
        raise save_manager.SaveError("disk penuh")


def test_game_loop_catches_save_error(monkeypatch, capsys):
    game = FakeGame()
    keys = iter(["save slot", "quit"])
    monkeypatch.setattr(builtins, "input", lambda _: next(keys))
    _game_loop(game)
    assert game.calls == 1
    assert "Gagal menyimpan: disk penuh" in capsys.readouterr().out
