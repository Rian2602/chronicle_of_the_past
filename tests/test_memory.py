from src.core.game_state import GameState
from src.models.player import Player
from src.systems.memory_system import grant_memory


def make_player():
    return Player(
        name="Rian",
        class_id="warrior",
        hp=100,
        mp=10,
        base_stats={
            "attack": 12,
            "defense": 14,
            "hp": 100,
            "mp": 10,
            "agility": 8,
            "intelligence": 7,
        },
    )


def make_game_state():
    gs = GameState()
    gs.player = make_player()
    gs.flags = {}
    return gs


def test_grant_sets_flags():
    gs = make_game_state()
    memory = {"id":"memory001","flags_set":["knows_village_burns"]}
    grant_memory(gs, "memory001", memory)
    assert any(m["id"] == "memory001" for m in gs.player.memories)
    assert gs.flags.get("knows_village_burns") is True


def test_grant_without_player_returns_none():
    gs = GameState()
    memory = {"id": "memory001", "flags_set": ["knows_village_burns"]}
    assert grant_memory(gs, "memory001", memory) is None
    assert gs.player is None


def test_grant_resolves_from_registry_when_memory_omitted():
    gs = make_game_state()
    memory = {
        "id": "memory001",
        "title": "Desa Terbakar",
        "flags_set": ["knows_village_burns"],
    }
    gs.memories = [memory]
    result = grant_memory(gs, "memory001")
    assert result is memory
    assert any(m["id"] == "memory001" for m in gs.player.memories)
    assert gs.flags.get("knows_village_burns") is True
    assert gs.player.memories == [memory]


def test_grant_unknown_id_from_registry_returns_none():
    gs = make_game_state()
    gs.memories = [{"id": "memory001", "flags_set": []}]
    assert grant_memory(gs, "tidak_ada") is None
    assert gs.player.memories == []


def test_grant_dedupe_keeps_single_entry():
    gs = make_game_state()
    memory = {"id": "memory001", "flags_set": ["knows_village_burns"]}
    grant_memory(gs, "memory001", memory)
    result = grant_memory(gs, "memory001", memory)
    assert result is memory
    assert gs.player.memories == [memory]
    assert gs.flags.get("knows_village_burns") is True


def test_grant_appends_memory():
    gs = make_game_state()
    assert gs.player.memories == []
    grant_memory(gs, "memory001", {"id": "memory001", "flags_set": []})
    assert any(m["id"] == "memory001" for m in gs.player.memories)


def test_memories_json_loads_via_load_json():
    from src.utils.json_loader import load_json

    memories = load_json("data/story/memories.json")
    assert isinstance(memories, list)
    assert len(memories) == 2
    assert memories[0]["id"] == "memory001"
    assert memories[1]["id"] == "memory002"
