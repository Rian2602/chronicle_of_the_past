from src.models.combat_interfaces import CombatState, StatusEffect
from src.models.enemy import Enemy
from src.models.player import Player
from src.systems.status_system import apply_status, tick_statuses


def make_state(player_hp=100, enemy_hp=50, cap=10):
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
        player_defending=False,
        enemy_defending=False,
        statuses={},
        player=player,
        enemy=enemy,
        max_status_duration=cap,
    )


def test_dot_reapply_keeps_power_and_adds_duration():
    state = make_state()
    apply_status(state, "goblin", "poison", power=3, duration=2)
    apply_status(state, "goblin", "poison", power=9, duration=3)
    assert state.statuses["goblin"] == [
        StatusEffect(kind="poison", duration=5, power=3)
    ]


def test_dot_duration_capped_at_max_status_duration():
    state = make_state(cap=3)
    apply_status(state, "goblin", "poison", power=3, duration=2)
    apply_status(state, "goblin", "poison", power=3, duration=2)
    assert state.statuses["goblin"] == [
        StatusEffect(kind="poison", duration=3, power=3)
    ]
    state2 = make_state(cap=3)
    apply_status(state2, "goblin", "burn", power=5, duration=99)
    assert state2.statuses["goblin"] == [
        StatusEffect(kind="burn", duration=3, power=5)
    ]


def test_control_reapply_refreshes_duration_not_additive():
    state = make_state()
    apply_status(state, "goblin", "sleep", power=0, duration=3)
    apply_status(state, "goblin", "sleep", power=0, duration=1)
    assert state.statuses["goblin"] == [
        StatusEffect(kind="sleep", duration=1, power=0)
    ]


def test_new_kind_appends():
    state = make_state()
    apply_status(state, "goblin", "poison", power=3, duration=2)
    apply_status(state, "goblin", "burn", power=5, duration=2)
    assert [e.kind for e in state.statuses["goblin"]] == ["poison", "burn"]


def test_tick_deals_dot_damage_and_removes_expired():
    state = make_state(enemy_hp=20)
    apply_status(state, "goblin", "poison", power=3, duration=1)
    apply_status(state, "goblin", "burn", power=5, duration=2)
    messages = tick_statuses(state, "goblin")
    assert state.enemy.stats["hp"] == 12
    assert messages == [
        "Goblin terkena racun, -3 HP.",
        "Racun Goblin hilang.",
        "Goblin terkena luka bakar, -5 HP.",
    ]
    assert state.statuses["goblin"] == [
        StatusEffect(kind="burn", duration=1, power=5)
    ]


def test_tick_player_hp_mutated_for_player_actor():
    state = make_state(player_hp=50)
    apply_status(state, "player", "bleed", power=4, duration=2)
    messages = tick_statuses(state, "player")
    assert state.player.hp == 46
    assert messages == ["Rian terkena pendarahan, -4 HP."]
    assert state.statuses["player"] == [
        StatusEffect(kind="bleed", duration=1, power=4)
    ]


def test_tick_dot_damage_floor_at_zero():
    state = make_state(enemy_hp=2)
    apply_status(state, "goblin", "poison", power=5, duration=2)
    tick_statuses(state, "goblin")
    assert state.enemy.stats["hp"] == 0
    tick_statuses(state, "goblin")
    assert state.enemy.stats["hp"] == 0


def test_control_tick_only_decrements_no_damage():
    state = make_state(enemy_hp=20)
    apply_status(state, "goblin", "sleep", power=0, duration=2)
    messages = tick_statuses(state, "goblin")
    assert state.enemy.stats["hp"] == 20
    assert messages == []
    assert state.statuses["goblin"] == [
        StatusEffect(kind="sleep", duration=1, power=0)
    ]


def test_control_expiry_emits_removal_message():
    state = make_state(enemy_hp=20)
    apply_status(state, "goblin", "sleep", power=0, duration=1)
    messages = tick_statuses(state, "goblin")
    assert state.enemy.stats["hp"] == 20
    assert messages == ["Tidur Goblin hilang."]
    assert state.statuses["goblin"] == []


def test_empty_statuses_return_no_messages():
    state = make_state()
    assert tick_statuses(state, "goblin") == []
    assert tick_statuses(state, "player") == []
