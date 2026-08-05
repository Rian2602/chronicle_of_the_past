"""Generate quest003-quest045 (Season 1) JSON files.

Run: .venv/bin/python tools/generate_season1_quests.py

Requirements kinds restricted to {talk, map, flag, enemy} per
test_quest_requirement_kinds. Kill counts use flags `killed_<enemy>_<N>`
set by the game engine hook. Collect requirements use flags
`have_<item>`. Reputation factions must be in FACTIONS.

Re-runnable: existing files are overwritten.
"""

import json
import os

OUT_DIR = "data/quests"


def quest(
    qid,
    title,
    description,
    objectives,
    requirements,
    rewards,
    flags_on_complete,
    next_id,
):
    return {
        "id": qid,
        "title": title,
        "type": "main",
        "description": description,
        "objectives": objectives,
        "requirements": requirements,
        "rewards": rewards,
        "flags_on_complete": flags_on_complete,
        "next": next_id,
    }


# ---------------------------------------------------------------------------
# Arc 2 - Jangkar Waktu (quest003-quest011)
# ---------------------------------------------------------------------------
QUESTS = {}

QUESTS["quest003"] = quest(
    "quest003",
    "Gema di Bawah Perpustakaan",
    "Bicaralah dengan Aria lalu hadapi mata-mata "
    "kerajaan di ruang bawah perpustakaan.",
    [
        "Bicaralah dengan Aria di desa.",
        "Kalahkan mata-mata kerajaan (royal_scout).",
    ],
    [
        {"kind": "talk", "target": "old_man"},
        {"kind": "enemy", "target": "royal_scout"},
    ],
    {"xp": 60, "gold": 20, "reputation": {"ancient_order": 5}},
    ["arc2_started", "map_anchor_vault_unlocked"],
    "quest004",
)

QUESTS["quest004"] = quest(
    "quest004",
    "Batu yang Berdenyut",
    "Turun ke ruang bawah tanah dan temukan dinding batu yang berdenyut.",
    ["Kunjungi ruang bawah tanah (anchor_vault)."],
    [{"kind": "map", "target": "anchor_vault"}],
    {"xp": 50, "gold": 15},
    ["found_anchor_vault"],
    "quest005",
)

QUESTS["quest005"] = quest(
    "quest005",
    "Utusan dari Ibukota",
    "Finn tertangkap basah mengirim burung surat ke ibukota.",
    [
        "Bicaralah dengan Finn.",
        "Tangkap atau lepaskan Finn.",
    ],
    [
        {"kind": "talk", "target": "finn"},
        {"kind": "flag", "target": "finn_caught"},
    ],
    {"xp": 60, "gold": 10},
    ["met_finn", "map_forest_deep_unlocked"],
    "quest006",
)

QUESTS["quest006"] = quest(
    "quest006",
    "Darah di Hutan Dalam",
    "Selidiki jejak darah dan kamp tentara bayaran di hutan dalam.",
    [
        "Kunjungi hutan dalam (forest_deep).",
        "Kalahkan 2 tentara bayaran (mercenary_soldier).",
    ],
    [
        {"kind": "map", "target": "forest_deep"},
        {"kind": "flag", "target": "killed_mercenary_soldier_2"},
    ],
    {"xp": 80, "gold": 25},
    ["forest_deep_searched"],
    "quest007",
)

QUESTS["quest007"] = quest(
    "quest007",
    "Pilihan Aliansi",
    "Pilih satu faksi untuk diajak bekerja sama "
    "menghadapi konflik yang memanas.",
    ["Bicaralah dengan pemimpin faksi pilihanmu."],
    [{"kind": "flag", "target": "aligned_any"}],
    {"xp": 70, "gold": 20, "reputation": {"ancient_order": 10}},
    [],
    "quest008",
)

