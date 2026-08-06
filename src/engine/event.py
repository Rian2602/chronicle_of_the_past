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

EVENT_DIR = Path(__file__).resolve().parents[2] / "data" / "events"

# Reputasi faksi dibatasi -100 s/d +100 (GDD §8).
REPUTATION_CLAMP = 100

TRIGGER_KINDS = {
    "flag",
    "quest_done",
    "tier_reached",
    "location_entered",
    "day_passed",
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
    "log",
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
    maupun flag yang hilang (dikunci test).
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
    # Jaring pengaman: kind ada di daftar tetapi belum ada cabangnya.
    raise ValueError(f"kind trigger tidak dikenal: {kind}")


def check_trigger(event: GameEvent, state: GameState) -> bool:
    """Kembalikan True bila semua kondisi trigger terpenuhi (AND).

    Semantik all([]) = True: event tanpa kondisi selalu memicu. Data
    dengan trigger kosong dicegah oleh validator (tests/test_event_data).
    """
    return all(_match_trigger(condition, state) for condition in event.trigger)


def _apply_action(
    action: dict[str, Any], state: GameState, result: EventResult
) -> None:
    """Terapkan satu aksi event ke state (GDD §15.3)."""
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
        state.player.gold += action.get("amount", 0)
    elif kind == "change_reputation":
        faction = action["faction"]
        current = state.reputation.get(faction, 0)
        state.reputation[faction] = max(
            -REPUTATION_CLAMP, min(REPUTATION_CLAMP, current + action["delta"])
        )
    elif kind == "start_dialog":
        result.dialogs.append(action["dialog_id"])
        result.logs.append(f"Sebuah dialog dimulai: {action['dialog_id']}.")
    elif kind == "log":
        result.logs.append(action["text"])


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
            _apply_action(action, state, result)
        result.fired.append(event.id)
        if event.once:
            state.flags[f"event_{event.id}_done"] = True
    return result
