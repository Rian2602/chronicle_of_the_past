from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.models.enemy import Enemy
    from src.models.item import Item
    from src.models.map import Map
    from src.models.player import Player


class GameState:
    """Semua data permainan yang bisa disimpan/dimuat."""

    def __init__(self):
        self.player: Player | None = None
        self.world: dict[str, Map] = {}
        self.flags: dict[str, bool | int | str] = {}
        self.time: str = "morning"
        self.day: int = 1
        self.current_map: Map | None = None
        self.enemies: dict[str, Enemy] = {}
        self.items: dict[str, Item] = {}
        self.quests: dict = {}
        self.memories: list = []
        self.scenes: list = []
        self.events: list = []
        self.rng_seed: int | None = None
        self.combat_data: dict | None = None
        self.kill_counts: dict[str, int] = {}
        self.counters: dict[str, int] = {}