QUESTS["quest008"] = quest(
    "quest008",
    "Punggung Pisau",
    "Kade tahu siapa yang membayar tentara bayaran. Tawarkan kesepakatan.",
    [
        "Bicaralah dengan Kade di sarang.",
        "Selesaikan kesepakatan dengan Kade.",
    ],
    [
        {"kind": "talk", "target": "kade"},
        {"kind": "flag", "target": "kade_deal_done"},
    ],
    {"xp": 80, "gold": 30},
    [],
    "quest009",
)

QUESTS["quest009"] = quest(
    "quest009",
    "Dinding Reruntuhan",
    "Gerbang reruntuhan terkunci. Kumpulkan rune_key dari pemulung reruntuhan.",
    [
        "Kunjungi pintu masuk reruntuhan (ruins_entrance).",
        "Dapatkan kunci batu berukir (rune_key).",
    ],
    [
        {"kind": "map", "target": "ruins_entrance"},
        {"kind": "flag", "target": "have_rune_key"},
    ],
    {"xp": 70, "gold": 20},
    ["map_ancient_ruins_unlocked"],
    "quest010",
)

QUESTS["quest010"] = quest(
    "quest010",
    "Reruntuhan Berbisik",
    "Roh Penjaga memainkan echo pertama. Kalahkan pemulung yang menyerbu.",
    [
        "Kunjungi reruntuhan kuno (ancient_ruins).",
        "Kalahkan 3 pemulung reruntuhan (ruins_scavenger).",
        "Bicaralah dengan Roh Penjaga.",
    ],
    [
        {"kind": "map", "target": "ancient_ruins"},
        {"kind": "flag", "target": "killed_ruins_scavenger_3"},
        {"kind": "talk", "target": "ancient_spirit"},
    ],
    {"xp": 90, "gold": 25, "reputation": {"ancient_order": 5}},
    ["echo_1_collected"],
    "quest011",
)

QUESTS["quest011"] = quest(
    "quest011",
    "Kapten Bayaran",
    "Kapten Reiner memimpin pasukan bayaran mengepung tepi hutan. Hadapi dia.",
    ["Kalahkan Kapten Reiner (captain_reiner)."],
    [{"kind": "enemy", "target": "captain_reiner"}],
    {"xp": 150, "gold": 60, "reputation": {"ancient_order": 10}},
    ["boss_arc2_defeated", "reiner_info"],
    "quest012",
)

# ---------------------------------------------------------------------------
# Arc 3 - Perang Bayangan (quest012-quest020)
# ---------------------------------------------------------------------------

QUESTS["quest012"] = quest(
    "quest012",
    "Api di Tepi Hutan",
    "Rumah Tom terbakar. Selidiki jejak minyak api suci milik gereja.",
    [
        "Bicaralah dengan Tom di desa.",
        "Periksa lokasi kebakaran di hutan dalam (forest_deep).",
    ],
    [
        {"kind": "talk", "target": "tom"},
        {"kind": "map", "target": "forest_deep"},
    ],
    {"xp": 80, "gold": 20},
    ["first_fire", "villager_missing"],
    "quest013",
)

QUESTS["quest013"] = quest(
    "quest013",
    "Gereja yang Menghakimi",
    "Sister Iris memberi ultimatum 5 hari. Pilih sikapmu.",
    [
        "Bicaralah dengan Sister Iris.",
        "Terima ultimatum gereja.",
    ],
    [
        {"kind": "talk", "target": "sister_iris"},
        {"kind": "flag", "target": "ultimatum_received"},
    ],
    {"xp": 80},
    ["ultimatum_5_days", "map_crime_den_unlocked"],
    "quest014",
)

QUESTS["quest014"] = quest(
    "quest014",
    "Sarang Serigala Malam",
    "Cari arsip pembayaran gereja di sarang Kade.",
    [
        "Kunjungi sarang (crime_den).",
        "Bicaralah dengan Kade tentang arsip pembayaran.",
    ],
    [
        {"kind": "map", "target": "crime_den"},
        {"kind": "talk", "target": "kade"},
    ],
    {"xp": 90, "gold": 35},
    ["crime_archive", "have_evidence_letter"],
    "quest015",
)

