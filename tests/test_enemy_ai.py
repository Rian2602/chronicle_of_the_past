from src.core.randomizer import Randomizer
from src.engine.combat_engine import enemy_turn, start_combat
from src.models.combat_interfaces import CombatResult
from src.models.enemy import Enemy
from src.models.player import Player, max_hp


def make_player(agility=8, intelligence=7, defense=4, attack=10, level=1, hp=None, mp=None):
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


def make_enemy(behavior="aggressive", hp=100, mp=20, attack=10, agility=6, intelligence=3, skills=None):
    return Enemy(
        id="goblin",
        name="Goblin",
        level=2,
        stats={
            "attack": attack,
            "defense": 2,
            "hp": hp,
            "mp": mp,
            "agility": agility,
            "intelligence": intelligence,
        },
        loot=[],
        skills=skills or [],
        behavior=behavior,
    )


SKILLS = {
    "rend": {"id": "rend", "name": "Robek", "type": "physical", "cost": 5, "power": 0},
    "charge": {"id": "charge", "name": "Seruduk", "type": "physical", "cost": 20, "power": 5},
    "bash": {"id": "bash", "name": "Hantaman", "type": "physical", "cost": 6, "power": 0},
    "zap": {"id": "zap", "name": "Sengatan", "type": "magic", "cost": 8, "power": 10},
    "tonic": {"id": "tonic", "name": "Ramuan Goblin", "type": "heal", "cost": 10, "heal": 90},
}


def test_aggressive_uses_first_affordable_skill_and_skips_unaffordable():
    enemy = make_enemy(mp=10, skills=["rend", "charge"])
    state = start_combat(make_player(), enemy, Randomizer(seed=7), skills=dict(SKILLS))
    enemy_turn(state)
    assert state.enemy.stats["mp"] == 5


def test_aggressive_uses_highest_priority_of_two_affordable_skills():
    skills = {
        "spark": {"id": "spark", "name": "Percikan", "type": "magic", "cost": 4, "power": 5},
        "fireball": {"id": "fireball", "name": "Bola Api", "type": "magic", "cost": 8, "power": 40},
    }
    enemy = make_enemy(mp=20, skills=["spark", "fireball"])
    state = start_combat(make_player(), enemy, Randomizer(seed=7), skills=skills)
    enemy_turn(state)
    assert state.enemy.stats["mp"] == 16
    assert "melontarkan mantra ke Rian, -2 HP." in " ".join(state.log)


def test_aggressive_falls_back_to_basic_attack_when_nothing_affordable():
    enemy = make_enemy(mp=4, attack=10, agility=34, skills=["rend", "charge"])
    state = start_combat(make_player(), enemy, Randomizer(seed=7), skills=dict(SKILLS))
    enemy_turn(state)
    assert state.enemy.stats["mp"] == 4
    assert state.player.hp < max_hp(state.player)


def test_aggressive_never_sets_enemy_defending():
    enemy = make_enemy(mp=20, skills=["rend", "charge"])
    state = start_combat(make_player(), enemy, Randomizer(seed=7), skills=dict(SKILLS))
    enemy_turn(state)
    assert state.enemy_defending is False
    enemy_turn(state)
    assert state.enemy_defending is False


def test_unknown_behavior_falls_back_to_aggressive():
    enemy = make_enemy(behavior="chaotic", mp=10, skills=["rend", "charge"])
    state = start_combat(make_player(), enemy, Randomizer(seed=7), skills=dict(SKILLS))
    enemy_turn(state)
    assert state.enemy.stats["mp"] == 5
    assert state.enemy_defending is False


def test_defensive_below_30_percent_heals_and_consumes_mp():
    enemy = make_enemy(behavior="defensive", hp=100, mp=20, skills=["tonic"])
    state = start_combat(make_player(), enemy, Randomizer(seed=7), skills=dict(SKILLS))
    state.enemy.stats["hp"] = 20
    enemy_turn(state)
    assert state.enemy.stats["hp"] == 100
    assert state.enemy.stats["mp"] == 10
    assert "memulihkan 90 HP" in state.log[-1]


