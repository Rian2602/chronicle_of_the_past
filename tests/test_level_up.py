import pytest

from src.models.player import Player
from src.systems.level_system import (
    LEVEL_CHOICES,
    apply_choice,
    learn_skill,
)


def make_player(**overrides):
    defaults = {
        "name": "Rian",
        "class_id": "warrior",
        "hp": 100,
        "mp": 10,
        "base_stats": {"hp": 100, "mp": 10},
        "attribute_bonuses": {
            "attack": 12,
            "defense": 14,
            "agility": 8,
            "intelligence": 7,
            "hp": 0,
            "mp": 0,
        },
    }
    defaults.update(overrides)
    return Player(**defaults)


def test_apply_attack_choice():
    p = make_player()
    apply_choice(p, "attack")
    assert p.attribute_bonuses["attack"] == 14


def test_apply_defense_choice():
    p = make_player()
    apply_choice(p, "defense")
    assert p.attribute_bonuses["defense"] == 16


def test_apply_agility_choice():
    p = make_player()
    apply_choice(p, "agility")
    assert p.attribute_bonuses["agility"] == 10


def test_apply_intelligence_choice():
    p = make_player()
    apply_choice(p, "intelligence")
    assert p.attribute_bonuses["intelligence"] == 9


def test_apply_hp_choice():
    p = make_player()
    apply_choice(p, "hp")
    assert p.attribute_bonuses["hp"] == 20


def test_apply_mp_choice():
    p = make_player()
    apply_choice(p, "mp")
    assert p.attribute_bonuses["mp"] == 10


def test_apply_skill_point_choice():
    p = make_player()
    apply_choice(p, "skill_point")
    assert p.skill_points == 1


def test_apply_choice_twice_accumulates():
    p = make_player()
    apply_choice(p, "attack")
    apply_choice(p, "attack")
    assert p.attribute_bonuses["attack"] == 16


def test_apply_choice_missing_attribute_starts_from_zero():
    p = make_player(attribute_bonuses={})
    apply_choice(p, "attack")
    assert p.attribute_bonuses["attack"] == 2


def test_apply_unknown_choice_raises_value_error():
    p = make_player()
    with pytest.raises(ValueError):
        apply_choice(p, "stealth")


def test_level_choices_shape():
    assert LEVEL_CHOICES == [
        ("attack", 2),
        ("defense", 2),
        ("agility", 2),
        ("intelligence", 2),
        ("hp", 20),
        ("mp", 10),
        ("skill_point", 1),
    ]


def test_learn_skill_spends_point_and_learns():
    p = make_player(skill_points=1)
    msg = learn_skill(p, "warrior", "shield_bash", ["shield_bash", "war_cry"])
    assert msg is None
    assert p.skill_points == 0
    assert "shield_bash" in p.learned_skills


def test_learn_skill_requires_skill_point():
    p = make_player(skill_points=0)
    msg = learn_skill(p, "warrior", "shield_bash", ["shield_bash"])
    assert msg == "Skill Point tidak cukup."
    assert p.learned_skills == []


def test_learn_skill_rejects_unlearnable_for_class():
    p = make_player(skill_points=1)
    msg = learn_skill(p, "warrior", "frost_bolt", ["shield_bash"])
    assert msg == "Kelas warrior tidak bisa mempelajari skill frost_bolt."
    assert p.skill_points == 1
    assert p.learned_skills == []


def test_learn_skill_rejects_already_learned():
    p = make_player(skill_points=1, learned_skills=["shield_bash"])
    msg = learn_skill(p, "warrior", "shield_bash", ["shield_bash"])
    assert msg == "Skill sudah kamu kuasai."
    assert p.skill_points == 1
