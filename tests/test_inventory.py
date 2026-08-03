import pytest

from src.core.game_state import GameState
from src.core.randomizer import Randomizer
from src.engine.combat_engine import player_action, start_combat, use_item
from src.engine.combat_interfaces import CombatAction
from src.models.enemy import Enemy
from src.models.item import Item
from src.models.player import Player
from src.systems.equipment_system import equip, total_stats, unequip
from src.systems.inventory_system import add_item, remove_item, use_consumable

IRON_SWORD = Item(
    id="iron_sword",
    name="Iron Sword",
    type="weapon",
    slot="weapon",
    modifiers={"attack": 8, "agility": -1},
    price=60,
)
STEEL_SWORD = Item(
    id="steel_sword",
    name="Steel Sword",
    type="weapon",
    slot="weapon",
    modifiers={"attack": 10, "agility": 2},
    price=120,
)
WOODEN_HELMET = Item(
    id="wooden_helmet",
    name="Wooden Helmet",
    type="helmet",
    slot="helmet",
    modifiers={"defense": 2},
    price=20,
)


def make_player(level=1, hp=100, mp=20, attack=10, defense=5, agility=8, intelligence=7):
    base = {
        "attack": attack,
        "defense": defense,
        "hp": 100,
        "mp": 20,
        "agility": agility,
        "intelligence": intelligence,
    }
    return Player(
        name="Rian",
        class_id="warrior",
        hp=hp,
        mp=mp,
        base_stats=base,
        level=level,
    )


def make_enemy(hp=5, reward=None, loot=None):
    return Enemy(
        id="goblin",
        name="Goblin",
        level=2,
        stats={
            "attack": 5,
            "defense": 2,
            "hp": hp,
            "mp": 0,
            "agility": 6,
            "intelligence": 3,
        },
        loot=loot or [],
        skills=[],
        reward=reward or {"xp": 30, "gold": [6, 12]},
    )


def test_add_item_new_entry():
    p = make_player()
    assert add_item(p, "herb") is True
    assert p.inventory == [{"id": "herb", "qty": 1}]


def test_add_item_merges_existing_entry():
    p = make_player()
    add_item(p, "herb", 2)
    assert add_item(p, "herb", 3) is True
    assert p.inventory == [{"id": "herb", "qty": 5}]


def test_add_item_over_capacity_rejected_no_partial():
    p = make_player(level=1)
    assert add_item(p, "herb", 32) is True
    assert add_item(p, "potion", 1) is False
    assert p.inventory == [{"id": "herb", "qty": 32}]


def test_add_item_capacity_scales_with_level():
    p = make_player(level=3)
    assert add_item(p, "herb", 36) is True
    assert add_item(p, "potion", 1) is False
    assert p.inventory == [{"id": "herb", "qty": 36}]


def test_remove_item_decrements_qty():
    p = make_player()
    add_item(p, "herb", 3)
    remove_item(p, "herb", 2)
    assert p.inventory == [{"id": "herb", "qty": 1}]


def test_remove_item_removes_entry_at_zero():
    p = make_player()
    add_item(p, "herb", 1)
    remove_item(p, "herb", 1)
    assert p.inventory == []


def test_remove_item_missing_raises_value_error():
    p = make_player()
    with pytest.raises(ValueError):
        remove_item(p, "nope", 1)


def test_remove_item_insufficient_qty_raises_value_error():
    p = make_player()
    add_item(p, "herb", 2)
    with pytest.raises(ValueError):
        remove_item(p, "herb", 3)


def test_use_consumable_heals_and_removes_one():
    p = make_player(hp=50)
    gs = GameState()
    gs.items = {"herb": Item("herb", "Herb", "consumable", heal=20, price=10)}
    add_item(p, "herb", 1)
    msg = use_consumable(p, p.inventory[0], gs)
    assert p.hp == 70
    assert p.inventory == []
    assert msg == "Kamu memakai Herb, memulihkan 20 HP."


def test_use_consumable_clamps_at_max_hp():
    p = make_player(hp=95)
    gs = GameState()
    gs.items = {"potion": Item("potion", "Potion", "consumable", heal=50, price=30)}
    add_item(p, "potion", 1)
    use_consumable(p, p.inventory[0], gs)
    assert p.hp == 100
    assert p.inventory == []


def test_use_consumable_missing_registry_no_consumption():
    p = make_player()
    gs = GameState()
    add_item(p, "herb", 1)
    msg = use_consumable(p, p.inventory[0], gs)
    assert msg == "Item ini tidak bisa dipakai."
    assert p.inventory == [{"id": "herb", "qty": 1}]
    assert p.hp == 100


