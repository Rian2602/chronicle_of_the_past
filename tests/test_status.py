"""Test status effects combat (GDD §16)."""

import pytest

from src.engine.combat import (
    STATUS_DURATIONS,
    Battle,
    apply_status,
    effective_stats,
    load_enemies,
    load_techniques,
    tick_statuses,
)
from src.models.combatant import (
    Combatant,
    combatant_from_enemy,
    combatant_from_player,
)
from src.models.player import Player

PLAYER_STATS = {
    "attack": 10,
    "defense": 4,
    "agility": 5,
    "intelligence": 6,
    "vitality": 5,
    "spirit": 5,
}


class _FixedRng:
    """RNG deterministik dengan nilai tetap."""

    def __init__(self, value: float) -> None:
        self.value = value

    def random(self) -> float:
        """Kembalikan nilai tetap."""
        return self.value


def _player() -> Combatant:
    """Combatant pemain standar (hp_max 80, qi_max 10)."""
    return combatant_from_player(Player(name="Akar", stats=dict(PLAYER_STATS)))


def _wolf() -> Combatant:
    """Combatant musuh Serigala Qi dari data."""
    enemies = load_enemies()
    wolf = next(enemy for enemy in enemies if enemy.id == "serigala_qi")
    return combatant_from_enemy(wolf)


def _battle(player, wolf) -> Battle:
    """Pertarungan 1v1 dengan RNG tetap."""
    return Battle(
        [player], [wolf], techniques=load_techniques(), rng=_FixedRng(0.5)
    )


def test_durasi_default_sesuai_tabel():
    """Durasi default tiap status sesuai tabel §16."""
    assert STATUS_DURATIONS == {
        "poison": 3,
        "burn": 3,
        "bleed": 2,
        "stun": 1,
        "freeze": 2,
        "charm": 2,
        "slow": 3,
        "seal": 2,
        "weaken": 3,
        "barrier": 3,
        "strengthen": 3,
        "haste": 3,
        "qi_flow": 3,
    }


def test_racun_damage_4_persen_max_hp():
    """Racun: 4% max HP per giliran, durasi 3 (§16)."""
    unit = _player()
    apply_status(unit, "poison")
    events = tick_statuses(unit)
    assert unit.hp == 80 - 3  # int(80 x 0.04) = 3
    assert len(events) == 1
    assert unit.statuses["poison"]["turns"] == 2


def test_dot_tidak_menumpuk_hanya_refresh():
    """Dot tidak menumpuk; status baru me-refresh durasi (§16)."""
    unit = _player()
    apply_status(unit, "poison")
    tick_statuses(unit)
    apply_status(unit, "poison")
    assert unit.statuses["poison"]["turns"] == 3
    assert unit.hp == 77  # hanya satu tick yang terjadi


def test_terbakar_dan_berdarah_pakai_power():
    """Terbakar/berdarah memakai power tetap dari sumber (§16)."""
    unit = _player()
    apply_status(unit, "burn", power=4)
    tick_statuses(unit)
    assert unit.hp == 80 - 4
    unit2 = _player()
    apply_status(unit2, "bleed", power=3)
    tick_statuses(unit2)
    assert unit2.hp == 80 - 3


def test_status_kedaluwarsa_setelah_durasi():
    """Status hilang setelah durasinya habis (§16)."""
    unit = _player()
    apply_status(unit, "burn", power=4)  # durasi default 3
    for _ in range(3):
        tick_statuses(unit)
    assert "burn" not in unit.statuses
    assert unit.hp == 80 - 12


def test_buff_sejenis_menggantikan_bukan_menumpuk():
    """Buff/debuff sejenis digantikan status baru (§16)."""
    unit = _player()
    apply_status(unit, "weaken", duration=3)
    apply_status(unit, "weaken", duration=2)
    assert unit.statuses["weaken"]["turns"] == 2


def test_modifier_debuff_pada_stat():
    """Weaken/slow menurunkan stat efektif (§16)."""
    unit = _player()
    apply_status(unit, "weaken")
    apply_status(unit, "slow")
    stats = effective_stats(unit)
    assert stats["attack"] == int(10 * 0.75)
    assert stats["agility"] == int(5 * 0.70)


