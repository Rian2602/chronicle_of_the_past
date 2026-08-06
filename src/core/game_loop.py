"""Alur permainan utama (GDD §18, §19.1, §20.4, §23).

GameSession memisahkan logika murni (diuji penuh) dari UI Textual:
App hanya memanggil metode ini dan menampilkan hasilnya.
"""

from __future__ import annotations

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
from src.engine.event import load_events, process_events
from src.models.combatant import (
    Combatant,
    combatant_from_enemy,
    combatant_from_player,
)
from src.models.enemy import Enemy
from src.models.player import Player

CULTIVATE_INSIGHT = 10
CULTIVATE_HOURS = 3
REST_HOUR = 8
START_LOCATION = "village_emberfall"
FOREST_ID = "ashfall_forest"
# Pertarungan MVP: Bandit Perbatasan (kalahkan-able oleh pemain tier 0).
# Serigala Qi tetap di data sebagai musuh lebih kuat untuk Fase 1.
FOREST_ENEMY = "bandit_perbatasan"
UNAVAILABLE = "Belum tersedia (Fase 1)."

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
    "cultivate",
    "breakthrough",
    "rest",
    "save",
    "load",
    "quit",
}


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
            "  go <lokasi> look cultivate breakthrough rest",
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
        return [
            f"{player.name} — {tier_name}",
            f"Lokasi: {self.state.location} | "
            f"Hari {self.state.time.day}, jam {self.state.time.hour:02d}",
            f"HP {player.hp}/{player.hp_max} | Qi {player.qi}/{player.qi_max}",
            f"Insight {player.insight} | Gold {player.gold}"
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
        items = self.state.inventory.get("items", {})
        if not items:
            return ["Tasmu kosong."]
        return [f"Tas: {items}"]

    def _cmd_quests(self, _command: Command) -> list[str]:
        if self.state.quests.started or self.state.quests.done:
            return [
                "Aktif: " + ", ".join(self.state.quests.started) or "-",
                "Selesai: " + ", ".join(self.state.quests.done) or "-",
            ]
        return ["Tidak ada quest aktif."]

    def _cmd_memories(self, _command: Command) -> list[str]:
        """Tampilkan echo memori yang terkumpul (GDD §15.3 grant_memory)."""
        if not self.state.memories:
            return ["Tidak ada memori."]
        return ["Echo memori:"] + [
            f"  - {memory_id}" for memory_id in self.state.memories
        ]

    def _cmd_party(self, _command: Command) -> list[str]:
        return [f"Timmu hanya {self.state.player.name} (rekan: Fase 1)."]

    def _cmd_go(self, command: Command) -> list[str]:
        if not command.args:
            return ["Tujuan? Contoh: go ashfall_forest"]
        location = command.args[0]
        if location == START_LOCATION:
            self.state.location = location
            return [f"Kamu kembali ke {location}."] + self._run_events()
        flag = f"map_{location}_unlocked"
        if self.state.flags.get(flag):
            self.state.location = location
            return [f"Kamu tiba di {location}."] + self._run_events()
        return [f"Lokasi belum terbuka: {location}."]

    def _cmd_look(self, _command: Command) -> list[str]:
        location = self.state.location
        if location == FOREST_ID:
            if self.state.flags.get("ashfall_forest_cleared"):
                return ["Hutan sunyi. Tidak ada musuh lagi."]
            return self._start_battle(FOREST_ENEMY)
        if location == START_LOCATION:
            return [
                "Desa Emberfall yang tenang di pagi hari.",
                "Hutan Perbatasan (ashfall_forest) tampak di kejauhan.",
            ]
        # Lokasi lain (mis. ruin_shrine hasil event unlock): deskripsi jujur
        # tanpa meniru desa; konten per-lokasi menyusul bersama data maps.
        return [
            f"Kamu di {location}. Tempat ini sunyi; tidak ada yang menonjol.",
        ]

    def _cmd_cultivate(self, _command: Command) -> list[str]:
        player = self.state.player
        player.add_insight(CULTIVATE_INSIGHT)
        self._advance_hours(CULTIVATE_HOURS)
        return [
            "Kamu bermeditasi menyerap qi langit-bumi...",
            f"Insight +{CULTIVATE_INSIGHT} (total {player.insight}).",
        ] + self._run_events()

    def _cmd_rest(self, _command: Command) -> list[str]:
        player = self.state.player
        self.state.time.day += 1
        self.state.time.hour = REST_HOUR
        player.hp = player.hp_max
        player.qi = player.qi_max
        healed = player.is_injured
        player.advance_day()
        # Event diproses sebelum autosave agar efeknya ikut tersimpan.
        event_lines = self._run_events()
        autosave_save(self.state, self.save_dir)
        message = "Kamu beristirahat hingga pagi. HP dan qi pulih penuh."
        if healed:
            message += " Cedera membaik."
        return [message, "Permainan tersimpan otomatis."] + event_lines

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
        # Event diproses sebelum autosave agar efeknya ikut tersimpan.
        event_lines = self._run_events()
        autosave_save(self.state, self.save_dir)
        if result.success:
            return [
                f"BREAKTHROUGH SUKSES! Kamu kini {result.tier_id} "
                f"({result.rate}%).",
                "Permainan tersimpan otomatis.",
            ] + event_lines
        note = ""
        if result.inner_demon:
            note = " Bayangan batin mengintai (pertarungan inner demon "
            note += "menyusul Fase 1)."
        return [
            "Breakthrough GAGAL. Tubuhmu terluka "
            f"({result.injury_days} hari cedera, stat -25%).{note}",
            "Permainan tersimpan otomatis.",
        ] + event_lines

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

    def _advance_hours(self, hours: int) -> None:
        """Majukan jam game dengan rollover ke hari berikutnya (§19.2)."""
        self.state.time.hour += hours
        while self.state.time.hour >= 24:
            self.state.time.hour -= 24
            self.state.time.day += 1

    def _run_events(self) -> list[str]:
        """Proses event data-driven setelah momen mutasi state (GDD §15.4).

        Dipanggil setelah go / cultivate / rest / breakthrough — sekali
        per momen. Kembalikan baris narasi event untuk ditampilkan UI.
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
        self._ally = ally
        self._enemy = enemy
        self.battle = Battle(
            allies=[ally],
            enemies=[combatant_from_enemy(enemy)],
            techniques=techniques,
            rng=self._rng,
        )
        return [
            f"{enemy.name} muncul dari bayangan!",
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
        return BattleFrame(
            log=list(battle.log),
            over=battle.over,
            victory=victory,
            escaped=battle.escaped,
            player_turn=not battle.over and self._is_player_turn(),
            enemies=battle.observe(),
            error=error,
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

    def _finish_battle(self) -> None:
        """Tutup pertarungan: reward, tulis balik hp/qi, pemulihan KO."""
        battle = self.battle
        player = self.state.player
        ally = self._ally
        enemy = self._enemy
        if ally is not None:
            player.hp = min(ally.hp, player.hp_max)
            player.qi = min(ally.qi, player.qi_max)
        if battle.winner == "allies":
            rewards = enemy.rewards if enemy is not None else {}
            player.add_insight(rewards.get("insight", 0))
            player.gold += rewards.get("gold", 0)
            self.state.flags[f"{self.state.location}_cleared"] = True
            battle.log.append(
                f"Menang! Insight +{rewards.get('insight', 0)}, "
                f"Gold +{rewards.get('gold', 0)}."
            )
        elif battle.winner == "enemies":
            # KO: pulih otomatis setelah pertarungan (GDD §20.4).
            player.hp = player.hp_max
            battle.log.append(
                "Kamu tersungkur... dan sadar kembali dengan luka menganga."
            )
