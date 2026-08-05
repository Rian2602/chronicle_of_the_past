"""
Data Loader dengan Caching untuk performa O(1).

Module ini menyediakan singleton DataLoader yang mem-cache semua data
game (quests, items, enemies, maps, npcs, skills, dll) saat inisialisasi.
"""

import json
from pathlib import Path
from typing import Any, ClassVar, Optional


class DataLoader:
    """Singleton loader untuk semua data game dengan caching."""

    _instance: Optional["DataLoader"] = None
    _cache: ClassVar[dict[str, dict[str, Any]]] = {}
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.base_dir = Path(__file__).parent.parent
            self._load_all_data()
            self._initialized = True

    def _load_all_data(self):
        """Load semua data dari folder data/ ke dalam cache."""
        data_dir = self.base_dir / "data"

        # Load setiap kategori data
        categories = [
            "quests",
            "items",
            "enemies",
            "maps",
            "npc",
            "skills",
            "dialogues",
            "factions",
            "classes",
            "story",
        ]

        for category in categories:
            cat_dir = data_dir / category
            if cat_dir.exists():
                self._cache[category] = {}
                for file_path in cat_dir.glob("*.json"):
                    try:
                        with open(file_path, encoding="utf-8") as f:
                            data = json.load(f)
                            # Handle list vs dict format
                            if isinstance(data, list):
                                for item in data:
                                    if "id" in item:
                                        self._cache[category][item["id"]] = item
                            elif isinstance(data, dict):
                                key = data.get("id", file_path.stem)
                                self._cache[category][key] = data
                    except Exception as e:
                        print(f"Warning: Failed to load {file_path}: {e}")

    def get(self, category: str, item_id: str) -> dict[str, Any] | None:
        """
        Ambil data item berdasarkan kategori dan ID.

        Args:
            category: Kategori data (quests, items, enemies, dll)
            item_id: ID item yang dicari

        Returns:
            Data item atau None jika tidak ditemukan
        """
        return self._cache.get(category, {}).get(item_id)

    def get_all(self, category: str) -> dict[str, Any]:
        """
        Ambil semua data dalam kategori tertentu.

        Args:
            category: Kategori data

        Returns:
            Dictionary semua item dalam kategori tersebut
        """
        return self._cache.get(category, {})

    def exists(self, category: str, item_id: str) -> bool:
        """Cek apakah item ada dalam cache."""
        return item_id in self._cache.get(category, {})

    def clear_cache(self):
        """Hapus semua cache dan reload data."""
        self._cache.clear()
        self._initialized = False
        self.__init__()

    def get_quest(self, quest_id: str) -> dict[str, Any] | None:
        """Helper: ambil data quest by ID."""
        return self.get("quests", quest_id)

    def get_item(self, item_id: str) -> dict[str, Any] | None:
        """Helper: ambil data item by ID."""
        return self.get("items", item_id)

    def get_enemy(self, enemy_id: str) -> dict[str, Any] | None:
        """Helper: ambil data enemy by ID."""
        return self.get("enemies", enemy_id)

    def get_map(self, map_id: str) -> dict[str, Any] | None:
        """Helper: ambil data map by ID."""
        return self.get("maps", map_id)

    def get_npc(self, npc_id: str) -> dict[str, Any] | None:
        """Helper: ambil data NPC by ID."""
        return self.get("npc", npc_id)


# Singleton instance global
_data_loader: DataLoader | None = None


def get_data_loader() -> DataLoader:
    """Dapatkan instance DataLoader singleton."""
    global _data_loader
    if _data_loader is None:
        _data_loader = DataLoader()
    return _data_loader


def get_quest(quest_id: str) -> dict[str, Any] | None:
    """Helper function: ambil quest by ID."""
    return get_data_loader().get_quest(quest_id)


def get_item(item_id: str) -> dict[str, Any] | None:
    """Helper function: ambil item by ID."""
    return get_data_loader().get_item(item_id)


def get_enemy(enemy_id: str) -> dict[str, Any] | None:
    """Helper function: ambil enemy by ID."""
    return get_data_loader().get_enemy(enemy_id)


def get_map(map_id: str) -> dict[str, Any] | None:
    """Helper function: ambil map by ID."""
    return get_data_loader().get_map(map_id)


def get_npc(npc_id: str) -> dict[str, Any] | None:
    """Helper function: ambil NPC by ID."""
    return get_data_loader().get_npc(npc_id)
