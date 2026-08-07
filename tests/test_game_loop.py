"""Test GameSession — alur main Fase 0 (GDD §18, §19.1, §20.4, §23)."""

import random

from src.core.game_loop import BattleFrame, GameSession, make_bar
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


def _bertarung(session: GameSession) -> BattleFrame:
    """Jalankan battle sampai tuntas: flame_strike hanya giliran protagonis.

    Rekan (Lin Wei) tidak menguasai flame_strike — aksi invalid = error
    frame tanpa advance = infinite loop (regresi multi-ally).
    """
    frame = session.battle_frame()
    while not frame.over:
        if session.battle.current is session._ally and session._ally.qi >= 8:
            frame = session.battle_step("technique:flame_strike")
        else:
            frame = session.battle_step("attack")
    return frame


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


def test_make_bar_proporsional():
    """Bar ASCII mengisi sesuai proporsi (0 -> kosong, penuh -> penuh)."""
    assert make_bar(0, 20, 10) == "░" * 10
    assert make_bar(20, 20, 10) == "█" * 10
    assert make_bar(10, 20, 10).count("█") == 5


def test_make_bar_total_nol_kosong():
    """Total 0 menghasilkan bar kosong (hindari pembagian nol)."""
    assert make_bar(0, 0, 8) == "░" * 8
    assert len(make_bar(5, 0, 8)) == 8


def test_status_lines_memuat_bar_hp_qi(tmp_path):
    """HUD menampilkan bar visual HP/Qi, bukan teks polos."""
    session = _session(tmp_path)
    session.new_game("Akar")
    session.state.player.hp = 40  # setengah: bar memuat █ dan ░
    session.state.player.qi = 5
    joined = "\n".join(session.status_lines())
    assert "█" in joined and "░" in joined


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


def test_status_lines_menampilkan_hp_battle_live(tmp_path):
    """HUD selama battle mencerminkan HP combatan asli, bukan player stale.

    Regresi: status_lines membaca state.player.hp yang baru disinkronkan
    saat _finish_battle; selama battle HUD harus memakai _ally.hp agar bar
    tidak menipu pemain yang sedang terluka.
    """
    session = _session(tmp_path)
    session.new_game("Akar")
    _dispatch(session, "go ashfall_forest")
    _dispatch(session, "look")
    # Lukai ally langsung (simulasi beberapa giliran battle).
    session._ally.hp = 40
    lines = session.status_lines()
    hp_line = next(line for line in lines if "HP" in line)
    assert "40/80" in hp_line
    assert "80/80" not in hp_line


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
        "vine_grasp",
        "earth_charge",
        "serbuan_akar",
        "perisai_tanah",
    }


def test_player_skills_tidak_duplikat_skill_formasi(tmp_path):
    """Skill formasi tidak menggandakan teknik yang sudah dipelajari."""
    session = _session(tmp_path)
    session.new_game("Akar")
    session.state.player.add_insight(100)
    _dispatch(session, "breakthrough")
    session.state.formation_active = "benteng_bumi"
    skills = session.player_skills
    assert skills.count("perisai_tanah") == 1


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
        # Flame strike hanya untuk giliran protagonis; rekan (Lin Wei)
        # tidak menguasai teknik itu — aksi invalid = error frame tanpa
        # advance = infinite loop (regresi multi-ally Task 3).
        if session.battle.current is session._ally and session._ally.qi >= 8:
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


def test_quest_lines_menampilkan_quest_aktif(tmp_path):
    """Panel quest memakai data yang sama dengan perintah quests."""
    session = _session(tmp_path)
    session.new_game("Akar")
    _dispatch(session, "cultivate")  # quest101 dimulai via event intro
    joined = "\n".join(session.quest_lines())
    assert "Qi Pertama" in joined


def test_party_lines_read_only_tanpa_efek_samping(tmp_path):
    """Panel party read-only tanpa efek samping (GDD §20)."""
    session = _session(tmp_path)
    session.new_game("Akar")
    joined = "\n".join(session.party_lines())
    assert "protagonis" in joined
    assert session.state.quests.started == []  # tidak memicu event


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


# ----------------------------------------------------------------------
# Choice Engine (Sprint 1): prompt_choice + choose command
# ----------------------------------------------------------------------


def test_cmd_choose_valid_menerapkan_opsi_dan_bersihkan_pending(tmp_path):
    """Choose <key>: menerapkan set_flag/change_reputation/log.

    clear pending, cascade.
    """
    session = _session(tmp_path)
    session.new_game("Akar")
    # Simulasikan prompt_choice sudah di-set via event engine
    session.state.flags["pending_choice"] = {
        "event_id": "evt_choice_test",
        "options": [
            {
                "key": "a",
                "text": "Lapor sungguhan",
                "set_flag": "lapor_jujur",
                "change_reputation": {"holy_order": 10, "rebels": -10},
                "log": "Kamu melaporkan apa yang kau lihat.",
            },
            {
                "key": "b",
                "text": "Menyesatkan",
                "set_flag": "lapor_bohong",
                "change_reputation": {"rebels": 10, "holy_order": -10},
                "log": "Kamu memutarbalikkan fakta.",
            },
        ],
    }
    # Pilih opsi a
    lines = _dispatch(session, "choose a")
    state = session.state
    # Opsi diterapkan
    assert state.flags.get("lapor_jujur") is True
    assert state.reputation["holy_order"] == 10
    assert state.reputation["rebels"] == -10
    # pending_choice dibersihkan
    assert "pending_choice" not in state.flags
    # Log berisi hasil pilihan
    joined = "\n".join(lines)
    assert "Kamu melaporkan" in joined
    # Quest/Event cascade (jika ada trigger dari flag/rep baru)
    # - tidak crash


