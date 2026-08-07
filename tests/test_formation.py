"""Test sistem formasi (GDD §7, §18.2) — engine data-driven."""

from src.systems.formation import (
    formation_buff,
    formation_skill,
    load_formations,
)


def test_load_formations_memuat_semua_file():
    """Loader memuat semua formasi di data/formations/, keyed by id."""
    formations = load_formations()
    assert "jaring_naga" in formations
    assert "benteng_bumi" in formations
    assert "langit_pecah" in formations


def test_formation_buff_mengembalikan_stat_bonus():
    """Buff formasi berupa dict stat -> bonus int, tidak kosong."""
    buff = formation_buff("jaring_naga")
    assert isinstance(buff, dict)
    assert all(isinstance(v, int) for v in buff.values())
    assert buff  # tidak kosong


def test_formation_buff_menolak_id_tak_dikenal():
    """Formasi tak dikenal ditolak keras dengan ValueError."""
    try:
        formation_buff("tidak_ada")
    except ValueError:
        pass
    else:
        raise AssertionError("harus ValueError")


def test_formation_skill_mengembalikan_id_atau_none():
    """Skill formasi berupa id teknik atau None (jika formasi tanpa skill)."""
    skill = formation_skill("langit_pecah")
    assert skill is None or isinstance(skill, str)
