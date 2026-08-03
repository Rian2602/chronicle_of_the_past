import pytest
from src.utils.validator import require_keys, validate_condition, SchemaError


def test_require_keys_missing():
    with pytest.raises(SchemaError):
        require_keys({"id": "x"}, ["id", "name"], "data/classes/warrior.json")


def test_require_keys_ok():
    require_keys({"id": "x", "name": "X"}, ["id", "name"], "p")


def test_schema_error_message_lists_missing_keys():
    with pytest.raises(SchemaError) as exc:
        require_keys({"id": "x"}, ["id", "name"], "data/classes/warrior.json")
    assert str(exc.value) == "Schema salah di data/classes/warrior.json: key hilang: ['name']"


def test_load_config_returns_dict(tmp_path, monkeypatch):
    from src.core.config import load_config
    cfg_dir = tmp_path / "config"
    cfg_dir.mkdir()
    (cfg_dir / "config.json").write_text('{"player_speed": 1}')
    monkeypatch.chdir(tmp_path)
    result = load_config(data_dir=".")
    assert result == {"player_speed": 1}


def test_load_config_uses_real_data_dir():
    from src.core.config import load_config
    result = load_config()
    assert isinstance(result, dict)


def test_constants():
    from src.core import constants
    assert constants.STATS == ["attack", "defense", "hp", "mp", "agility", "intelligence"]
    assert constants.TIMES == ["morning", "afternoon", "evening", "night"]
    assert constants.FACTIONS == [
        "royal_army", "church", "rebels", "merchant_guild",
        "scholar_society", "ancient_order", "crime",
    ]
    assert len(constants.COMBAT_ACTIONS) == 7
    assert constants.COMBAT_ACTIONS == [
        "attack", "skill", "magic", "item", "observe", "escape", "defend",
    ]
    assert constants.CONDITION_OPERATORS == (
        "EQ", "NE", "GT", "LT", "GTE", "LTE", "EXISTS", "MISSING",
    )


def test_validate_condition_ok():
    validate_condition({"kind": "flag", "name": "x", "operator": "EQ", "value": True}, "p")
    validate_condition({"kind": "level", "operator": "GTE", "value": 3}, "p")
    validate_condition({"kind": "flag", "name": "x"}, "p")


def test_validate_condition_unknown_operator():
    with pytest.raises(SchemaError):
        validate_condition({"kind": "flag", "name": "x", "operator": "FOO"}, "p")
