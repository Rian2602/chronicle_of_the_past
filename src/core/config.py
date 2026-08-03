import os

from src.utils.json_loader import load_json


def load_config(data_dir="data"):
    path = os.path.join(data_dir, "config", "config.json")
    return load_json(path)
