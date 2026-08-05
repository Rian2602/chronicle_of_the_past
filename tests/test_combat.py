"""End-to-end combat integration tests (Task 7.7).

Drives the full fight loop through start_combat + player_action +
enemy_turn + next_turn exactly like the CLI would, using seeded
Randomizer instances. Whole-loop outcome asserts only — never asserts
specific RNG roll sequences or stream positions.
"""

from src.core.randomizer import Randomizer
from src.engine.combat_engine import (
    enemy_turn,
    next_turn,
    player_action,
    start_combat,
)
from src.models.combat_interfaces import CombatAction, CombatResult
from src.models.enemy import Enemy
from src.models.player import Player

REWARD = {"xp": 30, "gold": [6, 12]}


def make_player(
    agility=8, intelligence=7, attack=10, defense=5, level=1, hp=None, mp=None
):
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


def make_enemy(
    hp=10,
    agility=6,
    attack=5,
    defense=2,
    intelligence=3,
    level=2,
    reward=None,
    behavior="aggressive",
):
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
        reward=reward or {},
        behavior=behavior,
    )


def make_magic_skill(cost=4, power=8, effects=None):
    return {
        "id": "fire",
        "name": "Bola Api",
        "type": "magic",
        "cost": cost,
        "power": power,
        "target": "enemy",
        "effects": effects or [],
        "requires": [],
        "description": "",
    }


def make_physical_skill(cost=3, power=8):
    return {
        "id": "strike",
        "name": "Strike",
        "type": "physical",
        "cost": cost,
        "power": power,
        "target": "enemy",
        "effects": [],
        "requires": [],
        "description": "",
    }


def run_fight(
    player,
    enemy,
    rng=None,
    skills=None,
    action=CombatAction.ATTACK,
    choice=None,
):
    state = start_combat(
        player, enemy, rng or Randomizer(seed=7), skills=skills
    )
    while not state.over:
        player_action(state, action, choice)
        if state.over:
            break
        enemy_turn(state)
        next_turn(state)
    return state


def test_victory_full_fight_applies_xp_and_gold_rewards():
    player = make_player(attack=50, defense=20, agility=30)
    player.xp = 10
    player.gold = 5
    enemy = make_enemy(hp=10, attack=1, reward=REWARD)
    state = run_fight(player, enemy)
    assert state.result == CombatResult.VICTORY
    assert state.over is True
    assert state.player.hp > 0
    assert state.xp == 30
    assert 6 <= state.gold <= 12
    assert state.player.xp == 10 + 30
    assert state.player.gold == 5 + state.gold
    assert state.enemy.stats["hp"] == 0


def test_victory_scholar_xp_bonus_applied():
    player = make_player(attack=50, defense=20, agility=30)
    player.xp_bonus = 1.2
    enemy = make_enemy(hp=10, attack=1, reward=REWARD)
    state = run_fight(player, enemy)
    assert state.result == CombatResult.VICTORY
    assert state.xp == 30
    assert state.player.xp == 36
    assert "mendapat 36 XP" in state.log[-1]


def test_combat_does_not_mutate_shared_enemy():
    player = make_player(attack=50, defense=20, agility=30)
    enemy = make_enemy(hp=10, attack=1, reward=REWARD)
    run_fight(player, enemy)
    assert enemy.stats["hp"] == 10
    state2 = start_combat(player, enemy, Randomizer(seed=7))
    assert state2.enemy.stats["hp"] == 10


def test_defeat_full_fight_grants_no_rewards():
    player = make_player(attack=1, defense=0, agility=1, hp=5)
    player.xp = 10
    player.gold = 50
    enemy = make_enemy(hp=1000, attack=100, defense=0, agility=1, reward=REWARD)
    state = run_fight(player, enemy)
    assert state.result == CombatResult.DEFEAT
    assert state.over is True
    assert state.player.hp == 0
    assert state.xp == 0
    assert state.gold == 0
    assert state.player.xp == 10
    assert state.player.gold == 50


