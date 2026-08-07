import pytest

from src.core.game_loop import make_bar


def test_make_bar_full():
    assert make_bar(10, 10, width=10) == "█" * 10


def test_make_bar_half():
    assert make_bar(5, 10, width=10) == "█" * 5 + "░" * 5


def test_make_bar_zero_total():
    assert make_bar(0, 0, width=10) == "░" * 10
