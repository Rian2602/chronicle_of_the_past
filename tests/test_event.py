"""Test engine event data-driven (GDD §15) — trigger, aksi, once, cascade."""

from pathlib import Path

import pytest

from src.core.state import GameState
from src.engine.event import (
    EventResult,
    GameEvent,
    check_trigger,
    load_events,
    process_events,
)
from src.models.player import Player

EVENT_DIR = Path(__file__).resolve().parents[1] / "data" / "events"


def _state() -> GameState:
    """State kosong untuk pengujian trigger/aksi event."""
    return GameState(player=Player(name="Akar"))


def _event(
    trigger: list[dict] | None = None,
    actions: list[dict] | None = None,
    once: bool = True,
    event_id: str = "evt_test",
) -> GameEvent:
    """Bangun event uji ringkas."""
    return GameEvent(
        id=event_id,
        trigger=trigger or [],
        actions=actions or [{"kind": "log", "text": "terpicu"}],
        once=once,
    )


def _fire(event: GameEvent, state: GameState) -> EventResult:
    """Evaluasi satu event terhadap state; kembalikan hasil pass."""
    return process_events(state, [event])


# ----------------------------------------------------------------------
# Parsing data
# ----------------------------------------------------------------------


def test_load_events_urut_berdasarkan_nama_file():
    """Event dimuat urut abjad nama file; id event cocok dengan stem."""
    events = load_events()
    assert events
    names = sorted(path.stem for path in EVENT_DIR.glob("*.json"))
    assert [event.id for event in events] == names


# ----------------------------------------------------------------------
# Trigger
# ----------------------------------------------------------------------


def test_trigger_flag_equals_cocok():
    """Flag EQUALS: memicu bila nilai flag sama dengan value."""
    state = _state()
    state.flags["gate_open"] = True
    event = _event(
        trigger=[
            {
                "kind": "flag",
                "flag": "gate_open",
                "operator": "EQUALS",
                "value": True,
            }
        ]
    )
    assert _fire(event, state).fired == ["evt_test"]


def test_trigger_flag_equals_tidak_cocok():
    """Flag EQUALS: tidak memicu bila nilai flag berbeda."""
    state = _state()
    state.flags["gate_open"] = False
    event = _event(
        trigger=[
            {
                "kind": "flag",
                "flag": "gate_open",
                "operator": "EQUALS",
                "value": True,
            }
        ]
    )
    assert _fire(event, state).fired == []


def test_trigger_flag_not_equals():
    """Flag NOT_EQUALS: memicu bila nilai flag berbeda dari value."""
    state = _state()
    event = _event(
        trigger=[
            {
                "kind": "flag",
                "flag": "gate_open",
                "operator": "NOT_EQUALS",
                "value": True,
            }
        ]
    )
    assert _fire(event, state).fired == ["evt_test"]


def test_check_trigger_flag_missing():
    """Flag MISSING: memicu hanya bila flag belum pernah diset."""
    state = _state()
    event = _event(
        trigger=[{"kind": "flag", "flag": "seen", "operator": "MISSING"}]
    )
    assert check_trigger(event, state)
    state.flags["seen"] = False
    assert not check_trigger(event, state)


def test_trigger_quest_done():
    """quest_done: memicu bila quest tercatat selesai."""
    state = _state()
    state.quests.done.append("quest101")
    event = _event(trigger=[{"kind": "quest_done", "quest": "quest101"}])
    assert _fire(event, state).fired == ["evt_test"]


def test_trigger_tier_reached():
    """tier_reached: memicu bila tier pemain sama dengan target."""
    state = _state()
    state.player.tier_id = "golden_core"
    event = _event(trigger=[{"kind": "tier_reached", "tier": "golden_core"}])
    assert _fire(event, state).fired == ["evt_test"]


def test_trigger_location_entered():
    """location_entered: memicu bila lokasi pemain sama dengan peta."""
    state = _state()
    state.location = "ruin_shrine"
    event = _event(trigger=[{"kind": "location_entered", "map": "ruin_shrine"}])
    assert _fire(event, state).fired == ["evt_test"]


def test_trigger_day_passed_mencapai():
    """day_passed: memicu bila hari game mencapai (>=) hari target."""
    state = _state()
    event = _event(trigger=[{"kind": "day_passed", "day": 7}])
    state.time.day = 6
    assert _fire(event, state).fired == []
    state.time.day = 7
    assert _fire(event, state).fired == ["evt_test"]


def test_trigger_semua_harus_cocok():
    """Semantik AND: semua kondisi trigger harus terpenuhi sekaligus."""
    state = _state()
    state.flags["a"] = True
    event = _event(
        trigger=[
            {"kind": "flag", "flag": "a", "operator": "EQUALS", "value": True},
            {"kind": "flag", "flag": "b", "operator": "EQUALS", "value": True},
        ]
    )
    assert _fire(event, state).fired == []
    state.flags["b"] = True
    assert _fire(event, state).fired == ["evt_test"]


def test_trigger_kosong_selalu_memicu():
    """Semantik all([])=True; trigger kosong dicegah validator data."""
    state = _state()
    event = _event(trigger=[])
    assert _fire(event, state).fired == ["evt_test"]


# ----------------------------------------------------------------------
# Aksi
# ----------------------------------------------------------------------


def test_action_set_flag_dan_clear_flag():
    """set_flag menetapkan nilai; clear_flag menghapus flag."""
    state = _state()
    set_event = _event(
        actions=[{"kind": "set_flag", "flag": "arc1_open", "value": True}]
    )
    _fire(set_event, state)
    assert state.flags["arc1_open"] is True
    clear_event = _event(
        event_id="evt_clear",
        actions=[{"kind": "clear_flag", "flag": "arc1_open"}],
    )
    _fire(clear_event, state)
    assert "arc1_open" not in state.flags


