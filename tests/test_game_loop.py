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
    """Melihat di hutan memicu pertarungan melawan Bandit Perbatasan."""
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


def test_look_setelah_hutan_bersih_menampilkan_deskripsi_peta(tmp_path):
    """Setelah hutan dibersihkan, look memakai deskripsi dari data maps (§9)."""
    session = _session(tmp_path)
    session.new_game("Akar")
    _dispatch(session, "go ashfall_forest")
    _dispatch(session, "look")
    frame = session.battle_frame()
    while not frame.over:
        frame = session.battle_step("attack")
    lines = _dispatch(session, "look")
    assert session.in_battle is False
    assert any("Hutan Perbatasan" in line for line in lines)
    assert any("abu" in line for line in lines)


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


def test_status_lines_tetap_berfungsi_saat_battle(tmp_path):
    """Status pemain tetap tersedia selama battle (dipakai HUD UI)."""
    session = _session(tmp_path)
    session.new_game("Akar")
    _dispatch(session, "go ashfall_forest")
    _dispatch(session, "look")
    assert session.in_battle
    lines = session.status_lines()
    assert any("HP" in line for line in lines)
    assert any("Insight" in line for line in lines)
    assert not any("bertarung" in line for line in lines)


def test_quit_tetap_berfungsi_saat_battle(tmp_path):
    """Perintah global quit tetap jalan saat bertarung (§18.1)."""
    session = _session(tmp_path)
    session.new_game("Akar")
    _dispatch(session, "go ashfall_forest")
    _dispatch(session, "look")
    assert session.in_battle
    lines = _dispatch(session, "quit")
    assert session.quit_requested is True
    assert any("jumpa" in line for line in lines)
    # Battle tetap utuh; keluar tidak merusak state.
    assert session.in_battle
    assert session.battle_frame().enemies[0]["name"] == "Bandit Perbatasan"


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


# ----------------------------------------------------------------------
# Event engine (GDD §15): hook setelah momen mutasi state
# ----------------------------------------------------------------------


def test_breakthrough_memicu_event_unlock_ruin_shrine(tmp_path):
    """Breakthrough ke tier 1 memicu event unlock Reruntuhan Kuil (§15)."""
    session = _session(tmp_path)
    session.new_game("Akar")
    session.state.player.add_insight(100)
    lines = _dispatch(session, "breakthrough")
    assert session.state.flags["event_unlock_ruin_shrine_done"] is True
    assert session.state.flags["map_ruin_shrine_unlocked"] is True
    assert "ruin_shrine" in session.state.map_unlocks
    assert any("Reruntuhan Kuil" in line for line in lines)
    map_lines = _dispatch(session, "map")
    assert any("ruin_shrine" in line for line in map_lines)


def test_go_hutan_memicu_event_memori_pertama(tmp_path):
    """Masuk Hutan Perbatasan memicu echo memori pertama (§15)."""
    session = _session(tmp_path)
    session.new_game("Akar")
    lines = _dispatch(session, "go ashfall_forest")
    assert session.state.flags["event_ashfall_memory_done"] is True
    assert "memory_ashfall_first_echo" in session.state.memories
    assert any("echo memori" in line for line in lines)


def test_rest_ke_hari_tujuh_memicu_event_narasi(tmp_path):
    """Mencapai hari ke-7 memicu narasi event sekali saja (§15.4)."""
    session = _session(tmp_path)
    session.new_game("Akar")
    session.state.time.day = 6
    lines = _dispatch(session, "rest")
    assert session.state.flags["event_day7_dawn_done"] is True
    assert any("Hari ketujuh" in line for line in lines)
    again = _dispatch(session, "rest")
    assert not any("Hari ketujuh" in line for line in again)


def test_event_unlock_peta_tersimpan_di_autosave(tmp_path):
    """Efek event ikut tersimpan autosave (event diproses sebelum save)."""
    session = _session(tmp_path)
    session.new_game("Akar")
    session.state.player.add_insight(100)
    _dispatch(session, "breakthrough")
    assert session.state.flags["map_ruin_shrine_unlocked"] is True
    fresh = _session(tmp_path)
    _dispatch(fresh, "load autosave")
    assert fresh.state.flags["map_ruin_shrine_unlocked"] is True
    assert fresh.state.flags["event_unlock_ruin_shrine_done"] is True


def test_memories_menampilkan_judul_dan_isi_echo(tmp_path):
    """Perintah memories menampilkan judul+isi memori dari data (GDD §15.3)."""
    session = _session(tmp_path)
    session.new_game("Akar")
    _dispatch(session, "go ashfall_forest")
    lines = _dispatch(session, "memories")
    joined = "\n".join(lines)
    assert "Hujan Abu" in joined
    assert "memory_ashfall_first_echo" not in joined