def test_cmd_choose_option_actions_mendukung_grant_item(tmp_path):
    """Choose dengan option ber-actions: grant_item dieksekusi.

    Perluasan prompt_choice (GDD §15.3): opsi bisa membawa daftar aksi
    penuh (grant_item, start_quest, dll) — bukan hanya set_flag/log.
    """
    session = _session(tmp_path)
    session.new_game("Akar")
    session.state.flags["pending_choice"] = {
        "event_id": "evt_choice_test",
        "options": [
            {
                "key": "a",
                "text": "Terima hadiah",
                "actions": [
                    {"kind": "grant_item", "id": "pil_uji_heal", "count": 2},
                    {"kind": "grant_gold", "amount": 50},
                ],
            },
            {"key": "b", "text": "Tolak"},
        ],
    }
    lines = _dispatch(session, "choose a")
    state = session.state
    # Aksi penuh dieksekusi via apply_action (satu sumber kebenaran).
    assert state.inventory["items"].get("pil_uji_heal") == 2
    assert state.player.gold == 50
    assert "pending_choice" not in state.flags
    assert isinstance(lines, list) and lines is not None


def test_cmd_choose_option_actions_mendukung_start_quest(tmp_path):
    """Choose dengan action start_quest: quest dimulai (GDD §15.3)."""
    session = _session(tmp_path)
    session.new_game("Akar")
    session.state.flags["pending_choice"] = {
        "event_id": "evt_choice_test",
        "options": [
            {
                "key": "a",
                "text": "Bergabung",
                "actions": [{"kind": "start_quest", "id": "quest101"}],
            }
        ],
    }
    _dispatch(session, "choose a")
    assert "quest101" in session.state.quests.started


def test_cmd_choose_invalid_key_memberi_error_pending_tetap(tmp_path):
    """Choose key salah: error, pending_choice tidak dibersihkan."""
    session = _session(tmp_path)
    session.new_game("Akar")
    session.state.flags["pending_choice"] = {
        "event_id": "evt_choice_test",
        "options": [{"key": "a", "text": "Opsi A"}],
    }
    lines = _dispatch(session, "choose z")
    state = session.state
    # Error dikembalikan
    assert any("tidak valid" in line.lower() for line in lines)
    # pending_choice tetap ada
    assert "pending_choice" in state.flags
    assert state.flags["pending_choice"]["options"][0]["key"] == "a"


def test_cmd_choose_tanpa_pending_memberi_error(tmp_path):
    """Choose tanpa pending_choice aktif: error jelas."""
    session = _session(tmp_path)
    session.new_game("Akar")
    lines = _dispatch(session, "choose a")
    assert any("tidak ada pilihan" in line.lower() for line in lines)


def test_cmd_choose_hanya_boleh_saat_tidak_battle(tmp_path):
    """Choose saat battle: ditolak (bukan perintah battle)."""
    session = _session(tmp_path)
    session.new_game("Akar")
    _dispatch(session, "go ashfall_forest")
    _dispatch(session, "look")
    session.state.flags["pending_choice"] = {
        "event_id": "evt_choice_test",
        "options": [{"key": "a", "text": "Opsi A"}],
    }
    lines = _dispatch(session, "choose a")
    assert any("bertarung" in line for line in lines)
    # pending_choice tidak dikonsumsi
    assert "pending_choice" in session.state.flags


# ----------------------------------------------------------------------
# Sprint 1.1 (continuation): Command use <item> (data-driven item effect)
# ----------------------------------------------------------------------


def test_inventory_mewarnai_per_tipe(tmp_path):
    """Inventory menampilkan warna semantik sesuai tipe item (GDD §7)."""
    session = _session(tmp_path)
    session.new_game("Akar")
    session.state.inventory.setdefault("items", {})["esensi_api"] = 2
    session.state.inventory.setdefault("items", {})["kuali_roh"] = 1
    session.state.inventory.setdefault("items", {})["resep_pemulih"] = 1
    joined = "\n".join(_dispatch(session, "inventory"))
    assert "[cyan]" in joined  # material
    assert "[gold3]" in joined  # tool
    assert "[violet]" in joined  # recipe


def test_use_pil_pemulih_memulihkan_hp(tmp_path):
    """Use pil heal_hp menambah HP pemain dan mengonsumsi item."""
    session = _session(tmp_path)
    session.new_game("Akar")
    player = session.state.player
    player.hp = 10
    session.state.inventory.setdefault("items", {})["pil_uji_heal"] = 1
    lines = _dispatch(session, "use pil_uji_heal")
    assert player.hp > 10
    assert any("Pil Uji Heal" in line for line in lines)


def test_use_item_buff_attack_mencatat_buff(tmp_path):
    """Use item buff_attack: tercatat di state.buffs (GDD §7).

    Efek combat-ready kini dieksekusi — buff disimpan untuk pertarungan
    berikutnya (diterapkan di _start_battle), bukan diabaikan.
    """
    session = _session(tmp_path)
    session.new_game("Akar")
    player = session.state.player
    before = (player.hp, player.qi, player.insight, player.meridian_buka)
    session.state.inventory.setdefault("items", {})["pil_uji_buff"] = 1
    lines = _dispatch(session, "use pil_uji_buff")
    after = (player.hp, player.qi, player.insight, player.meridian_buka)
    # Efek non-combat tidak berubah; buff combat tercatat.
    assert after == before
    assert session.state.buffs.get("attack") == 5
    assert session.state.inventory["items"].get("pil_uji_buff", 0) == 0
    assert any("buff" in line.lower() for line in lines)


def test_use_item_buff_defense_dan_resist_mencatat(tmp_path):
    """Use item buff_defense/resist_*: tercatat sesuai kunci efek."""
    session = _session(tmp_path)
    session.new_game("Akar")
    session.state.inventory.setdefault("items", {})["pil_besi_hitam"] = 1
    session.state.inventory.setdefault("items", {})["elixir_empedu_api"] = 1
    _dispatch(session, "use pil_besi_hitam")
    _dispatch(session, "use elixir_empedu_api")
    assert session.state.buffs.get("defense") == 30
    assert session.state.buffs.get("resist_poison") == 30


def test_start_battle_menerapkan_buff_ke_combatant(tmp_path):
    """Buff tercatat diterapkan ke combatant protagonis saat battle."""
    session = _session(tmp_path)
    session.new_game("Akar")
    session.state.buffs = {"attack": 5, "resist_poison": 30}
    session.state.flags["map_ashfall_forest_unlocked"] = True
    _dispatch(session, "go ashfall_forest")
    _dispatch(session, "look")
    ally = session.battle.allies[0]
    base_attack = 5  # Player base attack (data player)
    assert ally.stats["attack"] == base_attack + 5
    assert ally.stats.get("resist_poison") == 30


