"""Konfigurasi global untuk launcher game."""

import json
import os
from dataclasses import dataclass

SETTINGS_PATH = os.path.join("saves", "settings.json")
RENDER_MODES = ("auto", "unicode", "ascii")
ANIMATION_MODES = ("normal", "fast", "off")


class SettingsError(Exception):
    pass


@dataclass
class Settings:
    render_mode: str = "auto"
    animation_mode: str = "normal"

    def __post_init__(self):
        """Validasi nilai mode; tolak nilai yang tidak didukung."""
        if self.render_mode not in RENDER_MODES:
            raise ValueError(
                f"Mode tampilan tidak didukung: {self.render_mode}"
            )
        if self.animation_mode not in ANIMATION_MODES:
            raise ValueError(
                f"Mode animasi tidak didukung: {self.animation_mode}"
            )


def load_settings(path=SETTINGS_PATH):
    """Muat konfigurasi; file yang belum ada menggunakan nilai bawaan."""
    if not os.path.exists(path):
        return Settings()
    try:
        with open(path, encoding="utf-8") as file:
            data = json.load(file)
        if not isinstance(data, dict):
            raise ValueError("format harus berupa objek JSON")
        return Settings(
            render_mode=data.get("render_mode", "auto"),
            animation_mode=data.get("animation_mode", "normal"),
        )
    except (OSError, json.JSONDecodeError, ValueError) as error:
        raise SettingsError(f"Konfigurasi tidak valid: {error}") from error


def save_settings(settings, path=SETTINGS_PATH):
    """Simpan konfigurasi yang telah tervalidasi."""
    try:
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(path, "w", encoding="utf-8") as file:
            json.dump(
                {
                    "render_mode": settings.render_mode,
                    "animation_mode": settings.animation_mode,
                },
                file,
                indent=2,
                ensure_ascii=False,
            )
    except OSError as error:
        raise SettingsError(f"Gagal menyimpan konfigurasi: {error}") from error


def next_choice(value, choices):
    """Item berikutnya secara siklik dalam daftar pilihan."""
    return choices[(choices.index(value) + 1) % len(choices)]
