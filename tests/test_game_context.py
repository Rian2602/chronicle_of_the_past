import pytest

from src.core.constants import FACTIONS
from src.core.game_context import GameContext


def test_create_warrior():
    ctx = GameContext(data_dir="data")
    p = ctx.create_player("Rian", "warrior")
    assert p.base_stats["attack"] == 12
    assert p.hp == 100
    assert p.mp == 10
    assert p.learned_skills == ["slash"]
    assert set(p.reputation) == set(FACTIONS)
    assert all(v == 0 for v in p.reputation.values())


def test_create_scholar(tmp_path):
    ctx = GameContext(data_dir="data")
    class_data = ctx.classes["scholar"]
    assert class_data["xp_bonus"] == 1.2
    p = ctx.create_player("Dewi", "scholar")
    assert p.hp == 75
    assert p.mp == 45
    assert p.base_stats["intelligence"] == 16


def test_create_player_unknown_class_raises(tmp_path):
    ctx = GameContext(data_dir="data")
    with pytest.raises(ValueError):
        ctx.create_player("Rian", "tidak_ada")


def test_game_context_empty_data_dir(tmp_path):
    ctx = GameContext(data_dir=str(tmp_path))
    for attr in (
        "classes",
        "enemies",
        "items",
        "skills",
        "maps",
        "npc",
        "quests",
        "dialogues",
        "factions",
    ):
        assert getattr(ctx, attr) == {}
    assert ctx.events == []
    assert ctx.memories == []


def test_events_and_memories_load(tmp_path):
    (tmp_path / "events").mkdir()
    (tmp_path / "story").mkdir()
    (tmp_path / "events" / "events.json").write_text(
        '[{"id": "e1"}, {"id": "e2"}]', encoding="utf-8"
    )
    (tmp_path / "story" / "memories.json").write_text(
        '[{"id": "m1"}]', encoding="utf-8"
    )
    ctx = GameContext(data_dir=str(tmp_path))
    assert ctx.events == [{"id": "e1"}, {"id": "e2"}]
    assert ctx.memories == [{"id": "m1"}]