def test_buff_kosong_setelah_battle_selesai(tmp_path):
    """Buff dipakai sekali: kosong setelah battle selesai (sekali pakai)."""
    session = _session(tmp_path)
    session.new_game("Akar")
    session.state.buffs = {"attack": 5}
    session.state.flags["map_ashfall_forest_unlocked"] = True
    _dispatch(session, "go ashfall_forest")
    _dispatch(session, "look")
    frame = session.battle_frame()
    while not frame.over:
        frame = session.battle_step("attack")
    assert session.state.buffs == {}


def test_use_item_tidak_ada_di_tas_memberi_error(tmp_path):
    """Use item yang tidak dimiliki: pesan jelas, tidak crash."""
    session = _session(tmp_path)
    session.new_game("Akar")
    lines = _dispatch(session, "use pil_tidak_ada")
    assert any("tidak" in line.lower() for line in lines)


def test_use_item_tak_dikenal_tidak_konsumsi(tmp_path):
    """Use item tak dikenal data: item TIDAK boleh raib dari tas (bug).

    Regresi: sebelumnya item dikurangi dulu (game_loop.py) baru divalidasi
    ke katalog — item tak dikenal ikut terkonsumsi sia-sia.
    """
    session = _session(tmp_path)
    session.new_game("Akar")
    session.state.inventory.setdefault("items", {})["hantu_item"] = 1
    lines = _dispatch(session, "use hantu_item")
    assert any("tidak dikenal" in line for line in lines)
    assert session.state.inventory["items"].get("hantu_item", 0) == 1


def test_use_bahan_ditolak_tidak_konsumsi(tmp_path):
    """Use bahan material: ditolak, item tetap di tas (cegah perangkap).

    Bahan (type=material) tidak punya efek; memakainya hanya menghancurkan
    item. Pemain harus diarahkan ke refine.
    """
    session = _session(tmp_path)
    session.new_game("Akar")
    session.state.inventory.setdefault("items", {})["esensi_api"] = 1
    lines = _dispatch(session, "use esensi_api")
    assert any("racik" in line.lower() for line in lines)
    assert session.state.inventory["items"]["esensi_api"] == 1


# ----------------------------------------------------------------------
# Sprint E: Sistem Alkimia — belajar resep & refine (GDD §7, §18.2)
# ----------------------------------------------------------------------


def test_use_resep_mempelajari_resep(tmp_path):
    """Use item resep: flag recipe_<item>_known terset, item resep habis."""
    session = _session(tmp_path)
    session.new_game("Akar")
    session.state.inventory.setdefault("items", {})["resep_pemulih"] = 1
    lines = _dispatch(session, "use resep_pemulih")
    assert session.state.flags.get("recipe_pil_pemulih_known") is True
    assert session.state.inventory["items"].get("resep_pemulih", 0) == 0
    assert any("Resep Pil Pemulih" in line for line in lines)


def test_use_resep_sudah_dipelajari_ditolak(tmp_path):
    """Use item resep yang sudah dipelajari: ditolak, item tidak terbuang."""
    session = _session(tmp_path)
    session.new_game("Akar")
    session.state.flags["recipe_pil_pemulih_known"] = True
    session.state.inventory.setdefault("items", {})["resep_pemulih"] = 1
    lines = _dispatch(session, "use resep_pemulih")
    assert any("sudah mempelajari" in line.lower() for line in lines)
    assert session.state.inventory["items"]["resep_pemulih"] == 1


def test_refine_tanpa_resep_dipelajari_ditolak(tmp_path):
    """Refine butuh resep dipelajari dulu (keputusan desain)."""
    session = _session(tmp_path)
    session.new_game("Akar")
    session.state.inventory.setdefault("items", {})["kuali_roh"] = 1
    session.state.inventory.setdefault("items", {})["esensi_api"] = 2
    session.state.inventory.setdefault("items", {})["esensi_tanah"] = 1
    lines = _dispatch(session, "refine pil_pemulih")
    # Pesan utuh satu baris (regresi: sebelumnya terbelah 2 baris).
    refused = [line for line in lines if "belum mempelajari" in line]
    assert len(refused) == 1
    assert "Beli dan pakai item resepnya dulu." in refused[0]
    assert session.state.inventory["items"]["esensi_api"] == 2


def test_refine_tanpa_kuali_ditolak(tmp_path):
    """Refine butuh alat Kuali Roh di tas (keputusan desain)."""
    session = _session(tmp_path)
    session.new_game("Akar")
    session.state.flags["recipe_pil_pemulih_known"] = True
    session.state.inventory.setdefault("items", {})["esensi_api"] = 2
    session.state.inventory.setdefault("items", {})["esensi_tanah"] = 1
    lines = _dispatch(session, "refine pil_pemulih")
    assert any("kuali" in line.lower() for line in lines)
    assert session.state.inventory["items"]["esensi_api"] == 2


def test_refine_bahan_kurang_ditolak(tmp_path):
    """Refine dengan bahan kurang: ditolak, bahan tidak berubah."""
    session = _session(tmp_path)
    session.new_game("Akar")
    session.state.flags["recipe_pil_pemulih_known"] = True
    session.state.inventory.setdefault("items", {})["kuali_roh"] = 1
    session.state.inventory.setdefault("items", {})["esensi_api"] = 1
    session.state.inventory.setdefault("items", {})["esensi_tanah"] = 1
    lines = _dispatch(session, "refine pil_pemulih")
    assert any("tidak cukup" in line.lower() for line in lines)
    assert session.state.inventory["items"]["esensi_api"] == 1
    assert session.state.inventory["items"].get("pil_pemulih", 0) == 0


def test_refine_sukses_mengubah_bahan_menjadi_pil(tmp_path):
    """Refine sukses: bahan berkurang sesuai resep, pil masuk x1."""
    session = _session(tmp_path)
    session.new_game("Akar")
    session.state.flags["recipe_pil_pemulih_known"] = True
    session.state.inventory.setdefault("items", {})["kuali_roh"] = 1
    session.state.inventory.setdefault("items", {})["esensi_api"] = 2
    session.state.inventory.setdefault("items", {})["esensi_tanah"] = 1
    lines = _dispatch(session, "refine pil_pemulih")
    assert any("meracik" in line.lower() for line in lines)
    assert session.state.inventory["items"].get("esensi_api", 0) == 0
    assert session.state.inventory["items"].get("esensi_tanah", 0) == 0
    assert session.state.inventory["items"]["pil_pemulih"] == 1
    # Alat tidak ikut habis.
    assert session.state.inventory["items"]["kuali_roh"] == 1


