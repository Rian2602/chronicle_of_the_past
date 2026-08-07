"""Engine combat turn-based: elemen, formula, status, dan battle.

Acuan desain: GDD §6 (combat), §16 (status), §17.2 (formula stat).
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.core.utils import load_json_dir
from src.models.combatant import Combatant
from src.models.enemy import Enemy
from src.models.technique import Technique

TECHNIQUE_DIR = Path(__file__).resolve().parents[2] / "data" / "techniques"
ENEMY_DIR = Path(__file__).resolve().parents[2] / "data" / "enemies"


ELEMENT_CYCLE = ("metal", "wood", "earth", "water", "fire")
ELEMENT_ADVANTAGE = {
    "metal": "wood",
    "wood": "earth",
    "earth": "water",
    "water": "fire",
    "fire": "metal",
}

STATUS_IDS = {
    "poison",
    "burn",
    "bleed",
    "stun",
    "freeze",
    "charm",
    "slow",
    "seal",
    "weaken",
    "barrier",
    "strengthen",
    "haste",
    "qi_flow",
}
CONTROL_STATUSES = ("stun", "freeze", "charm")
DOT_STATUSES = ("poison", "burn", "bleed")
STATUS_DURATIONS = {
    "poison": 3,
    "burn": 3,
    "bleed": 2,
    "stun": 1,
    "freeze": 2,
    "charm": 2,
    "slow": 3,
    "seal": 2,
    "weaken": 3,
    "barrier": 3,
    "strengthen": 3,
    "haste": 3,
    "qi_flow": 3,
}

ATTACK_QI_GAIN = 1


def load_techniques(data_dir: Path = TECHNIQUE_DIR) -> list[Technique]:
    """Muat semua teknik dari data/techniques/, urut berdasarkan id."""
    return load_json_dir(data_dir, model_cls=Technique)


def load_enemies(data_dir: Path = ENEMY_DIR) -> list[Enemy]:
    """Muat semua musuh dari data/enemies/, urut berdasarkan id."""
    return load_json_dir(data_dir, model_cls=Enemy)


def element_multiplier(attacker: str, defender: str) -> float:
    """Multiplier elemen: 1.5 unggul, 0.7 kalah, 1.0 netral/sama (§6.2)."""
    if attacker == "netral" or defender == "netral":
        return 1.0
    if ELEMENT_ADVANTAGE.get(attacker) == defender:
        return 1.5
    if ELEMENT_ADVANTAGE.get(defender) == attacker:
        return 0.7
    return 1.0


def compute_turn_order(combatants: list[Combatant]) -> list[Combatant]:
    """Urutan giliran: agility tertinggi duluan, tetap sepanjang battle."""
    return sorted(
        combatants,
        key=lambda unit: unit.stats.get("agility", 0),
        reverse=True,
    )


def crit_chance(agility: int) -> float:
    """Peluang kritikal: 5% + agility x 0.1%, cap 25% (§6.4, §17.2)."""
    return min(0.25, 0.05 + agility * 0.001)


def dodge_chance(agility: int) -> float:
    """Peluang menghindar: 5% + agility x 0.1%, cap 30% (§6.4, §17.2)."""
    return min(0.30, 0.05 + agility * 0.001)


def miss_rate(agility: int) -> float:
    """Tingkat meleset: 20% - agility x 0.1%, minimum 5% (§6.4, §17.2)."""
    return max(0.05, 0.20 - agility * 0.001)


def _damage_multiplier(rng: Any) -> float:
    """Faktor acak damage 0.9-1.1 (§6.4)."""
    return 0.9 + rng.random() * 0.2


def physical_damage(
    attack: int, defense: int, element_mult: float, rng: Any
) -> int:
    """Damage fisik: max(1, attack - defense/2) x mult x rand(0.9-1.1)."""
    base = max(1.0, attack - defense / 2)
    return max(1, int(round(base * element_mult * _damage_multiplier(rng))))


def technique_damage(
    power: int, stat_inti: int, resist: int, element_mult: float, rng: Any
) -> int:
    """Damage teknik: max(1, power + stat x 0.5 - resist) x mult x rand."""
    base = max(1.0, power + stat_inti * 0.5 - resist)
    return max(1, int(round(base * element_mult * _damage_multiplier(rng))))


def apply_status(
    combatant: Combatant,
    status_id: str,
    duration: int | None = None,
    power: int = 0,
) -> bool:
    """Terapkan status; dot/buff sejenis tidak menumpuk (§16).

    Boss kebal terhadap kontrol (stun/freeze/charm). Durasi default dari
    tabel §16. Mengembalikan True bila status aktif (baru atau refresh).
    """
    if status_id not in STATUS_IDS:
        raise ValueError(f"status tidak dikenal: {status_id}")
    if combatant.is_boss and status_id in CONTROL_STATUSES:
        return False
    turns = duration if duration is not None else STATUS_DURATIONS[status_id]
    combatant.statuses[status_id] = {"turns": turns, "power": power}
    return True


def effective_stats(combatant: Combatant) -> dict[str, int]:
    """Stat efektif dengan modifikasi status (§16: slow/weaken/buff)."""
    stats = dict(combatant.stats)
    if "weaken" in combatant.statuses:
        stats["attack"] = int(stats["attack"] * 0.75)
    if "strengthen" in combatant.statuses:
        stats["attack"] = int(stats["attack"] * 1.25)
    if "slow" in combatant.statuses:
        stats["agility"] = int(stats["agility"] * 0.70)
    if "haste" in combatant.statuses:
        stats["agility"] = int(stats["agility"] * 1.25)
    if "barrier" in combatant.statuses:
        stats["defense"] = int(stats["defense"] * 1.30)
    if "freeze" in combatant.statuses:
        stats["defense"] = int(stats["defense"] * 1.50)
    return stats


def tick_statuses(combatant: Combatant) -> list[str]:
    """Proses efek dot di awal giliran; kembalikan pesan peristiwa (§16)."""
    events: list[str] = []
    for status_id, info in list(combatant.statuses.items()):
        if status_id == "poison":
            damage = max(1, int(combatant.hp_max * 0.04))
        elif status_id in DOT_STATUSES:
            damage = max(1, info.get("power", 1))
        else:
            damage = 0
        if damage:
            combatant.take_damage(damage, defend_reduces=False)
            message = f"{combatant.name} menderita {status_id} ({damage} HP)."
            events.append(message)
        info["turns"] -= 1
        if info["turns"] <= 0:
            del combatant.statuses[status_id]
    return events


@dataclass
class ActionResult:
    """Hasil satu aksi dalam pertarungan (GDD §6)."""

    action: str
    attacker: str
    target: str | None = None
    damage: int = 0
    crit: bool = False
    missed: bool = False
    dodged: bool = False
    qi_cost: int = 0
    statuses: tuple[str, ...] = ()
    escaped: bool = False


class Battle:
    """Pertarungan turn-based: urutan tetap, status, dan alur (GDD §6, §16)."""

    def __init__(
        self,
        allies: list[Combatant],
        enemies: list[Combatant],
        techniques: list[Technique] | dict[str, Technique] | None = None,
        rng: Any = None,
    ) -> None:
        """Mulai pertarungan: hitung urutan giliran sekali dari agility."""
        self.allies = allies
        self.enemies = enemies
        self.techniques: dict[str, Technique] = {}
        if isinstance(techniques, dict):
            self.techniques = dict(techniques)
        else:
            self.techniques = {
                technique.id: technique for technique in (techniques or [])
            }
        self._rng = rng if rng is not None else random
        self.turn_order = compute_turn_order([*allies, *enemies])
        self.turn_index = 0
        self.log: list[str] = []
        self.over = False
        self.winner: str | None = None
        self.escaped = False
        self._may_act = False

    @property
    def current(self) -> Combatant:
        """Unit yang sedang mengambil giliran."""
        return self.turn_order[self.turn_index]

    def observe(self) -> list[dict[str, Any]]:
        """Observe gratis: lihat HP/qi/elemen/status musuh (§6.1)."""
        return [
            {
                "name": enemy.name,
                "hp": enemy.hp,
                "hp_max": enemy.hp_max,
                "qi": enemy.qi,
                "element": enemy.element,
                "statuses": dict(enemy.statuses),
            }
            for enemy in self._alive(self.enemies)
        ]

    def _missed_result(
        self,
        unit: Combatant,
        target: Combatant,
        technique: Technique,
        action: str,
    ) -> ActionResult:
        """ActionResult untuk aksi yang meleset."""
        return ActionResult(
            action,
            unit.name,
            target.name,
            qi_cost=technique.qi_cost,
            missed=True,
        )

    def _dodged_result(
        self,
        unit: Combatant,
        target: Combatant,
        technique: Technique,
        action: str,
    ) -> ActionResult:
        """ActionResult untuk aksi yang dihindari target."""
        return ActionResult(
            action,
            unit.name,
            target.name,
            qi_cost=technique.qi_cost,
            dodged=True,
        )

    def step(self, action: str) -> ActionResult | None:
        """Jalankan aksi pemain untuk unit sekutu saat ini (GDD §18.3).

        Aksi divalidasi sebelum awal giliran: aksi tidak valid ditolak tanpa
        mengubah state (tanpa regen/tick), jadi percobaan ulang tidak
        menggandakan efek awal giliran.
        """
        if self._side(self.current) != "allies":
            raise RuntimeError("bukan giliran sekutu")
        self._validate_player_action(action)
        return self._step(action)

    def _validate_player_action(self, action: str) -> None:
        """Validasi aksi pemain sebelum awal giliran dijalankan."""
        if not action.startswith("technique:"):
            return
        unit = self.current
        technique_id = action.split(":", 1)[1]
        technique = self._check_technique_valid(unit, technique_id)
        if unit.qi < technique.qi_cost:
            raise ValueError("qi tidak cukup")

    def step_enemy(self) -> ActionResult | None:
        """Jalankan giliran musuh otomatis sesuai behavior (GDD §11)."""
        if self._side(self.current) != "enemies":
            raise RuntimeError("bukan giliran musuh")
        return self._step(action=None)

    def _step(self, action: str | None) -> ActionResult | None:
        """Proses satu giliran penuh: awal giliran, aksi, dan pergantian.

        Aksi musuh (None) dipilih AI setelah awal giliran, sehingga RNG
        tidak terbuang untuk musuh yang melewatkan giliran (kontrol).
        """
        if self.over:
            raise RuntimeError("pertarungan sudah berakhir")
        self._begin_turn()
        self._check_victory()
        if self.over:
            return None
        result: ActionResult | None = None
        if self._may_act:
            if action is None:
                action = self._enemy_choice()
            result = self._perform(action)
        self._check_victory()
        if not self.over:
            self._advance()
        return result

    def _begin_turn(self) -> None:
        """Awal giliran: reset defend, regen qi, tick status, cek kontrol."""
        unit = self.current
        unit.defending = False
        controlled = self._control_of(unit)
        regen = 0 if "seal" in unit.statuses else unit.qi_regen
        if "qi_flow" in unit.statuses:
            regen = int(regen * 1.5)
        unit.qi = min(unit.qi_max, unit.qi + regen)
        self.log.extend(tick_statuses(unit))
        if not unit.is_alive:
            # BUG-21: unit yang KO oleh DoT di awal giliran tidak boleh
            # menyerang — giliran dilewati, _advance mencari unit hidup.
            self._may_act = False
            return
        if controlled == "charm":
            allies = [
                member
                for member in self._side_units(unit)
                if member is not unit
            ]
            target = allies[0]
            self._resolve_physical(unit, target, log_verb="terpesona menyerang")
            self._may_act = False
            return
        if controlled:
            message = f"{unit.name} terkena {controlled}, melewatkan giliran."
            self.log.append(message)
            self._may_act = False
            return
        self._may_act = True

    def _control_of(self, unit: Combatant) -> str | None:
        """Status kontrol aktif; charm hanya efektif bila ada sekutu (§16)."""
        for control in CONTROL_STATUSES:
            if control not in unit.statuses:
                continue
            if control == "charm":
                allies = [
                    member
                    for member in self._side_units(unit)
                    if member is not unit
                ]
                if not allies:
                    continue
            return control
        return None

    def _perform(self, action: str) -> ActionResult:
        """Jalankan aksi sesuai string: attack/defend/escape/technique:<id>."""
        if action == "attack":
            return self.attack()
        if action == "defend":
            return self.defend()
        if action == "escape":
            return self.escape()
        if action.startswith("technique:"):
            return self.technique(action.split(":", 1)[1])
        raise ValueError(f"aksi tidak dikenal: {action}")

    def attack(self) -> ActionResult:
        """Serangan dasar: netral x1.0 dan mengisi sedikit qi (§18.3)."""
        unit = self.current
        result = self._resolve_physical(unit, self._first_target(unit))
        unit.qi = min(unit.qi_max, unit.qi + ATTACK_QI_GAIN)
        return result

    def _resolve_physical(
        self,
        unit: Combatant,
        target: Combatant,
        log_verb: str = "menyerang",
    ) -> ActionResult:
        """Hitung serangan fisik: miss, dodge, crit, dan damage (§6.4)."""
        stats = effective_stats(unit)
        target_stats = effective_stats(target)
        if self._rng.random() < miss_rate(stats["agility"]):
            return ActionResult("attack", unit.name, target.name, missed=True)
        if self._rng.random() < dodge_chance(target_stats["agility"]):
            return ActionResult("attack", unit.name, target.name, dodged=True)
        crit = self._rng.random() < crit_chance(stats["agility"])
        multiplier = element_multiplier(unit.element, target.element)
        damage = physical_damage(
            stats["attack"], target_stats["defense"], multiplier, self._rng
        )
        if crit:
            damage = int(damage * 1.8)
        actual = target.take_damage(damage)
        message = f"{unit.name} {log_verb} {target.name} ({actual} damage)."
        self.log.append(message)
        return ActionResult(
            "attack", unit.name, target.name, damage=actual, crit=crit
        )

    def defend(self) -> ActionResult:
        """Bertahan: damage masuk -50% hingga giliran berikutnya (§6.1)."""
        self.current.defending = True
        message = f"{self.current.name} bersiap bertahan."
        self.log.append(message)
        return ActionResult("defend", self.current.name)

    def escape(self) -> ActionResult:
        """Kabur dari pertarungan; selalu gagal melawan bos (§6.1, §11)."""
        if any(enemy.is_boss for enemy in self._alive(self.enemies)):
            self.log.append("Tidak bisa kabur: bos menghadang!")
            return ActionResult("escape", self.current.name, escaped=False)
        self.escaped = True
        self.over = True
        message = f"{self.current.name} kabur dari pertarungan."
        self.log.append(message)
        return ActionResult("escape", self.current.name, escaped=True)

    def technique(self, technique_id: str) -> ActionResult:
        """Gunakan teknik: bayar qi, hitung damage & efek status (§6.3)."""
        unit = self.current
        technique = self._check_technique_valid(unit, technique_id)
        if unit.qi < technique.qi_cost:
            raise ValueError("qi tidak cukup")
        target = self._first_target(unit)
        unit.qi -= technique.qi_cost
        stats = effective_stats(unit)
        target_stats = effective_stats(target)
        if self._rng.random() < miss_rate(stats["agility"]):
            return self._missed_result(unit, target, technique, "technique")
        if self._rng.random() < dodge_chance(target_stats["agility"]):
            return self._dodged_result(unit, target, technique, "technique")
        crit = self._rng.random() < crit_chance(stats["agility"])
        if technique.is_physical:
            stat_inti = stats["attack"]
        else:
            stat_inti = stats["intelligence"]
        multiplier = element_multiplier(technique.element, target.element)
        damage = technique_damage(
            technique.power,
            stat_inti,
            target_stats["defense"],
            multiplier,
            self._rng,
        )
        if crit:
            damage = int(damage * 1.8)
        actual = target.take_damage(damage)
        applied: list[str] = []
        for effect in technique.effects:
            status_id = effect["status"]
            if apply_status(
                target,
                status_id,
                effect.get("duration"),
                effect.get("power", 0),
            ):
                applied.append(status_id)
        message = (
            f"{unit.name} memakai {technique.name} "
            f"({actual} damage ke {target.name})."
        )
        self.log.append(message)
        return ActionResult(
            "technique",
            unit.name,
            target.name,
            damage=actual,
            crit=crit,
            qi_cost=technique.qi_cost,
            statuses=tuple(applied),
        )

    def _enemy_choice(self) -> str:
        """Pilih aksi AI: skill terkuat yang terjangkau atau serangan dasar."""
        unit = self.current
        usable = [
            technique
            for technique in self._usable_techniques(unit)
            if technique.qi_cost <= unit.qi
        ]
        if not usable:
            return "attack"
        if unit.behavior == "aggressive" or self._rng.random() < 0.5:
            best = max(usable, key=lambda technique: technique.power)
            return f"technique:{best.id}"
        return "attack"

    def _check_technique_valid(
        self, unit: Combatant, technique_id: str
    ) -> Technique:
        """Periksa teknik dikenal, dikuasai, dan tidak diblokir seal."""
        technique = self.techniques.get(technique_id)
        if technique is None:
            raise ValueError(f"teknik tidak dikenal: {technique_id}")
        if technique_id not in unit.skills:
            raise ValueError(f"{unit.name} tidak menguasai {technique_id}")
        if "seal" in unit.statuses:
            raise ValueError("qi terkunci: teknik diblokir")
        return technique

    def _usable_techniques(self, unit: Combatant) -> list[Technique]:
        """Teknik yang bisa dipakai unit (terkunci bila terkena seal)."""
        if "seal" in unit.statuses:
            return []
        return [
            self.techniques[skill_id]
            for skill_id in unit.skills
            if skill_id in self.techniques
        ]

    def _side(self, unit: Combatant) -> str:
        """Sisi unit: allies atau enemies (perbandingan identitas)."""
        if any(unit is member for member in self.allies):
            return "allies"
        if any(unit is member for member in self.enemies):
            return "enemies"
        raise ValueError("unit bukan bagian dari pertarungan")

    def _side_units(self, unit: Combatant) -> list[Combatant]:
        """Kembalikan anggota satu sisi dengan unit (yang masih hidup)."""
        if self._side(unit) == "allies":
            return self._alive(self.allies)
        return self._alive(self.enemies)

    def _opponents(self, unit: Combatant) -> list[Combatant]:
        """Kembalikan lawan unit yang masih hidup."""
        if self._side(unit) == "allies":
            return self._alive(self.enemies)
        return self._alive(self.allies)

    def _first_target(self, unit: Combatant) -> Combatant:
        """Lawan pertama yang hidup; dengan banyak lawan dipilih acak.

        Backward-compatible: 1 lawan ⇒ hasil identik dengan perilaku lama.
        Implementasi memakai indexing rng.random() agar kompatibel dengan
        RNG uji bertipe _FixedRng yang hanya menyediakan random().

        Note:
            # ponytail: target acak mengabaikan status charm (§16);
            upgrade saat charm memengaruhi penargetan musuh.
        """
        opponents = self._alive(self._opponents(unit))
        if not opponents:
            raise RuntimeError("tidak ada lawan yang hidup")
        if len(opponents) == 1:
            return opponents[0]
        index = min(
            len(opponents) - 1,
            int(self._rng.random() * len(opponents)),
        )
        return opponents[index]

    def _alive(self, units: list[Combatant]) -> list[Combatant]:
        """Kembalikan unit yang belum KO."""
        return [unit for unit in units if unit.is_alive]

    def _advance(self) -> None:
        """Pindah ke unit hidup berikutnya dalam urutan tetap (§6.1)."""
        size = len(self.turn_order)
        for step_count in range(1, size + 1):
            index = (self.turn_index + step_count) % size
            if self.turn_order[index].is_alive:
                self.turn_index = index
                return
        self._check_victory()

    def pass_turn(self) -> None:
        """Akhiri giliran unit aktif tanpa aksi engine (BUG-31).

        Dipanggil GameSession setelah aksi non-engine (pakai item di
        battle) diterapkan, agar aksi tersebut memakai giliran pemain
        (GDD §18.3 — hanya observe yang gratis).
        """
        self._advance()

    def _check_victory(self) -> None:
        """Akhiri pertarungan bila satu pihak tidak punya unit hidup."""
        if self.over:
            return
        if not self._alive(self.enemies):
            self.over = True
            self.winner = "allies"
        elif not self._alive(self.allies):
            self.over = True
            self.winner = "enemies"
