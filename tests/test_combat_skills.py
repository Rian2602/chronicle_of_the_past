import pytest

from src.core.randomizer import Randomizer
from src.engine.combat_engine import player_action, start_combat, use_item
from src.engine.combat_interfaces import CombatAction
from src.models.enemy import Enemy
from src.models.player import Player, max_hp


def make_player(agility=8, intelligence=7, attack=10, defense=5, level=1, hp=None, mp=None):
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
        hp=base["hp"] if hp is None else hp,
        mp=base["mp"] if mp is None else mp,
        base_stats=base,
        level=level,
    )


def make_enemy(hp=10, agility=6, attack=5, defense=2, intelligence=3, level=2):
    return Enemy(
        id="goblin",
        name="Goblin",
        level=level,
        stats={
            "attack": attack,
            "defense": defense,
            "hp": hp,
            "mp": 0,
            "agility": agility,
            "intelligence": intelligence,
        },
        loot=[],
        skills=[],
    )


def make_physical_skill(cost=3, power=8, effects=None):
    return {
        "id": "strike",
        "name": "Strike",
        "type": "physical",
        "cost": cost,
        "power": power,
        "target": "enemy",
        "effects": effects or [],
        "requires": [],
        "description": "",
    }


def make_magic_skill(cost=4, power=10, effects=None):
    return {
        "id": "fire",
        "name": "Fireball",
        "type": "magic",
        "cost": cost,
        "power": power,
        "target": "enemy",
        "effects": effects or [],
        "requires": [],
        "description": "",
    }


def test_physical_skill_costs_mp_and_deals_damage():
    player = make_player()
    enemy = make_enemy(hp=50)
    state = start_combat(
        player, enemy, Randomizer(seed=7), skills={"strike": make_physical_skill()}
    )
    assert player_action(state, CombatAction.SKILL, "strike") is False
    assert player.mp == 20 - 3
    assert 0 < enemy.stats["hp"] < 50
    assert any("menyerang" in line or "Kritikal" in line for line in state.log)


def test_magic_skill_uses_magic_formula_and_applies_burn():
    player = make_player(intelligence=8)
    enemy = make_enemy(hp=50, intelligence=3)
    skill = make_magic_skill(
        effects=[{"status": "burn", "duration": 3, "power": 2}]
    )
    state = start_combat(player, enemy, Randomizer(seed=7), skills={"fire": skill})
    assert player_action(state, CombatAction.MAGIC, "fire") is False
    assert enemy.stats["hp"] == 50 - 12
    assert "Kamu melontarkan mantra ke Goblin, -12 HP." in state.log
    burn = next(status for status in state.statuses[enemy.id] if status.kind == "burn")
    assert burn.power == 2
    assert burn.duration == 3


def test_skill_not_enough_mp_consumes_turn_without_action():
    player = make_player(mp=5, intelligence=0)
    enemy = make_enemy(hp=50)
    state = start_combat(
        player, enemy, Randomizer(seed=7), skills={"strike": make_physical_skill(cost=10)}
    )
    assert player_action(state, CombatAction.SKILL, "strike") is False
    assert player.mp == 5
    assert enemy.stats["hp"] == 50
    assert "MP tidak cukup." in state.log


def test_skill_unknown_id_logs_and_consumes_turn():
    state = start_combat(make_player(), make_enemy(), Randomizer(seed=7))
    assert player_action(state, CombatAction.SKILL, "nope") is False
    assert "Skill tidak dikenal." in state.log


def test_player_action_item_heals_and_decrements_qty():
    player = make_player(hp=50)
    player.inventory.append({"id": "potion", "name": "Potion", "qty": 2, "heal": 30})
    state = start_combat(player, make_enemy(), Randomizer(seed=7))
    assert player_action(state, CombatAction.ITEM, "potion") is False
    assert player.hp == 82
    assert player.inventory == [{"id": "potion", "name": "Potion", "qty": 1, "heal": 30}]
    assert "Kamu memakai Potion, memulihkan 30 HP." in state.log


def test_use_item_heal_clamped_at_max_hp():
    player = make_player(hp=95)
    player.inventory.append({"id": "potion", "name": "Potion", "qty": 1, "heal": 30})
    state = start_combat(player, make_enemy(), Randomizer(seed=7))
    message = use_item(state, "potion")
    assert player.hp == max_hp(player)
    assert player.inventory == []


def test_use_item_qty_zero_removes_from_inventory():
    player = make_player(hp=50)
    player.inventory.append({"id": "potion", "name": "Potion", "qty": 1, "heal": 30})
    state = start_combat(player, make_enemy(), Randomizer(seed=7))
    use_item(state, "potion")
    assert player.inventory == []


def test_use_item_unknown_raises_value_error():
    state = start_combat(make_player(), make_enemy(), Randomizer(seed=7))
    with pytest.raises(ValueError, match="Item tidak dimiliki"):
        use_item(state, "nope")


def test_use_item_non_consumable_not_consumed():
    player = make_player(hp=50)
    player.inventory.append({"id": "sword", "name": "Sword", "qty": 1})
    state = start_combat(player, make_enemy(), Randomizer(seed=7))
    message = use_item(state, "sword")
    assert player.inventory == [{"id": "sword", "name": "Sword", "qty": 1}]
    assert "Item ini tidak bisa dipakai di pertarungan." in message