def test_refine_sukses_dari_resep_item(tmp_path):
    """Refine sukses untuk pil_baja_tubuh (resep di resep_pil_baja)."""
    session = _session(tmp_path)
    session.new_game("Akar")
    session.state.flags["recipe_pil_baja_tubuh_known"] = True
    session.state.inventory.setdefault("items", {})["kuali_roh"] = 1
    session.state.inventory.setdefault("items", {})["batu_qi"] = 2
    session.state.inventory.setdefault("items", {})["esensi_kayu"] = 2
    lines = _dispatch(session, "refine pil_baja_tubuh")
    assert any("meracik" in line.lower() for line in lines)
    assert session.state.inventory["items"].get("batu_qi", 0) == 0
    assert session.state.inventory["items"].get("esensi_kayu", 0) == 0
    assert session.state.inventory["items"]["pil_baja_tubuh"] == 1


def test_refine_item_tanpa_resep_ditolak(tmp_path):
    """Refine item tanpa recipe / tak dikenal: pesan jelas."""
    session = _session(tmp_path)
    session.new_game("Akar")
    session.state.inventory.setdefault("items", {})["kuali_roh"] = 1
    lines = _dispatch(session, "refine pil_qi_tenang")
    assert any("resep" in line.lower() for line in lines)
    lines = _dispatch(session, "refine pil_hantu")
    assert any("tidak dikenal" in line.lower() for line in lines)


# ----------------------------------------------------------------------
# Sprint D: E2E Integration Tests (Arc 1 Variasi)
# ----------------------------------------------------------------------


def test_use_item_flow_grant_via_event(tmp_path):
    """Alur: event grant_item -> item di tas -> use -> effect applied."""
    session = _session(tmp_path)
    session.new_game("Akar")
    player = session.state.player
    player.hp = 20

    # Simulasikan event grant_item
    session.state.inventory.setdefault("items", {})["pil_pemulih"] = 1

    # Use item
    lines = _dispatch(session, "use pil_pemulih")

    # Effect applied
    assert player.hp == 60  # 20 + 40 (heal_hp:40) capped at hp_max
    assert any("Pil Pemulih" in line for line in lines)

    # Item consumed
    assert session.state.inventory["items"].get("pil_pemulih", 0) == 0


def test_quest_faksi_flow_start_complete_reward(tmp_path):
    """Alur nyata: event intro -> start fquest -> objektif -> reward + event."""
    session = _session(tmp_path)
    session.new_game("Akar")

    # Prasyarat quest103_done dipenuhi: event intro faksi menyala di
    # cascade berikutnya (start quest + set flag aktif + unlock peta).
    session.state.flags["quest103_done"] = True
    _dispatch(session, "rest")
    assert "fquest_hutan_ember" in session.state.quests.started
    assert session.state.flags.get("fquest_hutan_ember_active") is True
    assert session.state.flags["map_hutan_kelabu_unlocked"] is True

    # Objektif 1: talk Jati di Hutan Perbatasan.
    _dispatch(session, "go ashfall_forest")
    _dispatch(session, "talk jati")
    assert session.state.flags["talked_jati"] is True

    # Objektif 2-3: kalahkan hantu laut dan serigala ember.
    session.state.kills["hantu_laut"] = 1
    session.state.kills["serigala_ember"] = 1
    _dispatch(session, "rest")  # evaluasi quest + event done

    assert "fquest_hutan_ember" in session.state.quests.done
    assert "fquest_hutan_ember_done" in session.state.flags
    assert session.state.flags["event_fquest_hutan_ember_done_done"] is True
    assert session.state.reputation["rebels"] >= 20
    assert session.state.player.insight >= 50
    assert session.state.player.gold >= 40
    # Reward grant_item quest + grant_item event done.
    assert session.state.inventory["items"].get("pil_pemulih") == 1


def test_new_enemy_spawn_map_requires_flag(tmp_path):
    """Enemy baru di map baru spawn setelah flag terpenuhi."""
    session = _session(tmp_path)
    session.new_game("Akar")

    # Unlock map hutan_kelabu
    session.state.flags["map_hutan_kelabu_unlocked"] = True
    session.state.map_unlocks.append("hutan_kelabu")

    # Go to map
    _dispatch(session, "go hutan_kelabu")
    assert session.state.location == "hutan_kelabu"

    # Look - should trigger penunggu_hutan (requires fquest_abyssal_active)
    # First, set the required flag
    session.state.flags["fquest_abyssal_active"] = True
    _dispatch(session, "look")

    # Should spawn penunggu_hutan
    assert session.in_battle is True
    frame = session.battle_frame()
    assert frame.enemies[0]["name"] == "Penunggu Hutan"


def test_new_technique_available_after_breakthrough(tmp_path):
    """Teknik foundation_establishment tersedia setelah breakthrough tier 2."""
    session = _session(tmp_path)
    session.new_game("Akar")

    # Add insight and breakthrough to tier 2
    session.state.player.add_insight(500)
    _dispatch(session, "breakthrough")  # tier 1
    _dispatch(session, "breakthrough")  # tier 2 (foundation_establishment)

    # Check skills available
    skills = set(session.player_skills)
    assert "benteng_meridian" in skills  # formation, earth, foundation
    assert "senjata_roh" in skills  # spirit, metal, foundation


# ----------------------------------------------------------------------
# Sprint 3: Full Playthrough Arc 1→2 (E2E)
# ----------------------------------------------------------------------