QUESTS["quest015"] = quest(
    "quest015",
    "Harga Sebuah Nama",
    "Sebuah faksi memintamu mengungkap lokasi Jangkar. Pilih dengan bijak.",
    ["Buat keputusan tentang lokasi Jangkar."],
    [{"kind": "flag", "target": "quest015_resolved"}],
    {"xp": 100},
    ["map_rebel_camp_unlocked"],
    "quest016",
)

QUESTS["quest016"] = quest(
    "quest016",
    "Kamp Pemberontak",
    "Sera mengundangmu ke kamp pemberontak. Bantu mereka atau tolak.",
    [
        "Kunjungi kamp pemberontak (rebel_camp).",
        "Bicaralah dengan Sera.",
    ],
    [
        {"kind": "map", "target": "rebel_camp"},
        {"kind": "talk", "target": "sera"},
    ],
    {"xp": 100, "gold": 30, "reputation": {"rebels": 10}},
    [],
    "quest017",
)

QUESTS["quest017"] = quest(
    "quest017",
    "Sketsa dari Akademi",
    "Kumpulkan gulungan kuno dan bantu Prof. Kael mengartikan ukiran.",
    [
        "Kumpulkan 2 gulungan kuno (old_scroll).",
        "Bicaralah dengan Prof. Kael.",
    ],
    [
        {"kind": "flag", "target": "have_old_scrolls"},
        {"kind": "talk", "target": "kael"},
    ],
    {"xp": 100, "gold": 20, "reputation": {"scholar_society": 10}},
    ["ancient_script_decoded"],
    "quest018",
)

QUESTS["quest018"] = quest(
    "quest018",
    "Pengkhianatan di Pasar",
    "Marcus menjual info lokasi Jangkar. Selamatkan dia dari pengawal gilda.",
    [
        "Bicaralah dengan Marcus.",
        "Kalahkan pengawal gilda (guild_guard).",
    ],
    [
        {"kind": "talk", "target": "marcus"},
        {"kind": "enemy", "target": "guild_guard"},
    ],
    {"xp": 110, "gold": 40, "reputation": {"merchant_guild": 5}},
    [],
    "quest019",
)

QUESTS["quest019"] = quest(
    "quest019",
    "Malam Serigala",
    "Inkuisisi menyerang desa di malam hari. Pertahankan desa.",
    ["Kalahkan 3 tentara inkuisisi (inquisitor_soldier)."],
    [{"kind": "flag", "target": "killed_inquisitor_soldier_3"}],
    {"xp": 120, "gold": 30, "reputation": {"rebels": 5}},
    ["village_defended"],
    "quest020",
)

QUESTS["quest020"] = quest(
    "quest020",
    "Api Hakim",
    "Duel puncak dengan Sister Iris. "
    "Dia hanya alat - Varek yang memerintahkan.",
    ["Kalahkan Sister Iris (sister_iris)."],
    [{"kind": "enemy", "target": "sister_iris"}],
    {"xp": 200, "gold": 70, "reputation": {"ancient_order": 10}},
    ["boss_arc3_defeated", "iris_revealed", "map_ruins_depth_unlocked"],
    "quest021",
)

# ---------------------------------------------------------------------------
# Arc 4 - Reruntuhan Waktu (quest021-quest029)
# ---------------------------------------------------------------------------

QUESTS["quest021"] = quest(
    "quest021",
    "Gerbang yang Terkunci",
    "Gerbang dalam reruntuhan bertulis tiga segel. Buka jalan masuk.",
    ["Kunjungi kedalaman reruntuhan (ruins_depth)."],
    [{"kind": "map", "target": "ruins_depth"}],
    {"xp": 100, "gold": 20},
    [],
    "quest022",
)

