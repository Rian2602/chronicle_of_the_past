from src.core.randomizer import Randomizer
from src.models.enemy import Enemy
from src.systems.loot_system import roll_loot


def test_loot_item_chance():
    e = Enemy(
        "g",
        "Goblin",
        2,
        {
            "attack": 5,
            "defense": 2,
            "hp": 5,
            "mp": 0,
            "agility": 6,
            "intelligence": 3,
        },
        loot=[{"item": "herb", "chance": 100, "amount": 1}],
        skills=[],
        lore="",
        reward={"xp": 30, "gold": [6, 12]},
    )
    r = Randomizer(seed=9)
    drops = roll_loot(e, r)
    assert any(d["id"] == "herb" for d in drops)


def test_loot_chance_zero_no_drop():
    e = Enemy(
        "g",
        "Goblin",
        2,
        {
            "attack": 5,
            "defense": 2,
            "hp": 5,
            "mp": 0,
            "agility": 6,
            "intelligence": 3,
        },
        loot=[{"item": "herb", "chance": 0, "amount": 1}],
        skills=[],
        lore="",
        reward={"xp": 30, "gold": [6, 12]},
    )
    assert roll_loot(e, Randomizer(seed=9)) == []


def test_loot_chance_hundred_drop():
    e = Enemy(
        "g",
        "Goblin",
        2,
        {
            "attack": 5,
            "defense": 2,
            "hp": 5,
            "mp": 0,
            "agility": 6,
            "intelligence": 3,
        },
        loot=[{"item": "herb", "chance": 100, "amount": 1}],
        skills=[],
        lore="",
        reward={"xp": 30, "gold": [6, 12]},
    )
    assert roll_loot(e, Randomizer(seed=9)) == [{"id": "herb", "qty": 1}]


def test_loot_amount_respected():
    e = Enemy(
        "g",
        "Goblin",
        2,
        {
            "attack": 5,
            "defense": 2,
            "hp": 5,
            "mp": 0,
            "agility": 6,
            "intelligence": 3,
        },
        loot=[{"item": "potion", "chance": 100, "amount": 3}],
        skills=[],
        lore="",
        reward={"xp": 30, "gold": [6, 12]},
    )
    assert roll_loot(e, Randomizer(seed=9)) == [{"id": "potion", "qty": 3}]


def test_loot_multiple_entries_each_rolled_in_order():
    e = Enemy(
        "g",
        "Goblin",
        2,
        {
            "attack": 5,
            "defense": 2,
            "hp": 5,
            "mp": 0,
            "agility": 6,
            "intelligence": 3,
        },
        loot=[
            {"item": "herb", "chance": 100, "amount": 1},
            {"item": "potion", "chance": 100, "amount": 2},
        ],
        skills=[],
        lore="",
        reward={"xp": 30, "gold": [6, 12]},
    )
    drops = roll_loot(e, Randomizer(seed=9))
    assert drops == [{"id": "herb", "qty": 1}, {"id": "potion", "qty": 2}]


def test_loot_never_contains_gold():
    e = Enemy(
        "g",
        "Goblin",
        2,
        {
            "attack": 5,
            "defense": 2,
            "hp": 5,
            "mp": 0,
            "agility": 6,
            "intelligence": 3,
        },
        loot=[{"item": "herb", "chance": 100, "amount": 1}],
        skills=[],
        lore="",
        reward={"xp": 30, "gold": [6, 12]},
    )
    drops = roll_loot(e, Randomizer(seed=9))
    assert drops == [{"id": "herb", "qty": 1}]
    assert all("gold" not in drop for drop in drops)


def test_loot_empty_table_gives_empty_drops():
    e = Enemy(
        "g",
        "Goblin",
        2,
        {
            "attack": 5,
            "defense": 2,
            "hp": 5,
            "mp": 0,
            "agility": 6,
            "intelligence": 3,
        },
        loot=[],
        skills=[],
        lore="",
        reward={"xp": 30, "gold": [6, 12]},
    )
    assert roll_loot(e, Randomizer(seed=9)) == []
