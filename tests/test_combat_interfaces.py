from src.models.combat_interfaces import (
    CombatAction,
    CombatResult,
    CombatState,
    DamageResult,
    StatusEffect,
)
from src.models.enemy import Enemy


def test_combat_action_is_str_enum():
    assert issubclass(CombatAction, str)
    assert set(CombatAction.__members__) == {
        "ATTACK",
        "SKILL",
        "MAGIC",
        "ITEM",
        "OBSERVE",
        "ESCAPE",
        "DEFEND",
    }
    assert CombatAction.ATTACK == "attack"
    assert CombatAction.DEFEND == "defend"


def test_combat_result_is_str_enum():
    assert issubclass(CombatResult, str)
    assert set(CombatResult.__members__) == {"VICTORY", "DEFEAT", "ESCAPED"}
    assert CombatResult.VICTORY == "victory"
    assert CombatResult.ESCAPED == "escaped"


def test_status_effect_fields():
    effect = StatusEffect(kind="burn", duration=3, power=5)
    assert effect.kind == "burn"
    assert effect.duration == 3
    assert effect.power == 5


def test_damage_result_fields():
    dmg = DamageResult(damage=12, critical=True, missed=False)
    assert dmg.damage == 12
    assert dmg.critical is True
    assert dmg.missed is False


def test_combat_state_defaults():
    state = CombatState(
        round_no=0,
        turn_order=[],
        current_index=0,
        over=False,
        result=None,
        log=[],
        observe_used=False,
        player_defending=False,
        enemy_defending=False,
        statuses={},
    )
    assert state.xp == 0
    assert state.gold == 0
    assert state.loot == []
    assert state.observe_info is None
    assert state.player is None
    assert state.enemy is None
    assert state.randomizer is None
    assert state.skills == {}
    assert state.loot_resolver is None
    assert state.max_status_duration == 10


def test_combat_state_mutable_defaults_are_independent():
    kwargs = dict(
        round_no=0,
        turn_order=[],
        current_index=0,
        over=False,
        result=None,
        log=[],
        observe_used=False,
        player_defending=False,
        enemy_defending=False,
        statuses={},
    )
    a = CombatState(**kwargs)
    b = CombatState(**kwargs)
    a.loot.append("coin")
    a.skills["bash"] = {"power": 5}
    assert b.loot == []
    assert b.skills == {}


def test_enemy_new_field_defaults():
    e = Enemy(id="goblin", name="Goblin", level=2, stats={}, loot=[], skills=[])
    assert e.reward == {}
    assert e.behavior == "aggressive"
    assert e.tags == []


def test_enemy_positional_construction_backward_compat():
    e = Enemy("g", "Goblin", 2, {"hp": 10}, ["coin"], ["sk_bash"])
    assert e.id == "g"
    assert e.name == "Goblin"
    assert e.level == 2
    assert e.stats == {"hp": 10}
    assert e.loot == ["coin"]
    assert e.skills == ["sk_bash"]
    assert e.lore == ""
    assert e.reward == {}
    assert e.behavior == "aggressive"
    assert e.tags == []


def test_enemy_new_field_defaults_are_independent():
    e1 = Enemy(
        id="goblin", name="Goblin", level=2, stats={}, loot=[], skills=[]
    )
    e2 = Enemy(
        id="goblin", name="Goblin", level=2, stats={}, loot=[], skills=[]
    )
    e1.reward["gold"] = 5
    e1.tags.append("humanoid")
    assert e2.reward == {}
    assert e2.tags == []
