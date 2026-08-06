"""Test engine combat: elemen, urutan, formula, dan alur battle (GDD §6)."""

import pytest

from src.engine.combat import (
    ELEMENT_ADVANTAGE,
    ELEMENT_CYCLE,
    Battle,
    compute_turn_order,
    crit_chance,
    dodge_chance,
    element_multiplier,
    load_enemies,
    load_techniques,
    miss_rate,
    physical_damage,
    technique_damage,
)
from src.models.combatant import (
    Combatant,
    combatant_from_companion,
    combatant_from_enemy,
    combatant_from_player,
)
from src.models.party import Companion
from src.models.player import Player

PLAYER_STATS = {
    "attack": 10,
    "defense": 4,
    "agility": 5,
    "intelligence": 6,
    "vitality": 5,
    "spirit": 5,
}
SKILLS = ["qi_slash", "flame_strike", "frost_bind"]


class _FixedRng:
    """RNG deterministik dengan nilai tetap."""

    def __init__(self, value: float) -> None:
        self.value = value

    def random(self) -> float:
        """Kembalikan nilai tetap."""
        return self.value


class _SeqRng:
    """RNG deterministik dengan deret nilai."""

    def __init__(self, values: list[float]) -> None:
        self._values = iter(values)

    def random(self) -> float:
        """Kembalikan nilai berikutnya dari deret."""
        return next(self._values)


def _player(skills: list[str] | None = SKILLS) -> Combatant:
    """Combatant pemain standar untuk test battle."""
    return combatant_from_player(
        Player(name="Akar", stats=dict(PLAYER_STATS)), skills=skills
    )


def _wolf() -> Combatant:
    """Combatant musuh Serigala Qi dari data."""
    enemies = load_enemies()
    wolf = next(enemy for enemy in enemies if enemy.id == "serigala_qi")
    return combatant_from_enemy(wolf)


def _bandit() -> Combatant:
    """Combatant musuh Bandit Perbatasan dari data."""
    enemies = load_enemies()
    bandit = next(enemy for enemy in enemies if enemy.id == "bandit_perbatasan")
    return combatant_from_enemy(bandit)


def _battle(player=None, wolf=None, rng=None) -> Battle:
    """Pertarungan 1v1 standar pemain vs serigala."""
    return Battle(
        [player or _player()],
        [wolf or _wolf()],
        techniques=load_techniques(),
        rng=rng,
    )


def test_siklus_elemen_lengkap():
    """Siklus Metal->Kayu->Tanah->Air->Api->Metal (§6.2)."""
    assert len(ELEMENT_CYCLE) == 5
    for index, element in enumerate(ELEMENT_CYCLE):
        assert ELEMENT_ADVANTAGE[element] == ELEMENT_CYCLE[(index + 1) % 5]


def test_element_multiplier_unggul_kalah_netral():
    """Multiplier: 1.5 unggul, 0.7 kalah, 1.0 netral/sama (§6.2)."""
    assert element_multiplier("metal", "wood") == pytest.approx(1.5)
    assert element_multiplier("metal", "fire") == pytest.approx(0.7)
    assert element_multiplier("metal", "metal") == pytest.approx(1.0)
    assert element_multiplier("netral", "wood") == pytest.approx(1.0)
    assert element_multiplier("water", "netral") == pytest.approx(1.0)


def test_urutan_giliran_agility_tertinggi_duluan():
    """Urutan giliran dihitung dari agility (tertinggi duluan) (§6.1)."""
    player = _player()  # agility 5
    wolf = _wolf()  # agility 4
    order = compute_turn_order([wolf, player])
    assert order == [player, wolf]


def test_urutan_giliran_tetap_sepanjang_battle():
    """Urutan tetap untuk seluruh pertarungan (§6.1)."""
    battle = _battle()
    before = list(battle.turn_order)
    battle.step("attack")
    assert list(battle.turn_order) == before


def test_probabilitas_kritikal_dodge_miss():
    """Kritikal/dodge/miss mengikuti agility dengan batas (§6.4/§17.2)."""
    assert crit_chance(5) == pytest.approx(0.055)
    assert crit_chance(500) == pytest.approx(0.25)
    assert dodge_chance(5) == pytest.approx(0.055)
    assert dodge_chance(1000) == pytest.approx(0.30)
    assert miss_rate(5) == pytest.approx(0.195)
    assert miss_rate(5000) == pytest.approx(0.05)


def test_physical_damage_mengikuti_formula():
    """Damage fisik: max(1, attack - defense/2) x mult x rand(0.9-1.1)."""
    assert physical_damage(10, 4, 1.0, _FixedRng(0.5)) == 8
    assert physical_damage(10, 4, 1.0, _FixedRng(0.0)) == 7
    assert physical_damage(10, 4, 1.0, _FixedRng(1.0)) == 9
    assert physical_damage(2, 99, 1.0, _FixedRng(0.5)) == 1


