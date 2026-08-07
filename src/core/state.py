"""State permainan kanonik dan serialisasinya (GDD §19.2, §8, §9)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.engine.cultivation import load_tiers, restore_tier
from src.models.party import load_companion
from src.models.player import Player
from src.systems.faction import FACTIONS, add_reputation

SCHEMA_VERSION = 2
DEFAULT_LOCATION = "village_emberfall"


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
    # id rekan yang aktif bertarung (max 3 slot, GDD §20.1).
    party_active: list[str] = field(default_factory=list)
    inventory: dict[str, Any] = field(
        default_factory=lambda: {"items": {}, "equipped": {}, "artifacts": {}}
    )
    quests: QuestProgress = field(default_factory=QuestProgress)
    flags: dict[str, bool] = field(default_factory=dict)
    kills: dict[str, int] = field(default_factory=dict)
    reputation: dict[str, int] = field(
        default_factory=lambda: {faction: 0 for faction in FACTIONS}
    )
    memories: list[str] = field(default_factory=list)
    map_unlocks: list[str] = field(default_factory=list)
    location: str = DEFAULT_LOCATION
    time: GameTime = field(default_factory=GameTime)
    settings: dict[str, Any] = field(default_factory=dict)
    # Stok toko yang terjual: shop_id -> item_id -> jumlah (GDD §19.2).
    # Sisa stok = count di data/shops dikurangi angka ini; kosong = penuh.
    shop_sold: dict[str, dict[str, int]] = field(default_factory=dict)
    # Buff combat dari item (GDD §7): stat -> nilai; diterapkan ke
    # combatant protagonis saat battle dimulai, lalu dikonsumsi.
    buffs: dict[str, int] = field(default_factory=dict)
    # Formasi aktif (GDD §7, §18.2): id formasi yang terpasang, atau None.
    formation_active: str | None = None
    # Poin ending untuk Pondasi Fase 4: path -> poin.
    ending_points: dict[str, int] = field(
        default_factory=lambda: {"defy": 0, "seal": 0, "reconcile": 0}
    )
    # Ritual persiapan melawan entitas kuno selesai (GDD §21.3).
    # ritual_ready kini hanya flag — field dihapus P0.1 (2026-08-07).

    def __post_init__(self) -> None:
        """Normalisasi reputasi 5 faksi (§8), ending_points, dan hp/qi konkret.

        Invariant: state.reputation selalu memuat kelima faksi, dan
        state.player.hp/qi selalu angka (save lama tanpa field -> penuh).
        """
        self.reputation = {
            faction: int(self.reputation.get(faction, 0))
            for faction in FACTIONS
        }
        ending_defaults = {"defy": 0, "seal": 0, "reconcile": 0}
        for ep_path, ep_val in ending_defaults.items():
            self.ending_points.setdefault(ep_path, ep_val)
        if self.player.hp is None:
            self.player.hp = self.player.hp_max
        if self.player.qi is None:
            self.player.qi = self.player.qi_max
        self.player.hp = min(self.player.hp, self.player.hp_max)
        self.player.qi = min(self.player.qi, self.player.qi_max)

    def add_reputation(self, faction: str, delta: int) -> None:
        """Ubah reputasi faksi — delegasi ke sistem faksi (GDD §8).

        Args:
            faction: ID faksi kanonik (court/holy_order/rebels/guilds/
                ancient_order).
            delta: Perubahan nilai (bisa negatif).

        Raises:
            ValueError: Jika faksi tidak dikenal.
        """
        add_reputation(self, faction, delta)

    def to_dict(self) -> dict[str, Any]:
        """Serialize state ke dict save lengkap (§19.2)."""
        return {
            "schema_version": SCHEMA_VERSION,
            "player": self.player.to_dict(),
            "party": [dict(member) for member in self.party],
            "party_active": list(self.party_active),
            "inventory": {
                key: dict(value) if isinstance(value, dict) else value
                for key, value in self.inventory.items()
            },
            "quests": self.quests.to_dict(),
            "flags": dict(self.flags),
            "kills": dict(self.kills),
            "reputation": dict(self.reputation),
            "memories": list(self.memories),
            "map_unlocks": list(self.map_unlocks),
            "location": self.location,
            "time": self.time.to_dict(),
            "settings": dict(self.settings),
            "shop_sold": {
                shop_id: dict(sold) for shop_id, sold in self.shop_sold.items()
            },
            "buffs": dict(self.buffs),
            "formation_active": self.formation_active,
            "ending_points": dict(self.ending_points),
            # ritual_ready hanya di flags (P0.1) — serialisasi lewat self.flags.
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
        ending_points = data.get(
            "ending_points", {"defy": 0, "seal": 0, "reconcile": 0}
        )
        if not isinstance(ending_points, dict):
            raise ValueError("ending_points harus berupa objek")
        if not all(isinstance(v, int) for v in ending_points.values()):
            raise ValueError("nilai ending_points harus integer")
        shop_sold = data.get("shop_sold", {})
        if not isinstance(shop_sold, dict):
            raise ValueError("shop_sold harus berupa objek")
        normalized_sold: dict[str, dict[str, int]] = {}
        for shop_id, sold in shop_sold.items():
            if not isinstance(shop_id, str) or not isinstance(sold, dict):
                raise ValueError("shop_sold: id toko/terjual tidak valid")
            if not all(
                isinstance(item_id, str) and isinstance(count, int)
                for item_id, count in sold.items()
            ):
                raise ValueError("shop_sold: stok terjual harus item -> int")
            normalized_sold[shop_id] = dict(sold)
        # Backfill P0.1: ritual_ready field lama → pindah ke flag.
        flags = dict(data.get("flags", {}))
        if data.get("ritual_ready"):
            flags["ritual_ready"] = True
        # Backfill inventory (BUG-1): save parsial tanpa equipped/artifacts
        # tidak boleh memicu KeyError di handler equip/artifact.
        inventory_raw = data.get("inventory", {})
        if not isinstance(inventory_raw, dict):
            raise ValueError("inventory harus berupa objek")
        inventory = {"items": {}, "equipped": {}, "artifacts": {}}
        for key, value in inventory_raw.items():
            inventory[key] = dict(value) if isinstance(value, dict) else value
        # Backfill party (BUG-13): member dengan stats kosong ATAU parsial
        # (save korup/legacy) dilengkapi per-kunci dari data/companions agar
        # battle tidak crash (KeyError agility saat musuh menyerang ally).
        # Nilai stats yang sudah ada dipertahankan. Id tak dikenal
        # dibiarkan apa adanya — divalidasi keras di lapisan save (BUG-5).
        party: list[dict[str, Any]] = []
        for member in data.get("party", []):
            raw_member = dict(member)
            stats = raw_member.get("stats")
            if not isinstance(stats, dict):
                stats = {}
            if stats:
                try:
                    companion = load_companion(raw_member["id"])
                    for key, value in companion.stats.items():
                        stats.setdefault(key, value)
                except (ValueError, KeyError):
                    pass
            else:
                try:
                    companion = load_companion(raw_member["id"])
                    stats = dict(companion.stats)
                except (ValueError, KeyError):
                    pass
            raw_member["stats"] = stats
            party.append(raw_member)
        return cls(
            player=player,
            party=party,
            party_active=list(data.get("party_active", [])),
            inventory=inventory,
            quests=QuestProgress.from_dict(data.get("quests", {})),
            flags=flags,
            kills=dict(data.get("kills", {})),
            reputation=reputation,
            memories=list(data.get("memories", [])),
            map_unlocks=list(data.get("map_unlocks", [])),
            location=data.get("location", DEFAULT_LOCATION),
            time=GameTime.from_dict(data.get("time", {})),
            settings=dict(data.get("settings", {})),
            shop_sold=normalized_sold,
            buffs=dict(data.get("buffs", {})),
            formation_active=data.get("formation_active"),
            ending_points=dict(ending_points),
        )
