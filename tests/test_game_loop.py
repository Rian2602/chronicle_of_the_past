"""Test GameSession — alur main Fase 0 (GDD §18, §19.1, §20.4, §23)."""

import random

from src.core.game_loop import GameSession
from src.core.input import Command
from src.core.save import slot_exists
from src.core.state import FACTIONS


def _session(tmp_path, seed: int = 7) -> GameSession:
    """Sesi dengan rng deterministik dan folder save sementara."""
    return GameSession(save_dir=tmp_path, rng=random.Random(seed))


def _dispatch(session: GameSession, raw: str) -> list[str]:
    """Parse + kirim perintah; kembalikan pesan."""
    command = Command(name=raw.split()[0], args=tuple(raw.split()[1:]), raw=raw)
    return session.dispatch(command)


def test_new_game_membuat_state_awal(tmp_path):
    """State baru: nama, lokasi awal, waktu, reputasi 0, hp/qi penuh."""
    session = _session(tmp_path)
    session.new_game("Akar")
    state = session.state
    assert state.player.name == "Akar"
    assert state.location == "village_emberfall"
    assert state.time.day == 1
    assert state.time.hour == 8
    assert state.reputation == {faction: 0 for faction in FACTIONS}
    assert state.player.hp == state.player.hp_max
    assert state.player.qi == state.player.qi_max
    assert state.flags["map_ashfall_forest_unlocked"] is True


def test_status_berisi_info_pemain(tmp_path):
    """Perintah status menampilkan nama, lokasi, dan waktu."""
    session = _session(tmp_path)
    session.new_game("Akar")
    lines = _dispatch(session, "status")
    joined = "\n".join(lines)
    assert "Akar" in joined
    assert "village_emberfall" in joined
    assert "Hari 1" in joined


def test_cultivate_menambah_insight_dan_waktu(tmp_path):
    """Kultivasi memberi insight dan memajukan jam game (§18.2)."""
    session = _session(tmp_path)
    session.new_game("Akar")
    _dispatch(session, "cultivate")
    assert session.state.player.insight == 10
    assert session.state.time.hour == 11


def test_cultivate_rollover_hari(tmp_path):
    """Jam melebihi 24 melipat ke hari berikutnya."""
    session = _session(tmp_path)
    session.new_game("Akar")
    for _ in range(6):  # 6 x +3 jam = 18 jam: 8 -> 26 -> hari 2 jam 2
        _dispatch(session, "cultivate")
    assert session.state.time.day == 2
    assert session.state.time.hour == 2


def test_rest_menyembuhkan_menambah_hari_dan_autosave(tmp_path):
    """Rest: hari +1, bangun pagi, sembuh penuh, cedera berkurang, autosave."""
    session = _session(tmp_path)
    session.new_game("Akar")
    session.state.player.hp = 10
    session.state.player.qi = 0
    session.state.player.injury_days_remaining = 1
    _dispatch(session, "rest")
    assert session.state.time.day == 2
    assert session.state.time.hour == 8
    assert session.state.player.hp == session.state.player.hp_max
    assert session.state.player.qi == session.state.player.qi_max
    assert session.state.player.injury_days_remaining == 0
    assert slot_exists("autosave", tmp_path)


def test_breakthrough_sukses_naik_tier_dan_autosave(tmp_path):
    """Breakthrough sukses menaikkan tier dan memicu autosave (§19.1)."""
    session = _session(tmp_path)
    session.new_game("Akar")
    session.state.player.add_insight(100)
    lines = _dispatch(session, "breakthrough")
    assert session.state.player.tier_id == "qi_condensation"
    assert session.state.player.tier_order == 1
    assert any("sukses" in line.lower() for line in lines)
    assert slot_exists("autosave", tmp_path)


def test_breakthrough_gagal_menimbulkan_cedera(tmp_path):
    """Breakthrough gagal memberi cedera sementara 2 hari (§4.1)."""
    session = _session(tmp_path, seed=2)  # rng: lemparan pertama >= 0.55
    session.new_game("Akar")
    session.state.player.add_insight(100)
    _dispatch(session, "breakthrough")
    assert session.state.player.tier_id is None
    assert session.state.player.injury_days_remaining == 2


def test_breakthrough_insight_kurang_ditolak(tmp_path):
    """Breakthrough tanpa insight cukup memberi pesan jelas, tanpa autosave."""
    session = _session(tmp_path)
    session.new_game("Akar")
    lines = _dispatch(session, "breakthrough")
    assert any("insight" in line.lower() for line in lines)
    assert not slot_exists("autosave", tmp_path)


def test_save_load_roundtrip(tmp_path):
    """Save lalu load di sesi baru mengembalikan state yang sama."""
    session = _session(tmp_path)
    session.new_game("Akar")
    session.state.player.add_insight(35)
    session.state.time.day = 3
    _dispatch(session, "save 1")
    fresh = _session(tmp_path)
    _dispatch(fresh, "load 1")
    assert fresh.state.to_dict() == session.state.to_dict()