def test_burn_from_magic_skill_ticks_on_later_rounds():
    player = make_player(
        attack=0, intelligence=8, defense=5, agility=1, mp=50
    )
    player.learned_skills = ["fire"]
    enemy = make_enemy(hp=60, attack=1, intelligence=3)
    skills = {
        "fire": make_magic_skill(
            power=8, effects=[{"status": "burn", "power": 3, "duration": 3}]
        )
    }
    state = start_combat(player, enemy, Randomizer(seed=7), skills=skills)

    player_action(state, CombatAction.MAGIC, "fire")
    assert state.enemy.stats["hp"] == 50
    assert state.statuses[enemy.id][0].kind == "burn"
    assert state.statuses[enemy.id][0].duration == 3

    drops = []
    for _ in range(3):
        hp_before = state.enemy.stats["hp"]
        enemy_turn(state)
        drops.append(hp_before - state.enemy.stats["hp"])
        next_turn(state)
        player_action(state, CombatAction.DEFEND)

    assert drops == [3, 3, 3]
    assert state.enemy.stats["hp"] == 41
    assert state.statuses[enemy.id] == []
    assert "terkena luka bakar" in " ".join(state.log)
    assert state.round_no == 2


def test_physical_skill_in_full_fight_reaches_victory():
    player = make_player(attack=10, defense=5, agility=1, intelligence=7, mp=50)
    enemy = make_enemy(hp=30, attack=1, defense=2)
    skills = {"strike": make_physical_skill(cost=3, power=8)}
    state = run_fight(
        player, enemy, skills=skills, action=CombatAction.SKILL, choice="strike"
    )
    assert state.result == CombatResult.VICTORY
    assert state.over is True
    assert state.enemy.stats["hp"] == 0
    assert player.mp < 50


def test_magic_in_full_fight_reaches_victory():
    player = make_player(attack=1, intelligence=8, defense=5, agility=1, mp=50)
    enemy = make_enemy(hp=40, attack=1, intelligence=3)
    skills = {"fire": make_magic_skill(cost=4, power=8)}
    state = run_fight(
        player, enemy, skills=skills, action=CombatAction.MAGIC, choice="fire"
    )
    assert state.result == CombatResult.VICTORY
    assert state.over is True
    assert state.enemy.stats["hp"] == 0


def test_item_in_combat_heals_and_consumes_qty():
    player = make_player(hp=40)
    player.inventory.append(
        {"id": "potion", "name": "Potion", "qty": 2, "heal": 30}
    )
    enemy = make_enemy(hp=1000, attack=1)
    state = start_combat(player, enemy, Randomizer(seed=7))
    player_action(state, CombatAction.ITEM, "potion")
    assert player.hp == 72
    assert player.inventory == [
        {"id": "potion", "name": "Potion", "qty": 1, "heal": 30}
    ]
    assert "Kamu memakai Potion, memulihkan 30 HP." in state.log
    enemy_turn(state)
    assert state.over is False


def test_observe_in_combat_is_free_and_enemy_still_acts():
    player = make_player(intelligence=16, agility=1, defense=0, hp=100)
    enemy = make_enemy(hp=100, attack=1, agility=50)
    state = start_combat(player, enemy, Randomizer(seed=7))
    assert player_action(state, CombatAction.OBSERVE) is True
    assert state.observe_used is True
    assert "Goblin" in state.observe_info
    hp_before = player.hp
    enemy_turn(state)
    assert player.hp < hp_before
    assert state.over is False


def test_escape_success_ends_fight_without_rewards():
    player = make_player(agility=100)
    player.xp = 10
    player.gold = 50
    enemy = make_enemy(agility=6, reward=REWARD)
    state = start_combat(player, enemy, Randomizer(seed=7))
    assert player_action(state, CombatAction.ESCAPE) is False
    assert state.result == CombatResult.ESCAPED
    assert state.over is True
    assert state.xp == 0
    assert state.gold == 0
    assert player.xp == 10
    assert player.gold == 50


def test_escape_failure_grants_enemy_free_attack_and_fight_continues():
    player = make_player(agility=0, defense=0, hp=100)
    enemy = make_enemy(agility=100, attack=1)
    state = start_combat(player, enemy, Randomizer(seed=7))
    assert player_action(state, CombatAction.ESCAPE) is False
    assert state.over is False
    assert state.result is None
    assert "Gagal melarikan diri!" in state.log
    assert player.hp < 100


def test_defend_halves_enemy_physical_damage():
    player = make_player(attack=0, defense=0, agility=1, hp=100)
    enemy = make_enemy(hp=1000, attack=50, agility=50, defense=0)
    state = start_combat(player, enemy, Randomizer(seed=7))

    player_action(state, CombatAction.DEFEND)
    assert state.player_defending is True
    hp_before = player.hp
    enemy_turn(state)
    defended_loss = hp_before - player.hp
    next_turn(state)

    player_action(state, CombatAction.ATTACK)
    assert state.player_defending is False
    hp_before = player.hp
    enemy_turn(state)
    undefended_loss = hp_before - player.hp

    assert undefended_loss > defended_loss
