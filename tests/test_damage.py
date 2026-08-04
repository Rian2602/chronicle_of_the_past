from src.core.randomizer import Randomizer
from src.engine.combat_engine import magic_damage, resolve_hit
from src.models.combat_interfaces import CombatState, DamageResult, StatusEffect
from src.models.enemy import Enemy
from src.models.player import Player


class ScriptedRandomizer:
    def __init__(self, rolls):
        self._rolls = list(rolls)

    def roll(self, low, high):
        return self._rolls.pop(0)


def make_state(
    player_hp=100, enemy_hp=50, player_defending=False, enemy_defending=False
):
    player = Player(
        name="Rian", class_id="warrior", hp=player_hp, mp=10, base_stats={}
    )
    enemy = Enemy(
        id="goblin",
        name="Goblin",
        level=2,
        stats={"hp": enemy_hp},
        loot=[],
        skills=[],
    )
    return CombatState(
        round_no=1,
        turn_order=["player", "goblin"],
        current_index=0,
        over=False,
        result=None,
        log=[],
        observe_used=False,
        player_defending=player_defending,
        enemy_defending=enemy_defending,
        statuses={},
        player=player,
        enemy=enemy,
        randomizer=Randomizer(seed=7),
    )


ATTACKER = {"attack": 10, "defense": 5, "agility": 8, "intelligence": 15}
DEFENDER = {"defense": 5, "agility": 5, "intelligence": 3}


def test_magic_damage_formula():
    assert magic_damage(22, 15, 1.8) == 28
    assert magic_damage(5, 1, 0.6) == 5


def test_magic_damage_min_one_high_resistance():
    assert magic_damage(1, 1, 12) == 1


def test_resolve_hit_physical_uses_damage_roll_exact():
    state = make_state()
    state.randomizer = ScriptedRandomizer([0, 0, 0])
    result = resolve_hit(state, ATTACKER, DEFENDER, "goblin")
    assert result == DamageResult(damage=12, critical=True, missed=False)
    assert state.enemy.stats["hp"] == 38
    assert state.log == ["Kritikal! Goblin terkena -12 HP."]


def test_resolve_hit_physical_miss_passthrough_no_hp_change():
    state = make_state()
    state.randomizer = ScriptedRandomizer([0, 100, 100])
    result = resolve_hit(state, ATTACKER, DEFENDER, "goblin")
    assert result == DamageResult(damage=0, critical=False, missed=True)
    assert state.enemy.stats["hp"] == 50
    assert state.log == ["Seranganmu meleset!"]


def test_resolve_hit_halved_when_enemy_defending():
    state = make_state(enemy_defending=True)
    state.randomizer = ScriptedRandomizer([0, 0, 100])
    result = resolve_hit(state, ATTACKER, DEFENDER, "goblin")
    assert result == DamageResult(damage=4, critical=False, missed=False)
    assert state.enemy.stats["hp"] == 46


def test_resolve_hit_halved_when_player_defending():
    state = make_state(player_defending=True)
    state.randomizer = ScriptedRandomizer([0, 0, 100])
    result = resolve_hit(state, ATTACKER, DEFENDER, "player")
    assert result == DamageResult(damage=4, critical=False, missed=False)
    assert state.player.hp == 96
    assert state.log == ["Goblin menyerang Rian, -4 HP."]


def test_resolve_hit_magic_exact_damage():
    state = make_state()
    state.randomizer = ScriptedRandomizer([0, 100, 100])
    result = resolve_hit(
        state, ATTACKER, DEFENDER, "goblin", power=22, is_magic=True
    )
    assert result == DamageResult(damage=28, critical=False, missed=False)
    assert state.enemy.stats["hp"] == 22
    assert state.log == ["Kamu melontarkan mantra ke Goblin, -28 HP."]


