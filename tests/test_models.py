from src.models.enemy import Enemy
from src.models.item import Item
from src.models.map import Map
from src.models.player import Player, max_hp, max_mp


def test_player_max_hp():
    p = Player(
        name="Rian",
        class_id="warrior",
        hp=100,
        mp=10,
        base_stats={"hp": 100, "mp": 10},
    )
    assert max_hp(p) == 100


def test_player_max_mp():
    p = Player(
        name="Mira",
        class_id="mage",
        hp=60,
        mp=45,
        base_stats={"hp": 60, "mp": 45},
    )
    assert max_mp(p) == 45


def test_max_hp_includes_attribute_bonus():
    p = Player(
        name="Rian",
        class_id="warrior",
        hp=100,
        mp=10,
        base_stats={"hp": 100, "mp": 10},
        attribute_bonuses={"hp": 25},
    )
    assert max_hp(p) == 125


def test_max_mp_includes_attribute_bonus():
    p = Player(
        name="Mira",
        class_id="mage",
        hp=60,
        mp=45,
        base_stats={"hp": 60, "mp": 45},
        attribute_bonuses={"mp": 10},
    )
    assert max_mp(p) == 55


def test_player_defaults():
    p = Player(name="Rian", class_id="warrior", hp=100, mp=10, base_stats={})
    assert p.level == 1
    assert p.xp == 0
    assert p.gold == 0
    assert p.skill_points == 0
    assert p.attribute_bonuses == {}
    assert p.equipped == {}
    assert p.inventory == []
    assert p.reputation == {}
    assert p.relationship == {}
    assert p.flags == {}
    assert p.quests_active == {}
    assert p.quests_done == []
    assert p.memories == []
    assert p.learned_skills == []


def test_player_from_dict():
    data = {
        "name": "Rian",
        "class_id": "warrior",
        "hp": 100,
        "mp": 10,
        "base_stats": {"hp": 100, "mp": 10, "attack": 8},
        "attribute_bonuses": {"hp": 5},
        "level": 3,
        "xp": 150,
        "gold": 75,
        "skill_points": 2,
        "equipped": {"weapon": "iron_sword"},
        "inventory": ["potion", "bread"],
        "reputation": {"merchant_guild": 10},
        "relationship": {"mira": 5},
        "flags": {"met_queen": True},
        "quests_active": {"q001": 1},
        "quests_done": ["q000"],
        "memories": ["first_meeting"],
        "learned_skills": ["bash"],
    }
    p = Player(**data)
    for key, value in data.items():
        assert getattr(p, key) == value


def test_player_defaults_are_independent():
    p1 = Player(name="Rian", class_id="warrior", hp=100, mp=10, base_stats={})
    p2 = Player(name="Mira", class_id="mage", hp=60, mp=45, base_stats={})
    p1.inventory.append("potion")
    p1.flags["seen"] = True
    p1.learned_skills.append("bash")
    assert p2.inventory == []
    assert p2.flags == {}
    assert p2.learned_skills == []


def test_item_from_dict():
    data = {
        "id": "it_potion",
        "name": "Potion",
        "type": "consumable",
        "slot": "hand",
        "modifiers": {"hp": 30},
        "price": 10,
        "description": "Restores 30 HP.",
    }
    item = Item(**data)
    for key, value in data.items():
        assert getattr(item, key) == value


def test_item_defaults():
    i = Item(id="it_potion", name="Potion", type="consumable")
    assert i.slot is None
    assert i.modifiers == {}
    assert i.price == 0
    assert i.description == ""


def test_item_modifiers_are_independent():
    i1 = Item(id="i1", name="X", type="t")
    i2 = Item(id="i2", name="Y", type="t")
    i1.modifiers["hp"] = 10
    assert i2.modifiers == {}


def test_enemy_from_dict():
    data = {
        "id": "en_rat",
        "name": "Giant Rat",
        "level": 1,
        "stats": {"hp": 15, "attack": 3},
        "loot": ["rat_tail"],
        "skills": ["sk_bite"],
        "lore": "A mangy rodent.",
    }
    enemy = Enemy(**data)
    for key, value in data.items():
        assert getattr(enemy, key) == value


def test_enemy_default_lore():
    e = Enemy(
        id="en_rat", name="Giant Rat", level=1, stats={}, loot=[], skills=[]
    )
    assert e.lore == ""


def test_map_from_dict():
    data = {
        "id": "map_town",
        "name": "Riverford",
        "region": "riverlands",
        "threat_level": 1,
        "description": "A quiet market town.",
        "ascii_art": "~~~~",
        "exits": ["map_forest"],
        "npcs": ["np_blacksmith"],
        "enemy_pool": ["en_rat"],
        "time_effects": {"night": {"description": "Darker"}},
    }
    m = Map(**data)
    for key, value in data.items():
        assert getattr(m, key) == value


def test_map_default_time_effects():
    m = Map(
        id="map_town",
        name="Riverford",
        region="riverlands",
        threat_level=1,
        description="",
        ascii_art="",
        exits=[],
        npcs=[],
        enemy_pool=[],
    )
    assert m.time_effects == {}


def test_map_time_effects_are_independent():
    m1 = Map(
        id="m1",
        name="A",
        region="r",
        threat_level=1,
        description="",
        ascii_art="",
        exits=[],
        npcs=[],
        enemy_pool=[],
    )
    m2 = Map(
        id="m2",
        name="B",
        region="r",
        threat_level=1,
        description="",
        ascii_art="",
        exits=[],
        npcs=[],
        enemy_pool=[],
    )
    m1.time_effects["night"] = {"description": "dark"}
    assert m2.time_effects == {}
