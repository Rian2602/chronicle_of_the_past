import json
import os


class ContentError(Exception):
    pass


def load_json(path):
    """Muat satu file JSON.

    Raises:
        ContentError: Bila file tidak bisa dibaca atau bukan JSON valid.
    """
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        raise ContentError(f"Gagal memuat {path}: {e}") from e


def load_dir(dirpath):
    """Muat semua file JSON dalam direktori, dikunci oleh field id.

    Returns:
        Dict {id: data} untuk setiap file .json yang valid.
    """
    result = {}
    if not os.path.isdir(dirpath):
        return result
    for name in sorted(os.listdir(dirpath)):
        if name.endswith(".json"):
            data = load_json(os.path.join(dirpath, name))
            result[data["id"]] = data
    return result