def test_memories_kosong_memberi_pesan(tmp_path):
    """Tanpa memori, perintah memories memberi pesan jelas."""
    session = _session(tmp_path)
    session.new_game("Akar")
    lines = _dispatch(session, "memories")
    assert any("Tidak ada memori" in line for line in lines)


def test_look_di_lokasi_baru_tidak_menipu(tmp_path):
    """Look di lokasi non-desa menampilkan deskripsi dari data maps (§9)."""
    session = _session(tmp_path)
    session.new_game("Akar")
    session.state.player.add_insight(100)
    _dispatch(session, "breakthrough")
    _dispatch(session, "go ruin_shrine")
    lines = _dispatch(session, "look")
    assert any("Reruntuhan Kuil" in line for line in lines)
    assert not any("Desa Emberfall" in line for line in lines)


def test_look_kuil_sebelum_quest102_tidak_memicu_battle(tmp_path):
    """Gating §11: kuil tanpa quest102_done tidak memunculkan musuh."""
    session = _session(tmp_path)
    session.new_game("Akar")
    session.state.player.add_insight(100)
    _dispatch(session, "breakthrough")
    _dispatch(session, "go ruin_shrine")
    lines = _dispatch(session, "look")
    assert session.in_battle is False
    assert any("Reruntuhan Kuil" in line for line in lines)


def test_slice_kuil_lengkap_quest103_dan_rahasia(tmp_path):
    """Alur Arc 1: zombi -> bos -> quest103 -> memori + pil."""
    session = _session(tmp_path)
    session.new_game("Akar")
    _dispatch(session, "talk elder_mao")
    session.state.player.add_insight(100)
    _dispatch(session, "breakthrough")
    _dispatch(session, "talk lin_wei")
    _dispatch(session, "go ruin_shrine")
    assert "quest102_done" in session.state.flags
    assert "quest103" in session.state.quests.started
    _dispatch(session, "look")
    assert session.in_battle is True
    frame = session.battle_frame()
    while not frame.over:
        frame = session.battle_step("attack")
    assert frame.victory is True
    _dispatch(session, "look")
    assert session.in_battle is True
    frame = session.battle_frame()
    while not frame.over:
        if session._ally.qi >= 8:
            frame = session.battle_step("technique:flame_strike")
        else:
            frame = session.battle_step("attack")
    assert frame.victory is True
    assert "quest103_done" in session.state.flags
    assert "memory_shrine_trial" in session.state.memories
    assert session.state.inventory["items"]["pil_peneguh_fondasi"] == 1
    lines = _dispatch(session, "inventory")
    assert any("Pil Peneguh Fondasi" in line for line in lines)


# ----------------------------------------------------------------------
# Quest engine (GDD §12): talk, progres, penyelesaian, kills
# ----------------------------------------------------------------------


def test_quest101_dimulai_oleh_event_hari_pertama(tmp_path):
    """Aksi pertama memicu event intro: quest101 masuk daftar aktif."""
    session = _session(tmp_path)
    session.new_game("Akar")
    _dispatch(session, "cultivate")
    assert "quest101" in session.state.quests.started
    assert session.state.flags["event_quest101_intro_done"] is True


def test_talk_ke_elder_mao_memberi_flag_dan_dialog(tmp_path):
    """Talk ke Sesepuh Mao di desa: flag talked_elder_mao + baris dialog."""
    session = _session(tmp_path)
    session.new_game("Akar")
    lines = _dispatch(session, "talk elder_mao")
    assert session.state.flags["talked_elder_mao"] is True
    assert any("Sesepuh Mao" in line for line in lines)


def test_talk_tanpa_argumen_memberi_petunjuk(tmp_path):
    """Talk tanpa nama memberi pesan petunjuk, tanpa set flag."""
    session = _session(tmp_path)
    session.new_game("Akar")
    lines = _dispatch(session, "talk")
    assert any("siapa" in line.lower() for line in lines)
    assert "talked_" not in session.state.flags


def test_talk_sadar_lokasi(tmp_path):
    """Talk ke NPC yang tidak di lokasi saat ini ditolak."""
    session = _session(tmp_path)
    session.new_game("Akar")
    _dispatch(session, "go ashfall_forest")
    lines = _dispatch(session, "talk elder_mao")
    assert any("Sesepuh Mao tidak ada di sini" in line for line in lines)
    assert "talked_elder_mao" not in session.state.flags