def test_arc1_full_playthrough(tmp_path):
    """Full playthrough Arc 1: quest101→108 + 2 faksi (tanpa workaround)."""
    session = _session(tmp_path)
    session.new_game("Akar")

    # === Quest 101: Qi Pertama ===
    _dispatch(session, "cultivate")  # trigger quest101_intro
    _dispatch(session, "talk elder_mao")
    session.state.player.add_insight(100)
    _dispatch(session, "breakthrough")  # tier 1 + quest101 done
    assert session.state.player.tier_id == "qi_condensation"
    assert "quest101" in session.state.quests.done
    assert "quest102" in session.state.quests.started

    # === Quest 102: Panggilan Kuil ===
    _dispatch(session, "talk lin_wei")
    _dispatch(session, "go ruin_shrine")
    assert "quest102_done" in session.state.flags
    assert "quest103" in session.state.quests.started

    # === Quest 103: Ujian Orde Kuno (combat) ===
    _dispatch(session, "look")  # zombie_temple
    frame = _bertarung(session)
    assert frame.victory is True

    _dispatch(session, "look")  # penjaga_makam (bos)
    frame = _bertarung(session)
    assert frame.victory is True
    assert "quest103_done" in session.state.flags
    assert "memory_shrine_trial" in session.state.memories
    assert "pil_peneguh_fondasi" in session.state.inventory["items"]

    # === Transisi Arc 1→2 dipindah ke quest108 ===

    # === Quest 104: Kabar yang Tak Boleh Keluar ===
    _dispatch(session, "go village_emberfall")
    _dispatch(session, "talk elder_mao")
    _dispatch(session, "talk lin_wei")
    assert "quest104_done" in session.state.flags
    assert "quest105" in session.state.quests.started

    # === Quest 105: Peziarah dari Selatan (CHOICE) ===
    _dispatch(session, "talk diakon_soren")
    # Pilih: lapor jujur (holy_order +10, rebels -10)
    _dispatch(session, "choose a")
    assert session.state.flags["lapor_jujur"] is True
    assert (
        session.state.reputation["holy_order"] == 15
    )  # 5 quest reward + 10 choice
    assert (
        session.state.reputation["rebels"] == 10
    )  # 20 from previous quests - 10 choice
    assert "quest105_done" in session.state.flags
    assert "quest106" in session.state.quests.started
    # Cascade: quest faksi holy order ikut selesai di pass yang sama, dan
    # pilihan orde muncul — jawab sekarang sebelum choice ending menimpanya.
    assert "fquest_holyorder_mata" in session.state.quests.done
    _dispatch(session, "choose a")  # orde: lapor jujur
    assert session.state.flags["lapor_jujur_orde"] is True
    assert session.state.reputation["holy_order"] == 30

    # === Quest 106: Arsip yang Terbakar (combat) ===
    _dispatch(session, "talk guntur")
    _dispatch(session, "go ruin_shrine")
    _dispatch(session, "rest")  # recover HP/qi before boss
    _dispatch(session, "look")  # trigger penjaga_arsip
    frame = _bertarung(session)
    assert frame.victory is True
    _dispatch(session, "look")  # trigger quest/event cascade
    assert "quest106_done" in session.state.flags
    assert "quest107" in session.state.quests.started

    # === Quest 107: Nama di Dinding ===
    _dispatch(session, "go village_emberfall")
    _dispatch(session, "talk lin_wei")
    assert "quest107_done" in session.state.flags
    assert (
        "quest108_done" in session.state.flags
    )  # quest108 completes immediately after talk
    # Pilih ending path: Menentang Langit
    _dispatch(session, "choose a")
    assert "ending_path_defy" in session.state.flags
    assert (
        session.state.reputation["ancient_order"] == 30
    )  # quest106(+5) + quest108(+10) + choice(+15)

    # === Transisi Arc 1→2: quest108_done event ===
    assert session.state.flags.get("map_sect_azure_unlocked") is True
    assert session.state.flags.get("map_guild_city_unlocked") is True
    assert "memory_arc1_complete" in session.state.memories
    assert "quest201" in session.state.quests.started

    # === Faction Quest: Rebels ===
    _dispatch(session, "go ashfall_forest")
    _dispatch(session, "rest")  # recover HP/qi before faction battles
    _dispatch(session, "talk jati")
    # 3 pertarungan berurutan: bandit -> babi_hutan_qi -> pembelot.
    # Nama musuh bergantung pada urutan spawn di data/maps/ashfall_forest.json
    # (musuh pertama yang flag-nya terpenuhi & belum dikalahkan).
    for expected in (
        "Bandit Perbatasan",
        "Babi Hutan Qi",
        "Pembelot Pemberontak",
    ):
        _dispatch(session, "look")
        assert session.in_battle is True
        frame = session.battle_frame()
        assert frame.enemies[0]["name"] == expected
        frame = _bertarung(session)
        assert frame.victory is True
        _dispatch(session, "rest")  # recover sebelum pertarungan berikutnya
    # Quest selesai via cascade setelah kill terakhir (tanpa workaround).
    assert "fquest_rebels_kiriman_done" in session.state.flags
    assert "fquest_rebels_kiriman" in session.state.quests.done
    assert session.state.reputation["rebels"] >= 15

    # === Verifikasi Final ===
    # 8 quest utama done
    assert len(session.state.quests.done) >= 8
    main_quests = [
        q for q in session.state.quests.done if q.startswith("quest10")
    ]
    assert len(main_quests) == 8

    # 2 faction quest done
    faction_quests = [
        q for q in session.state.quests.done if q.startswith("fquest_")
    ]
    assert len(faction_quests) == 2

    # Memories collected
    assert len(session.state.memories) >= 3

    # Maps unlocked
    assert "sect_azure" in session.state.map_unlocks
    assert "guild_city" in session.state.map_unlocks

    # Skills available (5 elemen)
    skills = set(session.player_skills)
    assert "qi_slash" in skills
    assert "flame_strike" in skills
    assert "frost_bind" in skills
    assert "vine_grasp" in skills
    assert "earth_charge" in skills
    assert "serbuan_akar" in skills
    assert "perisai_tanah" in skills

    # Tier progression
    assert session.state.player.tier_order >= 1

    # Reputasi berubah dari choices
    assert session.state.reputation["holy_order"] != 0
    assert session.state.reputation["rebels"] != 0
    assert session.state.reputation["ancient_order"] != 0

    # Ending path flag set
    assert any(flag.startswith("ending_path_") for flag in session.state.flags)

    print("✅ Arc 1 full playthrough PASSED")


def _rekrut_lin_wei(session: GameSession) -> None:
    """Suntik rekan Lin Wei langsung ke state (bukan via event)."""
    from src.models.party import Companion

    session.state.party = [
        Companion(
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
        ).to_dict()
    ]
    session.state.party_active = ["lin_wei"]


