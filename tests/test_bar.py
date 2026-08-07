import pytest
from rich.bar import Bar

from src.core import game_loop
from src.core.game_loop import BattleFrame, GameSession
from src.ui.app import GameScreen


def test_make_bar_removed():
    """make_bar must be removed from core.game_loop."""
    assert not hasattr(game_loop, "make_bar")


def test_status_lines_uses_rich_bar():
    """status_lines should instantiate rich.bar.Bar instead of ASCII string."""
    session = GameSession()
    session.new_game("Tester")
    lines = session.status_lines()
    hp_line = lines[2]
    assert "Bar(" in hp_line


def test_enemy_lines_uses_rich_bar():
    """_enemy_lines in UI should use rich.bar.Bar."""
    screen = GameScreen()
    frame = BattleFrame(
        log=[],
        over=False,
        victory=None,
        escaped=False,
        player_turn=True,
        enemies=[{"name": "Wolf", "hp": 10, "hp_max": 20, "qi": 5, "element": "Physical"}],
    )
    lines = screen._enemy_lines(frame)
    assert len(lines) == 1
    assert "Bar(" in lines[0]
