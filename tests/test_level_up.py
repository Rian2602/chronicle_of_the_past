import pytest
from src.models.player import Player, max_hp, max_mp
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


def test_on_level_up_increases_max_hp_and_mp():
    p = make_player()
    on_level_up(p)
    assert p.attribute_bonuses["hp"] == 5
    assert p.attribute_bonuses["mp"] == 3
    assert max_hp(p) == 105
    assert max_mp(p) == 13


def test_on_level_up_full_heals_damaged_player():
    p = make_player(hp=10, mp=1)
    on_level_up(p)
    assert p.hp == max_hp(p)
    assert p.mp == max_mp(p)


def test_on_level_up_full_heals_when_already_at_max():
    p = make_player()
    on_level_up(p)
    assert p.hp == max_hp(p)
    assert p.mp == max_mp(p)


def test_on_level_up_twice_accumulates_growth():
    p = make_player()
    on_level_up(p)
    on_level_up(p)
    assert p.level == 3
    assert p.attribute_bonuses["hp"] == 10
    assert p.attribute_bonuses["mp"] == 6


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