def test_resolve_hit_magic_never_missed_even_with_bad_accuracy():
    state = make_state()
    state.randomizer = ScriptedRandomizer([0, 100, 100])
    result = resolve_hit(
        state,
        {"attack": 0, "defense": 0, "agility": 0, "intelligence": 1},
        {"defense": 0, "agility": 0, "intelligence": 1},
        "goblin",
        power=5,
        is_magic=True,
    )
    assert result == DamageResult(damage=5, critical=False, missed=False)


def test_resolve_hit_magic_never_critical():
    state = make_state()
    state.randomizer = ScriptedRandomizer([0, 0, 0])
    result = resolve_hit(
        state, ATTACKER, DEFENDER, "goblin", power=22, is_magic=True
    )
    assert result.critical is False
    assert result.missed is False


def test_resolve_hit_magic_min_one_damage():
    state = make_state()
    state.randomizer = ScriptedRandomizer([0, 100, 100])
    result = resolve_hit(
        state,
        {"attack": 0, "defense": 0, "agility": 0, "intelligence": 1},
        {"defense": 0, "agility": 0, "intelligence": 20},
        "goblin",
        power=1,
        is_magic=True,
    )
    assert result == DamageResult(damage=1, critical=False, missed=False)
    assert state.enemy.stats["hp"] == 49


def test_resolve_hit_magic_not_halved_by_defend():
    state = make_state(enemy_defending=True)
    state.randomizer = ScriptedRandomizer([0, 100, 100])
    result = resolve_hit(
        state, ATTACKER, DEFENDER, "goblin", power=22, is_magic=True
    )
    assert result == DamageResult(damage=28, critical=False, missed=False)
    assert state.enemy.stats["hp"] == 22


def test_resolve_hit_effects_applied_to_enemy_defender():
    state = make_state()
    state.randomizer = ScriptedRandomizer([0, 0, 100])
    resolve_hit(
        state,
        ATTACKER,
        DEFENDER,
        "goblin",
        effects=[{"kind": "poison", "power": 3, "duration": 2}],
    )
    assert state.statuses["goblin"] == [
        StatusEffect(kind="poison", duration=2, power=3)
    ]
    assert "player" not in state.statuses


def test_resolve_hit_effects_applied_to_player_defender():
    state = make_state()
    state.randomizer = ScriptedRandomizer([0, 0, 100])
    resolve_hit(
        state,
        ATTACKER,
        DEFENDER,
        "player",
        effects=[{"kind": "bleed", "power": 4, "duration": 2}],
    )
    assert state.statuses["player"] == [
        StatusEffect(kind="bleed", duration=2, power=4)
    ]
    assert "goblin" not in state.statuses


def test_resolve_hit_miss_does_not_apply_effects():
    state = make_state()
    state.randomizer = ScriptedRandomizer([0, 100, 100])
    resolve_hit(
        state,
        ATTACKER,
        DEFENDER,
        "goblin",
        effects=[{"kind": "poison", "power": 3, "duration": 2}],
    )
    assert state.statuses == {}


def test_resolve_hit_effects_none_appends_no_statuses():
    state = make_state()
    state.randomizer = ScriptedRandomizer([0, 100, 100])
    resolve_hit(state, ATTACKER, DEFENDER, "goblin")
    assert state.statuses == {}


def test_resolve_hit_damage_floored_at_zero_hp():
    state = make_state(enemy_hp=5)
    state.randomizer = ScriptedRandomizer([5, 0, 100])
    resolve_hit(state, ATTACKER, DEFENDER, "goblin")
    assert state.enemy.stats["hp"] == 0


def test_resolve_hit_player_hp_floored_at_zero():
    state = make_state(player_hp=3)
    state.randomizer = ScriptedRandomizer([5, 0, 100])
    resolve_hit(state, ATTACKER, DEFENDER, "player")
    assert state.player.hp == 0


def test_resolve_hit_appends_log_line():
    state = make_state()
    state.randomizer = ScriptedRandomizer([0, 0, 100])
    resolve_hit(state, ATTACKER, DEFENDER, "goblin")
    assert len(state.log) == 1
    assert "Goblin" in state.log[0]
