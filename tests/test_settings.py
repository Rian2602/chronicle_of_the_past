import json

import pytest

from src.core import settings


def test_load_missing_settings_uses_defaults(tmp_path):
    loaded = settings.load_settings(tmp_path / "settings.json")
    assert loaded == settings.Settings()


def test_settings_roundtrip(tmp_path):
    path = tmp_path / "settings.json"
    expected = settings.Settings(render_mode="ascii", animation_mode="fast")
    settings.save_settings(expected, path)
    assert settings.load_settings(path) == expected


@pytest.mark.parametrize(
    "contents", ["{not json", "[]", '{"render_mode": "invalid"}']
)
def test_invalid_settings_raise_clear_error(tmp_path, contents):
    path = tmp_path / "settings.json"
    path.write_text(contents, encoding="utf-8")
    with pytest.raises(settings.SettingsError):
        settings.load_settings(path)


def test_settings_json_has_only_public_values(tmp_path):
    path = tmp_path / "settings.json"
    settings.save_settings(settings.Settings(), path)
    assert json.loads(path.read_text(encoding="utf-8")) == {
        "render_mode": "auto",
        "animation_mode": "normal",
    }
