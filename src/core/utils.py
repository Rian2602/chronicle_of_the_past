"""Utility functions for core data structures and loading."""

import json
from pathlib import Path
from typing import Any


def load_json_dir(data_dir: Path, model_cls: type | None = None) -> Any:
    """Load JSON files from a directory into dict or model list.

    Args:
        data_dir: Directory containing JSON files.
        model_cls: Optional model class to instantiate for each JSON file.

    Returns:
        A list of model instances if model_cls is provided, else a dict mapping
        IDs to JSON raw data dicts.
    """
    items_dict = {}
    items_list = []

    for path in sorted(data_dir.glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        if model_cls:
            items_list.append(model_cls(**raw))
        else:
            items_dict[raw["id"]] = raw

    return items_list if model_cls else items_dict
