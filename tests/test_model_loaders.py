"""Tests for model and system loaders using generic load_json_dir."""

from src.models.party import load_companions
from src.systems.formation import load_formations


def test_model_loaders() -> None:
    """Verify load_companions and load_formations return expected types."""
    companions = load_companions()
    assert isinstance(companions, list)
    assert len(companions) > 0

    formations = load_formations()
    assert isinstance(formations, dict)
    assert len(formations) > 0
