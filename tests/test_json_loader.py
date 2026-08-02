import pytest
from src.utils.json_loader import load_json, load_dir, ContentError

def test_load_json_missing_file_raises(tmp_path):
    with pytest.raises(ContentError):
        load_json(str(tmp_path / "nope.json"))

def test_load_json_valid(tmp_path):
    p = tmp_path / "a.json"
    p.write_text('{"a": 1}')
    assert load_json(str(p)) == {"a": 1}

def test_load_dir_keys_are_ids(tmp_path):
    (tmp_path / "warrior.json").write_text('{"id":"warrior","x":1}')
    data = load_dir(str(tmp_path))
    assert data["warrior"]["x"] == 1

def test_load_dir_missing_dir_returns_empty(tmp_path):
    assert load_dir(str(tmp_path / "missing")) == {}