def test_modifier_buff_pada_stat():
    """Strengthen/haste/barrier menaikkan stat efektif (§16)."""
    unit = _player()
    apply_status(unit, "strengthen")
    apply_status(unit, "haste")
    apply_status(unit, "barrier")
    stats = effective_stats(unit)
    assert stats["attack"] == int(10 * 1.25)
    assert stats["agility"] == int(5 * 1.25)
    assert stats["defense"] == int(4 * 1.30)


def test_boss_kebal_status_kontrol():
    """Boss kebal terhadap stun/freeze/charm (§16)."""
    wolf = _wolf()
    wolf.is_boss = True
    for control in ("stun", "freeze", "charm"):
        assert not apply_status(wolf, control)
    assert wolf.statuses == {}
    assert apply_status(wolf, "weaken")  # debuff non-kontrol tetap masuk


def test_stun_melewatkan_satu_giliran():
    """Stun: skip 1 giliran (§16)."""
    player = _player()
    wolf = _wolf()
    apply_status(wolf, "stun")
    battle = _battle(player, wolf)
    battle.step("attack")
    battle.step_enemy()  # giliran dilewati
    assert "stun" not in wolf.statuses
    assert battle.current is player
    assert wolf.hp == 30 - 8  # hanya damage dari pemain


def test_freeze_melewatkan_dua_giliran():
    """Freeze: skip 2 giliran dan defense +50% (§16)."""
    player = _player()
    wolf = _wolf()
    apply_status(wolf, "freeze")
    battle = _battle(player, wolf)
    battle.step("attack")  # damage 10 - 6/2 = 7 (defense +50%)
    battle.step_enemy()
    battle.step("attack")
    battle.step_enemy()
    assert "freeze" not in wolf.statuses
    assert wolf.hp == 30 - 14  # dua serangan x 7


def test_seal_memblokir_regen_dan_teknik():
    """Seal: qi regen 0 dan teknik diblokir (§16)."""
    player = _player()
    player.qi = 0
    apply_status(player, "seal")
    battle = _battle(player, _wolf())
    with pytest.raises(ValueError):
        battle.step("technique:qi_slash")
    assert player.qi == 0  # tidak ada regen


def test_aliran_qi_menambah_regen_50_persen():
    """Qi flow: regen qi +50% (§16)."""
    player = _player()
    player.qi = 0
    apply_status(player, "qi_flow")
    battle = _battle(player, _wolf())
    battle.step("defend")
    assert player.qi == 3  # int(2 x 1.5)


def test_aksi_invalid_tidak_menggandakan_efek_awal_giliran():
    """Aksi invalid ditolak sebelum awal giliran (tanpa regen/tick ganda)."""
    player = combatant_from_player(
        Player(name="Akar", stats=dict(PLAYER_STATS)),
        skills=["flame_strike"],
    )
    apply_status(player, "burn", power=4)
    player.qi = 0
    battle = _battle(player, _wolf())
    hp_before = player.hp
    qi_before = player.qi
    with pytest.raises(ValueError):
        battle.step("technique:flame_strike")  # biaya 8 > qi 0
    # Validasi mendahului awal giliran: burn tidak tick, qi tidak regen.
    assert player.hp == hp_before
    assert player.qi == qi_before
    # Percobaan ulang dengan aksi valid: burn tick tepat satu kali (bukan dua).
    battle.step("defend")
    assert player.hp == hp_before - 4


def test_pesona_tanpa_sekutu_tidak_efektif():
    """Charm tanpa sekutu tidak mengubah aksi (1v1) (§16)."""
    player = _player()
    apply_status(player, "charm")
    battle = _battle(player, _wolf())
    result = battle.step("attack")
    assert result.damage == 8  # tetap bisa bertindak normal


def test_pesona_menyerang_sekutu_sendiri():
    """Charm: menyerang sekutu sendiri bila ada anggota tim (§16)."""
    a = _player()
    b = combatant_from_player(Player(name="Lin", stats=dict(PLAYER_STATS)))
    wolf = _wolf()
    apply_status(a, "charm")
    battle = Battle(
        [a, b], [wolf], techniques=load_techniques(), rng=_FixedRng(0.5)
    )
    battle.step("attack")  # a terpesona -> menyerang b
    assert b.hp == 80 - 8
    assert battle.current is b
