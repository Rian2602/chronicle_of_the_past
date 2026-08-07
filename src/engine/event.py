"""Engine event data-driven: gating cerita, unlock peta, narasi (GDD §15).

Semua gating (quest, unlock peta, echo memori) lewat event — bukan
hardcode di kode (§24.1 #16). Event diproses setelah momen mutasi state
(go / cultivate / rest / breakthrough), sekali per momen (§15.4).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.core.state import GameState
from src.engine.story import calculate_ending
from src.models.party import load_companion

EVENT_DIR = Path(__file__).resolve().parents[2] / "data" / "events"

TRIGGER_KINDS = {
    "flag",
    "quest_done",
    "tier_reached",
    "location_entered",
    "day_passed",
    "reputation_reached",
}
FLAG_OPERATORS = {"EQUALS", "NOT_EQUALS", "MISSING"}
ACTION_KINDS = {
    "set_flag",
    "clear_flag",
    "unlock_map",
    "start_quest",
    "grant_memory",
    "grant_item",
    "grant_gold",
    "change_reputation",
    "start_dialog",
    "add_companion",
    "log",
    "prompt_choice",
    "add_ending_points",
    "calculate_ending",
}


@dataclass(frozen=True)
class GameEvent:
    """Event naratif data-driven (skema §15.1)."""

    id: str
    trigger: list[dict[str, Any]]
    actions: list[dict[str, Any]]
    once: bool = True


@dataclass
class EventResult:
    """Hasil satu pass evaluasi event untuk UI/pemain."""

    logs: list[str] = field(default_factory=list)
    fired: list[str] = field(default_factory=list)
    dialogs: list[str] = field(default_factory=list)


def load_events(data_dir: Path = EVENT_DIR) -> list[GameEvent]:
    """Muat semua event dari data/events/ urut abjad nama file (§15.4)."""
    events: list[GameEvent] = []
    for path in sorted(data_dir.glob("*.json")):
        raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        events.append(GameEvent(**raw))
    return events


def _match_trigger(condition: dict[str, Any], state: GameState) -> bool:
    """Cocokkan satu kondisi trigger terhadap state (§15.2).

    Catatan: NOT_EQUALS dengan flag yang belum diset menganggap nilai
    aktual None — jadi NOT_EQUALS True cocok baik untuk flag False
    maupun flag yang hilang (dikunci test). EQUALS tanpa field ``value``
    berarti "flag diset" (hanya cocok saat flag bernilai True) — bukan
    cocok dengan flag yang hilang (BUG-6).
    """
    kind = condition["kind"]
    if kind not in TRIGGER_KINDS:
        raise ValueError(f"kind trigger tidak dikenal: {kind}")
    if kind == "flag":
        flag = condition["flag"]
        operator = condition.get("operator", "EQUALS")
        if operator not in FLAG_OPERATORS:
            raise ValueError(f"operator flag tidak dikenal: {operator}")
        if operator == "MISSING":
            return flag not in state.flags
        actual = state.flags.get(flag)
        value = condition.get("value")
        if operator == "EQUALS" and "value" not in condition:
            # BUG-6: EQUALS tanpa value = "flag diset" (True), bukan
            # cocok dengan flag yang hilang (None == None dulu memicu).
            return actual is True
        if operator == "EQUALS":
            return actual == value
        return actual != value
    if kind == "quest_done":
        return condition["quest"] in state.quests.done
    if kind == "tier_reached":
        return state.player.tier_id == condition["tier"]
    if kind == "location_entered":
        return state.location == condition["map"]
    if kind == "day_passed":
        return state.time.day >= condition["day"]
    if kind == "reputation_reached":
        faction = condition["faction"]
        return state.reputation.get(faction, 0) >= condition["threshold"]
    # Jaring pengaman: kind ada di daftar tetapi belum ada cabangnya.
    raise ValueError(f"kind trigger tidak dikenal: {kind}")


def check_trigger(event: GameEvent, state: GameState) -> bool:
    """Kembalikan True bila semua kondisi trigger terpenuhi (AND).

    Semantik all([]) = True: event tanpa kondisi selalu memicu. Data
    dengan trigger kosong dicegah oleh validator (tests/test_event_data).
    """
    return all(_match_trigger(condition, state) for condition in event.trigger)


def apply_action(
    action: dict[str, Any], state: GameState, result: EventResult, event_id: str
) -> None:
    """Terapkan satu aksi event ke state (GDD §15.3).

    Publik agar engine lain (mis. dialog §12.5) memakai parser aksi yang
    sama — satu sumber kebenaran untuk aksi, tanpa duplikasi logika.
    """
    kind = action["kind"]
    if kind not in ACTION_KINDS:
        raise ValueError(f"kind aksi tidak dikenal: {kind}")
    if kind == "set_flag":
        state.flags[action["flag"]] = action["value"]
    elif kind == "clear_flag":
        state.flags.pop(action["flag"], None)
    elif kind == "unlock_map":
        target = action["target"]
        state.flags[f"map_{target}_unlocked"] = True
        if target not in state.map_unlocks:
            state.map_unlocks.append(target)
    elif kind == "start_quest":
        quest_id = action["id"]
        if quest_id not in state.quests.started:
            state.quests.started.append(quest_id)
    elif kind == "grant_memory":
        memory_id = action["memory_id"]
        if memory_id not in state.memories:
            state.memories.append(memory_id)
    elif kind == "grant_item":
        item_id = action["id"]
        items = state.inventory.setdefault("items", {})
        items[item_id] = items.get(item_id, 0) + action.get("count", 1)
    elif kind == "grant_gold":
        # BUG-8: emas tidak boleh negatif (clamp 0) walau amount minus.
        state.player.gold = max(0, state.player.gold + action.get("amount", 0))
    elif kind == "change_reputation":
        state.add_reputation(action["faction"], action["delta"])
    elif kind == "start_dialog":
        # ponytail: BUG-3 — result.dialogs belum dikonsumsi pemanggil
        # (game_loop tidak membaca daftar ini); data/events belum memakai
        # aksi start_dialog. Upgrade saat event intro memerlukan dialog
        # bercabang: proses result.dialogs di _run_events -> _start_dialog.
        result.dialogs.append(action["dialog_id"])
        result.logs.append(f"Sebuah dialog dimulai: {action['dialog_id']}.")
    elif kind == "add_companion":
        companion_id = action["id"]
        known = any(m.get("id") == companion_id for m in state.party)
        if not known:
            raw = load_companion(companion_id)  # loader di models/party.py
            state.party.append(raw.to_dict())  # skema penuh utk save
        # GDD §20.1/§24.1: maks 3 slot rekan aktif. Saat penuh, rekan tetap
        # masuk roster (inaktif) — swap bisa mengaktifkan; refire event
        # mengaktifkan rekan roster yang belum aktif bila slot kosong.
        if (
            companion_id not in state.party_active
            and len(state.party_active) < 3
        ):
            state.party_active.append(companion_id)
        if not known:
            if companion_id in state.party_active:
                result.logs.append(f"{raw.name} kini bersamamu.")
            else:
                result.logs.append(
                    f"{raw.name} bergabung ke rombongan (slot aktif penuh)."
                )
    elif kind == "log":
        result.logs.append(action["text"])
    elif kind == "prompt_choice":
        # Opsi mendukung daftar aksi penuh (§15.3): _cmd_choose mengeksekusi
        # lewat apply_action — satu sumber kebenaran untuk semua aksi.
        options = action.get("options", [])
        if not options:
            raise ValueError("prompt_choice butuh minimal 1 opsi")
        for opt in options:
            if "key" not in opt or "text" not in opt:
                raise ValueError("opsi prompt_choice wajib punya key dan text")
        state.flags["pending_choice"] = {
            "event_id": event_id,
            "options": options,
        }
        # Tampilkan pilihan ke pemain via log
        for opt in options:
            result.logs.append(f"  [{opt['key']}] {opt['text']}")
    elif kind == "add_ending_points":
        ep_path = action["path"]
        if ep_path not in {"defy", "seal", "reconcile"}:
            # BUG-7: path di luar jalur ending ditolak — mencegah kunci
            # liar di state.ending_points yang tak pernah dibaca ending.
            raise ValueError(f"jalur ending tidak dikenal: {ep_path}")
        points = action.get("points", 0)
        curr = state.ending_points.get(ep_path, 0)
        state.ending_points[ep_path] = curr + points
    elif kind == "calculate_ending":
        # GDD §21.1: jalur poin tertinggi menentukan ending; hanya flag
        # pemenang yang diset (test menuntut flag loser None).
        winner = calculate_ending(state)
        state.flags[f"ending_{winner}_win"] = True


def process_events(state: GameState, events: list[GameEvent]) -> EventResult:
    """Evaluasi semua event satu pass dalam urutan daftar (§15.4).

    Efek event sebelumnya terlihat oleh event berikutnya (cascade) dalam
    pass yang sama; event dengan `once: true` men-set event_<id>_done dan
    dilewati pada pass berikutnya.
    """
    result = EventResult()
    for event in events:
        if event.once and state.flags.get(f"event_{event.id}_done"):
            continue
        if not check_trigger(event, state):
            continue
        for action in event.actions:
            apply_action(action, state, result, event.id)
        result.fired.append(event.id)
        if event.once:
            state.flags[f"event_{event.id}_done"] = True
    return result