QUESTS["quest022"] = quest(
    "quest022",
    "Echo: Hari Pembuat",
    "Roh Penjaga memainkan echo terbesar: hari Jangkar ditempa.",
    ["Bicaralah dengan Roh Penjaga."],
    [{"kind": "talk", "target": "ancient_spirit"}],
    {"xp": 110},
    [],
    "quest023",
)

QUESTS["quest023"] = quest(
    "quest023",
    "Segel Darah",
    "Segel pertama dibuka dengan kekuatan: kalahkan penjaga altar.",
    ["Kalahkan penjaga reruntuhan (ruin_warden)."],
    [{"kind": "enemy", "target": "ruin_warden"}],
    {"xp": 120, "gold": 25},
    [],
    "quest024",
)

QUESTS["quest024"] = quest(
    "quest024",
    "Segel Kebijaksanaan",
    "Segel kedua dibuka dengan akal: jawab teka-teki Roh Penjaga.",
    [
        "Bicaralah dengan Roh Penjaga.",
        "Jawab teka-teki dengan benar.",
    ],
    [
        {"kind": "talk", "target": "ancient_spirit"},
        {"kind": "flag", "target": "seal_of_wisdom_ok"},
    ],
    {"xp": 120},
    [],
    "quest025",
)

QUESTS["quest025"] = quest(
    "quest025",
    "Segel Waktu",
    "Segel ketiga adalah ujian waktu: selaraskan memori.",
    ["Selaraskan memori dengan Jangkar."],
    [{"kind": "flag", "target": "seal_of_time_ok"}],
    {"xp": 120},
    ["map_anchor_chamber_unlocked"],
    "quest026",
)

QUESTS["quest026"] = quest(
    "quest026",
    "Koridor yang Berdenyut",
    "Jalan menuju ruang Jangkar dipenuhi hantu waktu.",
    [
        "Kunjungi ruang Jangkar (anchor_chamber).",
        "Kalahkan 2 hantu waktu (time_wraith).",
    ],
    [
        {"kind": "map", "target": "anchor_chamber"},
        {"kind": "flag", "target": "killed_time_wraith_2"},
    ],
    {"xp": 130, "gold": 30},
    ["map_capital_unlocked"],
    "quest027",
)

QUESTS["quest027"] = quest(
    "quest027",
    "Raja yang Terlupakan",
    "Perjalanan ke ibukota. Hadap raja Aldric dan pilih sikapmu.",
    [
        "Kunjungi ibukota (capital).",
        "Bicaralah dengan Raja Aldric.",
    ],
    [
        {"kind": "map", "target": "capital"},
        {"kind": "talk", "target": "king_aldric"},
    ],
    {"xp": 140, "gold": 40},
    [],
    "quest028",
)

QUESTS["quest028"] = quest(
    "quest028",
    "Pendengaran Rahasia",
    "Kumpulkan bukti terakhir bahwa Varek memerintahkan pembakaran.",
    [
        "Pegang surat bukti (evidence_letter).",
        "Buktikan konspirasi Varek.",
    ],
    [
        {"kind": "flag", "target": "have_evidence_letter"},
        {"kind": "flag", "target": "conspiracy_proven"},
    ],
    {"xp": 140, "gold": 20},
    [],
    "quest029",
)

QUESTS["quest029"] = quest(
    "quest029",
    "Penjaga Waktu",
    "Konstruk Penjaga Waktu menyerang di ruang Jangkar. Kalahkan dia.",
    ["Kalahkan Penjaga Waktu (time_guardian)."],
    [{"kind": "enemy", "target": "time_guardian"}],
    {"xp": 280, "gold": 90, "reputation": {"ancient_order": 10}},
    ["boss_arc4_defeated", "met_anchor_avatar"],
    "quest030",
)

# ---------------------------------------------------------------------------
# Arc 5 - Sejarah Baru (quest030-quest036)
# ---------------------------------------------------------------------------