def test_defensive_below_30_percent_with_unaffordable_heal_defends():
    enemy = make_enemy(behavior="defensive", hp=100, mp=5, skills=["tonic"])
    state = start_combat(make_player(), enemy, Randomizer(seed=7), skills=dict(SKILLS))
    state.enemy.stats["hp"] = 20
    enemy_turn(state)
    assert state.enemy.stats["hp"] == 20
    assert state.enemy.stats["mp"] == 5
    assert state.enemy_defending is True


def test_defensive_without_heal_defends_then_attacks_and_clears_flag():
    enemy = make_enemy(behavior="defensive", hp=100, attack=10, agility=34, skills=["rend"])
    state = start_combat(make_player(), enemy, Randomizer(seed=7), skills=dict(SKILLS))
    state.enemy.stats["hp"] = 20
    enemy_turn(state)
    assert state.enemy_defending is True
    assert "bertahan" in state.log[-1]
    assert state.player.hp == max_hp(state.player)
    enemy_turn(state)
    assert state.enemy_defending is False
    assert state.player.hp < max_hp(state.player)


def test_mage_prefers_magic_skill_over_physical():
    enemy = make_enemy(behavior="mage", mp=20, skills=["bash", "zap"])
    state = start_combat(make_player(), enemy, Randomizer(seed=7), skills=dict(SKILLS))
    enemy_turn(state)
    assert state.enemy.stats["mp"] == 12
    assert "melontarkan mantra" in " ".join(state.log)


def test_mage_falls_back_to_basic_attack_when_nothing_affordable():
    enemy = make_enemy(behavior="mage", mp=3, attack=10, agility=34, skills=["zap", "bash"])
    state = start_combat(make_player(), enemy, Randomizer(seed=7), skills=dict(SKILLS))
    enemy_turn(state)
    assert state.enemy.stats["mp"] == 3
    assert state.player.hp < max_hp(state.player)


def test_coward_below_20_percent_failed_escape_ends_turn_without_attack():
    enemy = make_enemy(behavior="coward", hp=100, skills=["rend"])
    state = start_combat(make_player(), enemy, Randomizer(seed=7), skills=dict(SKILLS))
    state.enemy.stats["hp"] = 15
    enemy_turn(state)
    assert "mencoba kabur tapi gagal" in " ".join(state.log)
    assert state.over is False
    assert state.result is None
    assert state.player.hp == max_hp(state.player)
    assert state.enemy_defending is False


def test_coward_above_20_percent_defends():
    enemy = make_enemy(behavior="coward", hp=100, skills=["rend"])
    state = start_combat(make_player(), enemy, Randomizer(seed=7), skills=dict(SKILLS))
    state.enemy.stats["hp"] = 50
    enemy_turn(state)
    assert state.enemy_defending is True
    assert "bertahan" in state.log[-1]
    assert state.player.hp == max_hp(state.player)


def test_enemy_physical_skill_applies_status_effects():
    skills = {
        "venom_bite": {
            "id": "venom_bite",
            "name": "Gigitan Beracun",
            "type": "physical",
            "cost": 5,
            "power": 0,
            "effects": [{"status": "poison", "power": 4, "duration": 2}],
        }
    }
    enemy = make_enemy(mp=10, skills=["venom_bite"])
    state = start_combat(make_player(), enemy, Randomizer(seed=7), skills=skills)
    enemy_turn(state)
    assert state.enemy.stats["mp"] == 5
    poison = state.statuses["player"][0]
    assert poison.kind == "poison"
    assert poison.power == 4
    assert poison.duration == 2


def test_enemy_magic_skill_killing_player_sets_defeat():
    skills = {"zap": {"id": "zap", "name": "Sengatan", "type": "magic", "cost": 8, "power": 500}}
    enemy = make_enemy(behavior="mage", mp=20, attack=1, skills=["zap"])
    state = start_combat(make_player(hp=50, defense=200), enemy, Randomizer(seed=7), skills=skills)
    enemy_turn(state)
    assert state.result == CombatResult.DEFEAT
    assert state.over is True
    assert state.player.hp == 0


def test_same_seed_produces_identical_outcome_and_log():
    results = []
    for _ in range(2):
        enemy = make_enemy(mp=20, skills=["rend", "charge"])
        state = start_combat(make_player(), enemy, Randomizer(seed=42), skills=dict(SKILLS))
        enemy_turn(state)
        results.append((state.player.hp, state.enemy.stats["mp"], tuple(state.log)))
    assert results[0] == results[1]
