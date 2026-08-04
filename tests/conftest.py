import pytest

from src.core.game_state import GameState


@pytest.fixture
def randomizer():
    from src.core.randomizer import Randomizer

    return Randomizer(seed=12345)


@pytest.fixture
def game_state():
    return GameState()