def test_battle_dengan_rekan_aktif_dan_bond_xp(tmp_path):
    """Rekan aktif ikut bertarung; bond XP naik setelah menang (GDD §20.3)."""
    session = _session(tmp_path)
    session.new_game("Akar")
    _rekrut_lin_wei(session)
    _dispatch(session, "talk elder_mao")
    session.state.player.add_insight(100)
    _dispatch(session, "breakthrough")
    _dispatch(session, "go ashfall_forest")
    _dispatch(session, "look")
    assert len(session.battle.allies) == 2
    frame = session.battle_frame()
    while not frame.over:
        frame = session.battle_step("attack")
    assert frame.victory is True
    member = next(m for m in session.state.party if m["id"] == "lin_wei")
    assert member["bond_xp"] > 0


def test_rekan_ko_pulih_setelah_pertarungan(tmp_path):
    """KO rekan dipulihkan otomatis pasca battle (GDD §20.4)."""
    session = _session(tmp_path)
    session.new_game("Akar")
    _rekrut_lin_wei(session)
    _dispatch(session, "talk elder_mao")
    session.state.player.add_insight(100)
    _dispatch(session, "breakthrough")
    _dispatch(session, "go ashfall_forest")
    _dispatch(session, "look")
    ally = session.battle.allies[1]
    ally.hp = 0  # simulasi KO
    while not session.battle_frame().over:
        session.battle_step("attack")
    member = next(m for m in session.state.party if m["id"] == "lin_wei")
    assert member["hp"] == member["stats"]["hp"]  # pulih penuh


def test_swap_hanya_di_lokasi_aman(tmp_path):
    """Swap komposisi dilarang di area berbahaya (GDD §20.1)."""
    session = _session(tmp_path)
    session.new_game("Akar")
    _rekrut_lin_wei(session)
    _dispatch(session, "go ashfall_forest")  # peta dengan musuh
    lines = _dispatch(session, "swap lin_wei")
    assert any("aman" in line.lower() for line in lines)


def test_party_menampilkan_rekan_dan_bond(tmp_path):
    """Perintah party menampilkan anggota aktif + bond XP (GDD §20.3)."""
    session = _session(tmp_path)
    session.new_game("Akar")
    _rekrut_lin_wei(session)
    session.state.party[0]["bond_xp"] = 25
    lines = _dispatch(session, "party")
    assert any("Lin Wei" in line for line in lines)
    assert any("bond" in line.lower() for line in lines)


def test_battleframe_mengumumkan_giliran_rekan(tmp_path):
    """BattleFrame menyebut nama sekutu yang menunggu perintah (GDD §6).

    Regresi multi-ally: pemain (dan AI tester) harus tahu giliran siapa
    yang aktif — aksi invalid untuk rekan = error frame tanpa advance.
    """
    session = _session(tmp_path)
    session.new_game("Akar")
    _rekrut_lin_wei(session)
    _dispatch(session, "talk elder_mao")
    session.state.player.add_insight(100)
    _dispatch(session, "breakthrough")
    _dispatch(session, "go ashfall_forest")
    _dispatch(session, "look")
    assert len(session.battle.allies) == 2
    frame = session.battle_frame()
    # Musuh berinisiatif duluan mungkin; maju sampai giliran sekutu.
    while not frame.player_turn and not frame.over:
        frame = session.battle_step("attack")
    assert frame.player_turn is True
    assert frame.active_ally_name in {"Akar", "Lin Wei"}
    assert any(
        line.startswith(f"[Giliran {frame.active_ally_name}]")
        for line in frame.log
    )


def test_battleframe_giliran_kosong_saat_pertarungan_selesai(tmp_path):
    """Pasca pertarungan, tidak ada penanda giliran (GDD §6)."""
    session = _session(tmp_path)
    session.new_game("Akar")
    _rekrut_lin_wei(session)
    _dispatch(session, "talk elder_mao")
    session.state.player.add_insight(100)
    _dispatch(session, "breakthrough")
    _dispatch(session, "go ashfall_forest")
    _dispatch(session, "look")
    while not session.battle_frame().over:
        session.battle_step("attack")
    frame = session.battle_frame()
    assert frame.active_ally_name is None
    assert not any(line.startswith("[Giliran ") for line in frame.log)


def test_party_lines_menampilkan_header_dan_slot_kosong(tmp_path):
    """Panel party: header PARTY (n/4) + slot rekan kosong (GDD §14.1)."""
    session = _session(tmp_path)
    session.new_game("Akar")
    joined = "\n".join(session.party_lines())
    assert "PARTY (1/4)" in joined
    assert "(kosong)" in joined


def test_party_lines_menampilkan_tier_dan_bond_rekan(tmp_path):
    """Panel party menampilkan tier + bond rekan aktif (GDD §20.3)."""
    session = _session(tmp_path)
    session.new_game("Akar")
    _rekrut_lin_wei(session)
    session.state.party[0]["bond_xp"] = 25
    joined = "\n".join(session.party_lines())
    assert "PARTY (2/4)" in joined
    assert "qi_condensation" in joined  # tier rekan
    assert "bond 25" in joined


def test_party_lines_hp_live_saat_battle(tmp_path):
    """Panel party memakai HP combatan live selama battle (regresi Bug 1).

    Sebelumnya panel membaca state.party (stale) — HUD pemain pakai
    _ally.hp live, jadi panel rekan menyesatkan saat bertarung.
    """
    session = _session(tmp_path)
    session.new_game("Akar")
    _rekrut_lin_wei(session)
    _dispatch(session, "talk elder_mao")
    session.state.player.add_insight(100)
    _dispatch(session, "breakthrough")
    _dispatch(session, "go ashfall_forest")
    _dispatch(session, "look")
    session.battle.allies[1].hp = 5  # lukai combatant live Lin Wei
    joined = "\n".join(session.party_lines())
    assert "5/30" in joined
    assert "30/30" not in joined