def test_action_unlock_map():
    """unlock_map membuka peta: flag map_<id>_unlocked + daftar unlock."""
    state = _state()
    event = _event(actions=[{"kind": "unlock_map", "target": "ruin_shrine"}])
    _fire(event, state)
    assert state.flags["map_ruin_shrine_unlocked"] is True
    assert "ruin_shrine" in state.map_unlocks


def test_action_start_quest():
    """start_quest menambahkan quest ke daftar quest aktif."""
    state = _state()
    event = _event(actions=[{"kind": "start_quest", "id": "quest101"}])
    _fire(event, state)
    assert state.quests.started == ["quest101"]


def test_action_grant_memory():
    """grant_memory menambahkan echo memori tanpa duplikat."""
    state = _state()
    event = _event(
        actions=[{"kind": "grant_memory", "memory_id": "memory_first_echo"}]
    )
    _fire(event, state)
    _fire(event, state)
    assert state.memories == ["memory_first_echo"]


def test_action_grant_item():
    """grant_item menambah item ke tas; count default 1."""
    state = _state()
    event = _event(
        actions=[{"kind": "grant_item", "id": "pill_insight", "count": 2}]
    )
    _fire(event, state)
    assert state.inventory["items"]["pill_insight"] == 2


def test_action_grant_gold():
    """grant_gold menambah emas pemain."""
    state = _state()
    event = _event(actions=[{"kind": "grant_gold", "amount": 50}])
    _fire(event, state)
    assert state.player.gold == 50


def test_action_change_reputation_di_clamp():
    """change_reputation menambah delta dan di-clamp ke [-100, +100] (§8)."""
    state = _state()
    state.reputation["rebels"] = 90
    event = _event(
        actions=[
            {"kind": "change_reputation", "faction": "rebels", "delta": 30}
        ]
    )
    _fire(event, state)
    assert state.reputation["rebels"] == 100
    drop = _event(
        event_id="evt_drop",
        actions=[
            {"kind": "change_reputation", "faction": "court", "delta": -500}
        ],
    )
    _fire(drop, state)
    assert state.reputation["court"] == -100


def test_action_start_dialog_masuk_result():
    """start_dialog menyimpan id dialog di result + pesan di log."""
    state = _state()
    event = _event(
        actions=[{"kind": "start_dialog", "dialog_id": "dlg_elder_intro"}]
    )
    result = _fire(event, state)
    assert result.dialogs == ["dlg_elder_intro"]
    assert any("dialog" in line.lower() for line in result.logs)


def test_action_log_masuk_result():
    """Log menambahkan teks narasi ke hasil pass."""
    state = _state()
    event = _event(actions=[{"kind": "log", "text": "Abu turun bagai hujan."}])
    result = _fire(event, state)
    assert result.logs == ["Abu turun bagai hujan."]


# ----------------------------------------------------------------------
# Aturan proses (§15.4)
# ----------------------------------------------------------------------


def test_once_memicu_sekali_saja():
    """once: true -> set event_<id>_done dan dilewati pass berikutnya."""
    state = _state()
    event = _event(actions=[{"kind": "grant_gold", "amount": 10}])
    first = process_events(state, [event])
    second = process_events(state, [event])
    assert first.fired == ["evt_test"]
    assert state.flags["event_evt_test_done"] is True
    assert second.fired == []
    assert state.player.gold == 10


def test_repeatable_memicu_setiap_pass():
    """once: false -> event repeatable, dibatasi trigger-nya sendiri."""
    state = _state()
    event = _event(once=False, actions=[{"kind": "grant_gold", "amount": 5}])
    process_events(state, [event])
    process_events(state, [event])
    assert state.player.gold == 10
    assert "event_evt_test_done" not in state.flags


def test_cascade_dalam_satu_pass():
    """Efek event A terlihat oleh event B dalam pass yang sama (§15.4)."""
    state = _state()
    first = _event(
        event_id="evt_a",
        actions=[{"kind": "set_flag", "flag": "gate", "value": True}],
    )
    second = _event(
        event_id="evt_b",
        trigger=[
            {
                "kind": "flag",
                "flag": "gate",
                "operator": "EQUALS",
                "value": True,
            }
        ],
        actions=[{"kind": "grant_gold", "amount": 1}],
    )
    result = process_events(state, [first, second])
    assert result.fired == ["evt_a", "evt_b"]
    assert state.player.gold == 1


def test_event_terkunci_oleh_trigger_tidak_memicu():
    """Event yang trigger-nya tidak cocok tidak memicu sama sekali."""
    state = _state()
    event = _event(
        trigger=[
            {
                "kind": "flag",
                "flag": "nope",
                "operator": "EQUALS",
                "value": True,
            }
        ],
        actions=[{"kind": "grant_gold", "amount": 100}],
    )
    result = _fire(event, state)
    assert result.fired == []
    assert result.logs == []
    assert state.player.gold == 0


def test_kind_trigger_tidak_dikenal_memunculkan_error():
    """Guard engine: kind trigger di luar daftar ditolak, bukan senyap."""
    state = _state()
    event = _event(trigger=[{"kind": "bogus"}])
    with pytest.raises(ValueError):
        _fire(event, state)


def test_kind_aksi_tidak_dikenal_memunculkan_error():
    """Guard engine: kind aksi di luar daftar ditolak, bukan senyap."""
    state = _state()
    event = _event(actions=[{"kind": "bogus"}])
    with pytest.raises(ValueError):
        _fire(event, state)
