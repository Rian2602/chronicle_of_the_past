import pytest
from src.models.player import Player
from src.systems import level_system
from src.systems.level_system import LEVEL_CHOICES, apply_choice, on_level_up


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
    assert p.attribute_bonuses["hp"] == 15


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


def test_on_level_up_increments_level():
    p = make_player(level=1)
    on_level_up(p)
    assert p.level == 2


def test_on_level_up_raises_hp_and_mp():
    p = make_player(hp=40, mp=3)
    on_level_up(p)
    assert p.hp == 50
    assert p.mp == 8


def test_on_level_up_clamps_hp_and_mp_at_max():
    p = make_player(hp=115, mp=14, base_stats={"hp": 100, "mp": 10}, attribute_bonuses={"hp": 20, "mp": 5})
    on_level_up(p)
    assert p.hp == 120
    assert p.mp == 15


def test_on_level_up_returns_level_choices():
    p = make_player()
    assert on_level_up(p) is LEVEL_CHOICES


def test_level_choices_shape():
    assert LEVEL_CHOICES == [
        ("attack", 2),
        ("defense", 2),
        ("agility", 2),
        ("intelligence", 2),
        ("hp", 15),
        ("mp", 10),
        ("skill_point", 1),
    ]