def test_use_consumable_zero_heal_no_consumption():
    p = make_player()
    gs = GameState()
    gs.items = {"iron_sword": IRON_SWORD}
    add_item(p, "iron_sword", 1)
    msg = use_consumable(p, p.inventory[0], gs)
    assert msg == "Item ini tidak bisa dipakai."
    assert p.inventory == [{"id": "iron_sword", "qty": 1}]


def test_equip_applies_modifiers_and_sets_slot():
    p = make_player()
    msg = equip(p, IRON_SWORD)
    assert msg == "Iron Sword dipasang di slot weapon."
    assert p.equipped == {"weapon": "iron_sword"}
    assert p.attribute_bonuses == {"attack": 8, "agility": -1}


def test_equip_without_slot_rejected():
    p = make_player()
    msg = equip(p, Item("herb", "Herb", "consumable", heal=20))
    assert msg == "Item ini tidak bisa dipasang."
    assert p.equipped == {}
    assert p.attribute_bonuses == {}


def test_equip_replaces_existing_slot_subtracts_old_modifiers():
    p = make_player()
    equip(p, IRON_SWORD)
    msg = equip(p, STEEL_SWORD, {"iron_sword": IRON_SWORD, "steel_sword": STEEL_SWORD})
    assert msg == "Steel Sword dipasang di slot weapon."
    assert p.equipped == {"weapon": "steel_sword"}
    assert p.attribute_bonuses == {"attack": 10, "agility": 2}


def test_unequip_subtracts_modifiers_and_removes_slot():
    p = make_player()
    equip(p, IRON_SWORD)
    msg = unequip(p, "weapon", {"iron_sword": IRON_SWORD})
    assert msg == "Iron Sword dilepas dari slot weapon."
    assert p.equipped == {}
    assert p.attribute_bonuses == {}


def test_unequip_empty_slot_noop():
    p = make_player()
    msg = unequip(p, "weapon", {})
    assert msg == "Tidak ada item di slot weapon."
    assert p.equipped == {}


def test_total_stats_base_plus_attribute_bonuses():
    p = make_player()
    p.attribute_bonuses = {"attack": 2, "hp": 15}
    stats = total_stats(p)
    assert stats["attack"] == 12
    assert stats["hp"] == 115
    assert stats["mp"] == 20
    assert stats["defense"] == 5
    assert stats["agility"] == 8
    assert stats["intelligence"] == 7


def test_total_stats_includes_equipment():
    p = make_player()
    equip(p, IRON_SWORD)
    stats = total_stats(p)
    assert stats["attack"] == 18
    assert stats["agility"] == 7
    assert stats["defense"] == 5


def test_combat_use_item_resolves_heal_via_registry():
    p = make_player(hp=50)
    add_item(p, "potion", 1)
    state = start_combat(
        p,
        make_enemy(),
        Randomizer(seed=7),
        items={"potion": Item("potion", "Potion", "consumable", heal=50, price=30)},
    )
    msg = use_item(state, "potion")
    assert msg == "Kamu memakai Potion, memulihkan 50 HP."
    assert p.hp == 100
    assert p.inventory == []


def test_combat_use_item_registry_precedes_inline():
    p = make_player(hp=50)
    add_item(p, "potion", 1)
    p.inventory[0]["name"] = "Old Potion"
    p.inventory[0]["heal"] = 999
    state = start_combat(
        p,
        make_enemy(),
        Randomizer(seed=7),
        items={"potion": Item("potion", "Potion", "consumable", heal=50, price=30)},
    )
    msg = use_item(state, "potion")
    assert msg == "Kamu memakai Potion, memulihkan 50 HP."
    assert p.hp == 100
    assert p.inventory == []


def test_combat_loot_routes_through_add_item_bare_entries():
    p = make_player()

    def resolver(enemy, randomizer):
        return [{"id": "herb", "qty": 2}]

    state = start_combat(p, make_enemy(), Randomizer(seed=7), loot_resolver=resolver)
    while not state.over:
        player_action(state, CombatAction.ATTACK)
    assert p.inventory == [{"id": "herb", "qty": 2}]


def test_combat_loot_over_capacity_skipped():
    p = make_player()
    add_item(p, "herb", 32)

    def resolver(enemy, randomizer):
        return [{"id": "herb", "qty": 1}]

    state = start_combat(p, make_enemy(), Randomizer(seed=7), loot_resolver=resolver)
    while not state.over:
        player_action(state, CombatAction.ATTACK)
    assert p.inventory == [{"id": "herb", "qty": 32}]