QUESTS["quest030"] = quest(
    "quest030",
    "Suara Jangkar",
    "Avatar Jangkar menjelaskan kebenaran: darahmu terhubung dengan Kaum Arah.",
    ["Bicaralah dengan Suara Jangkar (anchor_avatar)."],
    [{"kind": "talk", "target": "anchor_avatar"}],
    {"xp": 130},
    [],
    "quest031",
)

QUESTS["quest031"] = quest(
    "quest031",
    "Persiapan Badai",
    "Kumpulkan sekutu untuk menghadapi pengepungan.",
    [
        "Bicaralah dengan 2 sekutu (Lyra dan Sera).",
    ],
    [
        {"kind": "talk", "target": "lyra"},
        {"kind": "talk", "target": "sera"},
    ],
    {"xp": 150},
    [],
    "quest032",
)

QUESTS["quest032"] = quest(
    "quest032",
    "Pengepungan Gereja",
    "Inkuisisi mengepung desa. Pertahankan garis terakhir.",
    ["Kalahkan 4 tentara inkuisisi (inquisitor_soldier)."],
    [{"kind": "flag", "target": "killed_inquisitor_soldier_4"}],
    {"xp": 160, "gold": 40},
    ["siege_won"],
    "quest033",
)

QUESTS["quest033"] = quest(
    "quest033",
    "Kanselir Varek",
    "Kebenaran penuh: Varek merekayasa segalanya. Konfrontasi dia.",
    [
        "Buktikan konspirasi Varek.",
        "Bicaralah dengan Raja Aldric.",
    ],
    [
        {"kind": "flag", "target": "conspiracy_proven"},
        {"kind": "talk", "target": "king_aldric"},
    ],
    {"xp": 170, "gold": 50},
    ["varek_unmasked"],
    "quest034",
)

QUESTS["quest034"] = quest(
    "quest034",
    "Api Dimulai",
    "Inkuisisi membakar desa. Evakuasi Tom dan warga ke kamp pemberontak.",
    ["Evakuasi warga desa (village_evacuated)."],
    [{"kind": "flag", "target": "village_evacuated"}],
    {"xp": 180, "reputation": {"rebels": 10}},
    ["map_capital_keep_unlocked"],
    "quest035",
)

QUESTS["quest035"] = quest(
    "quest035",
    "Menembus Cincin Api",
    "Blokade api menghalangi jalan ke ibukota. Terobos.",
    [
        "Kunjungi benteng kerajaan (capital_keep).",
        "Kalahkan 2 ksatria kerajaan (royal_knight).",
    ],
    [
        {"kind": "map", "target": "capital_keep"},
        {"kind": "flag", "target": "killed_royal_knight_2"},
    ],
    {"xp": 190, "gold": 60},
    [],
    "quest036",
)

QUESTS["quest036"] = quest(
    "quest036",
    "Pilihan Terakhir",
    "Kau memegang takdir Jangkar. Keputusan ini menentukan akhir cerita.",
    ["Buat keputusan tentang nasib Jangkar."],
    [{"kind": "flag", "target": "ending_choice_pending"}],
    {"xp": 200},
    [],
    None,
)

# ---------------------------------------------------------------------------
# Quest jalur ending (quest037a-f, quest038a-f)
# ---------------------------------------------------------------------------

QUESTS["quest037a"] = quest(
    "quest037a",
    "Benteng Terakhir",
    "Pertahankan ruang Jangkar dari pasukan gereja yang menyerbu.",
    [
        "Kalahkan 3 tentara inkuisisi (inquisitor_soldier).",
        "Kalahkan Inkuisitor Agung (high_inquisitor).",
    ],
    [
        {"kind": "flag", "target": "killed_inquisitor_soldier_3"},
        {"kind": "enemy", "target": "high_inquisitor"},
    ],
    {"xp": 200, "gold": 50},
    ["quest037a_done"],
    "quest038a",
)

