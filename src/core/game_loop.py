"""Alur permainan utama (GDD §18, §19.1, §20.4, §23).

GameSession memisahkan logika murni (diuji penuh) dari UI Textual:
App hanya memanggil metode ini dan menampilkan hasilnya.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.core.input import Command
from src.core.save import (
    SAVE_DIR,
    SLOTS,
    VALID_SLOTS,
    autosave_save,
    load_game,
    save_game,
    slot_exists,
)
from src.core.state import GameState
from src.engine.combat import Battle, load_enemies, load_techniques
from src.engine.cultivation import (
    attempt_breakthrough,
    load_tiers,
    next_tier,
)
from src.engine.dialog import (
    apply_actions,
    find_dialog,
    get_node,
    load_dialogs,
    visible_choices,
)
from src.engine.event import (
    EventResult,
    apply_action,
    load_events,
    process_events,
)
from src.engine.items import load_items
from src.engine.maps import load_maps
from src.engine.quest import (
    active_quests,
    advance_quest,
    check_objective,
    load_quests,
    objective_label,
)
from src.engine.shop import load_shops, sell_price
from src.engine.story import load_memories
from src.models.combatant import (
    Combatant,
    combatant_from_companion,
    combatant_from_enemy,
    combatant_from_player,
)
from src.models.enemy import Enemy
from src.models.party import Companion
from src.models.player import Player

CULTIVATE_INSIGHT = 10
CULTIVATE_HOURS = 3
REST_HOUR = 8
START_LOCATION = "village_emberfall"
NPC_DIR = Path(__file__).resolve().parents[2] / "data" / "npc"
UNAVAILABLE = "Belum tersedia (Fase 1)."
# Bond XP per kemenangan untuk tiap rekan yang masih hidup (GDD §20.3).
# ponytail: nilai keseimbangan sementara (§24.2) — disetel saat playtest.
BOND_XP_VICTORY = 10

# Warna semantik item di inventory (GDD §14.2): material, resep, alat.
ITEM_TYPE_COLORS = {"material": "cyan", "recipe": "violet", "tool": "gold3"}

# Perintah yang sistemnya sudah ada di MVP; sisanya menjawab "belum
# tersedia" (kebijakan rencana: bukan error, bukan implementasi setengah).
AVAILABLE = {
    "help",
    "status",
    "map",
    "inventory",
    "quests",
    "memories",
    "party",
    "go",
    "look",
    "talk",
    "cultivate",
    "breakthrough",
    "rest",
    "save",
    "load",
    "quit",
    "choose",
    "use",
    "shop",
    "buy",
    "sell",
    "refine",
    "swap",
}


def make_bar(current: int, total: int, width: int = 20) -> str:
    """Bar ASCII proporsional (█ terisi, ░ kosong).

    Args:
        current: Nilai saat ini (>= 0).
        total: Nilai maksimum; 0 menghasilkan bar kosong.
        width: Lebar bar dalam karakter.

    Returns:
        String bar, panjang tepat ``width``.
    """
    if total <= 0:
        return "░" * width
    filled = max(0, min(width, round(current / total * width)))
    return "█" * filled + "░" * (width - filled)


@dataclass
class BattleFrame:
    """Kapsul status pertarungan untuk UI (GDD §6)."""

    log: list[str]
    over: bool
    victory: bool | None
    escaped: bool
    player_turn: bool
    enemies: list[dict[str, Any]]
    error: str | None = None
    active_ally_name: str | None = None


class GameSession:
    """Satu sesi permainan: state, perintah dunia, dan pertarungan."""

    def __init__(self, save_dir: Path = SAVE_DIR, *, rng: Any = None) -> None:
        """Buat sesi; rng bisa disuntikkan untuk test deterministik."""
        self.save_dir = save_dir
        self._rng = rng if rng is not None else random
        self.state: GameState | None = None
        self.battle: Battle | None = None
        self._ally: Combatant | None = None
        self._enemy: Enemy | None = None
        # id rekan -> combatan, untuk tulis balik hp/qi pasca battle.
        self._ally_map: dict[str, Combatant] = {}
        self.quit_requested = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def new_game(self, name: str) -> None:
        """Mulai permainan baru di Desa Emberfall (GDD §9)."""
        self.state = GameState(player=Player(name=name.strip() or "Tanpa Nama"))
        # MVP: hutan terbuka sejak awal agar pertarungan Fase 0 tercapai;
        # gating ketat via event engine (unlock_map) menyusul di Fase 1.
        self.state.flags["map_ashfall_forest_unlocked"] = True
        self.battle = None
        self.quit_requested = False

    def load(self, slot: str) -> list[str]:
        """Muat save; kembalikan pesan hasil."""
        try:
            self.state = load_game(slot, self.save_dir)
        except Exception as exc:
            return [f"Tidak bisa memuat {slot}: {exc}"]
        self.battle = None
        return [f"Save {slot} dimuat. Selamat datang kembali."]

    def save(self, slot: str) -> list[str]:
        """Simpan ke slot; kembalikan pesan hasil."""
        if self.state is None:
            return ["Belum ada permainan untuk disimpan."]
        try:
            save_game(self.state, slot, self.save_dir)
        except Exception as exc:
            return [f"Gagal menyimpan {slot}: {exc}"]
        return [f"Tersimpan di {slot}."]

    # ------------------------------------------------------------------
    # Dispatch perintah dunia
    # ------------------------------------------------------------------
    def dispatch(self, command: Command) -> list[str]:
        """Kirim perintah dunia; kembalikan baris pesan untuk UI."""
        if command.name not in AVAILABLE:
            return [UNAVAILABLE]
        # quit adalah perintah global (§18.1): tetap jalan saat bertarung.
        if self.in_battle and command.name != "quit":
            return ["Kamu sedang bertarung! (attack/defend/observe/escape)"]
        # load harus jalan meski belum ada permainan aktif.
        if self.state is None and command.name != "load":
            return ["Belum ada permainan. Mulai baru atau muat save."]
        handler = getattr(self, f"_cmd_{command.name}")
        return handler(command)

    def _cmd_help(self, _command: Command) -> list[str]:
        return [
            "Perintah tersedia:",
            "  help status map inventory quests memories party",
            "  go <lokasi> look talk <nama> cultivate breakthrough rest",
            "  shop buy <item> [jumlah] sell <item> [jumlah]",
            "  use <item> refine <item>",
            "  save [1-3] load [1-3] quit",
            "  load autosave (kembali ke simpan otomatis terakhir)",
            "Saat bertarung: attack, defend, technique <nama>,",
            "  observe, escape (alias Indonesia juga berlaku).",
        ]

    def status_lines(self) -> list[str]:
        """Baris status pemain; dipakai perintah status & HUD UI.

        Metode publik agar HUD tidak lewat dispatch (yang memblokir
        perintah dunia saat battle) — stat tetap terlihat di HUD saat
        bertarung.
        """
        player = self.state.player
        tier = next((t for t in load_tiers() if t.id == player.tier_id), None)
        tier_name = tier.name if tier else "Mortal (belum bertingkat)"
        injury = ""
        if player.is_injured:
            injury = f" | CEDERA ({player.injury_days_remaining} hari)"
        # Selama battle, HP/qi live ada di combatan (_ally) — state.player
        # baru disinkronkan saat _finish_battle; tanpa ini HUD menipu
        # pemain yang sedang terluka (bar tetap penuh).
        hp = self._ally.hp if self._ally is not None else player.hp
        qi = self._ally.qi if self._ally is not None else player.qi
        hp_bar = make_bar(hp, player.hp_max, 12)
        qi_bar = make_bar(qi, player.qi_max, 12)
        return [
            f"[bold gold3]{player.name}[/] — {tier_name}",
            f"Lokasi: {self.state.location} | "
            f"Hari {self.state.time.day}, jam {self.state.time.hour:02d}",
            f"HP [red]{hp_bar}[/] {hp}/{player.hp_max} | "
            f"Qi [cyan]{qi_bar}[/] {qi}/{player.qi_max}",
            f"Insight [violet]{player.insight}[/] | "
            f"Gold [gold3]{player.gold}[/]"
            f" | Meridian {player.meridian_buka}/8{injury}",
        ]

    def _cmd_status(self, _command: Command) -> list[str]:
        return self.status_lines()

    def _cmd_map(self, _command: Command) -> list[str]:
        unlocked = [START_LOCATION]
        for flag, value in self.state.flags.items():
            if flag.startswith("map_") and flag.endswith("_unlocked") and value:
                unlocked.append(flag[len("map_") : -len("_unlocked")])
        lines = ["Lokasi terbuka:"]
        for location in unlocked:
            marker = " <- di sini" if location == self.state.location else ""
            lines.append(f"  {location}{marker}")
        return lines

    def _cmd_inventory(self, _command: Command) -> list[str]:
        """Tampilkan isi tas dengan warna semantik per tipe (GDD §14.2).

        Warna: material cyan, resep violet, alat (tool) gold3; item lain
        tampil polos. Item tanpa data (save lama) memakai id mentah.
        """
        items = self.state.inventory.get("items", {})
        if not items:
            return ["Tasmu kosong."]
        names = load_items()
        lines = ["Isi tas:"]
        for item_id, count in sorted(items.items()):
            # ponytail: item tanpa data (save lama) -> id mentah; validator
            # §25.3 menjamin event->item ter-resolve.
            item = names.get(item_id, {})
            name = item.get("name", item_id)
            color = ITEM_TYPE_COLORS.get(item.get("type", ""), "")
            if color:
                lines.append(f"  [{color}]{name}[/] x{count}")
            else:
                lines.append(f"  {name} x{count}")
        return lines

    def _cmd_use(self, command: Command) -> list[str]:
        """Pakai item konsumabel di luar combat (GDD §18.2).

        Item divalidasi ke data/items sebelum dikonsumsi (item tak dikenal
        tidak boleh raib); bahan (type=material) ditolak — arahkan ke
        refine. Efek non-combat (heal_hp, restore_qi, add_insight,
        add_meridian) diterapkan segera. Efek combat-ready (buff_*) diparse
        tapi tidak dieksekusi.
        """
        if not command.args:
            return ["Pakai apa? Contoh: use <nama_item>."]
        item_id = command.args[0]
        items = self.state.inventory.get("items", {})
        if items.get(item_id, 0) <= 0:
            return [f"Kamu tidak punya {item_id} di tas."]
        catalog = load_items()
        item = catalog.get(item_id)
        if item is None:
            return [f"Item '{item_id}' tidak dikenal di data."]
        if item.get("type") == "material":
            return [
                f"{item['name']} adalah bahan — tidak bisa dipakai "
                "langsung. Racik dulu dengan refine."
            ]
        learned = (item.get("effect") or {}).get("learn_recipe")
        if learned and self.state.flags.get(f"recipe_{learned}_known"):
            return [f"Kamu sudah mempelajari resep {item['name']}."]
        items[item_id] -= 1
        if items[item_id] == 0:
            del items[item_id]
        lines = [f"Kamu memakai {item['name']}."]
        effect = item.get("effect")
        player = self.state.player
        if effect:
            learned = effect.get("learn_recipe")
            if learned:
                # Belajar resep: pengetahuan permanen di flags (GDD §7).
                self.state.flags[f"recipe_{learned}_known"] = True
                target = catalog.get(learned, {}).get("name", learned)
                lines.append(f"Kamu mempelajari resep {target}.")
            if effect.get("heal_hp"):
                player.hp = min(player.hp_max, player.hp + effect["heal_hp"])
                lines.append(f"HP pulih {effect['heal_hp']}.")
            if effect.get("restore_qi"):
                player.qi = min(player.qi_max, player.qi + effect["restore_qi"])
                lines.append(f"Qi pulih {effect['restore_qi']}.")
            if effect.get("add_insight"):
                player.add_insight(effect["add_insight"])
                lines.append(f"Insight +{effect['add_insight']}.")
            if effect.get("add_meridian"):
                player.meridian_buka = min(
                    8, player.meridian_buka + effect["add_meridian"]
                )
                lines.append(f"Meridian terbuka ({player.meridian_buka}/8).")
            # Efek combat-ready (buff_*/resist_*): catat ke state.buffs
            # (GDD §7); diterapkan ke combatant di _start_battle, lalu
            # dikonsumsi sekali pakai. buff_<stat> dinormalisasi jadi
            # <stat> (cocok dengan Combatant.stats); resist_<x> tetap
            # utuh — siap dibaca engine combat Fase 2 (GDD §17.2).
            for key, value in effect.items():
                if key.startswith("buff_"):
                    stat = key[len("buff_") :]
                    self.state.buffs[stat] = (
                        self.state.buffs.get(stat, 0) + value
                    )
                elif key.startswith("resist_"):
                    self.state.buffs[key] = self.state.buffs.get(key, 0) + value
            if any(
                key.startswith("buff_") or key.startswith("resist_")
                for key in effect
            ):
                lines.append("Efek combat aktif untuk pertarungan berikutnya.")
        lines += self._run_quests()
        lines += self._run_events()
        return lines

    def _shop_at_location(self) -> tuple[str, dict[str, Any]] | None:
        """Temukan (shop_id, data toko) di lokasi pemain saat ini.

        Toko dilampirkan ke NPC via field ``shop`` di data/npc; toko
        pertama yang NPC-nya berada di lokasi ini yang dipakai.
        """
        if self.state is None:
            return None
        # ponytail: rescan 11 file NPC tiap panggilan -> cache lokasi->shop
        # bila jumlah NPC > 50 (GDD §10: 10 NPC final per arc).
        shops = load_shops()
        for npc_path in sorted(NPC_DIR.glob("*.json")):
            npc = json.loads(npc_path.read_text(encoding="utf-8"))
            shop_id = npc.get("shop")
            if shop_id and npc.get("location") == self.state.location:
                shop = shops.get(shop_id)
                if shop is not None:
                    return shop_id, shop
        return None

    def _cmd_shop(self, _command: Command) -> list[str]:
        """Tampilkan dagangan toko di lokasi saat ini (GDD §18.2).

        Harga beli dari data/items (price); sisa stok = count di
        data/shops dikurangi stok terjual (state.shop_sold); harga jual
        kembali 40% dari harga beli.
        """
        found = self._shop_at_location()
        if found is None:
            return ["Tidak ada pedagang di sini."]
        _, shop = found
        items = load_items()
        sold = self.state.shop_sold.get(shop["id"], {})
        lines = [f"{shop['name']}:"]
        for entry in shop["stock"]:
            item_id = entry["item"]
            item = items.get(item_id, {})
            price = item.get("price")
            remaining = entry["count"] - sold.get(item_id, 0)
            label = item.get("name", item_id)
            price_text = f"{price} emas" if price else "tak berharga"
            lines.append(f"  {label} - {price_text} (sisa {remaining})")
        lines.append("Jual kembali: 40% dari harga beli.")
        return lines

    def _cmd_buy(self, command: Command) -> list[str]:
        """Beli item dari toko di lokasi saat ini (GDD §18.2).

        Validasi: toko ada, item dijual, stok tersisa, jumlah valid, dan
        emas cukup. Memperbarui gold, inventory, dan shop_sold, lalu
        cascade quest+event (objektif collect).
        """
        if not command.args:
            return ["Beli apa? Contoh: buy <item> [jumlah]"]
        item_id = command.args[0]
        count = 1
        if len(command.args) > 1:
            try:
                count = int(command.args[1])
            except ValueError:
                return ["Jumlah tidak valid. Contoh: buy esensi_api 2"]
            if count < 1:
                return ["Jumlah harus minimal 1."]
        found = self._shop_at_location()
        if found is None:
            return ["Tidak ada pedagang di sini."]
        shop_id, shop = found
        entry = next((e for e in shop["stock"] if e["item"] == item_id), None)
        if entry is None:
            return [f"{item_id} tidak dijual di sini."]
        remaining = entry["count"] - self.state.shop_sold.get(shop_id, {}).get(
            item_id, 0
        )
        if remaining <= 0:
            return [
                f"{item_id} sudah habis dijual. "
                "Istirahat untuk mengisi ulang dagangan."
            ]
        if count > remaining:
            return [f"Stok {item_id} tinggal {remaining}."]
        item = load_items().get(item_id, {})
        price = item.get("price")
        if not price:
            return [f"{item.get('name', item_id)} tak bernilai jual."]
        total = price * count
        if self.state.player.gold < total:
            return [
                f"Emasmu kurang: butuh {total} (punya "
                f"{self.state.player.gold})."
            ]
        self.state.player.gold -= total
        inventory = self.state.inventory.setdefault("items", {})
        inventory[item_id] = inventory.get(item_id, 0) + count
        sold = self.state.shop_sold.setdefault(shop_id, {})
        sold[item_id] = sold.get(item_id, 0) + count
        name = item.get("name", item_id)
        lines = [f"Kamu membeli {name} x{count} seharga {total} emas."]
        lines += self._run_quests()
        lines += self._run_events()
        return lines

    def _cmd_sell(self, command: Command) -> list[str]:
        """Jual item milik pemain ke toko di lokasi saat ini (GDD §18.2).

        Harga jual = 40% harga beli (sell_price). Item tanpa price tidak
        bisa dijual. Memperbarui inventory dan gold, lalu cascade
        quest+event.
        """
        if not command.args:
            return ["Jual apa? Contoh: sell <item> [jumlah]"]
        item_id = command.args[0]
        count = 1
        if len(command.args) > 1:
            try:
                count = int(command.args[1])
            except ValueError:
                return ["Jumlah tidak valid. Contoh: sell esensi_api 2"]
            if count < 1:
                return ["Jumlah harus minimal 1."]
        if self._shop_at_location() is None:
            return ["Tidak ada pedagang di sini."]
        inventory = self.state.inventory.get("items", {})
        owned = inventory.get(item_id, 0)
        if owned <= 0:
            return [f"Kamu tidak punya {item_id} di tas."]
        if count > owned:
            return [f"Kamu hanya punya {item_id} x{owned}."]
        item = load_items().get(item_id, {})
        price = item.get("price")
        if not price:
            return [f"{item.get('name', item_id)} tak bernilai jual."]
        total = sell_price(price) * count
        inventory[item_id] = owned - count
        if inventory[item_id] == 0:
            del inventory[item_id]
        self.state.player.gold += total
        name = item.get("name", item_id)
        lines = [f"Kamu menjual {name} x{count} seharga {total} emas."]
        lines += self._run_quests()
        lines += self._run_events()
        return lines

    def _cmd_refine(self, command: Command) -> list[str]:
        """Racik pil dari bahan sesuai resep (GDD §18.2).

        Syarat: resep sudah dipelajari (flag ``recipe_<item>_known``),
        Kuali Roh ada di tas, dan semua bahan tersedia. Mengonsumsi
        bahan sesuai resep lalu menambah pil hasil; cascade quest+event
        (pola buy/sell).
        """
        if not command.args:
            return ["Racik apa? Contoh: refine <nama_pil>."]
        target_id = command.args[0]
        catalog = load_items()
        item = catalog.get(target_id)
        if item is None:
            return [f"Resep '{target_id}' tidak dikenal."]
        recipe = item.get("recipe")
        if not recipe:
            return [f"{item['name']} tidak memiliki resep."]
        if not self.state.flags.get(f"recipe_{target_id}_known"):
            msg = (
                f"Kamu belum mempelajari resep {item['name']}. "
                "Beli dan pakai item resepnya dulu."
            )
            return [msg]
        items = self.state.inventory.setdefault("items", {})
        if items.get("kuali_roh", 0) <= 0:
            return ["Kamu butuh Kuali Roh untuk meracik."]
        for req in recipe:
            if items.get(req["item"], 0) < req["qty"]:
                need = catalog.get(req["item"], {}).get("name", req["item"])
                return [f"Bahan tidak cukup: butuh {req['qty']}x {need}."]
        for req in recipe:
            items[req["item"]] -= req["qty"]
            if items[req["item"]] == 0:
                del items[req["item"]]
        items[target_id] = items.get(target_id, 0) + 1
        lines = [f"Kamu meracik {item['name']} x1."]
        lines += self._run_quests()
        lines += self._run_events()
        return lines

    def _cmd_quests(self, _command: Command) -> list[str]:
        """Tampilkan quest aktif dengan progres per objektif (GDD §12)."""
        quests = load_quests()
        active = [
            quest
            for quest in quests
            if quest.id in self.state.quests.started
            and quest.id not in self.state.quests.done
        ]
        done = [quest for quest in quests if quest.id in self.state.quests.done]
        if not active and not done:
            return ["Tidak ada quest aktif."]
        lines: list[str] = []
        if active:
            lines.append("Quest aktif:")
            for quest in active:
                lines.append(f"  {quest.title}")
                lines.append(f"    {quest.description}")
                for index, objective in enumerate(quest.objectives):
                    mark = (
                        "[x]"
                        if check_objective(self.state, quest, index)
                        else "[ ]"
                    )
                    lines.append(f"    {mark} {objective_label(objective)}")
        if done:
            lines.append("Selesai:")
            for quest in done:
                lines.append(f"  {quest.title}")
        return lines

    def _cmd_talk(self, command: Command) -> list[str]:
        """Bicara dengan NPC di lokasi saat ini (GDD §18.2, §12.5).

        Bila NPC punya file dialog data-driven yang belum selesai,
        percakapan bercabang dimulai (state machine via `choose`).
        Tanpa file dialog, fallback ke dialog statis lama (`greeting`
        + array) — kompatibilitas data eksisting (AGENTS §6).
        """
        if not command.args:
            return ["Bicara dengan siapa? Contoh: talk elder_mao"]
        npc_id = command.args[0]
        npc_path = NPC_DIR / f"{npc_id}.json"
        if not npc_path.is_file():
            return [f"Kamu tidak mengenal siapa pun bernama {npc_id}."]
        npc = json.loads(npc_path.read_text(encoding="utf-8"))
        if npc["location"] != self.state.location:
            return [f"{npc['name']} tidak ada di sini."]
        self.state.flags[f"talked_{npc_id}"] = True
        dialog = find_dialog(load_dialogs(), npc_id, self.state)
        if dialog is not None:
            return self._start_dialog(npc, dialog)
        return (
            [npc["greeting"]]
            + list(npc["dialog"])
            + self._run_quests()
            + self._run_events()
        )

    def _start_dialog(
        self, npc: dict[str, Any], dialog: dict[str, Any]
    ) -> list[str]:
        """Mulai percakapan bercabang: tampilkan node start + pilihan.

        State machine disimpan di ``state.flags["pending_dialog"]``
        (dialog_id + node saat ini) — pola sama dengan `pending_choice`.
        Pilihan dijawab lewat perintah `choose <nomor>` (GDD §18.2).
        """
        node = get_node(dialog, "start")
        self.state.flags["pending_dialog"] = {
            "dialog_id": dialog["id"],
            "node": "start",
        }
        lines = [f"{npc['name']}: {node['text']}"]
        for index, choice in enumerate(visible_choices(node, self.state), 1):
            lines.append(f"  [{index}] {choice['text']}")
        lines.append("Pilih: choose <nomor>")
        lines.extend(self._run_quests())
        lines.extend(self._run_events())
        return lines

    def _cmd_memories(self, _command: Command) -> list[str]:
        """Tampilkan echo memori yang terkumpul (GDD §15.3 grant_memory)."""
        if not self.state.memories:
            return ["Tidak ada memori."]
        contents = load_memories()
        lines = ["Echo memori:"]
        for memory_id in self.state.memories:
            data = contents.get(memory_id)
            if data is None:
                # ponytail: memori tak ada di data/story (save lama) ->
                # tampil id mentah; validator §25.3 sudah menjamin
                # event->memory ter-resolve.
                lines.append(f"  - {memory_id}")
                continue
            lines.append(f"  - {data['title']}")
            lines.append(f"    {data['text']}")
        return lines

    def _cmd_party(self, _command: Command) -> list[str]:
        """Tampilkan tim: protagonis + rekan aktif dengan bond (GDD §20)."""
        player = self.state.player
        active = set(self.state.party_active)
        all_members = [Companion.from_dict(raw) for raw in self.state.party]
        members = [member for member in all_members if member.id in active]
        lines = [f"[bold gold3]PARTY ({1 + len(members)}/4)[/]"]
        lines.append(f"  {player.name} (protagonis)")
        for companion in members:
            # HP live dari combatan saat battle (konsisten dgn HUD, Bug 1);
            # di luar battle, HP/qi tersimpan di state.party.
            combatant = (
                self._ally_map.get(companion.id) if self.in_battle else None
            )
            if combatant is not None:
                hp, hp_max = combatant.hp, combatant.hp_max
            else:
                hp = (
                    companion.hp
                    if companion.hp is not None
                    else companion.hp_max
                )
                hp_max = companion.hp_max
            bar = make_bar(hp, hp_max, 10)
            lines.append(
                f"  [cyan]{companion.name}[/] · {companion.tier} · "
                f"{companion.element} · HP {bar} {hp}/{hp_max} · "
                f"bond {companion.bond_xp} (peringkat {companion.rank})"
            )
        # Clamp defensif: cap aktif (3) dijaga event/swap, tapi panel tak
        # boleh crash walau state korup (ponytail: len > 3 tak mungkin).
        for _ in range(max(0, 3 - len(members))):
            lines.append("  (kosong)")
        # Roster cadangan (Bug 3): rekan direkrut tapi belum aktif tampil
        # agar pemain tahu id-nya untuk `swap <id>`.
        inactive = [member for member in all_members if member.id not in active]
        if inactive:
            names = ", ".join(member.name for member in inactive)
            lines.append(f"  Cadangan: {names}")
        return lines

    def _cmd_swap(self, command: Command) -> list[str]:
        """Tukar komposisi tim, hanya di lokasi aman (GDD §20.1).

        Lokasi aman = peta tanpa musuh (desa/kota). Swap di combat
        ditunda (ponytail: butuh roster cadangan > 3 anggota).
        """
        if self.in_battle:
            return [
                "Tidak bisa mengganti tim saat bertarung "
                "(swap combat ditunda — Fase 2 lanjutan)."
            ]
        location_data = load_maps().get(self.state.location, {})
        if location_data.get("enemies"):
            return [
                "Area ini tidak aman untuk mengatur tim. "
                "Kembali ke desa atau kota dulu."
            ]
        if not command.args:
            return ["Tukar siapa? Contoh: swap <id_rekan>"]
        companion_id = command.args[0]
        ids = [raw["id"] for raw in self.state.party]
        if companion_id not in ids:
            return [f"Rekan '{companion_id}' tidak ada di timmu."]
        active = list(self.state.party_active)
        if companion_id in active:
            active.remove(companion_id)
        else:
            if len(active) >= 3:
                return ["Tim sudah penuh (maksimal 3 rekan aktif)."]
            active.append(companion_id)
        self.state.party_active = active
        name = next(
            Companion.from_dict(raw).name
            for raw in self.state.party
            if raw["id"] == companion_id
        )
        state = "aktif" if companion_id in active else "cadangan"
        return [f"{name} kini {state}."]

    def quest_lines(self) -> list[str]:
        """Ringkasan quest aktif untuk panel UI (read-only, tanpa efek).

        Reuse logika ``_cmd_quests`` agar panel dan perintah quests tidak
        mungkin berbeda; tanpa cascade quest/event (murni tampilan).
        """
        return self._cmd_quests(Command(name="quests", args=(), raw="quests"))

    def party_lines(self) -> list[str]:
        """Ringkasan tim untuk panel UI (read-only, tanpa efek)."""
        return self._cmd_party(Command(name="party", args=(), raw="party"))

    def _cmd_go(self, command: Command) -> list[str]:
        if not command.args:
            return ["Tujuan? Contoh: go ashfall_forest"]
        location = command.args[0]
        if location == START_LOCATION:
            self.state.location = location
            return (
                [f"Kamu kembali ke {location}."]
                + self._run_quests()
                + self._run_events()
            )
        flag = f"map_{location}_unlocked"
        if self.state.flags.get(flag):
            self.state.location = location
            return (
                [f"Kamu tiba di {location}."]
                + self._run_quests()
                + self._run_events()
            )
        return [f"Lokasi belum terbuka: {location}."]

    def _cmd_look(self, _command: Command) -> list[str]:
        """Amati lokasi saat ini: deskripsi dari data/maps (GDD §9).

        Musuh per peta didefinisikan di data (enemies + requires_flag);
        yang pertama memenuhi syarat dan belum dikalahkan memicu
        pertarungan (GDD §11).
        """
        location = self.state.location
        data = load_maps().get(location)
        if data is not None:
            for entry in data.get("enemies", []):
                enemy_id = entry["enemy"]
                requires = entry.get("requires_flag")
                if requires and not self.state.flags.get(requires):
                    continue
                if self.state.kills.get(enemy_id, 0) >= 1:
                    continue
                return self._start_battle(enemy_id)
        if data is None:
            # ponytail: peta tanpa data -> teks netral; hilang begitu semua
            # peta punya file JSON di data/maps.
            return [
                f"Kamu di {location}. Tempat ini sunyi.",
            ]
        return [f"{data['name']}: {data['description']}"]

    def _cmd_cultivate(self, _command: Command) -> list[str]:
        player = self.state.player
        player.add_insight(CULTIVATE_INSIGHT)
        self._advance_hours(CULTIVATE_HOURS)
        return (
            [
                "Kamu bermeditasi menyerap qi langit-bumi...",
                f"Insight +{CULTIVATE_INSIGHT} (total {player.insight}).",
            ]
            + self._run_quests()
            + self._run_events()
        )

    def _cmd_rest(self, _command: Command) -> list[str]:
        player = self.state.player
        self.state.time.day += 1
        self.state.time.hour = REST_HOUR
        player.hp = player.hp_max
        player.qi = player.qi_max
        healed = player.is_injured
        player.advance_day()
        # Restock toko (GDD §7): dagangan diisi ulang saat pemain
        # istirahat. Diproses sebelum autosave agar stok tersimpan ikut
        # ter-reset.
        restock_note = ""
        if self.state.shop_sold:
            self.state.shop_sold.clear()
            restock_note = " Pedagang mengisi ulang dagangan mereka."
        # Quest lalu event diproses sebelum autosave agar efeknya ikut
        # tersimpan dan cascade quest->event menyala satu pass (§15.4).
        quest_lines = self._run_quests()
        event_lines = self._run_events()
        autosave_save(self.state, self.save_dir)
        message = "Kamu beristirahat hingga pagi. HP dan qi pulih penuh."
        if healed:
            message += " Cedera membaik."
        message += restock_note
        return (
            [message, "Permainan tersimpan otomatis."]
            + quest_lines
            + event_lines
        )

    def _cmd_breakthrough(self, _command: Command) -> list[str]:
        player = self.state.player
        tiers = load_tiers()
        target = next_tier(player, tiers)
        if target is None:
            return ["Kamu sudah di puncak kultivasi."]
        if player.insight < target.insight_required:
            return [
                f"Insight belum cukup: butuh {target.insight_required} "
                f"(kini {player.insight}).",
                "Kultivasi dulu untuk menambah pemahaman.",
            ]
        result = attempt_breakthrough(player, tiers, rng=self._rng)
        # Quest lalu event diproses sebelum autosave agar efeknya ikut
        # tersimpan dan cascade quest->event menyala satu pass (§15.4).
        quest_lines = self._run_quests()
        event_lines = self._run_events()
        autosave_save(self.state, self.save_dir)
        if result.success:
            return (
                [
                    f"BREAKTHROUGH SUKSES! Kamu kini {result.tier_id} "
                    f"({result.rate}%).",
                    "Permainan tersimpan otomatis.",
                ]
                + quest_lines
                + event_lines
            )
        note = ""
        if result.inner_demon:
            note = " Bayangan batin mengintai (pertarungan inner demon "
            note += "menyusul Fase 1)."
        return (
            [
                "Breakthrough GAGAL. Tubuhmu terluka "
                f"({result.injury_days} hari cedera, stat -25%).{note}",
                "Permainan tersimpan otomatis.",
            ]
            + quest_lines
            + event_lines
        )

    def _cmd_save(self, command: Command) -> list[str]:
        slot = self._slot_arg(command, default="save1")
        if slot is None:
            return ["Slot simpan harus 1-3. Contoh: save 2"]
        return self.save(slot)

    def _cmd_load(self, command: Command) -> list[str]:
        slot = self._slot_arg(command, default="save1")
        if slot is None:
            return ["Slot muat harus 1-3. Contoh: load 2"]
        if not slot_exists(slot, self.save_dir):
            return [f"Tidak ada save di {slot}."]
        return self.load(slot)

    def _cmd_quit(self, _command: Command) -> list[str]:
        self.quit_requested = True
        return ["Sampai jumpa, kultivator."]

    def _cmd_choose(self, command: Command) -> list[str]:
        """Pilih opsi dari prompt_choice event (Sprint 1 - Choice Engine).

        Hanya jalan saat TIDAK dalam battle. Menerapkan opsi yang dipilih:
        set_flag, change_reputation, log. Lalu clear pending_choice dan
        jalankan cascade quest+event.
        """
        if self.in_battle:
            return ["Kamu sedang bertarung! (attack/defend/observe/escape)"]
        if self.state is None:
            return ["Belum ada permainan. Mulai baru atau muat save."]
        pending = self.state.flags.get("pending_choice")
        if not pending:
            return self._choose_dialog(command)
        options = pending.get("options", [])
        if not command.args:
            return ["Pilih opsi: choose <key> (contoh: choose a)"]
        key = command.args[0]
        chosen = next((opt for opt in options if opt["key"] == key), None)
        if chosen is None:
            valid = ", ".join(opt["key"] for opt in options)
            return [f"Opsi '{key}' tidak valid. Pilihan: {valid}"]
        # Terapkan opsi yang dipilih. Format baru: daftar aksi penuh
        # (GDD §15.3: grant_item, grant_gold, start_quest, dll) via
        # apply_action — satu sumber kebenaran aksi. Format lama
        # (set_flag/change_reputation/log) tetap didukung.
        lines: list[str] = []
        for action in chosen.get("actions", []):
            result = EventResult()
            apply_action(
                action, self.state, result, pending.get("event_id", "choose")
            )
            lines.extend(result.logs)
        if "set_flag" in chosen:
            self.state.flags[chosen["set_flag"]] = True
        if "change_reputation" in chosen:
            for faction, delta in chosen["change_reputation"].items():
                self.state.add_reputation(faction, delta)
        if "log" in chosen:
            lines.append(chosen["log"])
        # Clear pending_choice
        self.state.flags.pop("pending_choice", None)
        # Cascade quest + event (sama seperti perintah dunia lain)
        lines.extend(self._run_quests())
        lines.extend(self._run_events())
        return lines

    def _choose_dialog(self, command: Command) -> list[str]:
        """Pilih nomor pilihan dalam dialog bercabang (GDD §12.5).

        Membaca ``state.flags["pending_dialog"]`` (diset `_start_dialog`),
        mengeksekusi aksi pilihan via event parser, lalu pindah ke node
        berikutnya atau mengakhiri percakapan. `next: null` menandakan
        akhir; saat itulah flag `talked_<dialog_id>` diset (sekali jalan).
        """
        pending = self.state.flags.get("pending_dialog")
        if not pending:
            return [
                "Tidak ada pilihan aktif. Tunggu event yang meminta keputusan."
            ]
        if not command.args:
            return ["Pilih opsi: choose <nomor> (contoh: choose 1)"]
        raw = command.args[0]
        if not raw.isdigit():
            return [f"'{raw}' bukan nomor pilihan yang valid."]
        dialogs = load_dialogs()
        dialog = dialogs.get(pending["dialog_id"])
        if dialog is None:
            # ponytail: dialog tak ada di data (save lama) -> bersihkan
            # state; validator §25.3 menjamin data->dialog ter-resolve.
            self.state.flags.pop("pending_dialog", None)
            return ["Dialog tidak ditemukan di data (save lama?)."]
        node = get_node(dialog, pending["node"])
        choices = visible_choices(node, self.state)
        number = int(raw)
        if not 1 <= number <= len(choices):
            valid = ", ".join(str(i) for i in range(1, len(choices) + 1))
            return [f"Pilihan '{number}' tidak valid. Pilihan: {valid}"]
        choice = choices[number - 1]
        lines: list[str] = []
        result = EventResult()
        apply_actions(
            choice.get("actions", []),
            self.state,
            result,
            dialog["id"],
        )
        lines.extend(result.logs)
        next_id = choice.get("next")
        if next_id is None:
            # Percakapan selesai: flag once + bersihkan state machine.
            self.state.flags[f"talked_{dialog['id']}"] = True
            self.state.flags.pop("pending_dialog", None)
            lines.extend(self._run_quests())
            lines.extend(self._run_events())
            return lines
        # Lanjut ke node berikutnya.
        self.state.flags["pending_dialog"] = {
            "dialog_id": dialog["id"],
            "node": next_id,
        }
        next_node = get_node(dialog, next_id)
        lines.append(next_node["text"])
        for index, option in enumerate(
            visible_choices(next_node, self.state), 1
        ):
            lines.append(f"  [{index}] {option['text']}")
        lines.append("Pilih: choose <nomor>")
        return lines

    def _advance_hours(self, hours: int) -> None:
        """Majukan jam game dengan rollover ke hari berikutnya (§19.2)."""
        self.state.time.hour += hours
        while self.state.time.hour >= 24:
            self.state.time.hour -= 24
            self.state.time.day += 1

    def _run_quests(self) -> list[str]:
        """Evaluasi quest aktif setelah momen mutasi state (GDD §12.4).

        Dipanggil sebelum _run_events agar flag quest<id>_done sudah diset
        sebelum event dengan trigger quest_done dievaluasi (cascade satu
        pass), dan setelah kemenangan pertarungan (kind enemy/kill_count).
        """
        if self.state is None:
            return []
        lines: list[str] = []
        for quest in active_quests(self.state, load_quests()):
            lines.extend(advance_quest(self.state, quest))
        return lines

    def _run_events(self) -> list[str]:
        """Proses event data-driven setelah momen mutasi state (GDD §15.4).

        Dipanggil setelah go / cultivate / rest / breakthrough / talk —
        sekali per momen. Kembalikan baris narasi event untuk UI.
        """
        if self.state is None:
            return []
        return process_events(self.state, load_events()).logs

    def _slot_arg(self, command: Command, default: str) -> str | None:
        """Terjemahkan argumen slot; '2' -> 'save2', slot literal diterima.

        Baik angka (2 -> save2) maupun nama slot sah (save2, autosave)
        dipetakan langsung; default dipakai saat argumen kosong.
        """
        if not command.args:
            return default
        raw = command.args[0]
        if raw in VALID_SLOTS:
            return raw
        slot = f"save{raw}"
        if slot in SLOTS:
            return slot
        return None

    # ------------------------------------------------------------------
    # Pertarungan
    # ------------------------------------------------------------------
    @property
    def in_battle(self) -> bool:
        """Kembalikan True selama pertarungan aktif belum selesai."""
        return self.battle is not None and not self.battle.over

    @property
    def player_skills(self) -> list[str]:
        """Skill pemain diturunkan dari data (GDD §4.1, §5.2).

        Teknik dengan requires.tier == tier pemain; tanpa field skills
        di save — derivasi murni dari data/cultivation + data/techniques.
        """
        if self.state is None:
            return []
        return [
            technique.id
            for technique in load_techniques()
            if technique.requires.get("tier") == self.state.player.tier_id
        ]

    def _start_battle(self, enemy_id: str) -> list[str]:
        player = self.state.player
        techniques = load_techniques()
        enemy = next((e for e in load_enemies() if e.id == enemy_id), None)
        if enemy is None:
            raise ValueError(f"musuh tidak dikenal: {enemy_id}")
        ally = combatant_from_player(player, skills=self.player_skills)
        # Terapkan buff item (GDD §7): buff_<stat> menambah stat langsung;
        # resist_<x> tercatat di stats (dibaca engine combat Fase 2).
        # Buff dikonsumsi setelah battle (sekali pakai).
        for key, value in self.state.buffs.items():
            ally.stats[key] = ally.stats.get(key, 0) + value
        allies = [ally]
        self._ally_map = {}
        # Rekan aktif ikut bertarung (GDD §20.1: protagonis + max 3 slot).
        active = set(self.state.party_active)
        for raw in self.state.party:
            if len(allies) >= 4:
                # GDD §24.1 poin 3: tim combat maks 4 (1 protagonis + 3
                # rekan). Clamp pertahanan untuk save yang diedit manual.
                break
            companion = Companion.from_dict(raw)
            if companion.id not in active:
                continue
            ally_combatant = combatant_from_companion(companion)
            allies.append(ally_combatant)
            self._ally_map[companion.id] = ally_combatant
        self._ally = ally
        self._enemy = enemy
        self.battle = Battle(
            allies=allies,
            enemies=[combatant_from_enemy(enemy)],
            techniques=techniques,
            rng=self._rng,
        )
        names = ", ".join(combatant.name for combatant in allies)
        return [
            f"{enemy.name} muncul dari bayangan!",
            f"Tim bertarung: {names}.",
            "Pertarungan dimulai! (Ketik 'escape' jika ingin melarikan diri)",
            "Gunakan attack / defend / technique / observe / escape.",
        ]

    def battle_frame(self, error: str | None = None) -> BattleFrame:
        """Kapsul status pertarungan terkini untuk UI."""
        battle = self.battle
        if battle is None:
            raise RuntimeError("tidak ada pertarungan")
        victory: bool | None = None
        if battle.winner == "allies":
            victory = True
        elif battle.winner == "enemies":
            victory = False
        active_name = (
            battle.current.name
            if not battle.over and self._is_player_turn()
            else None
        )
        log = list(battle.log)
        if active_name is not None:
            # Penanda giliran: pemain (atau AI tester) tahu siapa yang
            # sedang menunggu perintah — aksi invalid untuk rekan lain
            # berujung error frame tanpa advance (regresi multi-ally).
            log.append(
                f"[Giliran {active_name}] Gunakan attack / defend / "
                "technique / observe / escape."
            )
        return BattleFrame(
            log=log,
            over=battle.over,
            victory=victory,
            escaped=battle.escaped,
            player_turn=not battle.over and self._is_player_turn(),
            enemies=battle.observe(),
            error=error,
            active_ally_name=active_name,
        )

    def battle_step(self, action: str) -> BattleFrame:
        """Satu langkah pertarungan: aksi pemain + giliran musuh otomatis.

        Aksi tidak valid ditangkap sebagai error frame (tanpa crash), dan
        karena Battle.step memvalidasi sebelum awal giliran, percobaan
        ulang tidak menggandakan efek regen/tick.
        """
        battle = self.battle
        if battle is None:
            raise RuntimeError("tidak ada pertarungan")
        error: str | None = None
        if not battle.over:
            self._resolve_enemy_turns()
            if not battle.over and self._is_player_turn():
                try:
                    battle.step(action)
                except ValueError as exc:
                    error = str(exc)
            self._resolve_enemy_turns()
            if battle.over:
                self._finish_battle()
        return self.battle_frame(error=error)

    def _is_player_turn(self) -> bool:
        """Kembalikan True bila giliran aktif milik sekutu pemain."""
        current = self.battle.current
        return any(current is member for member in self.battle.allies)

    def _resolve_enemy_turns(self) -> None:
        """Jalankan giliran musuh otomatis sampai giliran pemain/berakhir."""
        battle = self.battle
        while not battle.over and not self._is_player_turn():
            battle.step_enemy()

    def _write_back_allies(self) -> None:
        """Tulis balik hp/qi combatan ke player & rekan; KO pulih penuh.

        Luka di dunia ikut terbawa ke pertarungan (§17.2); setelah
        pertarungan, yang KO pulih otomatis (§20.4) sedangkan yang hidup
        menyimpan luka tersisa.
        """
        player = self.state.player
        ally = self._ally
        if ally is not None:
            player.hp = min(ally.hp, player.hp_max)
            player.qi = min(ally.qi, player.qi_max)
        for raw in self.state.party:
            companion = Companion.from_dict(raw)
            combatant = self._ally_map.get(companion.id)
            if combatant is None:
                continue
            if combatant.hp <= 0:
                # KO: pulih otomatis (GDD §20.4).
                raw["hp"] = companion.hp_max
                raw["qi"] = companion.qi_max
            else:
                raw["hp"] = min(combatant.hp, companion.hp_max)
                raw["qi"] = min(combatant.qi, companion.qi_max)

    def _grant_bond_xp(self, battle: Battle) -> None:
        """Naikkan bond XP rekan yang hidup setelah kemenangan (§20.3)."""
        for raw in self.state.party:
            companion = Companion.from_dict(raw)
            combatant = self._ally_map.get(companion.id)
            if combatant is None or combatant.hp <= 0:
                continue
            raw["bond_xp"] = companion.bond_xp + BOND_XP_VICTORY
            battle.log.append(
                f"Ikatan dengan {companion.name} menguat "
                f"(+{BOND_XP_VICTORY} bond XP)."
            )

    def _finish_battle(self) -> None:
        """Tutup pertarungan: reward, tulis balik hp/qi, pemulihan KO."""
        battle = self.battle
        player = self.state.player
        enemy = self._enemy
        self._write_back_allies()
        # Buff item sekali pakai: dikonsumsi setelah pertarungan selesai
        # (menang/kalah/kabur), GDD §7.
        self.state.buffs.clear()
        if battle.winner == "allies":
            rewards = enemy.rewards if enemy is not None else {}
            player.add_insight(rewards.get("insight", 0))
            player.gold += rewards.get("gold", 0)
            self.state.flags[f"{self.state.location}_cleared"] = True
            if enemy is not None:
                enemy_id = enemy.id
                self.state.kills[enemy_id] = (
                    self.state.kills.get(enemy_id, 0) + 1
                )
            battle.log.append(
                f"Menang! Insight +{rewards.get('insight', 0)}, "
                f"Gold +{rewards.get('gold', 0)}."
            )
            self._grant_bond_xp(battle)
            # Quest dievaluasi setelah kemenangan (GDD §12.4); narasi
            # quest masuk log pertarungan agar terlihat UI.
            for line in self._run_quests():
                battle.log.append(line)
            for line in self._run_events():
                battle.log.append(line)
        elif battle.winner == "enemies":
            # KO protagonis: pulih otomatis setelah pertarungan (§20.4).
            player.hp = player.hp_max
            battle.log.append(
                "Kamu tersungkur... dan sadar kembali dengan luka menganga."
            )
