"""Tests for engine module data loaders using generic load_json_dir."""

from src.engine.combat import load_enemies, load_techniques
from src.engine.cultivation import load_tiers
from src.engine.dialog import load_dialogs
from src.engine.event import load_events
from src.engine.items import load_items
from src.engine.maps import load_maps
from src.engine.quest import load_quests
from src.engine.shop import load_shops
from src.engine.story import load_memories


def test_engine_loaders() -> None:
    """Verify all engine load_* functions return expected types and content."""
    items = load_items()
    assert isinstance(items, dict)
    assert len(items) > 0

    memories = load_memories()
    assert isinstance(memories, dict)

    shops = load_shops()
    assert isinstance(shops, dict)

    events = load_events()
    assert isinstance(events, list)

    maps = load_maps()
    assert isinstance(maps, dict)

    dialogs = load_dialogs()
    assert isinstance(dialogs, dict)

    tiers = load_tiers()
    assert isinstance(tiers, list)

    quests = load_quests()
    assert isinstance(quests, list)

    techniques = load_techniques()
    assert isinstance(techniques, list)
    assert len(techniques) > 0

    enemies = load_enemies()
    assert isinstance(enemies, list)
