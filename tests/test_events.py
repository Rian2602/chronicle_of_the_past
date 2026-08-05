from src.core.game_state import GameState
from src.engine.event_engine import process_day_tick, process_events
from src.models.player import Player


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


def test_event_play_scene_returns_rendered_scene():
    gs = GameState()
    gs.flags["x"] = True
    gs.scenes = [{"id": "s1", "lines": ["Baris satu."]}]
    events = [
        {
            "id": "e1",
            "trigger": [{"kind": "flag", "flag": "x", "value": True}],
            "actions": [{"kind": "play_scene", "id": "s1"}],
        }
    ]
    out = process_events(gs, None, events)
    assert "Baris satu." in out[0]


def test_event_recap_uses_ending_flag():
    gs = GameState()
    gs.flags["x"] = True
    gs.flags["ending_e_done"] = True
    gs.player = Player("Rian", "warrior", 100, 10, {"hp": 100, "mp": 10})
    gs.player.quests_done = ["quest001", "quest002"]
    events = [
        {
            "id": "e1",
            "trigger": [{"kind": "flag", "flag": "x", "value": True}],
            "actions": [{"kind": "recap"}],
        }
    ]
    out = process_events(gs, None, events)
    assert "menghancurkan Jangkar" in "\n".join(out)
    assert "Quest selesai: 2" in "\n".join(out)


def test_process_day_tick_counts_ultimatum_days():
    gs = GameState()
    gs.flags["ultimatum_5_days"] = True
    assert process_day_tick(gs) == ["Ultimatum gereja tersisa 4 hari."]
    for _ in range(4):
        out = process_day_tick(gs)
    assert gs.flags["ultimatum_expired"] is True
    assert out == ["Ultimatum gereja habis. Inkuisisi mulai bergerak."]
