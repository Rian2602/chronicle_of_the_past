import logging
from src.utils.helpers import clamp
from src.utils.logger import get_logger

def test_clamp_bounds():
    assert clamp(5, 0, 10) == 5
    assert clamp(-1, 0, 10) == 0
    assert clamp(11, 0, 10) == 10

def test_get_logger_has_handlers():
    logger = get_logger("test.game")
    assert isinstance(logger, logging.Logger)
    assert any(isinstance(h, logging.FileHandler) for h in logger.handlers)
    assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)

def test_get_logger_does_not_duplicate_handlers():
    name = "test.game"
    get_logger(name)
    count = len(get_logger(name).handlers)
    assert count > 0
    assert len(get_logger(name).handlers) == count
