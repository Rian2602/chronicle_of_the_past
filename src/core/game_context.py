import os

from src.core.constants import FACTIONS
from src.models.player import Player
from src.utils.json_loader import load_dir, load_json


class GameContext:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.classes = self._load_dir("classes")
        self.enemies = self._load_dir("enemies")
        self.items = self._load_dir("items")
        self.skills = self._load_dir("skills")
        self.maps = self._load_dir("maps")
        self.npc = self._load_dir("npc")
        self.quests = self._load_dir("quests")
        self.dialogues = self._load_dir("dialogues")
        self.factions = self._load_dir("factions")
        self.events = self._load_file_list("events/events.json")
        self.memories = self._load_file_list("story/memories.json")

    def _load_dir(self, name):
        return load_dir(os.path.join(self.data_dir, name))

    def _load_file_list(self, relpath):
        path = os.path.join(self.data_dir, relpath)
        if not os.path.isfile(path):
            return []
        data = load_json(path)
        return list(data)

    def create_player(self, name, class_id):
        class_data = self.classes[class_id]
        base_stats = dict(class_data["base_stats"])
        reputation = {faction: 0 for faction in FACTIONS}
        return Player(
            name=name,
            class_id=class_id,
            hp=base_stats["hp"],
            mp=base_stats["mp"],
            base_stats=base_stats,
            attribute_bonuses={},
            reputation=reputation,
            learned_skills=list(class_data["starting_skills"]),
        )
