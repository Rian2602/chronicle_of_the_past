import os
from typing import Any

from src.core.constants import FACTIONS
from src.models.player import Player
from src.utils.json_loader import load_dir, load_json


class GameContext:
    """Memuat seluruh konten game (kelas, peta, NPC, quest, dll) dari disk."""

    def __init__(self, data_dir: str = "data"):
        self.data_dir: str = data_dir
        self.classes: dict[str, Any] = self._load_dir("classes")
        self.enemies: dict[str, Any] = self._load_dir("enemies")
        self.items: dict[str, Any] = self._load_dir("items")
        self.skills: dict[str, Any] = self._load_dir("skills")
        self.maps: dict[str, Any] = self._load_dir("maps")
        self.npc: dict[str, Any] = self._load_dir("npc")
        self.quests: dict[str, Any] = self._load_dir("quests")
        self.dialogues: dict[str, Any] = self._load_dir("dialogues")
        self.factions: dict[str, Any] = self._load_dir("factions")
        self.events: list[str] = self._load_file_list("events/events.json")
        self.memories: list[str] = self._load_file_list("story/memories.json")
        self.scenes: list[dict[str, Any]] = self._load_file_list(
            "story/scenes.json"
        )

    def _load_dir(self, name: str) -> dict[str, Any]:
        """Load all JSON files from a directory."""
        return load_dir(os.path.join(self.data_dir, name))

    def _load_file_list(self, relpath: str) -> list[str]:
        """Load a list of file paths from a JSON file."""
        path = os.path.join(self.data_dir, relpath)
        if not os.path.isfile(path):
            return []
        data = load_json(path)
        return list(data) if isinstance(data, list) else []

    def create_player(self, name: str, class_id: str) -> Player:
        """
        Create a new player with the specified name and class.

        Args:
            name: Player's name (must be non-empty)
            class_id: ID of the class to use

        Returns:
            New Player instance

        Raises:
            ValueError: If class_id is not found in loaded classes
                or name is empty
            KeyError: If class data is missing required fields
        """
        # Validate name
        if not name or not name.strip():
            raise ValueError("Player name cannot be empty")
        name = name.strip()

        if class_id not in self.classes:
            available_classes = (
                ", ".join(self.classes.keys()) if self.classes else "none"
            )
            raise ValueError(
                f"Class '{class_id}' not found. "
                f"Available classes: {available_classes}"
            )

        class_data = self.classes[class_id]

        # Validate required fields
        if "base_stats" not in class_data:
            raise KeyError(f"Class '{class_id}' is missing 'base_stats' field")
        if "starting_skills" not in class_data:
            raise KeyError(
                f"Class '{class_id}' is missing 'starting_skills' field"
            )

        base_stats = dict(class_data["base_stats"])

        # Validate base_stats has all required stat fields
        from src.core.constants import STATS

        required_stats = list(
            STATS
        )  # ['hp', 'mp', 'attack', 'defense', 'agility', 'intelligence']
        for stat in required_stats:
            if stat not in base_stats:
                raise KeyError(
                    f"Class '{class_id}' base_stats is missing "
                    f"required field '{stat}'"
                )

        reputation = {faction: 0 for faction in FACTIONS}

        # Safely handle starting_skills
        starting_skills = class_data["starting_skills"]
        if not isinstance(starting_skills, list):
            starting_skills = [starting_skills] if starting_skills else []

        # Get xp_bonus from class data (default to 1.0)
        xp_bonus = float(class_data.get("xp_bonus", 1.0))

        return Player(
            name=name,
            class_id=class_id,
            hp=base_stats["hp"],
            mp=base_stats["mp"],
            base_stats=base_stats,
            attribute_bonuses={},
            reputation=reputation,
            learned_skills=list(starting_skills),
            xp_bonus=xp_bonus,
        )