def test_technique_damage_mengikuti_formula():
    """Damage teknik: power + stat x 0.5 - resist, x mult x rand (§6.4)."""
    assert technique_damage(8, 10, 0, 0.7, _FixedRng(0.5)) == 9
    assert technique_damage(8, 10, 3, 1.0, _FixedRng(0.5)) == 10


def test_serangan_dasar_netral_dan_damage():
    """Serangan dasar netral x1.0 sesuai formula (§6.2/§6.4)."""
    player = _player()
    wolf = _wolf()
    battle = _battle(player=player, wolf=wolf, rng=_FixedRng(0.5))
    result = battle.step("attack")
    assert result.action == "attack"
    assert result.damage == 8  # 10 - 4/2 = 8
    assert wolf.hp == 30 - 8
    assert battle.current is wolf


def test_kritikal_menggandakan_damage():
    """Kritikal: damage x1.8 bila lemparan kritikal berhasil (§6.4)."""
    rng = _SeqRng([0.9, 0.9, 0.01, 0.5])  # lolos miss/dodge, kritikal
    battle = _battle(rng=rng)
    result = battle.step("attack")
    assert result.crit
    assert result.damage == 14  # 8 x 1.8 = 14.4


def test_serangan_meleset_tanpa_damage():
    """Serangan bisa meleset; tidak ada damage (§6.4)."""
    battle = _battle(rng=_SeqRng([0.01]))
    result = battle.step("attack")
    assert result.missed
    assert result.damage == 0


def test_serangan_dihindari_lawan():
    """Lawan bisa menghindari serangan (§6.4)."""
    battle = _battle(rng=_SeqRng([0.9, 0.01]))
    result = battle.step("attack")
    assert result.dodged
    assert result.damage == 0


def test_teknik_menguras_qi_dan_efek_status():
    """Teknik membayar qi dan menerapkan efek status (§6.3/§16)."""
    player = _player()
    wolf = _wolf()
    battle = _battle(player=player, wolf=wolf, rng=_FixedRng(0.5))
    result = battle.step("technique:flame_strike")
    assert result.qi_cost == 8
    assert player.qi == 2  # 10 - 8
    assert result.damage == 13  # 10 + int 6x0.5 = 13, api vs api = 1.0
    assert "burn" in result.statuses


def test_teknik_unggul_elemen_membekukan():
    """Teknik unggul elemen x1.5 dan menerapkan freeze (§6.2/§16)."""
    player = _player()
    wolf = _wolf()
    battle = _battle(player=player, wolf=wolf, rng=_FixedRng(0.5))
    result = battle.step("technique:frost_bind")
    assert result.damage == 14  # 9 x 1.5 = 13.5 -> 14
    assert "freeze" in result.statuses


def test_teknik_qi_tidak_cukup_ditolak():
    """Teknik ditolak bila qi tidak cukup (§6.3)."""
    player = _player()
    player.qi = 0
    battle = _battle(player=player, rng=_FixedRng(0.5))
    with pytest.raises(ValueError):
        battle.step("technique:qi_slash")


def test_teknik_qi_dinilai_sebelum_regen():
    """Kelayakan qi teknik dinilai sebelum regen awal giliran (konservatif)."""
    player = _player()
    player.qi = 4  # biaya qi_slash 5; regen +2 belum berlaku saat memilih
    battle = _battle(player=player, rng=_FixedRng(0.5))
    with pytest.raises(ValueError):
        battle.step("technique:qi_slash")


def test_teknik_tidak_dikuasai_ditolak():
    """Teknik yang tidak dikuasai pemain ditolak."""
    player = _player(skills=[])
    battle = _battle(player=player, rng=_FixedRng(0.5))
    with pytest.raises(ValueError):
        battle.step("technique:qi_slash")


def test_bertahan_mengurangi_damage():
    """Defend: damage masuk -50% hingga giliran berikutnya (§6.1)."""
    player = _player()
    wolf = _wolf()
    battle = _battle(player=player, wolf=wolf, rng=_FixedRng(0.5))
    battle.step("defend")
    result = battle.step_enemy()
    assert result.damage == 5  # flame_strike 11 dibagi 2
    assert player.hp == 80 - 5


def test_regen_qi_per_giliran():
    """Qi pulih per giliran dari meridian (§6.3/§17.2)."""
    player = _player()
    player.qi = 0
    battle = _battle(player=player, rng=_FixedRng(0.5))
    battle.step("defend")
    assert player.qi == 2


def test_kabur_berhasil_melawan_musuh_biasa():
    """Kabur berhasil melawan musuh non-bos (§6.1)."""
    battle = _battle()
    result = battle.step("escape")
    assert result.escaped
    assert battle.over
    assert battle.winner is None


def test_kabur_gagal_melawan_bos():
    """Kabur selalu gagal melawan bos (§11)."""
    wolf = _wolf()
    wolf.is_boss = True
    battle = _battle(wolf=wolf, rng=_FixedRng(0.5))
    result = battle.step("escape")
    assert not result.escaped
    assert not battle.over


