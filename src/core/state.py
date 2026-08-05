"""State permainan kanonik dan serialisasinya (GDD §19.2, §8, §9)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.engine.cultivation import load_tiers, restore_tier
from src.models.player import Player

SCHEMA_VERSION = 1
DEFAULT_LOCATION = "village_emberfall"
FACTIONS = ("court", "holy_order", "rebels", "guilds", "ancient_order")


@dataclass
class GameTime:
    """Waktu game (hari/jam) yang disimpan di save (§19.2)."""

    day: int = 1
    hour: int = 8

    def __post_init__(self) -> None:
        """Validasi rentang waktu: hari >= 1, jam 0-23."""
        if self.day < 1:
            raise ValueError("day harus >= 1")
        if not 0 <= self.hour <= 23:
            raise ValueError("hour harus 0-23")

    def to_dict(self) -> dict[str, int]:
        """Serialize ke dict waktu (§19.2)."""
        return {"day": self.day, "hour": self.hour}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GameTime:
        """Buat GameTime dari dict waktu (default saat kosong)."""
        if not isinstance(data, dict):
            raise ValueError("waktu harus berupa objek")
        return cls(day=data.get("day", 1), hour=data.get("hour", 8))


@dataclass
class QuestProgress:
    """Progres quest: id yang dimulai/selesai/gagal (§19.2)."""

    started: list[str] = field(default_factory=list)
    done: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, list[str]]:
        """Serialize ke dict progres quest (§19.2)."""
        return {
            "started": list(self.started),
            "done": list(self.done),
            "failed": list(self.failed),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> QuestProgress:
        """Buat QuestProgress dari dict; daftar wajib list of string.

        Mencegah nilai string diam-diam menjadi daftar karakter.
        """
        if not isinstance(data, dict):
            raise ValueError("progres quest harus berupa objek")
        started = data.get("started", [])
        done = data.get("done", [])
        failed = data.get("failed", [])
        groups = (started, done, failed)
        if not all(isinstance(group, list) for group in groups):
            raise ValueError("daftar quest harus berupa list")
        if not all(isinstance(item, str) for group in groups for item in group):
            raise ValueError("id quest harus string")
        return cls(
            started=list(started),
            done=list(done),
            failed=list(failed),
        )


@dataclass
class GameState:
    """State permainan kanonik (GDD §19.2) — sumber kebenaran state."""

    player: Player
    party: list[dict[str, Any]] = field(default_factory=list)
    inventory: dict[str, Any] = field(
        default_factory=lambda: {"items": {}, "equipped": {}, "artifacts": {}}
    )
    quests: QuestProgress = field(default_factory=QuestProgress)
    flags: dict[str, bool] = field(default_factory=dict)
    reputation: dict[str, int] = field(
        default_factory=lambda: {faction: 0 for faction in FACTIONS}
    )
    memories: list[str] = field(default_factory=list)
    map_unlocks: list[str] = field(default_factory=list)
    location: str = DEFAULT_LOCATION
    time: GameTime = field(default_factory=GameTime)
    settings: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Normalisasi reputasi ke 5 faksi kanonik (GDD §8).

        Invariant: state.reputation selalu memuat kelima faksi; dipakai
        semua sistem (quest, ending) tanpa cek kehadiran kunci.
        """
        self.reputation = {
            faction: int(self.reputation.get(faction, 0))
            for faction in FACTIONS
        }

    def to_dict(self) -> dict[str, Any]:
        """Serialize state ke dict save lengkap (§19.2)."""
        return {
            "schema_version": SCHEMA_VERSION,
            "player": self.player.to_dict(),
            "party": [dict(member) for member in self.party],
            "inventory": {
                key: dict(value) if isinstance(value, dict) else value
                for key, value in self.inventory.items()
            },
            "quests": self.quests.to_dict(),
            "flags": dict(self.flags),
            "reputation": dict(self.reputation),
            "memories": list(self.memories),
            "map_unlocks": list(self.map_unlocks),
            "location": self.location,
            "time": self.time.to_dict(),
            "settings": dict(self.settings),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GameState:
        """Buat state dari dict save; kunci ekstra ditoleransi.

        Kunci wajib: schema_version ditangani lapisan save; player wajib
        ada. tier_order/tier_bonus direkonstruksi dari data/cultivation.
        """
        if not isinstance(data, dict):
            raise ValueError("save harus berupa objek JSON")
        player_data = data.get("player")
        if not isinstance(player_data, dict) or not player_data.get("name"):
            raise ValueError("field player tidak valid atau nama kosong")
        player = Player.from_dict(player_data)
        restore_tier(player, load_tiers())
        reputation = data.get("reputation", {})
        if not isinstance(reputation, dict):
            raise ValueError("reputasi harus berupa objek")
        return cls(
            player=player,
            party=[dict(member) for member in data.get("party", [])],
            inventory=dict(
                data.get(
                    "inventory",
                    {"items": {}, "equipped": {}, "artifacts": {}},
                )
            ),
            quests=QuestProgress.from_dict(data.get("quests", {})),
            flags=dict(data.get("flags", {})),
            reputation=reputation,
            memories=list(data.get("memories", [])),
            map_unlocks=list(data.get("map_unlocks", [])),
            location=data.get("location", DEFAULT_LOCATION),
            time=GameTime.from_dict(data.get("time", {})),
            settings=dict(data.get("settings", {})),
        )
