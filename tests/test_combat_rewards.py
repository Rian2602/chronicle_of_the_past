from src.core.randomizer import Randomizer
from src.engine.combat_engine import enemy_turn, next_turn, player_action, start_combat
from src.models.combat_interfaces import CombatAction, CombatResult
from src.models.enemy import Enemy
from src.models.player import Player

REWARD = {"xp": 30, "gold": [6, 12]}
LOOT = [{"id": "herb", "qty": 1}]


def make_player(attack=50, defense=5, agility=8, intelligence=7, hp=100, mp=20, level=1):
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


def make_enemy(hp=10, attack=1, defense=0, agility=1, intelligence=3, reward=None, behavior="aggressive"):
    return Enemy(
        id="goblin",
        name="Goblin",
        level=2,
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


def win_fight(player=None, enemy=None, rng=None, loot_resolver=None):
    player = player or make_player()
    enemy = enemy or make_enemy()
    state = start_combat(player, enemy, rng or Randomizer(seed=7), loot_resolver=loot_resolver)
    while not state.over:
        player_action(state, CombatAction.ATTACK)
        if state.over:
            break
        enemy_turn(state)
        next_turn(state)
    assert state.result == CombatResult.VICTORY
    return state


def test_victory_applies_exact_xp_from_reward():
    state = win_fight(enemy=make_enemy(reward=REWARD))
    assert state.xp == 30
    assert state.player.xp == 30
    assert any("Kamu mendapat" in line for line in state.log)


def test_victory_gold_within_inclusive_range_and_varies_across_seeds():
    golds = set()
    for seed in range(1, 9):
        state = win_fight(enemy=make_enemy(reward=REWARD), rng=Randomizer(seed=seed))
        assert 6 <= state.gold <= 12
        assert state.player.gold == state.gold
        golds.add(state.gold)
    assert len(golds) > 1


def test_victory_loot_via_resolver_appends_to_inventory():
    def resolver(enemy, randomizer):
        return [{"id": "herb", "qty": 1}]

    state = win_fight(enemy=make_enemy(reward=REWARD), loot_resolver=resolver)
    assert state.loot == LOOT
    assert state.player.inventory == LOOT


def test_victory_without_resolver_gives_empty_loot_and_unchanged_inventory():
    player = make_player()
    player.inventory = [{"id": "stone", "qty": 3}]
    state = win_fight(player=player, enemy=make_enemy(reward=REWARD))
    assert state.loot == []
    assert state.player.inventory == [{"id": "stone", "qty": 3}]


def test_victory_without_gold_key_guards_zero():
    state = win_fight(enemy=make_enemy(reward={"xp": 10}))
    assert state.xp == 10
    assert state.gold == 0
    assert state.player.gold == 0
    assert state.player.xp == 10


def test_no_rewards_on_defeat():
    player = make_player(attack=1, defense=0, agility=1, hp=5)
    player.inventory = [{"id": "stone", "qty": 3}]
    enemy = make_enemy(hp=1000, attack=100, agility=1, defense=0, reward=REWARD)
    state = start_combat(player, enemy, Randomizer(seed=7))
    while not state.over:
        player_action(state, CombatAction.ATTACK)
        if state.over:
            break
        enemy_turn(state)
        next_turn(state)
    assert state.result == CombatResult.DEFEAT
    assert state.xp == 0
    assert state.gold == 0
    assert state.player.xp == 0
    assert state.player.gold == 0
    assert state.player.inventory == [{"id": "stone", "qty": 3}]


def test_escape_does_not_fill_rewards():
    player = make_player(agility=100)
    player.xp = 10
    player.gold = 50
    player.inventory = [{"id": "stone", "qty": 3}]
    state = start_combat(player, make_enemy(reward=REWARD), Randomizer(seed=7))
    assert player_action(state, CombatAction.ESCAPE) is False
    assert state.result == CombatResult.ESCAPED
    assert state.over is True
    assert state.xp == 0
    assert state.gold == 0
    assert state.player.xp == 10
    assert state.player.gold == 50
    assert state.player.inventory == [{"id": "stone", "qty": 3}]