def test_observe_gratis_tanpa_memakai_giliran():
    """Observe gratis: intel musuh tanpa memakai giliran (§6.1)."""
    battle = _battle()
    before = battle.current
    info = battle.observe()
    assert info[0]["name"] == "Serigala Qi"
    assert info[0]["hp"] == 30
    assert battle.current is before
    battle.step("attack")
    assert battle.turn_index == 1  # serangan pemain memakai giliran


def test_alur_pertarungan_pemain_menang():
    """Alur battle penuh: pemain menang setelah mengalahkan musuh."""
    player = _player()
    wolf = _wolf()
    battle = _battle(player=player, wolf=wolf, rng=_FixedRng(0.5))
    while not battle.over:
        if battle.current is player:
            battle.step("attack")
        else:
            battle.step_enemy()
    assert battle.winner == "allies"
    assert wolf.hp == 0
    assert player.hp > 0


def test_alur_pertarungan_musuh_menang():
    """Alur battle penuh: musuh menang saat pemain KO."""
    player = _player()
    player.hp = 5
    wolf = _wolf()
    battle = _battle(player=player, wolf=wolf, rng=_FixedRng(0.5))
    battle.step("attack")
    battle.step_enemy()
    assert battle.over
    assert battle.winner == "enemies"


def test_musuh_menggunakan_teknik_saat_qi_cukup():
    """AI musuh agresif memakai teknik bila qi cukup (§11)."""
    wolf = _wolf()
    battle = _battle(wolf=wolf, rng=_FixedRng(0.5))
    battle.step("attack")
    result = battle.step_enemy()
    assert result.action == "technique"
    assert result.damage == 11  # 10 + int 2x0.5 = 11


def test_musuh_menyerang_dasar_saat_qi_kurang():
    """AI musuh memakai serangan dasar bila qi tidak cukup."""
    wolf = _wolf()
    wolf.qi = 0
    battle = _battle(wolf=wolf, rng=_FixedRng(0.5))
    battle.step("attack")
    result = battle.step_enemy()
    assert result.action == "attack"
    assert result.damage == 5  # 7 - 4/2 = 5


def test_musuh_defensif_memakai_teknik_dengan_rng():
    """AI defensif memakai teknik bila lemparan < 0.5 (§11)."""
    battle = _battle(wolf=_bandit(), rng=_FixedRng(0.4))
    battle.step("attack")
    result = battle.step_enemy()
    assert result.action == "technique"


def test_musuh_defensif_menyerang_dasar_dengan_rng():
    """AI defensif memakai serangan dasar bila lemparan >= 0.5 (§11)."""
    battle = _battle(wolf=_bandit(), rng=_FixedRng(0.6))
    battle.step("attack")
    result = battle.step_enemy()
    assert result.action == "attack"


def test_serangan_dasar_mengisi_qi():
    """Serangan dasar mengisi sedikit qi (§18.3)."""
    player = _player()
    player.qi = 5
    battle = _battle(player=player, rng=_FixedRng(0.5))
    battle.step("attack")
    assert player.qi == 8  # regen 2 + bonus serangan 1


def _companion_uji() -> Companion:
    """Companion uji standar (stat Lin Wei data Task 1)."""
    return Companion(
        id="lin_wei",
        name="Lin Wei",
        tier="qi_condensation",
        element="wood",
        stats={
            "attack": 5,
            "defense": 3,
            "agility": 4,
            "intelligence": 3,
            "vitality": 5,
            "spirit": 3,
            "hp": 30,
            "qi": 8,
        },
        skills=["qi_slash"],
    )


def test_battle_dua_sekutu_keduanya_dapat_giliran_pemain():
    """Dengan 2 sekutu, tiap sekutu mendapat giliran perintah (GDD §6.1)."""
    player = _player()  # combatant_from_player, agility 5
    ally = combatant_from_companion(_companion_uji())
    enemy = _wolf()
    battle = Battle(
        allies=[player, ally],
        enemies=[enemy],
        techniques=load_techniques(),
        rng=_FixedRng(0.5),
    )
    acted: set[str] = set()
    while not battle.over and len(acted) < 6:
        if battle.current in battle.allies:
            acted.add(battle.current.name)
            battle.step("attack")  # pemain mengendalikan tiap sekutu
        else:
            battle.step_enemy()
    assert acted >= {"Akar", "Lin Wei"}


def test_target_musuh_acak_dengan_banyak_sekutu():
    """Musuh membidik sekutu hidup secara acak (bukan selalu slot 1)."""
    player = _player()
    ally = combatant_from_companion(_companion_uji())
    enemy = _wolf()
    battle = Battle(
        allies=[player, ally],
        enemies=[enemy],
        techniques=load_techniques(),
        rng=_FixedRng(0.5),
    )
    hit_targets: set[str] = set()
    while not battle.over:
        if battle.current in battle.allies:
            battle.step("attack")
        else:
            result = battle.step_enemy()
            if result is not None and result.target:
                hit_targets.add(result.target)
    assert "Lin Wei" in hit_targets