def test_quit_menandai_keluar(tmp_path):
    """Perintah quit menandai permintaan keluar."""
    session = _session(tmp_path)
    session.new_game("Akar")
    _dispatch(session, "quit")
    assert session.quit_requested is True


def test_perintah_belum_tersedia(tmp_path):
    """Perintah tanpa sistem memberi jawaban jujur, bukan error."""
    session = _session(tmp_path)
    session.new_game("Akar")
    assert any("Belum tersedia" in line for line in _dispatch(session, "talk"))
    assert any("Belum tersedia" in line for line in _dispatch(session, "racik"))


def test_go_lokasi_terbuka_dan_tertutup(tmp_path):
    """Pergi ke lokasi terbuka berhasil; tertutup ditolak (gating §9)."""
    session = _session(tmp_path)
    session.new_game("Akar")
    _dispatch(session, "go ashfall_forest")
    assert session.state.location == "ashfall_forest"
    lines = _dispatch(session, "go guild_city")
    assert any("belum terbuka" in line for line in lines)
    assert session.state.location == "ashfall_forest"


def test_look_di_hutan_memicu_pertarungan(tmp_path):
    """Melihat di hutan memicu pertarungan melawan Serigala Qi."""
    session = _session(tmp_path)
    session.new_game("Akar")
    _dispatch(session, "go ashfall_forest")
    lines = _dispatch(session, "look")
    assert session.in_battle is True
    assert any("Bandit" in line for line in lines)


def test_skills_pemain_berasal_dari_data(tmp_path):
    """Skill pemain diturunkan dari data (requires.tier == tier pemain)."""
    session = _session(tmp_path)
    session.new_game("Akar")
    session.state.player.add_insight(100)
    _dispatch(session, "breakthrough")
    _dispatch(session, "go ashfall_forest")
    _dispatch(session, "look")
    assert session.in_battle
    assert set(session.player_skills) == {
        "qi_slash",
        "flame_strike",
        "frost_bind",
    }


def test_pertarungan_menang_memberi_reward(tmp_path):
    """Menang melawan bandit memberi reward insight/gold dari data."""
    session = _session(tmp_path)
    session.new_game("Akar")
    _dispatch(session, "go ashfall_forest")
    _dispatch(session, "look")
    frame = session.battle_frame()
    while not frame.over:
        frame = session.battle_step("attack")
    assert frame.victory is True
    assert session.state.player.insight == 25
    assert session.state.player.gold == 20
    assert session.state.flags["ashfall_forest_cleared"] is True


def test_pertarungan_kalah_ko_pulih(tmp_path):
    """Kalah (KO) pulih otomatis setelah pertarungan (§20.4)."""
    session = _session(tmp_path)
    session.new_game("Akar")
    session.state.player.hp = 5  # luka berat sebelum bertarung
    _dispatch(session, "go ashfall_forest")
    _dispatch(session, "look")
    frame = session.battle_frame()
    while not frame.over:
        frame = session.battle_step("attack")
    assert frame.victory is False
    assert session.state.player.hp == session.state.player.hp_max


def test_escape_tanpa_reward_dan_hp_menetap(tmp_path):
    """Kabur: tidak ada reward; kerusakan tetap menetap (§18.3)."""
    session = _session(tmp_path)
    session.new_game("Akar")
    _dispatch(session, "go ashfall_forest")
    _dispatch(session, "look")
    hp_sebelum = session.state.player.hp
    frame = session.battle_step("escape")
    assert frame.escaped is True
    assert frame.victory is None
    assert session.state.player.insight == 0
    assert session.state.player.hp <= hp_sebelum


def test_dispatch_saat_battle_tidak_menimpa_pertarungan(tmp_path):
    """Perintah dunia saat battle aktif ditolak, battle tidak tergantikan."""
    session = _session(tmp_path)
    session.new_game("Akar")
    _dispatch(session, "go ashfall_forest")
    _dispatch(session, "look")
    lines = _dispatch(session, "look")  # mencoba memicu battle baru
    assert any("bertarung" in line for line in lines)
    frame = session.battle_frame()
    assert frame.enemies[0]["name"] == "Bandit Perbatasan"
    assert session.state.location == "ashfall_forest"


def test_teknik_tidak_dikenal_di_battle_memberi_error(tmp_path):
    """Aksi battle yang tidak valid menghasilkan error tanpa crash."""
    session = _session(tmp_path)
    session.new_game("Akar")
    session.state.player.add_insight(100)
    _dispatch(session, "breakthrough")
    _dispatch(session, "go ashfall_forest")
    _dispatch(session, "look")
    frame = session.battle_step("technique:ghost_slash")
    assert frame.error is not None
    assert "tidak dikenal" in frame.error