QUESTS["quest038a"] = quest(
    "quest038a",
    "Sumpah Penjaga",
    "Ritual penyegelan bersama Aria dan Lyra. Jadilah Penjaga Baru.",
    ["Selesaikan ritual penyegelan Jangkar."],
    [{"kind": "flag", "target": "seal_ritual_done"}],
    {"xp": 250},
    ["season1_path_done", "ending_a_done"],
    "quest039",
)

QUESTS["quest037b"] = quest(
    "quest037b",
    "Menyerbu Ibukota",
    "Bantu pemberontak merebut istana.",
    [
        "Kalahkan 2 ksatria kerajaan (royal_knight).",
        "Kalahkan pengawal elit (elite_guard).",
    ],
    [
        {"kind": "flag", "target": "killed_royal_knight_2"},
        {"kind": "enemy", "target": "elite_guard"},
    ],
    {"xp": 200, "gold": 50},
    ["quest037b_done"],
    "quest038b",
)

QUESTS["quest038b"] = quest(
    "quest038b",
    "Pena Rakyat",
    "Sera memakai Jangkar untuk menulis ulang dekrit penindasan.",
    ["Selesaikan penulisan ulang dekrit."],
    [{"kind": "flag", "target": "decree_written"}],
    {"xp": 250},
    ["season1_path_done", "ending_b_done"],
    "quest039",
)

QUESTS["quest037c"] = quest(
    "quest037c",
    "Pembersihan Istana",
    "Kalahkan pasukan Varek yang masih setia di istana.",
    [
        "Kalahkan 2 pemuja kultus (cult_acolyte).",
        "Kalahkan pembunuh mahkota (crown_assassin).",
    ],
    [
        {"kind": "flag", "target": "killed_cult_acolyte_2"},
        {"kind": "enemy", "target": "crown_assassin"},
    ],
    {"xp": 200, "gold": 50},
    ["quest037c_done"],
    "quest038c",
)

QUESTS["quest038c"] = quest(
    "quest038c",
    "Tahta yang Jujur",
    "Raja Aldric menyegel Jangkar di bawah istana. Varek dihukum.",
    ["Selesaikan penyegelan Jangkar di istana."],
    [{"kind": "flag", "target": "throne_sealed"}],
    {"xp": 250},
    ["season1_path_done", "ending_c_done"],
    "quest039",
)

QUESTS["quest037d"] = quest(
    "quest037d",
    "Menara Terkepung",
    "Akademi diserang. Pertahankan laboratorium.",
    [
        "Kalahkan 2 hantu waktu (time_wraith).",
        "Kalahkan arwah penguasa waktu (time_lord_wraith).",
    ],
    [
        {"kind": "flag", "target": "killed_time_wraith_2"},
        {"kind": "enemy", "target": "time_lord_wraith"},
    ],
    {"xp": 200, "gold": 50},
    ["quest037d_done"],
    "quest038d",
)

QUESTS["quest038d"] = quest(
    "quest038d",
    "Halaman Baru",
    "Kael membuka sekolah waktu dengan Jangkar.",
    ["Selesaikan pembukaan sekolah waktu."],
    [{"kind": "flag", "target": "school_opened"}],
    {"xp": 250},
    ["season1_path_done", "ending_d_done"],
    "quest039",
)

QUESTS["quest037e"] = quest(
    "quest037e",
    "Memutus Jangkar",
    "Ritual penghancuran. Lawan jelmaan marah Jangkar.",
    ["Kalahkan bayangan Jangkar (anchor_shade)."],
    [{"kind": "enemy", "target": "anchor_shade"}],
    {"xp": 200, "gold": 50},
    ["quest037e_done"],
    "quest038e",
)

QUESTS["quest038e"] = quest(
    "quest038e",
    "Pagi Tanpa Batu",
    "Jangkar hancur. Ancaman hilang, tapi waktu mulai tak menentu.",
    ["Selesaikan penghancuran Jangkar."],
    [{"kind": "flag", "target": "anchor_destroyed"}],
    {"xp": 250},
    ["season1_path_done", "ending_e_done"],
    "quest039",
)

