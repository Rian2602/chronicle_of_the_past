import pytest

from src.core.randomizer import Randomizer
from src.engine.combat_engine import (
    enemy_stats,
    enemy_turn,
    next_turn,
    player_action,
    player_stats,
    start_combat,
)
from src.models.combat_interfaces import CombatAction, CombatResult, StatusEffect
from src.models.enemy import Enemy
from src.models.player import Player, max_hp, max_mp


class ScriptedRandomizer:
    def __init__(self, rolls):
        self._rolls = list(rolls)

    def roll(self, low, high):
        return self._rolls.pop(0)


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


def make_enemy(hp=10, agility=6, attack=5, defense=2, intelligence=3, level=2, lore="", behavior="aggressive"):
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
        lore=lore,
        behavior=behavior,
    )


def _observe_state(intelligence):
    player = make_player(intelligence=intelligence, agility=6)
    enemy = make_enemy(hp=5, agility=6, defense=2, intelligence=3, lore="Makhluk kecil yang agresif.", behavior="aggressive")
    return start_combat(player, enemy, Randomizer(seed=7))


def test_start_combat_builds_state_with_initiative_order_player_first():
    player = make_player(agility=20)
    enemy = make_enemy(hp=8, agility=1)
    rng = ScriptedRandomizer([5, 5])
    state = start_combat(player, enemy, rng)
    assert state.round_no == 1
    assert state.current_index == 0
    assert state.over is False
    assert state.result is None
    assert state.log == []
    assert state.observe_used is False
    assert state.player_defending is False
    assert state.enemy_defending is False
    assert state.statuses == {}
    assert state.player is player
    assert state.enemy.id == enemy.id
    assert state.enemy is not enemy
    assert state.randomizer is rng
    assert state.skills == {}
    assert state.loot_resolver is None
    assert state.max_status_duration == 10
    assert state.turn_order == ["player", "goblin"]
    assert state.enemy.stats["max_hp"] == 8


def test_start_combat_enemy_first_when_faster():
    player = make_player(agility=1)
    enemy = make_enemy(agility=20)
    state = start_combat(player, enemy, ScriptedRandomizer([5, 5]))
    assert state.turn_order == ["goblin", "player"]
    assert state.current_index == 0


def test_player_stats_include_effective_and_derived():
    player = make_player(attack=12, agility=8, intelligence=7, level=3)
    player.attribute_bonuses["agility"] = 2
    state = start_combat(player, make_enemy(), Randomizer(seed=7))
    stats = player_stats(state)
    assert stats["attack"] == 12
    assert stats["agility"] == 10
    assert stats["hp_regen"] == 4
    assert stats["mana_regen"] == pytest.approx(1.4)


def test_enemy_stats_returns_enemy_stats():
    enemy = make_enemy()
    state = start_combat(make_player(), enemy, Randomizer(seed=7))
    assert enemy_stats(state) is state.enemy.stats
    assert enemy_stats(state) is not enemy.stats


def test_basic_attack_flow_reaches_victory():
    player = make_player(attack=50, agility=30, defense=20)
    enemy = make_enemy(hp=10, attack=1)
    state = start_combat(player, enemy, Randomizer(seed=7))
    while not state.over:
        player_action(state, CombatAction.ATTACK)
        if state.over:
            break
        enemy_turn(state)
        next_turn(state)
    assert state.result == CombatResult.VICTORY
    assert state.over is True
    assert state.enemy.stats["hp"] == 0
    assert state.player.hp > 0


def test_basic_attack_flow_reaches_defeat():
    player = make_player(attack=1, agility=1, defense=5, hp=5)
    enemy = make_enemy(hp=100, attack=10, agility=1, defense=2)
    state = start_combat(player, enemy, Randomizer(seed=7))
    while not state.over:
        player_action(state, CombatAction.ATTACK)
        if state.over:
            break
        enemy_turn(state)
        next_turn(state)
    assert state.result == CombatResult.DEFEAT
    assert state.over is True
    assert state.player.hp == 0


def test_defend_halves_enemy_damage_then_resets():
    player = make_player(attack=10, agility=8, defense=4)
    enemy = make_enemy(hp=30, attack=10)
    state = start_combat(player, enemy, ScriptedRandomizer([0, 0, 0, 0, 0, 0, 100, 0, 0, 0, 0, 100, 0, 0, 0, 100]))
    assert player_action(state, CombatAction.DEFEND) is False
    assert state.player_defending is True
    enemy_turn(state)
    assert state.player.hp == max_hp(player) - 4
    assert state.enemy_defending is False
    player_action(state, CombatAction.ATTACK)
    assert state.player_defending is False
    enemy_turn(state)
    assert state.player.hp == max_hp(player) - 4 + 2 - 8


def test_escape_success_high_agility():
    player = make_player(agility=30)
    enemy = make_enemy(agility=6)
    state = start_combat(player, enemy, ScriptedRandomizer([0, 0, 0, 0]))
    assert player_action(state, CombatAction.ESCAPE) is False
    assert state.result == CombatResult.ESCAPED
    assert state.over is True
    assert "berhasil melarikan diri" in state.log[-1]


