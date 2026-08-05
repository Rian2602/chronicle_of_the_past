import pytest

from src.utils.json_loader import ContentError, load_dir, load_json


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


def test_load_dir_missing_id_raises_content_error(tmp_path):
    (tmp_path / "bad.json").write_text('{"no_id": 1}')
    with pytest.raises(ContentError):
        load_dir(str(tmp_path))


def test_load_dir_non_dict_root_raises_content_error(tmp_path):
    (tmp_path / "bad.json").write_text('[1, 2, 3]')
    with pytest.raises(ContentError):
        load_dir(str(tmp_path))


def test_load_json_invalid_utf8_raises_content_error(tmp_path):
    p = tmp_path / "bad.json"
    p.write_bytes(b'{"a": "\xff\xfe"}')
    with pytest.raises(ContentError):
        load_json(str(p))


def test_load_file_list_non_list_raises_content_error(tmp_path):
    from src.core.game_context import GameContext

    ctx = GameContext(data_dir="data")
    p = tmp_path / "list.json"
    p.write_text('{"a": 1}')
    with pytest.raises(ContentError):
        ctx._load_file_list(str(p))