QUESTS["quest037f"] = quest(
    "quest037f",
    "Malam Kedua",
    "Gunakan semua echo untuk kembali ke hari pembuatan Jangkar.",
    ["Kalahkan tiran kuno (ancient_tyrant)."],
    [{"kind": "enemy", "target": "ancient_tyrant"}],
    {"xp": 200, "gold": 50},
    ["quest037f_done"],
    "quest038f",
)

QUESTS["quest038f"] = quest(
    "quest038f",
    "Sejarah yang Tidak Pernah Ada",
    "Konflik tak pernah terjadi. Desa tak terbakar. "
    "Kau kehilangan sebagian ingatan.",
    ["Selesaikan penulisan ulang masa lalu."],
    [{"kind": "flag", "target": "rewrite_done"}],
    {"xp": 250},
    ["season1_path_done", "ending_f_done"],
    "quest039",
)

# ---------------------------------------------------------------------------
# Epilog (quest039-quest045)
# ---------------------------------------------------------------------------

QUESTS["quest039"] = quest(
    "quest039",
    "Perubahan Akhir",
    "Dunia berubah sesuai keputusanmu. Selesaikan urusan terakhir.",
    ["Selesaikan urusan akhir sesuai jalan cerita."],
    [{"kind": "flag", "target": "season1_path_done"}],
    {"xp": 150},
    [],
    "quest040",
)

QUESTS["quest040"] = quest(
    "quest040",
    "Perpisahan Sekutu",
    "Ucapkan selamat tinggal pada sekutu yang bertahan.",
    [
        "Bicaralah dengan Lyra.",
        "Bicaralah dengan Sera.",
    ],
    [
        {"kind": "talk", "target": "lyra"},
        {"kind": "talk", "target": "sera"},
    ],
    {"xp": 100},
    [],
    "quest041",
)

QUESTS["quest041"] = quest(
    "quest041",
    "Kenangan Terakhir",
    "Kumpulkan sisa kenangan dan pahami makna Pejalan Waktu.",
    [
        "Bicaralah dengan Lyra.",
    ],
    [
        {"kind": "talk", "target": "lyra"},
    ],
    {"xp": 100},
    [],
    "quest042",
)

QUESTS["quest042"] = quest(
    "quest042",
    "Waktu yang Tersisa",
    "Di ambang perpisahan, buat pilihan kecil: "
    "meninggalkan masa ini atau tinggal.",
    ["Bicaralah dengan Suara Jangkar (anchor_avatar)."],
    [{"kind": "talk", "target": "anchor_avatar"}],
    {"xp": 100},
    ["quest042_done"],
    "quest043",
)

QUESTS["quest043"] = quest(
    "quest043",
    "Catatan Seorang Pejalan Waktu",
    "Tuliskan catatan perjalananmu ke dalam buku perpustakaan.",
    ["Siapkan catatan perjalanan (recap_prepared)."],
    [{"kind": "flag", "target": "recap_prepared"}],
    {"xp": 100},
    [],
    "quest044",
)

QUESTS["quest044"] = quest(
    "quest044",
    "Epilog: Pagi di Ashen",
    "Scene penutup. Pagi di Ashen, bab terakhir musim pertama.",
    ["Selesaikan cerita musim pertama."],
    [{"kind": "flag", "target": "season1_path_done"}],
    {"xp": 0},
    ["season1_ended"],
    "quest045",
)

QUESTS["quest045"] = quest(
    "quest045",
    "Benih Musim Kedua",
    "Tanda anomali waktu muncul. Cerita berlanjut...",
    ["Lihat tanda dari masa depan."],
    [{"kind": "flag", "target": "season1_ended"}],
    {"xp": 0},
    ["season2_hint"],
    None,
)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for qid, data in QUESTS.items():
        path = os.path.join(OUT_DIR, f"{qid}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"wrote {path}")
    print(f"\n{len(QUESTS)} quests written to {OUT_DIR}/")


if __name__ == "__main__":
    main()
