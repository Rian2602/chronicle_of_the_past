"""Tests for src.core.utils module."""

import json
from dataclasses import dataclass
from pathlib import Path

from src.core.utils import load_json_dir


@dataclass
class MockModel:
    """Mock model for testing load_json_dir."""

    id: str
    name: str


def test_load_json_dir(tmp_path: Path) -> None:
    """Test loading JSON directory as dict and as list of model instances."""
    # Setup mock data
    file_path = tmp_path / "mock.json"
    file_path.write_text(json.dumps({"id": "1", "name": "Test"}))

    # Test loading as dict
    data_dict = load_json_dir(tmp_path)
    assert data_dict["1"]["name"] == "Test"

    # Test loading as model list
    data_list = load_json_dir(tmp_path, model_cls=MockModel)
    assert len(data_list) == 1
    assert data_list[0].id == "1"