def test_start_battle_clamp_maksimal_tiga_rekan(tmp_path):
    """Save korup party_active>3 tetap dibatasi 3 rekan (GDD §24.1)."""
    session = _session(tmp_path)
    session.new_game("Akar")
    from src.models.party import Companion

    for i in range(4):
        session.state.party.append(
            Companion(
                id=f"r{i}",
                name=f"Rekan {i}",
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
            ).to_dict()
        )
    session.state.party_active = ["r0", "r1", "r2", "r3"]
    _dispatch(session, "go ashfall_forest")
    _dispatch(session, "look")
    assert len(session.battle.allies) == 4  # protagonis + maks 3 rekan


def test_party_menampilkan_roster_cadangan(tmp_path):
    """Rekan di roster tapi tidak aktif tampil sebagai cadangan (Bug 3)."""
    session = _session(tmp_path)
    session.new_game("Akar")
    _rekrut_lin_wei(session)  # lin_wei aktif
    from src.models.party import Companion

    session.state.party.append(
        Companion(
            id="mira",
            name="Mira",
            tier="qi_condensation",
            element="fire",
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
        ).to_dict()
    )
    joined = "\n".join(session.party_lines())
    assert "Mira" in joined
    assert "Cadangan" in joined


# ----------------------------------------------------------------------
# UI No-Typing (GDD §18.2, §14.1): menu_actions + dialog_choices
# ----------------------------------------------------------------------


def test_menu_actions_dunia_berisi_aksi_standar(tmp_path):
    """Menu dunia memuat aksi inti dengan command raw yang valid."""
    session = _session(tmp_path)
    session.new_game("Akar")
    actions = session.menu_actions()
    ids = {action["id"] for action in actions}
    assert {"lihat", "pergi", "istirahat", "status"} <= ids
    pergi = next(a for a in actions if a["id"] == "pergi")
    assert any(sub["command"] == "go ashfall_forest" for sub in pergi["sub"])
    assert any(sub["command"] == "go village_emberfall" for sub in pergi["sub"])


def test_menu_actions_sub_bicara_hanya_npc_di_lokasi(tmp_path):
    """Sub-menu bicara hanya NPC yang berada di lokasi pemain."""
    session = _session(tmp_path)
    session.new_game("Akar")
    actions = session.menu_actions()
    bicara = next(a for a in actions if a["id"] == "bicara")
    ids = {sub["id"] for sub in bicara["sub"]}
    assert "elder_mao" in ids  # di village_emberfall
    assert "penjaga_makam" not in ids  # di ruin_shrine


def test_menu_actions_battle_memuat_aksi_giliran(tmp_path):
    """Menu battle memuat serang/bertahan/amati/kabur + teknik & item."""
    session = _session(tmp_path)
    session.new_game("Akar")
    session.state.flags["map_ashfall_forest_unlocked"] = True
    _dispatch(session, "go ashfall_forest")
    _dispatch(session, "look")
    assert session.in_battle
    actions = session.menu_actions()
    ids = {action["id"] for action in actions}
    assert {"serang", "bertahan", "amati", "kabur"} <= ids
    assert all(action["battle"] for action in actions)


def test_menu_actions_toko_hanya_saat_pedagang_ada(tmp_path):
    """Aksi toko hanya muncul bila ada pedagang di lokasi."""
    session = _session(tmp_path)
    session.new_game("Akar")
    assert any(a["id"] == "toko" for a in session.menu_actions())
    session.state.flags["map_ashfall_forest_unlocked"] = True
    _dispatch(session, "go ashfall_forest")
    assert not any(a["id"] == "toko" for a in session.menu_actions())


def test_dialog_choices_membaca_pending_dialog(tmp_path):
    """dialog_choices: pilihan dialog aktif + hint efek dari aksi."""
    session = _session(tmp_path)
    session.new_game("Akar")
    assert session.dialog_choices() == []
    _dispatch(session, "talk elder_mao")
    choices = session.dialog_choices()
    assert choices, "dialog elder_mao harus punya pilihan"
    assert choices[0]["id"]
    assert "text" in choices[0]


def test_battle_frame_memuat_allies(tmp_path):
    """BattleFrame.allies: nama + hp/qi tiap anggota tim (GDD §6)."""
    session = _session(tmp_path)
    session.new_game("Akar")
    session.state.flags["map_ashfall_forest_unlocked"] = True
    _dispatch(session, "go ashfall_forest")
    _dispatch(session, "look")
    frame = session.battle_frame()
    assert len(frame.allies) == 1  # hanya protagonis
    assert frame.allies[0]["name"] == "Akar"
    assert "hp" in frame.allies[0] and "qi_max" in frame.allies[0]


def test_missing_exploration_commands(tmp_path):
    """Test perintah non-stub yang masih ada (settings, recall)."""
    session = _session(tmp_path)
    session.new_game("Akar")

    # settings
    res = _dispatch(session, "settings")
    assert "Pengaturan" in res[0]

    # recall
    res = _dispatch(session, "recall")
    assert "recall" in res[0].lower()


# ----------------------------------------------------------------------
# Sistem Formasi (GDD §7, §18.2): command formation + buff battle
# ----------------------------------------------------------------------


def test_cmd_formation_set_dan_clear(tmp_path):
    """Formation <id> memasang formasi; tanpa argumen membongkarnya."""
    session = _session(tmp_path)
    session.new_game("Akar")
    res = _dispatch(session, "formation jaring_naga")
    assert "Jaring Naga" in " ".join(res)
    assert session.state.formation_active == "jaring_naga"
    res = _dispatch(session, "formation")
    assert session.state.formation_active is None


def test_cmd_formation_menolak_id_tak_dikenal(tmp_path):
    """Formation dengan id tak dikenal ditolak, tidak mengubah state."""
    session = _session(tmp_path)
    session.new_game("Akar")
    res = _dispatch(session, "formation tidak_ada")
    assert any("tidak dikenal" in line for line in res)
    assert session.state.formation_active is None


def test_cmd_formation_ditolak_saat_battle(tmp_path):
    """Mengatur formasi saat bertarung ditolak (sama dengan swap)."""
    session = _session(tmp_path)
    session.new_game("Akar")
    session.state.flags["map_ashfall_forest_unlocked"] = True
    _dispatch(session, "go ashfall_forest")
    _dispatch(session, "look")
    res = _dispatch(session, "formation jaring_naga")
    assert any("bertarung" in line for line in res)
    assert session.state.formation_active is None


