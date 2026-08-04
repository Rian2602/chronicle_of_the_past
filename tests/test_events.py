from src.core.game_state import GameState
from src.engine.event_engine import process_events


def test_event_fires_on_flag():
    gs = GameState()
    gs.flags["trigger_me"] = True
    events = [
        {
            "id": "e1",
            "trigger": [{"kind": "flag", "flag": "trigger_me", "value": True}],
            "actions": [
                {"kind": "set_flag", "flag": "e1_fired", "value": True}
            ],
        }
    ]
    process_events(gs, None, events)
    assert gs.flags.get("e1_fired") is True


def test_event_does_not_fire_when_condition_missing():
    gs = GameState()
    events = [
        {
            "id": "e1",
            "trigger": [{"kind": "flag", "flag": "nope", "value": True}],
            "actions": [
                {"kind": "set_flag", "flag": "e1_fired", "value": True}
            ],
        }
    ]
    process_events(gs, None, events)
    assert gs.flags.get("e1_fired") is None


def test_event_log_action_returned():
    gs = GameState()
    gs.current_map = "village"
    events = [
        {
            "id": "e1",
            "trigger": [{"kind": "map", "name": "village", "operator": "EQ"}],
            "actions": [{"kind": "log", "text": "Selamat datang di desa."}],
        }
    ]
    assert process_events(gs, None, events) == ["Selamat datang di desa."]


def test_event_grant_memory_skips_without_player():
    gs = GameState()
    gs.memories = [
        {
            "id": "memory001",
            "title": "Desa Terbakar",
            "text": "Aku pernah membaca... desa ini akan terbakar.",
            "flags_set": ["knows_village_burns"],
        }
    ]
    events = [
        {
            "id": "e1",
            "trigger": [{"kind": "flag", "flag": "x", "value": True}],
            "actions": [{"kind": "grant_memory", "id": "memory001"}],
        }
    ]
    gs.flags["x"] = True
    process_events(gs, None, events)
    assert gs.player is None
    assert "knows_village_burns" not in gs.flags
