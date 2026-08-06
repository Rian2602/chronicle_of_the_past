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
        "vine_grasp",
        "earth_charge",
        "serbuan_akar",
        "perisai_tanah",
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


def test_use_item_tanpa_efek_eksekusi_tetap_mengonsumsi(tmp_path):
    """Item effect combat-ready: konsumsi tapi tak ubah stat (YAGNI combat)."""
    session = _session(tmp_path)
    session.new_game("Akar")
    player = session.state.player
    before = (player.hp, player.qi, player.insight, player.meridian_buka)
    session.state.inventory.setdefault("items", {})["pil_uji_buff"] = 1
    _dispatch(session, "use pil_uji_buff")
    after = (player.hp, player.qi, player.insight, player.meridian_buka)
    assert after == before
    assert session.state.inventory["items"].get("pil_uji_buff", 0) == 0


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
    frame = session.battle_frame()
    while not frame.over:
        frame = session.battle_step("attack")
    assert frame.victory is True

    _dispatch(session, "look")  # penjaga_makam (bos)
    frame = session.battle_frame()
    while not frame.over:
        if session._ally.qi >= 8:
            frame = session.battle_step("technique:flame_strike")
        else:
            frame = session.battle_step("attack")
    assert frame.victory is True
    assert "quest103_done" in session.state.flags
    assert "memory_shrine_trial" in session.state.memories
    assert "pil_peneguh_fondasi" in session.state.inventory["items"]

    # === Transisi Arc 1→2: quest103_done event ===
    assert session.state.flags["map_sect_azure_unlocked"] is True
    assert session.state.flags["map_guild_city_unlocked"] is True
    assert "memory_arc1_complete" in session.state.memories
    assert "quest201" in session.state.quests.started

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
    frame = session.battle_frame()
    while not frame.over:
        if session._ally.qi >= 8:
            frame = session.battle_step("technique:flame_strike")
        else:
            frame = session.battle_step("attack")
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
        while not frame.over:
            if session._ally.qi >= 8:
                frame = session.battle_step("technique:flame_strike")
            else:
                frame = session.battle_step("attack")
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