def test_cmd_formation_hanya_di_lokasi_aman(tmp_path):
    """Formation di area berbahaya (peta dengan musuh) ditolak."""
    session = _session(tmp_path)
    session.new_game("Akar")
    session.state.flags["map_ashfall_forest_unlocked"] = True
    _dispatch(session, "go ashfall_forest")
    res = _dispatch(session, "formation jaring_naga")
    assert any("aman" in line.lower() for line in res)
    assert session.state.formation_active is None


def test_start_battle_menerapkan_buff_formasi_ke_semua_ally(tmp_path):
    """Buff formasi diterapkan ke seluruh ally (protagonis + rekan)."""
    session = _session(tmp_path)
    session.new_game("Akar")
    base_defense = session.state.player.stats["defense"]
    session.state.formation_active = "jaring_naga"
    session._start_battle("babi_hutan_qi")
    ally = session.battle.allies[0]
    assert ally.stats["defense"] == base_defense + 20


def test_start_battle_buff_formasi_ke_rekan_aktif(tmp_path):
    """Rekan aktif ikut menerima buff formasi (GDD §7, buff area)."""
    session = _session(tmp_path)
    session.new_game("Akar")
    _rekrut_lin_wei(session)
    base_defense = session.state.party[0]["stats"]["defense"]
    session.state.formation_active = "jaring_naga"
    session._start_battle("babi_hutan_qi")
    ally = session.battle.allies[1]
    assert ally.stats["defense"] == base_defense + 20


def test_battle_step_formation_skill_menggunakan_teknik_formasi(tmp_path):
    """Aksi formation_skill diterjemahkan ke teknik formasi aktif.

    Perilaku: aksi diterjemahkan tanpa ValueError "aksi tidak dikenal"
    dari Battle; bila qi kurang, error yang muncul soal qi (bukan aksi).
    """
    session = _session(tmp_path)
    session.new_game("Akar")
    session.state.formation_active = "benteng_bumi"
    session._start_battle("babi_hutan_qi")
    frame = session.battle_step("formation_skill")
    assert frame.error is None or "qi" in frame.error.lower()


def test_player_skills_memuat_skill_formasi_aktif(tmp_path):
    """Skill formasi aktif ikut tersedia di player_skills (GDD §18.3)."""
    session = _session(tmp_path)
    session.new_game("Akar")
    assert "perisai_tanah" not in session.player_skills
    session.state.formation_active = "benteng_bumi"
    assert "perisai_tanah" in session.player_skills


# ----------------------------------------------------------------------
# Binatang Roh (GDD §20.3): recall via swap, telur menetas jadi rekan
# ----------------------------------------------------------------------


def test_cmd_recall_mendelegasikan_ke_swap(tmp_path):
    """Recall panggil/lepas rekan — semantik sama dengan swap."""
    session = _session(tmp_path)
    session.new_game("Akar")
    session.state.party = [{"id": "lin_wei", "name": "Lin Wei"}]
    session.state.party_active = []
    res = session._cmd_recall(
        Command(name="recall", args=("lin_wei",), raw="recall lin_wei")
    )
    assert "Lin Wei" in " ".join(res)
    assert "lin_wei" in session.state.party_active
    res = session._cmd_recall(
        Command(name="recall", args=("lin_wei",), raw="recall lin_wei")
    )
    assert "lin_wei" not in session.state.party_active


def test_cmd_recall_tanpa_argumen_memberi_hint(tmp_path):
    """Recall tanpa argumen memunculkan hint penggunaan (GDD §18.2)."""
    session = _session(tmp_path)
    session.new_game("Akar")
    res = session._cmd_recall(Command(name="recall", args=(), raw="recall"))
    assert "recall" in res[0].lower()


def test_cmd_use_menetaskan_telur_menambah_rekan(tmp_path):
    """Item effect hatch_companion menambah rekan dan menghapus telur."""
    session = _session(tmp_path)
    session.new_game("Akar")
    session.state.inventory["items"]["telur_phoenix_abu"] = 1
    session._cmd_use(
        Command(
            name="use",
            args=("telur_phoenix_abu",),
            raw="use telur_phoenix_abu",
        )
    )
    ids = [raw["id"] for raw in session.state.party]
    assert "phoenix_abu" in ids
    assert session.state.inventory["items"].get("telur_phoenix_abu", 0) == 0


def test_run_events_menampilkan_epilog_sekali(tmp_path):
    """Setelah flag ending diset, _run_events memuat epilog satu kali saja."""
    session = _session(tmp_path)
    session.new_game("Akar")
    session.state.flags["ending_defy_win"] = True
    first = session._run_events()
    assert any("EPILOG" in line for line in first)
    second = session._run_events()
    assert not any("EPILOG" in line for line in second)


def test_bos_kalah_memantik_ending_dan_epilog_satu_pass(tmp_path):
    """Rantai penuh: bos kalah -> ending event + epilog satu pass."""
    session = _session(tmp_path)
    session.new_game("Akar")
    session.state.ending_points = {"defy": 1, "seal": 8, "reconcile": 2}
    session.state.flags["arc4_boss_defeated"] = True
    first = session._run_events()
    joined = "\n".join(first)
    assert session.state.flags.get("ending_seal_win") is True
    assert "MENYEGEL DIRI" in joined
    assert "— EPILOG —" in joined
    second = session._run_events()
    assert "— EPILOG —" not in "\n".join(second)


def test_quest408_selesai_memantik_ending_in_game(tmp_path):
    """quest408 selesai (bos suara kalah) -> arc4_boss_defeated -> ending."""
    session = _session(tmp_path)
    session.new_game("Akar")
    session.state.ending_points = {"defy": 50, "seal": 10, "reconcile": 10}
    session.state.quests.done.append("quest408")
    session.state.flags["quest408_done"] = True
    # Pass 1: suara_defeated (s) men-set arc4_boss_defeated; pass 2:
    # calculate_ending_trigger (c) men-set ending_defy_win -> ending_defy.
    session._run_events()
    joined = "\n".join(session._run_events())
    assert session.state.flags.get("arc4_boss_defeated") is True
    assert session.state.flags.get("ending_defy_win") is True
    assert "MENENTANG LANGIT" in joined
    assert "— EPILOG —" in joined
