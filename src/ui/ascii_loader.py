import os

from src.utils.json_loader import ContentError


def load(name, assets_dir="assets/ascii"):
    """Baca file ASCII art dari folder assets.

    Raises:
        ContentError: Bila file tidak ditemukan.
    """
    path = os.path.join(assets_dir, f"{name}.txt")
    if not os.path.isfile(path):
        raise ContentError(f"Ascii art tidak ditemukan: {path}")
    with open(path, encoding="utf-8") as f:
        return f.read()