def test_escape_failure_gives_enemy_free_attack():
    player = make_player(agility=1, defense=4)
    enemy = make_enemy(agility=20, attack=10)
    state = start_combat(player, enemy, ScriptedRandomizer([0, 0, 0, 50, 0, 0, 0, 100]))
    assert player_action(state, CombatAction.ESCAPE) is False
    assert state.over is False
    assert state.result is None
    assert "Gagal melarikan diri!" in state.log
    assert state.player.hp == max_hp(player) - 8


def test_escape_failure_kills_player_sets_defeat():
    player = make_player(agility=1, defense=0, hp=3)
    enemy = make_enemy(agility=20, attack=10)
    state = start_combat(player, enemy, ScriptedRandomizer([0, 0, 0, 50, 0, 0, 0, 100]))
    player_action(state, CombatAction.ESCAPE)
    assert state.result == CombatResult.DEFEAT
    assert state.over is True
    assert state.player.hp == 0


def test_observe_tier_below_8_name_and_hp_bar_only():
    state = _observe_state(7)
    assert player_action(state, CombatAction.OBSERVE) is True
    info = state.observe_info
    assert "Goblin" in info
    assert "HP" in info
    assert "Kelemahan" not in info
    assert "Ketahanan" not in info
    assert "HP tepat" not in info
    assert "Petunjuk" not in info


def test_observe_tier_8_to_12_adds_weakness():
    state = _observe_state(10)
    player_action(state, CombatAction.OBSERVE)
    info = state.observe_info
    assert "Kelemahan" in info
    assert "Ketahanan" not in info
    assert "HP tepat" not in info


def test_observe_tier_13_to_15_adds_resistance_and_lore():
    state = _observe_state(14)
    player_action(state, CombatAction.OBSERVE)
    info = state.observe_info
    assert "Kelemahan" in info
    assert "Ketahanan" in info
    assert "Lore" in info
    assert "HP tepat" not in info


def test_observe_tier_16_adds_exact_hp_and_hint():
    state = _observe_state(16)
    player_action(state, CombatAction.OBSERVE)
    info = state.observe_info
    assert "HP tepat" in info
    assert "Petunjuk" in info
    assert "5/5" in info


def test_observe_tiers_produce_different_info():
    infos = set()
    for intelligence in (7, 10, 14, 16):
        state = _observe_state(intelligence)
        player_action(state, CombatAction.OBSERVE)
        infos.add(state.observe_info)
    assert len(infos) == 4


def test_observe_once_only():
    state = _observe_state(10)
    assert player_action(state, CombatAction.OBSERVE) is True
    assert state.observe_used is True
    first = state.observe_info
    assert player_action(state, CombatAction.OBSERVE) is False
    assert state.observe_info == first
    assert state.log[-1] == "Kamu sudah mengamati musuh ini."


def test_status_ticks_at_start_of_player_turn():
    player = make_player()
    state = start_combat(player, make_enemy(), Randomizer(seed=7))
    state.statuses["player"] = [StatusEffect(kind="poison", duration=3, power=5)]
    player_action(state, CombatAction.DEFEND)
    assert state.player.hp == max_hp(player) - 5 + 2
    assert "terkena racun" in " ".join(state.log)
    assert state.statuses["player"] == [StatusEffect(kind="poison", duration=2, power=5)]


def test_enemy_status_tick_kills_and_sets_victory():
    enemy = make_enemy(hp=3)
    state = start_combat(make_player(), enemy, Randomizer(seed=7))
    state.statuses[enemy.id] = [StatusEffect(kind="poison", duration=1, power=5)]
    enemy_turn(state)
    assert state.result == CombatResult.VICTORY
    assert state.over is True
    assert state.enemy.stats["hp"] == 0


def test_player_status_tick_death_sets_defeat():
    player = make_player(hp=2)
    state = start_combat(player, make_enemy(), Randomizer(seed=7))
    state.statuses["player"] = [StatusEffect(kind="poison", duration=1, power=5)]
    player_action(state, CombatAction.ATTACK)
    assert state.result == CombatResult.DEFEAT
    assert state.over is True
    assert state.player.hp == 0


def test_next_turn_wraps_round_number():
    state = start_combat(make_player(), make_enemy(), Randomizer(seed=7))
    assert (state.current_index, state.round_no) == (0, 1)
    next_turn(state)
    assert (state.current_index, state.round_no) == (1, 1)
    next_turn(state)
    assert (state.current_index, state.round_no) == (0, 2)
    state.over = True
    next_turn(state)
    assert (state.current_index, state.round_no) == (0, 2)


def test_player_action_returns_false_when_over():
    state = start_combat(make_player(), make_enemy(), Randomizer(seed=7))
    state.over = True
    assert player_action(state, CombatAction.ATTACK) is False


@pytest.mark.parametrize("action", [CombatAction.SKILL, CombatAction.MAGIC])
def test_skill_magic_unknown_skill_raises_value_error(action):
    state = start_combat(make_player(), make_enemy(), Randomizer(seed=7))
    with pytest.raises(ValueError, match="Skill tidak dikenal"):
        player_action(state, action, "nope")


def test_item_unknown_id_raises_value_error():
    state = start_combat(make_player(), make_enemy(), Randomizer(seed=7))
    with pytest.raises(ValueError, match="Item tidak dimiliki"):
        player_action(state, CombatAction.ITEM, "nope")


def test_unknown_action_logged_and_not_free():
    state = start_combat(make_player(), make_enemy(), Randomizer(seed=7))
    assert player_action(state, "dance") is False
    assert state.log[-1] == "Aksi tidak dikenal."
