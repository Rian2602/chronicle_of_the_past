from src.core import input_handler, save_manager
import copy
from src.core.game_state import GameState
from src.core.randomizer import Randomizer
from src.engine import dialog_engine, event_engine, quest_engine
from src.engine.combat_engine import enemy_turn, player_action, start_combat
from src.models.combat_interfaces import CombatAction, CombatResult
from src.engine.time_engine import rest
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
    travel_system,
)
from src.ui import ascii_loader, combat_view, dialog_view, hud, inventory_view

_COMBAT_ACTIONS = {action.value for action in CombatAction}


class Game:
    def __init__(self, game_context, rng_seed=None):
        self.ctx = game_context
        self.state = GameState()
        self.state.rng_seed = rng_seed if rng_seed is not None else 20260803
        self.randomizer = Randomizer(self.state.rng_seed)
        self._current_dialog = None
        self._talk_npc_id = None
        self._combat = None

    def _wire(self):
        s = self.state
        s.world = {mid: Map(**data) for mid, data in self.ctx.maps.items()}
        s.enemies = {eid: Enemy(**data) for eid, data in self.ctx.enemies.items()}
        s.items = {iid: Item(**data) for iid, data in self.ctx.items.items()}
        s.quests = dict(self.ctx.quests)
        s.memories = list(self.ctx.memories)
        s.events = list(self.ctx.events)
        if s.current_map is None:
            s.current_map = s.world.get("village")

    def new_game(self, name, class_id):
        self._wire()
        self.state.player = self.ctx.create_player(name, class_id)
        self._current_dialog = None
        self._talk_npc_id = None
        self._combat = None
        assert self.state.player is not None
        lines = event_engine.process_events(self.state, self.randomizer)
        return "\n".join(lines) or "Kamu terbangun di Ashen Village."

    def continue_game(self, save_path):
        self.state = save_manager.load_game(save_path, self.ctx)
        self._wire()
        s = self.state
        map_id = s.current_map.id if hasattr(s.current_map, "id") else s.current_map
        s.current_map = s.world.get(map_id, s.world.get("village"))
        seed = s.rng_seed if s.rng_seed is not None else 20260803
        s.rng_seed = seed
        self.randomizer = Randomizer(seed)
        self._current_dialog = None
        self._talk_npc_id = None
        # Restore combat state jika ada
        self._combat = None
        if hasattr(s, "combat_data") and s.combat_data is not None:
            self._restore_combat(s.combat_data)
        if self.state.player is None:
            raise save_manager.SaveError("Save tidak lengkap (tanpa data pemain).")
        lines = event_engine.process_events(self.state, self.randomizer)
        return "\n".join(lines) or "Save dimuat."
    
    def _restore_combat(self, combat_data):
        """Restore combat state dari data yang di-load."""
        from src.models.combat_interfaces import CombatResult, CombatState, StatusEffect
        enemy_id = combat_data.get("enemy_id")
        if enemy_id is None or enemy_id not in self.state.enemies:
            return  # Tidak bisa restore tanpa enemy yang valid
        enemy = self.state.enemies[enemy_id]
        enemy = copy.copy(enemy)
        enemy.stats = dict(enemy.stats)
        enemy.stats.setdefault("max_hp", enemy.stats.get("hp", 1))
        # Set HP enemy sesuai yang tersimpan
        enemy.stats["hp"] = combat_data.get("enemy_hp", enemy.stats.get("hp", 1))
        # Rekonstruksi statuses dari dict ke StatusEffect objects
        restored_statuses = {}
        for target_id, effects in combat_data.get("statuses", {}).items():
            restored_statuses[target_id] = [
                StatusEffect(kind=eff["kind"], duration=eff["duration"], power=eff["power"])
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
        cmd = input_handler.parse_input(text)
        out = []
        if self._combat is not None and cmd.action in _COMBAT_ACTIONS:
            self._combat_turn(cmd, out)
        elif self._current_dialog is not None and cmd.action == "select":
            self._dialog_select(cmd, out)
        elif self._combat is not None and cmd.action not in ("save", "help", "inventory"):
            out.append("Tidak bisa saat bertarung.")
            out.append(combat_view.render(self._combat))
        else:
            self._dispatch(cmd, out)
        if self._combat is None:
            logs = event_engine.process_events(self.state, self.randomizer)
            out.extend(logs)
        return hud.render(self.state.player, self.state) + "\n\n" + "\n".join(out)

    def _dispatch(self, cmd, out):
        """Dispatch command to appropriate handler method."""
        action = cmd.action
        action_handlers = {
            "status": lambda: self._cmd_status(out),
            "help": lambda: self._cmd_help(out),
            "go": lambda: self._cmd_go(cmd, out),
            "rest": lambda: self._cmd_rest(out),
            "talk": lambda: self._cmd_talk(cmd, out),
            "look": lambda: self._cmd_look(out),
            "explore": lambda: self._cmd_explore(out),
            "inventory": lambda: self._cmd_inventory(out),
            "memories": lambda: self._cmd_memories(out),
            "use": lambda: self._cmd_use(cmd, out),
            "equip": lambda: self._cmd_equip(cmd, out),
            "unequip": lambda: self._cmd_unequip(cmd, out),
            "save": lambda: self._cmd_save(cmd, out),
            "quests": lambda: self._cmd_quests(out),
            "item": lambda: self._cmd_use_alias(cmd, out),
        }

        if action in action_handlers:
            action_handlers[action]()
        elif action == "select":
            out.append("Tidak ada dialog aktif.")
        elif action == "":
            out.append("Ketik 'help' untuk daftar perintah.")
        else:
            out.append(
                f"Perintah tidak dikenal: {cmd.action}. Ketik 'help' untuk bantuan."
            )

    def _cmd_use_alias(self, cmd, out):
        """Alias 'item <id>' → 'use <id>' di luar combat."""
        if not cmd.args:
            out.append("Gunakan: use <item>. (atau: item <id> saat bertarung)")
            return
        self._cmd_use(cmd, out)

    def _cmd_status(self, out):
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
                parts.append(f"{labels.get(slot, slot)}: {item.name if item else item_id}")
            out.append("Perlengkapan: " + ", ".join(parts))
        else:
            out.append("Perlengkapan: (kosong)")
        if p.learned_skills:
            out.append("Skill: " + ", ".join(p.learned_skills))
        location = self.state.current_map.name if self.state.current_map else "-"
        out.append(f"Lokasi: {location}")

    def _cmd_help(self, out):
        out.append("Perintah: status, help, go <peta>, rest, talk <id_npc>, look, explore,")
        out.append("inventory, memories, use <item>, equip <item>, unequip <slot>,")
        out.append("save <path>, quests, quit")
        out.append("Saat bertarung: attack, skill <id>, magic <id>, item <id>, observe, escape, defend")
        out.append("Saat dialog: ketik nomor pilihan (mis. 1)")

    def _cmd_memories(self, out):
        p = self.state.player
        if not p.memories:
            out.append("Kamu belum memiliki kenangan.")
            return
        out.append("Kenangan:")
        for memory in p.memories:
            out.append(f"- {memory['title']}: {memory['text']}")

    def _cmd_go(self, cmd, out):
        if not cmd.args:
            out.append("Gunakan: go <nama peta>.")
            return
        self._current_dialog = None
        self._talk_npc_id = None
        try:
            out.append(travel_system.travel(self.state, cmd.args[0]))
        except ValueError as e:
            out.append(str(e))

    def _cmd_rest(self, out):
        rest(self.state)
        out.append(f"Kamu beristirahat hingga pagi. Kini Hari {self.state.day}.")

    def _cmd_talk(self, cmd, out):
        if not cmd.args:
            out.append("Gunakan: talk <nama NPC>.")
            return
        npc_id = cmd.args[0]
        npc = self.ctx.npc.get(npc_id)
        if npc is None:
            out.append(f"NPC tidak dikenal: {npc_id}.")
            return
        m = self.state.current_map
        if m is None or npc.get("location") != m.id:
            out.append(f"{npc['name']} tidak ada di sini.")
            return
        if not npc.get("dialogs"):
            out.append(f"{npc['name']} tidak punya dialog.")
            return
        dialog = self.ctx.dialogues.get(npc["dialogs"][0])
        if dialog is None:
            out.append(f"{npc['name']} tidak punya dialog.")
            return
        self._current_dialog = dialog
        self._talk_npc_id = npc_id
        # Perbaikan: tampilkan nama NPC yang benar (bukan ID)
        out.append(dialog_view.render(dialog, self.state, npc_id=npc_id, npc_name=npc["name"]))

    def _cmd_look(self, out):
        m = self.state.current_map
        if m is None:
            out.append("Kamu tidak berada di peta mana pun.")
            return
        try:
            out.append(ascii_loader.load(m.ascii_art))
        except Exception:
            pass
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
        enemy = exploration_system.check_encounter(self.state, self.randomizer)
        if enemy is None:
            out.append("Kamu menjelajah, tetapi tidak ada yang mengancam.")
            return
        self._current_dialog = None
        self._talk_npc_id = None
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
        out.append(inventory_view.render(self.state.player, self.state.items))

    def _cmd_use(self, cmd, out):
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
            out.append(inventory_system.use_consumable(self.state.player, entry, self.state))
        except ValueError as e:
            out.append(str(e))

    def _cmd_equip(self, cmd, out):
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
        out.append(equipment_system.equip(self.state.player, item, items=self.state.items))

    def _cmd_unequip(self, cmd, out):
        if not cmd.args:
            out.append("Gunakan: unequip <slot>.")
            return
        out.append(equipment_system.unequip(self.state.player, cmd.args[0], items=self.state.items))

    def _cmd_save(self, cmd, out):
        if not cmd.args:
            out.append("Gunakan: save <path>.")
            return
        path = " ".join(cmd.args)
        try:
            save_manager.save_game(self.state, path, combat=self._combat)
        except save_manager.SaveError as e:
            out.append(str(e))
            return
        out.append(f"Permainan tersimpan di {path}.")

    def _cmd_quests(self, out):
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
        if next_id is None:
            self._end_dialog(out)
        else:
            self._current_dialog = self.ctx.dialogues.get(next_id, dialog)
            npc = self.ctx.npc.get(self._talk_npc_id) if self._talk_npc_id else None
            out.append(
                dialog_view.render(
                    self._current_dialog,
                    self.state,
                    npc_id=self._talk_npc_id,
                    npc_name=npc["name"] if npc else None,
                )
            )

    def _end_dialog(self, out):
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
        out = []
        s = self.state
        if state.result == CombatResult.VICTORY:
            msg = quest_engine.complete_requirement(s, "enemy", state.enemy.id)
            # Perbaikan: hanya tampilkan pesan jika quest benar-benar ter-update
            if msg and msg != "Tidak ada syarat yang sesuai.":
                out.append(msg)
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

    def _apply_pending_levels(self, out):
        levels = level_system.gain_xp(self.state.player, 0)
        if levels:
            self._apply_level_ups(levels)
            out.append(f"Naik level! Kamu kini level {self.state.player.level}.")

    def _apply_level_ups(self, levels):
        p = self.state.player
        for _ in levels:
            # gain_xp sudah menaikkan level; di sini hanya bonus base + pilihan HP
            p.attribute_bonuses["hp"] = p.attribute_bonuses.get("hp", 0) + 5
            p.attribute_bonuses["mp"] = p.attribute_bonuses.get("mp", 0) + 3
            # Auto-apply pilihan HP sebagai default (bisa dikembangkan dengan input user nanti)
            level_system.apply_choice(p, "hp")
            p.hp = max_hp(p)
            p.mp = max_mp(p)
