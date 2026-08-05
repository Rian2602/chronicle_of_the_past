import copy

from src.core import input_handler, save_manager
from src.core.game_state import GameState
from src.core.randomizer import Randomizer
from src.engine import dialog_engine, event_engine, quest_engine
from src.engine.combat_engine import enemy_turn, player_action, start_combat
from src.engine.time_engine import rest
from src.models.combat_interfaces import CombatAction, CombatResult
from src.models.enemy import Enemy
from src.models.item import Item
from src.models.map import Map
from src.models.player import max_hp, max_mp
from src.systems import (
    equipment_system,
    exploration_system,
    inventory_system,
    level_system,
    loot_system,
    shop_system,
    travel_system,
)
from src.ui import (
    ascii_loader,
    combat_view,
    dialog_view,
    hud,
    inventory_view,
    shop_view,
)
from src.utils.json_loader import ContentError

_COMBAT_ACTIONS = {action.value for action in CombatAction}


class GameQuit(Exception):
    """Sinyal keluar ke menu utama; dilempar oleh perintah 'quit'."""


class Game:
    """Pengendali utama permainan: route perintah, dialog, combat, quest."""

    def __init__(self, game_context, rng_seed=None):
        self.ctx = game_context
        self.state = GameState()
        self.state.rng_seed = rng_seed if rng_seed is not None else 20260803
        self.randomizer = Randomizer(self.state.rng_seed)
        self._current_dialog = None
        self._talk_npc_id = None
        self._shop_npc_id = None
        self._combat = None
        self._pending_levels = 0

    def _wire(self):
        """Hubungkan data mentah GameContext ke state sebagai objek model."""
        s = self.state
        s.world = {mid: Map(**data) for mid, data in self.ctx.maps.items()}
        s.enemies = {
            eid: Enemy(**data) for eid, data in self.ctx.enemies.items()
        }
        s.items = {iid: Item(**data) for iid, data in self.ctx.items.items()}
        s.quests = dict(self.ctx.quests)
        s.memories = list(self.ctx.memories)
        s.events = list(self.ctx.events)
        s.scenes = list(self.ctx.scenes)
        if s.current_map is None:
            s.current_map = s.world.get("village")

    def new_game(self, name, class_id):
        """Mulai permainan baru dengan nama dan kelas; proses event awal.

        Returns:
            Teks pembuka (hasil event processing).
        """
        self._wire()
        self.state.player = self.ctx.create_player(name, class_id)
        self._current_dialog = None
        self._talk_npc_id = None
        self._shop_npc_id = None
        self._combat = None
        self._pending_levels = 0
        assert self.state.player is not None
        lines = event_engine.process_events(self.state, self.randomizer)
        return "\n".join(lines) or "Kamu terbangun di Ashen Village."

    def continue_game(self, save_path):
        """Muat save: wire ulang state, restore combat, proses event.

        Returns:
            Teks status setelah dimuat.

        Raises:
            SaveError: Bila save tidak valid atau tanpa data pemain.
        """
        loaded = save_manager.load_game(save_path, self.ctx)
        if loaded.player is None:
            raise save_manager.SaveError(
                "Save tidak lengkap (tanpa data pemain)."
            )
        self.state = loaded
        self._wire()
        s = self.state
        map_id = (
            s.current_map.id if hasattr(s.current_map, "id") else s.current_map
        )
        s.current_map = s.world.get(map_id, s.world.get("village"))
        seed = s.rng_seed if s.rng_seed is not None else 20260803
        s.rng_seed = seed
        self.randomizer = Randomizer(seed)
        self._current_dialog = None
        self._talk_npc_id = None
        self._shop_npc_id = None
        self._pending_levels = 0
        # Restore combat state jika ada
        self._combat = None
        if hasattr(s, "combat_data") and s.combat_data is not None:
            self._restore_combat(s.combat_data)
        lines = event_engine.process_events(self.state, self.randomizer)
        return "\n".join(lines) or "Save dimuat."

    def _restore_combat(self, combat_data):
        """Restore combat state dari data yang di-load."""
        from src.models.combat_interfaces import (
            BuffEffect,
            CombatResult,
            CombatState,
            StatusEffect,
        )

        enemy_id = combat_data.get("enemy_id")
        if enemy_id is None or enemy_id not in self.state.enemies:
            return  # Tidak bisa restore tanpa enemy yang valid
        enemy = self.state.enemies[enemy_id]
        enemy = copy.copy(enemy)
        enemy.stats = dict(enemy.stats)
        enemy.stats.setdefault("max_hp", enemy.stats.get("hp", 1))
        # Set HP enemy sesuai yang tersimpan
        enemy.stats["hp"] = combat_data.get(
            "enemy_hp", enemy.stats.get("hp", 1)
        )
        # Set MP enemy sesuai yang tersimpan (fallback MP template utk
        # save lama yang belum punya enemy_mp)
        enemy.stats["mp"] = combat_data.get(
            "enemy_mp", enemy.stats.get("mp", 0)
        )
        # Rekonstruksi statuses dari dict ke StatusEffect objects
        restored_statuses = {}
        for target_id, effects in combat_data.get("statuses", {}).items():
            restored_statuses[target_id] = [
                StatusEffect(
                    kind=eff["kind"],
                    duration=eff["duration"],
                    power=eff["power"],
                )
                for eff in effects
            ]
        # Rekonstruksi buffs dari dict ke BuffEffect objects
        restored_buffs = {}
        for target_id, effects in combat_data.get("buffs", {}).items():
            restored_buffs[target_id] = [
                BuffEffect(
                    stat=eff["stat"],
                    duration=eff["duration"],
                    power=eff["power"],
                )
                for eff in effects
            ]
        # Buat CombatState baru dengan data yang tersimpan
        saved_result = combat_data.get("result")
        result = (
            CombatResult(saved_result)
            if saved_result in {r.value for r in CombatResult}
            else None
        )
        self._combat = CombatState(
            round_no=combat_data.get("round_no", 1),
            turn_order=combat_data.get("turn_order", ["player", enemy_id]),
            current_index=combat_data.get("current_index", 0),
            over=combat_data.get("over", False),
            result=result,
            log=combat_data.get("log", []),
            observe_used=combat_data.get("observe_used", False),
            player_defending=combat_data.get("player_defending", False),
            enemy_defending=combat_data.get("enemy_defending", False),
            statuses=restored_statuses,
            buffs=restored_buffs,
            player=self.state.player,
            enemy=enemy,
            randomizer=self.randomizer,
            skills=self.ctx.skills,
            loot_resolver=loot_system.roll_loot,
            max_status_duration=10,
            items=self.state.items,
        )
        self._combat.xp = combat_data.get("xp", 0)
        self._combat.gold = combat_data.get("gold", 0)
        self._combat.loot = combat_data.get("loot", [])
        if combat_data.get("observe_info"):
            self._combat.observe_info = combat_data["observe_info"]

    def run_turn(self, text):
        """Proses satu perintah pemain dan kembalikan teks hasil giliran.

        Prioritas routing: pilihan level-up pending → aksi combat →
        pilihan dialog → perintah eksplorasi biasa.

        Returns:
            Teks lengkap (HUD + baris hasil) untuk ditampilkan.
        """
        cmd = input_handler.parse_input(text)
        out = []
        if self._pending_levels > 0:
            self._level_choice_select(cmd, out)
        elif self._combat is not None and cmd.action in _COMBAT_ACTIONS:
            self._combat_turn(cmd, out)
        elif self._current_dialog is not None and cmd.action == "select":
            self._dialog_select(cmd, out)
        elif self._combat is not None and cmd.action not in (
            "save",
            "help",
            "inventory",
            "look",
        ):
            out.append("Tidak bisa saat bertarung.")
            out.append(combat_view.render(self._combat))
        else:
            self._dispatch(cmd, out)
        if self._combat is None:
            logs = event_engine.process_events(self.state, self.randomizer)
            out.extend(logs)
        if (
            self._combat is None
            and self._current_dialog is None
            and self._pending_levels == 0
        ):
            self._apply_pending_levels(out)
        return (
            hud.render(self.state.player, self.state, self.ctx.npc)
            + "\n\n"
            + "\n".join(out)
        )

    def _dispatch(self, cmd, out):
        """Dispatch command to appropriate handler method."""
        action = cmd.action
        action_handlers = {
            "status": lambda: self._cmd_status(out),
            "help": lambda: self._cmd_help(out),
            "go": lambda: self._cmd_go(cmd, out),
            "rest": lambda: self._cmd_rest(out),
            "talk": lambda: self._cmd_talk(cmd, out),
            "shop": lambda: self._cmd_shop(cmd, out),
            "buy": lambda: self._cmd_buy(cmd, out),
            "sell": lambda: self._cmd_sell(cmd, out),
            "look": lambda: self._cmd_look(out),
            "explore": lambda: self._cmd_explore(out),
            "inventory": lambda: self._cmd_inventory(out),
            "inv": lambda: self._cmd_inventory(out),  # alias ringkas
            "memories": lambda: self._cmd_memories(out),
            "use": lambda: self._cmd_use(cmd, out),
            "equip": lambda: self._cmd_equip(cmd, out),
            "unequip": lambda: self._cmd_unequip(cmd, out),
            "learn": lambda: self._cmd_learn(cmd, out),
            "save": lambda: self._cmd_save(cmd, out),
            "load": lambda: self._cmd_load(cmd, out),
            "quests": lambda: self._cmd_quests(out),
            "item": lambda: self._cmd_use_alias(cmd, out),
            "quit": lambda: self._cmd_quit(),
        }

        if action in action_handlers:
            action_handlers[action]()
        elif action == "select":
            out.append("Tidak ada dialog aktif.")
        elif action == "":
            out.append("Ketik 'help' untuk daftar perintah.")
            self._append_quest_hint(out)
        else:
            out.append(
                f"Perintah tidak dikenal: {cmd.action}. "
                "Ketik 'help' untuk bantuan."
            )
            self._append_quest_hint(out)

    def _cmd_use_alias(self, cmd, out):
        """Alias 'item <id>' → 'use <id>' di luar combat."""
        if not cmd.args:
            out.append("Gunakan: use <item>. (atau: item <id> saat bertarung)")
            return
        self._cmd_use(cmd, out)

    def _append_quest_hint(self, out):
        """Tambahkan petunjuk quest aktif ke daftar baris output."""
        objective = quest_engine.next_objective(self.state)
        if objective:
            out.append(f"Petunjuk: {objective}")

    def _cmd_status(self, out):
        """Handler perintah status: tampilkan stat & perlengkapan pemain."""
        p = self.state.player
        class_name = (
            self.ctx.classes[p.class_id]["name"]
            if p.class_id in self.ctx.classes
            else p.class_id
        )
        out.append(f"{p.name} — {class_name} (Level {p.level})")
        out.append(f"HP: {p.hp}/{max_hp(p)}  MP: {p.mp}/{max_mp(p)}")
        out.append(f"XP: {p.xp}/{level_system.xp_to_next(p.level)}")
        out.append(f"Emas: {p.gold}")
        if p.equipped:
            labels = {"weapon": "Senjata", "armor": "Zirah", "helmet": "Helm"}
            parts = []
            for slot, item_id in p.equipped.items():
                item = self.state.items.get(item_id)
                parts.append(
                    f"{labels.get(slot, slot)}: "
                    f"{item.name if item else item_id}"
                )
            out.append("Perlengkapan: " + ", ".join(parts))
        else:
            out.append("Perlengkapan: (kosong)")
        if p.learned_skills:
            out.append("Skill: " + ", ".join(p.learned_skills))
        location = (
            self.state.current_map.name if self.state.current_map else "-"
        )
        out.append(f"Lokasi: {location}")

    def _cmd_help(self, out):
        """Handler perintah help: daftar navigasi, menu, dan perintah teks."""
        out.append(
            "Navigasi: ↑/↓ atau w/s untuk berpindah, Enter untuk memilih, "
            "'q' kembali/keluar."
        )
        out.append(
            "Menu utama: Lihat, Jelajah, Pergi, Bicara, Istirahat, "
            "Inventori, Kenangan, Quest, Latih Skill, Status, Bantuan, "
            "Simpan, Muat, Keluar."
        )
        out.append(
            "Saat bicara dengan pedagang: shop (buka toko), "
            "buy <item> [jumlah], sell <item> [jumlah]."
        )
        out.append(
            "Saat bertarung: Serang, Skill, Sihir, Item, Amati, Kabur, "
            "Bertahan, Simpan."
        )
        out.append(
            "Saat dialog: pilih dengan ↑/↓ + Enter, atau "
            "'Akhiri Percakapan' untuk keluar."
        )
        out.append("Perintah teks: save <file>, load <file>, quit.")
        objective = quest_engine.next_objective(self.state)
        if objective:
            out.append(f"Tujuan saat ini: {objective}")

    def _cmd_memories(self, out):
        """Handler perintah memories: tampilkan kenangan yang telah dibuka."""
        p = self.state.player
        if not p.memories:
            out.append("Kamu belum memiliki kenangan.")
            return
        out.append("Kenangan:")
        for memory in p.memories:
            out.append(f"- {memory['title']}: {memory['text']}")

    def _cmd_go(self, cmd, out):
        """Handler perintah go: pindah ke peta tujuan."""
        if not cmd.args:
            out.append("Gunakan: go <nama peta>.")
            return
        self._current_dialog = None
        self._talk_npc_id = None
        self._shop_npc_id = None
        origin = self.state.current_map.id if self.state.current_map else None
        try:
            out.append(travel_system.travel(self.state, cmd.args[0]))
        except ValueError as e:
            out.append(str(e))
            return
        msg = quest_engine.complete_requirement(self.state, "map", cmd.args[0])
        if msg and msg != "Tidak ada syarat yang sesuai.":
            out.append(msg)
        # Syarat quest kind escort: dicek saat tiba di map tujuan (§12.1).
        escort_msg = quest_engine.progress_requirement(
            self.state,
            "escort",
            None,
            to_map=cmd.args[0],
            from_map=origin,
        )
        if escort_msg and escort_msg != "Tidak ada syarat yang sesuai.":
            out.append(escort_msg)

    def _cmd_rest(self, out):
        """Handler perintah rest: istirahat hingga pagi."""
        rest(self.state)
        out.append(
            f"Kamu beristirahat hingga pagi. Kini Hari {self.state.day}."
        )
        out.extend(event_engine.process_day_tick(self.state))

    def _find_npc(self, query: str):
        """Cari NPC berdasarkan ID, nama display, atau prefix.

        Case-insensitive.
        """
        # 1. Exact ID match
        npc = self.ctx.npc.get(query)
        if npc:
            return query, npc
        # Normalize query: lowercase, ganti _ dan - dengan spasi
        q = query.lower().replace("_", " ").replace("-", " ")
        # 2. Case-insensitive exact match (ID atau nama)
        for npc_id, npc_data in self.ctx.npc.items():
            name = npc_data.get("name", "").lower()
            if name == q or npc_id.lower() == q or name.replace(" ", "_") == q:
                return npc_id, npc_data
        # 3. Prefix match
        for npc_id, npc_data in self.ctx.npc.items():
            name = npc_data.get("name", "").lower()
            if name.startswith(q) or npc_id.lower().startswith(q):
                return npc_id, npc_data
        return None, None

    def _cmd_talk(self, cmd, out):
        """Handler perintah talk: mulai dialog dengan NPC di peta ini."""
        if not cmd.args:
            out.append("Gunakan: talk <nama NPC>.")
            return
        # Support multi-word names: 'talk kepala desa'
        query = " ".join(cmd.args)
        npc_id, npc = self._find_npc(query)
        if npc is None:
            m = self.state.current_map
            available = []
            if m:
                for nid in m.npcs or []:
                    nd = self.ctx.npc.get(nid)
                    if nd:
                        available.append(nd["name"])
            hint = f" (tersedia: {', '.join(available)})" if available else ""
            out.append(f"NPC tidak dikenal: {query}.{hint}")
            return
        m = self.state.current_map
        if m is None or npc.get("location") != m.id:
            out.append(f"{npc['name']} tidak ada di sini.")
            return
        if not npc.get("dialogs"):
            out.append(f"{npc['name']} tidak punya dialog.")
            return

        dialog = None
        for did in npc["dialogs"]:
            d = self.ctx.dialogues.get(did)
            if not d:
                continue
            reqs = d.get("require_flags", [])
            if not all(f in self.state.flags for f in reqs):
                continue
            not_reqs = d.get("require_not_flags", [])
            if any(f in self.state.flags for f in not_reqs):
                continue
            dialog = d
            break

        # Tanpa dialog yang cocok, jangan tampilkan dialog flag-gated;
        # fallback lama `dialogs[-1]` bisa bocorkan dialog terkunci bila
        # data diurutkan ulang. NPC dianggap tidak punya dialog saat itu.
        if dialog is None:
            out.append(f"{npc['name']} tidak punya dialog.")
            return
        self._current_dialog = dialog
        self._talk_npc_id = npc_id
        self._shop_npc_id = None
        # Perbaikan: tampilkan nama NPC yang benar (bukan ID)
        out.append(
            dialog_view.render(
                dialog,
                self.state,
                npc_id=npc_id,
                npc_name=npc["name"],
                has_shop=shop_system.has_shop(npc),
            )
        )

    def _cmd_shop(self, cmd, out):
        """Handler perintah shop: buka toko NPC (butuh field 'shop').

        Tanpa argumen, memakai NPC yang sedang diajak bicara
        (`talk <npc>` terakhir). Dengan argumen, mencari NPC seperti
        `talk` dan langsung membuka tokonya bila tersedia di peta ini.
        """
        if cmd.args:
            query = " ".join(cmd.args)
            npc_id, npc = self._find_npc(query)
        else:
            npc_id = self._talk_npc_id
            npc = self.ctx.npc.get(npc_id) if npc_id else None
        if npc is None:
            out.append(
                "Tidak sedang bicara dengan siapa pun. "
                "Gunakan: shop <nama pedagang>."
            )
            return
        m = self.state.current_map
        if m is None or npc.get("location") != m.id:
            out.append(f"{npc['name']} tidak ada di sini.")
            return
        if not shop_system.has_shop(npc):
            out.append(f"{npc['name']} tidak berjualan.")
            return
        self._shop_npc_id = npc_id
        out.append(shop_view.render(self.state, npc))

    def _cmd_buy(self, cmd, out):
        """Handler perintah buy: beli item dari toko yang sedang dibuka."""
        if self._shop_npc_id is None:
            out.append(
                "Tidak sedang berbelanja. Ketik 'shop' saat bicara "
                "dengan pedagang."
            )
            return
        if not cmd.args:
            out.append("Gunakan: buy <item> [jumlah].")
            return
        qty = 1
        if len(cmd.args) > 1:
            try:
                qty = int(cmd.args[1])
            except ValueError:
                out.append("Jumlah tidak valid.")
                return
        npc = self.ctx.npc.get(self._shop_npc_id)
        out.append(shop_system.buy(self.state, npc, cmd.args[0], qty))

    def _cmd_sell(self, cmd, out):
        """Handler perintah sell: jual item ke toko yang sedang dibuka."""
        if self._shop_npc_id is None:
            out.append(
                "Tidak sedang berbelanja. Ketik 'shop' saat bicara "
                "dengan pedagang."
            )
            return
        if not cmd.args:
            out.append("Gunakan: sell <item> [jumlah].")
            return
        qty = 1
        if len(cmd.args) > 1:
            try:
                qty = int(cmd.args[1])
            except ValueError:
                out.append("Jumlah tidak valid.")
                return
        npc = self.ctx.npc.get(self._shop_npc_id)
        out.append(shop_system.sell(self.state, npc, cmd.args[0], qty))

    def _cmd_look(self, out):
        """Handler perintah look: deskripsi peta, pintu keluar, dan NPC."""
        m = self.state.current_map
        if m is None:
            out.append("Kamu tidak berada di peta mana pun.")
            return
        try:
            out.append(ascii_loader.load(m.ascii_art))
        except ContentError:
            pass  # ASCII art opsional; tampilan tetap lanjut tanpa gambar.
        out.append(m.description)
        if m.exits:
            out.append("Jalan keluar: " + ", ".join(m.exits))
        if m.npcs:
            names = []
            for npc_id in m.npcs:
                npc = self.ctx.npc.get(npc_id)
                names.append(npc["name"] if npc else npc_id)
            out.append("Di sini ada: " + ", ".join(names))

    def _cmd_explore(self, out):
        """Handler perintah explore: cek pertemuan dan mulai combat bila ada."""
        enemy = exploration_system.check_encounter(self.state, self.randomizer)
        if enemy is None:
            out.append("Kamu menjelajah, tetapi tidak ada yang mengancam.")
            return
        self._current_dialog = None
        self._talk_npc_id = None
        self._shop_npc_id = None
        out.append(f"Kamu bertemu {enemy.name}!")
        self._combat = start_combat(
            self.state.player,
            enemy,
            self.randomizer,
            skills=self.ctx.skills,
            loot_resolver=loot_system.roll_loot,
            items=self.state.items,
        )
        out.append(combat_view.render(self._combat))

    def _cmd_inventory(self, out):
        """Handler perintah inventory: tampilkan perlengkapan dan barang."""
        out.append(inventory_view.render(self.state.player, self.state.items))

    def _cmd_use(self, cmd, out):
        """Handler perintah use: pakai item konsumabel dari inventaris."""
        if not cmd.args:
            out.append("Gunakan: use <item>.")
            return
        item_id = cmd.args[0]
        entry = next(
            (e for e in self.state.player.inventory if e["id"] == item_id), None
        )
        if entry is None:
            out.append(f"Kamu tidak memiliki {item_id}.")
            return
        try:
            out.append(
                inventory_system.use_consumable(
                    self.state.player, entry, self.state
                )
            )
        except ValueError as e:
            out.append(str(e))

    def _cmd_equip(self, cmd, out):
        """Handler perintah equip: pasang item yang dimiliki pemain."""
        if not cmd.args:
            out.append("Gunakan: equip <item>.")
            return
        item = self.state.items.get(cmd.args[0])
        if item is None:
            out.append(f"Item tidak dikenal: {cmd.args[0]}.")
            return
        owned = item.id in self.state.player.equipped.values() or any(
            e["id"] == item.id for e in self.state.player.inventory
        )
        if not owned:
            out.append(f"Kamu tidak memiliki {item.name}.")
            return
        out.append(
            equipment_system.equip(
                self.state.player, item, items=self.state.items
            )
        )

    def _cmd_unequip(self, cmd, out):
        """Handler perintah unequip: lepas item dari satu slot."""
        if not cmd.args:
            out.append("Gunakan: unequip <slot>.")
            return
        out.append(
            equipment_system.unequip(
                self.state.player, cmd.args[0], items=self.state.items
            )
        )

    def _cmd_learn(self, cmd, out):
        """Handler perintah learn: belajar skill baru dengan Skill Point."""
        if not cmd.args:
            out.append("Gunakan: learn <skill>.")
            return
        skill_id = cmd.args[0]
        if skill_id not in self.ctx.skills:
            out.append(f"Skill tidak dikenal: {skill_id}.")
            return
        player = self.state.player
        class_id = player.class_id
        learnable = self.ctx.classes.get(class_id, {}).get(
            "learnable_skills", []
        )
        error = level_system.learn_skill(player, class_id, skill_id, learnable)
        if error:
            out.append(error)
        else:
            name = self.ctx.skills.get(skill_id, {}).get("name", skill_id)
            out.append(f"Kamu mempelajari skill {name}!")

    def _cmd_save(self, cmd, out):
        """Handler perintah save: simpan state ke path (dengan combat)."""
        if not cmd.args:
            out.append("Gunakan: save <path>.")
            return
        path = " ".join(cmd.args)
        try:
            save_manager.save_game(self.state, path, combat=self._combat)
        except save_manager.SaveError as e:
            raise  # Re-raise agar test bisa menangkap exception
        out.append(f"Permainan tersimpan di {path}.")

    def _cmd_load(self, cmd, out):
        """Handler perintah load: muat save (dilarang saat bertarung)."""
        if self._combat is not None:
            out.append("Tidak bisa memuat saat bertarung.")
            return
        path = " ".join(cmd.args) if cmd.args else "saves/slot1.json"
        try:
            msg = self.continue_game(path)
        except save_manager.SaveError as e:
            raise  # Re-raise agar test bisa menangkap exception
        out.append(msg or f"Permainan dimuat dari {path}.")

    def _cmd_quit(self):
        """Handler perintah quit: lemparkan GameQuit ke menu utama."""
        raise GameQuit()

    def _track_kills(self, state, out):
        """Catat jumlah kill musuh dan set flag killed_<id>_<n> untuk quest.

        Jumlah kill dihitung ulang dari flag `killed_<id>_<N>` yang sudah
        ada (bukan dari dict in-memory) agar tetap benar setelah save/load,
        karena hanya flag yang ikut disimpan.
        """
        s = self.state
        eid = state.enemy.id
        count = 1
        while f"killed_{eid}_{count}" in s.flags:
            count += 1
        s.kill_counts[eid] = count
        flag = f"killed_{eid}_{count}"
        s.flags[flag] = True
        msg = quest_engine.complete_requirement(s, "flag", flag)
        if msg and msg != "Tidak ada syarat yang sesuai.":
            out.append(msg)
        # Syarat quest kind kill_count native (§12.1 story-season1-spec).
        kc_msg = quest_engine.progress_requirement(
            s, "kill_count", eid, amount=1
        )
        if kc_msg and kc_msg != "Tidak ada syarat yang sesuai.":
            out.append(kc_msg)

    def _track_loot_flags(self, state, out):
        """Set quest_flag item saat item kunci quest didapat dari loot.

        Flag dibaca dari field `quest_flag` katalog item (data-driven),
        bukan dari dict hardcoded.
        """
        s = self.state
        owned = {e["id"] for e in s.player.inventory}
        for item_id in owned:
            item_def = s.items.get(item_id)
            if item_def is None:
                continue
            flag = getattr(item_def, "quest_flag", None)
            if flag and flag not in s.flags:
                s.flags[flag] = True
                msg = quest_engine.complete_requirement(s, "flag", flag)
                if msg and msg != "Tidak ada syarat yang sesuai.":
                    out.append(msg)

    def _track_collect_from_loot(self, state, out):
        """Perbarui syarat quest kind collect untuk item hasil loot."""
        s = self.state
        for entry in state.loot or []:
            owned = next(
                (
                    e["qty"]
                    for e in s.player.inventory
                    if e["id"] == entry["id"]
                ),
                0,
            )
            msg = quest_engine.progress_requirement(
                s, "collect", entry["id"], amount=owned
            )
            if msg and msg != "Tidak ada syarat yang sesuai.":
                out.append(msg)

    def _cmd_quests(self, out):
        """Handler perintah quests: daftar quest aktif dan progresnya."""
        p = self.state.player
        if not p.quests_active:
            out.append("Tidak ada quest aktif.")
            return
        for quest_id, info in p.quests_active.items():
            quest = self.state.quests.get(quest_id)
            title = quest["title"] if quest else quest_id
            total = len(quest["requirements"]) if quest else 0
            met = len(info.get("met", []))
            out.append(f"- {title} ({met}/{total})")

    def _dialog_select(self, cmd, out):
        """Terapkan pilihan dialog dan lanjutkan ke dialog berikutnya."""
        dialog = self._current_dialog
        choices = dialog_engine.available_choices(dialog, self.state)
        if cmd.index is None:
            out.append("Pilihan tidak valid.")
            return
        index = cmd.index - 1
        if index < 0 or index >= len(choices):
            out.append("Pilihan tidak valid.")
            return
        selected = choices[index]
        full_index = dialog["choices"].index(selected)
        next_id = dialog_engine.choose(self.state, dialog, full_index)
        # Syarat quest kind flag: tandai tiap flag yang diset dialog.
        for flag in selected.get("set_flags", []):
            msg = quest_engine.complete_requirement(self.state, "flag", flag)
            if msg and msg != "Tidak ada syarat yang sesuai.":
                out.append(msg)
        if next_id is None:
            self._end_dialog(out)
        else:
            self._current_dialog = self.ctx.dialogues.get(next_id, dialog)
            npc = (
                self.ctx.npc.get(self._talk_npc_id)
                if self._talk_npc_id
                else None
            )
            out.append(
                dialog_view.render(
                    self._current_dialog,
                    self.state,
                    npc_id=self._talk_npc_id,
                    npc_name=npc["name"] if npc else None,
                    has_shop=shop_system.has_shop(npc) if npc else False,
                )
            )

    def _end_dialog(self, out):
        """Akhiri dialog: proses syarat talk quest dan deteksi level-up."""
        out.append("Percakapan berakhir.")
        npc_id = self._talk_npc_id
        self._current_dialog = None
        self._talk_npc_id = None
        if npc_id is not None:
            msg = quest_engine.complete_requirement(self.state, "talk", npc_id)
            # Perbaikan: hanya tampilkan pesan jika quest benar-benar ter-update
            if msg and msg != "Tidak ada syarat yang sesuai.":
                out.append(msg)
            self._apply_pending_levels(out)

    def _combat_turn(self, cmd, out):
        """Jalankan satu giliran combat dari perintah pemain."""
        state = self._combat
        choice = cmd.args[0] if cmd.args else None
        try:
            free_turn = player_action(state, cmd.action, choice=choice)
        except ValueError as e:
            out.append(str(e))
            out.append(combat_view.render(state))
            return
        if not state.over and not free_turn and cmd.action != "escape":
            enemy_turn(state)
        if state.over:
            out.extend(self._finish_combat(state))
            self._combat = None
        else:
            out.append(combat_view.render(state))

    def _finish_combat(self, state):
        """Rangkum hasil combat: quest, log, level-up, dan pesan akhir."""
        out = []
        s = self.state
        if state.result == CombatResult.VICTORY:
            msg = quest_engine.complete_requirement(s, "enemy", state.enemy.id)
            # Perbaikan: hanya tampilkan pesan jika quest benar-benar ter-update
            if msg and msg != "Tidak ada syarat yang sesuai.":
                out.append(msg)
            self._track_kills(state, out)
            self._track_loot_flags(state, out)
            self._track_collect_from_loot(state, out)
            out.extend(state.log)
            self._apply_pending_levels(out)
            out.append("Kemenangan!")
        elif state.result == CombatResult.DEFEAT:
            out.extend(state.log)
            out.append("Kamu gugur dalam pertarungan...")
        elif state.result == CombatResult.ESCAPED:
            out.extend(state.log)
            out.append("Pertarungan berakhir: kamu melarikan diri.")
        else:
            out.append("Pertarungan berakhir.")
        return out

    def _check_level_up(self) -> list:
        """Cek apakah XP yang tersimpan sudah cukup untuk naik level.

        Tidak menambah XP baru — hanya mengolah XP yang sudah ada di
        player.xp; logika level-up ada di level_system.process_level_ups.
        """
        return level_system.process_level_ups(self.state.player)

    def _apply_pending_levels(self, out):
        """Deteksi level-up dan tunda bonus stat sampai pemain memilih."""
        levels = self._check_level_up()
        if levels:
            self._pending_levels = len(levels)
            out.append(
                f"Naik level! Kamu kini level {self.state.player.level}."
            )
            self._append_level_choice_prompt(out)

    def _append_level_choice_prompt(self, out):
        """Tampilkan daftar pilihan bonus level-up ke output."""
        out.append("Pilih bonus level-up (ketik angka):")
        for index, (key, _) in enumerate(level_system.LEVEL_CHOICES, start=1):
            out.append(f"  {index}. {level_system.choice_label(key)}")

    def _level_choice_select(self, cmd, out):
        """Terima pilihan bonus level-up dari pemain (angka 1..N)."""
        choices = level_system.LEVEL_CHOICES
        if cmd.action != "select" or cmd.index is None:
            out.append(
                f"Ketik angka pilihan bonus level-up (1-{len(choices)})."
            )
            self._append_level_choice_prompt(out)
            return
        index = cmd.index - 1
        if index < 0 or index >= len(choices):
            out.append("Pilihan tidak valid.")
            self._append_level_choice_prompt(out)
            return
        key = choices[index][0]
        level_system.apply_choice(self.state.player, key)
        self._pending_levels -= 1
        p = self.state.player
        p.hp = max_hp(p)
        p.mp = max_mp(p)
        out.append(f"Bonus dipilih: {level_system.choice_label(key)}.")
        if self._pending_levels > 0:
            out.append(f"Masih ada {self._pending_levels} bonus level-up lagi.")
            self._append_level_choice_prompt(out)
        else:
            out.append("HP dan MP dipulihkan penuh.")