def test_quests_menampilkan_title_dan_progres(tmp_path):
    """Quest aktif menampilkan title + status per objektif (reuse check)."""
    session = _session(tmp_path)
    session.new_game("Akar")
    _dispatch(session, "cultivate")  # quest101 dimulai via event intro
    lines = _dispatch(session, "quests")
    joined = "\n".join(lines)
    assert "Qi Pertama" in joined
    assert "Bicaralah dengan elder_mao" in joined
    assert "[ ]" in joined
    _dispatch(session, "talk elder_mao")
    joined = "\n".join(_dispatch(session, "quests"))
    assert "[x] Bicaralah dengan elder_mao" in joined


def test_quest101_selesai_setelah_talk_dan_breakthrough(tmp_path):
    """Quest selesai: reward + flag kelulusan otomatis engine (§12.2)."""
    session = _session(tmp_path)
    session.new_game("Akar")
    _dispatch(session, "cultivate")  # quest101 dimulai via event intro
    _dispatch(session, "talk elder_mao")
    session.state.player.add_insight(100)
    lines = _dispatch(session, "breakthrough")
    state = session.state
    assert state.player.tier_id == "qi_condensation"
    assert state.quests.done == ["quest101"]
    # Kontrak quest lanjutan: quest102 dimulai otomatis di pass yang sama.
    assert state.quests.started == ["quest102"]
    assert state.flags["quest101_done"] is True
    assert state.flags["path_unlocked_sword"] is True
    assert state.player.insight >= 150  # 10 + 100 + reward 50
    assert state.player.gold == 20
    assert state.reputation["rebels"] == 5
    assert any("Quest selesai: Qi Pertama" in line for line in lines)
    # Cascade quest -> event: event quest_done menyala di pass yang sama.
    assert state.flags["event_quest101_done_done"] is True
    assert any("Sesepuh Mao" in line for line in lines)


def test_quest102_selesai_setelah_talk_lin_wei_dan_go_shrine(tmp_path):
    """Quest lanjutan: dimulai otomatis, selesai di Reruntuhan Kuil.

    Alur: quest101 selesai (breakthrough) -> quest102 dimulai seketika ->
    bicara Lin Wei di desa -> masuk ruin_shrine -> quest102_done.
    """
    session = _session(tmp_path)
    session.new_game("Akar")
    _dispatch(session, "cultivate")  # quest101 dimulai via event intro
    _dispatch(session, "talk elder_mao")
    session.state.player.add_insight(100)
    _dispatch(session, "breakthrough")  # quest101 selesai -> quest102 mulai
    state = session.state
    assert state.quests.started == ["quest102"]
    assert state.flags["event_quest102_intro_done"] is True
    lines = _dispatch(session, "talk lin_wei")
    assert state.flags["talked_lin_wei"] is True
    assert any("Lin Wei" in line for line in lines)
    _dispatch(session, "go ruin_shrine")
    assert state.flags["quest102_done"] is True
    assert "quest102" in state.quests.done


def test_quests_menampilkan_deskripsi_quest(tmp_path):
    """Quest aktif menampilkan deskripsi naratif dari data (GDD §12.3)."""
    session = _session(tmp_path)
    session.new_game("Akar")
    _dispatch(session, "cultivate")  # quest101 dimulai via event intro
    joined = "\n".join(_dispatch(session, "quests"))
    assert "Sesepuh Mao mengajarkanmu menghirup qi langit-bumi" in joined


def test_quest_selesai_saat_talk_setelah_breakthrough(tmp_path):
    """Breakthrough dulu, talk kemudian: quest selesai di momen talk."""
    session = _session(tmp_path)
    session.new_game("Akar")
    _dispatch(session, "cultivate")  # quest101 dimulai via event intro
    session.state.player.add_insight(100)
    _dispatch(session, "breakthrough")  # objektif breakthrough terpenuhi
    assert session.state.player.tier_id == "qi_condensation"
    assert "quest101" in session.state.quests.started  # belum selesai
    lines = _dispatch(session, "talk elder_mao")
    state = session.state
    assert state.quests.done == ["quest101"]
    assert state.flags["quest101_done"] is True
    assert state.flags["event_quest101_done_done"] is True
    assert any("Quest selesai: Qi Pertama" in line for line in lines)


def test_kills_tercatat_saat_menang(tmp_path):
    """Menang pertarungan mencatat kill musuh di state.kills."""
    session = _session(tmp_path)
    session.new_game("Akar")
    _dispatch(session, "go ashfall_forest")
    _dispatch(session, "look")
    frame = session.battle_frame()
    while not frame.over:
        frame = session.battle_step("attack")
    assert frame.victory is True
    assert session.state.kills.get("bandit_perbatasan") == 1
