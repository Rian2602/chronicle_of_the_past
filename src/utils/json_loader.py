import json, os

class ContentError(Exception):
    pass

def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        raise ContentError(f"Gagal memuat {path}: {e}") from e

def load_dir(dirpath):
    result = {}
    if not os.path.isdir(dirpath):
        return result
    for name in sorted(os.listdir(dirpath)):
        if name.endswith(".json"):
            data = load_json(os.path.join(dirpath, name))
            result[data["id"]] = data
    return result
