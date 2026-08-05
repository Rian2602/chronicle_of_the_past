# Spesifikasi Season 1 — "Jangkar Waktu" (The Time Anchor)

**Game:** Chronicle of the Past (CLI RPG teks, Python 3.12+ stdlib, Bahasa Indonesia)
**Status dokumen:** Draf spesifikasi — belum ada implementasi.
**Tujuan:** Melengkapi cerita game dari 2 quest menjadi **~45 quest utama hingga tamat (Season 1)**, dengan konten baru (peta, NPC, musuh, bos, item, skill) dan mekanik baru (kind quest baru, toko, perjalanan waktu, 4+ ending).

---

## 1. Ringkasan Eksekutif

Saat ini game hanya memiliki Arc 1 yang berakhir di quest002 ("Bahaya di Hutan") dengan banner **PERCABANGAN WAKTU**. Spesifikasi ini mendesain **Season 1 yang lengkap** dengan judul **"Jangkar Waktu"**:

- **5 arc**, total **45 quest utama** (2 sudah ada + 43 baru).
- **1 bos per arc** (total 4 bos baru + 1 set bos final bervariasi).
- **10 peta baru**, **±22 NPC baru**, **±25 musuh baru**, item bertier, dan skill kelas baru.
- **Mekanik baru:** kind quest `collect` / `kill_count` / `escort`, toko via dialog, kilas balik (echo) & penulisan ulang masa lalu, dan **6 ending berbeda** yang ditentukan keputusan besar + reputasi faksi.
- **Kompatibel dengan save lama** (pemain yang sudah menuntaskan Arc 1 bisa langsung lanjut ke quest003).

---

## 2. Pilar Desain (hasil wawancara)

Keputusan kunci yang disepakati:

| # | Aspek | Keputusan |
|---|-------|-----------|
| 1 | Fokus cerita | **Ancaman dari luar** — kebakaran desa hanya awal; ada ancaman besar dari ibukota kerajaan. |
| 2 | Antagonis | **Konflik antar faksi** — tidak ada penjahat tunggal; drama dari bentrokan 7 faksi. |
| 3 | Jumlah quest | **±45 quest, hampir semua utama**, mengalir berkelanjutan. |
| 4 | Akhir Season 1 | **Tamat + benih lanjutan** (teaser Season 2). |
| 5 | Peta baru | **7–10 peta baru**, termasuk dungeon berlapis dan ibukota kerajaan. |
| 6 | NPC baru | **16–30 NPC**: pemimpin faksi, pedagang, pendukung. |
| 7 | Bos | **Boss per arc** (~4–5 bos besar). |
| 8 | Toko | **Toko via dialog** (butuh mekanik engine baru). |
| 9 | Variasi quest | **Engine diperluas**: kind baru `collect`, `kill_count`, `escort`. |
| 10 | Percabangan | **Pilihan memengaruhi alur** — beberapa quest punya 2–3 penyelesaian; keputusan faksi mengubah jalan cerita. |
| 11 | Reputasi | **Memengaruhi ending** — reputasi akhir menentukan ending & benih Season 2. |
| 12 | Kurva level | **Level akhir 30–35**, musuh puncak level 25–30. |
| 13 | Struktur | **5 arc** (~9 quest/arc, 1 bos di akhir tiap arc). |
| 14 | Nada | **Gelap & serius** — pengkhianatan, korban berjatuhan, pilihan terasa berat. |
| 15 | Detail spec | **Semua quest dirinci penuh** (alur, NPC, syarat, hadiah, dialog inti, koneksi). |
| 16 | Save lama | **Harus kompatibel** — tanpa reset. |
| 17 | Perjalanan waktu | **Sangat sentral** — kilas balik, mengubah kejadian masa lalu, konsekuensi di masa kini. |
| 18 | Faksi | **Semua 7 faksi aktif**, masing-masing punya quest line. |
| 19 | Konten tambahan | **Item tier + skill baru** per kelas. |
| 20 | Ending | **4+ ending berbeda** (didesain 6 ending) tergantung keputusan besar. |
| 21 | Contoh JSON | **Contoh penuh** untuk semua struktur baru disertakan. |
| 22 | Cara kerja | **Bertahap per arc** dengan tes di tiap tahap. |
| 23 | Prioritas spec | **Seimbang semua** — arc & sistem dirinci merata. |

---

## 3. Premis Besar & Latar

### 3.1 Premis

Desa Ashen dibangun di atas **Jangkar Waktu** — artefak dari era yang terlupakan yang mampu *menulis ulang sejarah*. Kebakaran yang diramalkan Aria bukan sekadar bencana: itu adalah **Pembersihan** yang dikirim dari ibukota kerajaan Ashenfeld, dipicu oleh Gereja Api Suci yang menyebut Jangkar "Batu Iblis".

Kamu, sang **Pejalan Waktu**, terseret lintas waktu ke masa ini karena Jangkar terganggu. Selama Season 1 kamu akan:

1. Mengungkap keberadaan Jangkar dan sejarah aslinya lewat **kilas balik (echo)**.
2. Terjebak di tengah **intrik 7 faksi** yang saling berebut Jangkar.
3. Mengungkap dalang di balik kebakaran: **Kanselir Varek**, penasihat raja yang merekayasa segalanya demi menguasai Jangkar.
4. Pada klimaks, **memutuskan nasib Jangkar** → 6 ending berbeda.

### 3.2 Latar Dunia

- **Kerajaan Ashenfeld** — kerajaan luas dengan ibukota Ashenfeld; raja **Aldric** tua dan lemah, dikendalikan kanselir.
- **Desa Ashen** — desa kecil di tepi kerajaan, dulu pusat persembunyian Ancient Order yang menjaga Jangkar.
- **Reruntuhan Kuno** — sisa peradaban **Kaum Arah** (The Meridian), pembuat Jangkar; terpendam di bawah desa.
- **Periode waktu:** Season 1 berlangsung sekitar **3 minggu** dalam waktu game (dari pagi hari ke-1 hingga hari ke-21), memberi rasa urgensi karena api semakin dekat.

### 3.3 Kebenaran yang Terungkap Berjenjang

| Tahap | Fakta yang terungkap | Quest |
|-------|----------------------|-------|
| Arc 2 | Ada artefak kuno di bawah desa; kerajaan mencurigainya. | q003–q011 |
| Arc 3 | Gereja berniat membumihanguskan desa; kanselir mendalangi. | q012–q020 |
| Arc 4 | Jangkar adalah mesin penulis ulang sejarah; sejarah aslinya terungkap lewat echo. | q021–q029 |
| Arc 5 | Kanselir ingin memakai Jangkar untuk menulis ulang sejarah kerajaan; keputusan final. | q030–q045 |

---

## 4. Peta Faksi (Season 1)

Semua 7 faksi aktif. Posisi & tujuan masing-masing:

| Faksi | Tokoh kunci | Tujuan | Sikap ke Jangkar |
|-------|-------------|--------|------------------|
| **royal_army** | Raja Aldric (boneka), Kanselir Varek (dalang), Panglima Corvin | Menertibkan desa, menguasai Jangkar | Rebut untuk kekuasaan |
| **church** | Sister Iris (inkuisitor), Paus? (tak muncul) | Memurnikan "sihir terlarang" | Musnahkan (membakar desa) |
| **rebels** | Sera (pemimpin), Reed (mata-mata) | Menjatuhkan mahkota yang korup | Pakai untuk membebaskan rakyat |
| **merchant_guild** | Marcus | Meraup untung dari konflik | Jual ke penawar tertinggi |
| **scholar_society** | Profesor Kael | Memahami Jangkar | Pelajari & buka rahasianya |
| **ancient_order** | Aria, Lyra | Menjaga keseimbangan waktu | Segel & sembunyikan |
| **crime** | Kade (Serigala Malam) | Keuntungan dari kegelapan | Curi untuk dijual |

**Catatan desain:** reputasi pemain dihitung dari hadiah quest (`reputation`) dan pilihan dialog. Ambang reputasi menentukan quest eksklusif (lihat §12.4) dan ending (lihat §12.5).

---

## 5. Struktur Arc & Peta Quest

```
Arc 1 (sudah ada)      Arc 2            Arc 3             Arc 4              Arc 5
quest001 ─ quest002    quest003–011     quest012–020      quest021–029       quest030–045
   │                        │               │                 │                 │
PERCABANGAN            JANGKAR WAKTU    PERANG BAYANGAN   RERUNTUHAN WAKTU   SEJARAH BARU
WAKTU (banner)         (bos: Reiner)    (bos: Iris)       (bos: Penjaga)     (bos final + ending)
```

| Arc | Judul | Quest | Bos | Lokasi utama | Target level akhir |
|-----|-------|-------|-----|--------------|--------------------|
| 1 | Prolog (ada) | q001–q002 | — | Desa, Hutan | Lv 2–3 |
| 2 | Jangkar Waktu | q003–q011 | Kapten Reiner (Lv 10) | Perpustakaan, Reruntuhan, Hutan Dalam | Lv 8–10 |
| 3 | Perang Bayangan | q012–q020 | Sister Iris (Lv 15) | Kamp Pemberontak, Sarang Kriminal, Desa | Lv 15–17 |
| 4 | Reruntuhan Waktu | q021–q029 | Penjaga Waktu (Lv 22) | Dungeon Reruntuhan, Ibukota | Lv 23–25 |
| 5 | Sejarah Baru | q030–q045 | 6 bos final (Lv 28–30) | Ashen Terbakar, Benteng Kerajaan | Lv 30–35 |

---

## 6. Peta & Dunia Baru (10 peta)

| ID | Nama | Region | Threat | Muncul | Musuh khas |
|----|------|--------|--------|--------|-----------|
| `forest_deep` | Hutan Ashen Dalam | 3 | 8 | Arc 2–3 | direwolf, mercenary_soldier, forest_spider |
| `ruins_entrance` | Pintu Reruntuhan | 2 | 5 | Arc 2 | ruins_scavenger |
| `ancient_ruins` | Reruntuhan Kuno (L1) | 2 | 7 | Arc 2–4 | ruins_scavenger, ruin_warden |
| `ruins_depth` | Kedalaman Reruntuhan (L2) | 2 | 10 | Arc 4 | time_wraith, ruin_warden |
| `anchor_chamber` | Ruang Jangkar | 2 | 12 | Arc 4–5 | time_wraith, anchor_guard |
| `rebel_camp` | Kamp Pemberontak | 3 | 6 | Arc 3 | rebel_soldier |
| `crime_den` | Sarang Serigala Malam | 1 | 7 | Arc 3 | thug, guild_guard |
| `capital` | Ibukota Ashenfeld | 5 | 4 | Arc 4 | city_guard |
| `capital_keep` | Benteng Kerajaan | 5 | 11 | Arc 5 | royal_knight, elite_guard |
| `burning_village` | Ashen yang Terbakar | 1 | 9 | Arc 5 | inquisitor_soldier, burnt_husk |

**Catatan:** `burning_village` adalah versi transformasi `village` saat Arc 5 (desa terbakar). `ruins_entrance` → `ancient_ruins` → `ruins_depth` → `anchor_chamber` membentuk dungeon berlapis 4 lantai.

**Eksistensi peta dikendalikan flag:** peta baru hanya muncul di menu `go` setelah flag `map_<id>_unlocked` diset oleh event/quest (mis. `map_forest_deep_unlocked`). Ini mencegah pemain lompat ke konten arc berikutnya.

---

## 7. NPC Baru (±22)

### 7.1 Daftar NPC

| ID | Nama | Lokasi | Faksi | Peran | Shop |
|----|------|--------|-------|-------|------|
| `finn` | Finn | village, lalu capital | royal_army | Mata-mata kerajaan yang menyamar | — |
| `lyra` | Lyra | village (perpustakaan) | ancient_order | Sejarawan, rekan Aria | — |
| `marcus` | Marcus | village | merchant_guild | Pedagang keliling; **toko pertama** | ✅ |
| `sera` | Sera | rebel_camp | rebels | Pemimpin pemberontak | — |
| `kade` | Kade | crime_den | crime | Bos Serigala Malam | — |
| `sister_iris` | Sister Iris | village, lalu capital | church | Inkuisitor; bos Arc 3 | — |
| `kael` | Prof. Kael | village (tenda riset) | scholar_society | Akademisi; **toko riset** | ✅ |
| `king_aldric` | Raja Aldric | capital_keep | royal_army | Raja boneka | — |
| `chancellor_varek` | Kanselir Varek | capital_keep | royal_army | Dalang utama (antagonis rahasia) | — |
| `general_corvin` | Panglima Corvin | capital_keep | royal_army | Panglima; bos final (ending B) | — |
| `anchor_avatar` | Suara Jangkar | anchor_chamber | — | Wujud kesadaran Jangkar Waktu | — |
| `ancient_spirit` | Roh Penjaga | ancient_ruins | ancient_order | Penjaga reruntuhan; teka-teki | — |
| `helen` | Helen | village | — | Pemilik penginapan; **toko ramuan** | ✅ |
| `ben` | Ben | village | — | Pandai besi; **toko senjata** | ✅ |
| `mother_maria` | Ibu Maria | village | church | Bidan/penyembuh (netral) | — |
| `tom` | Tom | village | — | Petani; korban pertama kebakaran (escort) | — |
| `nil` | Nil | village | — | Anak desa; pengingat harapan | — |
| `guard_erik` | Erik | village | royal_army | Penjaga desa (dulu) | — |
| `scout_reed` | Reed | forest_deep, rebel_camp | rebels | Mata-mata pemberontak | — |
| `innkeeper_mira` | Mira | capital | — | Penginapan ibukota; **toko** | ✅ |
| `smith_brock` | Brock | capital | — | Pandai besi ibukota; **toko tier tinggi** | ✅ |
| `alchemist_yara` | Yara | capital | scholar_society | Alkemis; **toko ramuan tier tinggi** | ✅ |

### 7.2 Struktur NPC baru (penambahan field)

```json
{
  "id": "marcus",
  "name": "Marcus",
  "location": "village",
  "role": "merchant",
  "relationship": {"trust": 0, "affinity": 0, "knowledge": 0},
  "faction": "merchant_guild",
  "dialogs": ["dialog_marcus_main"],
  "shop": {
    "buy": [
      {"item": "potion", "price": 25},
      {"item": "steel_sword", "price": 120},
      {"item": "chain_armor", "price": 150}
    ],
    "sell_multiplier": 0.5
  }
}
```

- `shop.buy`: daftar item yang dijual; harga tetap (bisa diubah quest/faksi).
- `shop.sell_multiplier`: persentase harga jual item milik pemain.
- Toko dibuka lewat opsi **"Berbelanja"** di dialog (lihat §12.2).

---

## 8. Musuh & Bos Baru

### 8.1 Musuh reguler baru (±20)

| ID | Nama | Lv | Perilaku | Muncul di | Catatan |
|----|------|----|----------|-----------|---------|
| `direwolf` | Serigala Guruh | 6 | aggressive | forest_deep | varian kuat wild_wolf |
| `forest_spider` | Laba-laba Hutan | 5 | defensive | forest_deep | bisa poison |
| `mercenary_soldier` | Tentara Bayaran | 7 | aggressive | forest_deep | utusan kerajaan |
| `royal_scout` | Pengintai Kerajaan | 6 | coward | forest_deep, village | kabur saat terluka |
| `ruins_scavenger` | Pemulung Reruntuhan | 5 | aggressive | ruins_entrance, ancient_ruins | drop rune_key |
| `ruin_warden` | Penjaga Reruntuhan | 9 | defensive | ancient_ruins, ruins_depth | konstruk kuno |
| `time_wraith` | Hantu Waktu | 12 | mage | ruins_depth, anchor_chamber | serangan sihir |
| `anchor_guard` | Pengawal Jangkar | 14 | defensive | anchor_chamber | konstruk penjaga |
| `rebel_soldier` | Prajurit Pemberontak | 8 | aggressive | rebel_camp | netral bila reputasi rebels tinggi |
| `thug` | Preman | 7 | aggressive | crime_den | |
| `guild_guard` | Pengawal Gilda | 10 | defensive | crime_den, village | |
| `inquisitor_soldier` | Tentara Inkuisisi | 13 | aggressive | burning_village, village | pasukan gereja |
| `burnt_husk` | Arang Hidup | 11 | mage | burning_village | korban sihir api |
| `city_guard` | Penjaga Kota | 9 | defensive | capital | netral |
| `royal_knight` | Ksatria Kerajaan | 16 | aggressive | capital_keep | |
| `elite_guard` | Pengawal Elit | 18 | defensive | capital_keep | |
| `cult_acolyte` | Acolyte Kultus | 15 | mage | capital | pengikut kanselir |
| `crown_assassin` | Pembunuh Mahkota | 17 | aggressive | capital, capital_keep | |
| `shadow_stalker` | Penghisap Bayangan | 13 | coward | crime_den | |
| `rebel_elite` | Elit Pemberontak | 15 | aggressive | rebel_camp | |

### 8.2 Bos (3 bos arc + 6 bos final)

| ID | Nama | Lv | Arc | Perilaku | HP | Lore singkat |
|----|------|----|-----|----------|-----|-------------|
| `captain_reiner` | Kapten Reiner | 10 | 2 | aggressive | ~90 | Kapten tentara bayaran yang dikirim kerajaan; percaya desa menyembunyikan harta |
| `sister_iris` | Sister Iris | 15 | 3 | mage | ~160 | Inkuisitor Api Suci; mengungkap kanselir sebagai dalang |
| `time_guardian` | Penjaga Waktu | 22 | 4 | defensive | ~300 | Konstruk kuno penjaga ruang Jangkar; bicara setelah kalah |
| `anchor_shade` | Bayangan Jangkar | 28 | 5 (E) | mage | ~420 | Jelmaan marah Jangkar saat dihancurkan |
| `general_corvin` | Panglima Corvin | 29 | 5 (B) | aggressive | ~450 | Panglima kerajaan saat pemberontak menyerbu |
| `chancellor_varek` | Kanselir Varek | 30 | 5 (C) | mage | ~480 | Wujud final kanselir memakai kekuatan Jangkar |
| `time_lord_wraith` | Tuan Hantu Waktu | 29 | 5 (D) | mage | ~460 | Jelmaan waktu yang dikendalikan akademi |
| `high_inquisitor` | Inkuisitor Agung | 28 | 5 (A) | aggressive | ~430 | Pemimpin pasukan gereja |
| `ancient_tyrant` | Tiran Kuno | 30 | 5 (F) | aggressive | ~500 | Penguasa era Kaum Arah; bos ending paradoks |

**Aturan bos:**
- Bos punya `tags: ["boss"]` dan tidak bisa `escape` (kabur dari bos selalu gagal).
- Bos memberi hadiah istimewa: XP besar + item epic + reputasi faksi besar.
- **Multi-phase didefer penuh** (keputusan terkunci §19): bos Season 1 single-phase; fase kedua (HP < 50% → skill baru) menjadi enhancement terpisah di luar scope Season 1.

---

## 9. Item Baru (tier) & Skill Baru

### 9.1 Tier perlengkapan

| Tier | Nama | Contoh | Sumber |
|------|------|--------|--------|
| Umum | (ada) | iron_sword, leather_armor, wooden_helmet | loot & toko awal |
| Bagus (fine) | `steel_sword` (+12 atk), `chain_armor` (+7 def), `iron_helmet` (+5 def) | toko Ben, loot bos Arc 2 |
| Langka (rare) | `rune_blade` (+18 atk, +3 int), `rune_plate` (+11 def), `rune_crown` (+6 def, +2 int) | loot bos Arc 3–4, toko Brock |
| Epik (epic) | `time_edged_blade` (+25 atk, +2 agi), `guardian_plate` (+15 def), `anchor_crown` (+8 def, +4 int) | bos final, quest ending |

### 9.2 Konsumabel baru

| ID | Nama | Efek |
|----|------|------|
| `elixir` | Elixir | Pulihkan HP penuh |
| `time_tincture` | Ramuan Waktu | Pulihkan MP penuh |
| `smoke_bomb` | Bom Asap | Kabur dari pertarungan pasti berhasil (satu kali pakai) |

### 9.3 Item quest (non-konsumabel)

`rune_key` (kunci gerbang reruntuhan), `old_scroll` (gulungan ukiran), `evidence_letter` (surat bukti kanselir), `seal_of_blood`, `seal_of_wisdom`, `seal_of_time` (segel dungeon), `anchor_shard` (pecahan Jangkar).

### 9.4 Skill baru per kelas (1–2 per kelas)

Struktur skill mengikuti `data/skills/*.json` yang ada (`type`, `cost`, `power`, `effects`).

| Kelas | Skill | Tipe | Cost | Power | Efek |
|-------|-------|------|------|-------|------|
| Warrior | `shield_bash` | fisik | 6 | 10 | `stun` 1 giliran (kontrol) |
| Warrior | `war_cry` | fisik | 8 | 0 | buff attack 2 giliran (butuh engine self-buff) |
| Mage | `frost_bolt` | sihir | 7 | 10 | `slow` (agility turun) 2 giliran |
| Mage | `arcane_barrier` | sihir | 6 | 0 | kurangi damage 1 giliran (butuh engine self-buff) |
| Assassin | `poison_blade` | fisik | 6 | 8 | `poison` 3 giliran |
| Assassin | `shadow_step` | fisik | 5 | 6 | dodge tinggi (butuh engine self-buff) |
| Ranger | `multishot` | fisik | 8 | 7×2 | serang dua kali |
| Ranger | `snare` | fisik | 6 | 5 | `sleep`/`blind` 1 giliran |
| Scholar | `lore_strike` | sihir | 7 | 11 | damage dari intelligence |
| Scholar | `time_study` | sihir | 4 | 0 | buff XP sementara (butuh engine self-buff) |

**Keputusan desain (terkunci §19):** skill damage + status (`shield_bash`, `frost_bolt`, `poison_blade`, `multishot`, `snare`, `lore_strike`) mengikuti struktur yang sudah didukung engine → Phase 1. Skill self-buff (`war_cry`, `arcane_barrier`, `shadow_step`, `time_study`) **masuk Phase 0**: combat_engine diperluas untuk aksi target-self (buff attack/defense/dodge/XP sementara) beserta unit test-nya.

---

## 10. Rincian Quest per Arc

### 10.0 Format quest (mengikuti engine yang ada)

```json
{
  "id": "quest00X",
  "title": "...",
  "type": "main",
  "description": "...",
  "objectives": ["..."],
  "requirements": [ {"kind": "talk|enemy|map|flag|collect|kill_count|escort", "target": "...", "amount": N} ],
  "rewards": {"xp": N, "gold": N, "reputation": {"faksi": N}},
  "flags_on_complete": ["..."],
  "next": "quest00Y"
}
```

`next` menautkan quest otomatis; event/flag dipakai untuk quest percabangan dan gate (lihat §12).

**Standar panjang dialog (keputusan terkunci §19):** deskriptif, gaya novel ringan — tiap beat 2–5 baris; quest kunci (q007, q015, q036) boleh lebih panjang.

---

### 10.1 Arc 2 — "Jangkar Waktu" (quest003–quest011)

**Plot:** Setelah PERCABANGAN WAKTU, Aria mengungkap ruang rahasia perpustakaan. Mata-mata kerajaan beroperasi di sekitar desa. Pemain memilih aliansi faksi pertama dan memasuki reruntuhan kuno.

| Quest | Judul | Pemberi/Lokasi | Inti |
|-------|-------|----------------|------|
| q003 | **Gema di Bawah Perpustakaan** | Aria, village | Ruang rahasia perpustakaan diserbu mata-mata kerajaan |
| q004 | **Batu yang Berdenyut** | Lyra, village | Menemukan ruang Jangkar di bawah desa |
| q005 | **Utusan dari Ibukota** | Finn, village | Mata-mata Finn terungkap; pilihan tangkap/lepas |
| q006 | **Darah di Hutan Dalam** | Guard Erik, village | Selidiki jejak tentara bayaran di hutan dalam |
| q007 | **Pilihan Aliansi** | bebas, village | Pilih faksi kerja sama pertama (percabangan) |
| q008 | **Punggung Pisau** | Kade, crime_den | Info rahasia dari gilda kriminal (trade-off reputasi) |
| q009 | **Dinding Reruntuhan** | Lyra, ruins_entrance | Kumpulkan rune_key untuk membuka gerbang |
| q010 | **Reruntuhan Berbisik** | ancient_spirit, ancient_ruins | Echo pertama; kalahkan 3 pemulung reruntuhan |
| q011 | **Kapten Bayaran** (BOS) | forest_deep | Hadapi Kapten Reiner |

#### quest003 — Gema di Bawah Perpustakaan
- **Trigger:** event `event_arc2_gate` (lihat §13.3) setelah quest002_done.
- **Alur:** Aria membawamu ke ruang bawah perpustakaan. Dua mata-mata kerajaan menyerang. Setelah pertarungan, Aria memperlihatkan simbol Kaum Arah di lantai.
- **Requirements:** `talk old_man` (Aria), lalu `enemy royal_scout` ×1.
- **Hadiah:** 60 XP, 20 emas, +5 reputasi ancient_order. **Flags:** `arc2_started`, `map_anchor_vault_unlocked`.
- **Next:** quest004.
- **Dialog inti (Aria):** "Desa ini bukan desa biasa. Kami berdiri di atas sesuatu yang jauh lebih tua... sesuatu yang mereka sebut Jangkar Waktu."
- **Pilihan:** jawab 1 "Jelaskan." / 2 "Kamu yakin?" / 3 (diam) — kosmetik, semua lanjut.

#### quest004 — Batu yang Berdenyut
- **Alur:** Turun ke ruang bawah tanah (map `anchor_vault` dibuka). Di sana: dinding batu yang berdenyut seperti jantung.
- **Requirements:** `map anchor_vault`.
- **Hadiah:** 50 XP, 15 emas. **Flags:** `found_anchor_vault`.
- **Next:** quest005.
- **Dialog inti (Lyra):** "Ini bukan batu biasa. Ia bernapas. Dan ia mengenalimu — Pejalan Waktu."

#### quest005 — Utusan dari Ibukota
- **Alur:** Finn (pengembara yang tampak ramah) tertangkap basah mengirim burung surat ke ibukota.
- **Requirements:** `talk finn` + `flag finn_caught` (diset pilihan dialog).
- **Hadiah:** 60 XP, 10 emas. **Flags:** `met_finn`.
- **Next:** quest006.
- **Pilihan penting (membentuk reputasi):**
  1. **Tangkap Finn** → +8 reputasi ancient_order, set `finn_arrested`; dialog Finn berhenti (ia dirantai, bisa diinterogasi lagi di quest007).
  2. **Lepaskan Finn** → +8 reputasi royal_army (ia berhutang budi), set `finn_freed`; Finn jadi sumber info kerajaan di Arc 4 (quest027).
- **Catatan desain:** kedua jalur tetap membuka quest006–011; perbedaannya terasa di Arc 4 (jalur `finn_freed` mendapat bantuan Finn; jalur `finn_arrested` mendapat informasi dari Lyra).

#### quest006 — Darah di Hutan Dalam
- **Alur:** Erik (penjaga desa) melaporkan jejak darah & kamp tentara bayaran di hutan dalam. Periksa kamp; kalahkan tentara bayaran.
- **Requirements:** `map forest_deep` + `kill_count mercenary_soldier` ×2.
- **Hadiah:** 80 XP, 25 emas. **Flags:** `forest_deep_searched`.
- **Next:** quest007.
- **Lore beat:** menemukan panji kerajaan bercap elang emas — bukti kerajaan mengirim pasukan diam-diam.

#### quest007 — Pilihan Aliansi (percabangan faksi pertama)
- **Alur:** Kamu tahu konflik akan memanas. Aria menyarankan mencari sekutu. Kamu bisa memilih **satu** dari 4 faksi untuk diajak kerja sama dulu:
  1. **ancient_order** (bicara Lyra) → membuka wawasan sejarah; +10 reputasi; quest line "penjaga".
  2. **rebels** (temui Sera di forest_deep → kamp dibuka) → +10 reputasi rebels.
  3. **merchant_guild** (bicara Marcus) → +10 reputasi merchant_guild; diskon toko.
  4. **scholar_society** (bicara Kael) → +10 reputasi scholar_society.
- **Requirements:** `talk <tokoh sesuai pilihan>` — event `event_alias_choice` membaca pilihan dan set flag `aligned_<faksi>`, lalu menutup opsi lain (pilihan lain tidak lagi muncul di dialog).
- **Hadiah:** 70 XP, 20 emas, +10 reputasi faksi pilihan.
- **Next:** quest008.
- **Konsekuensi jauh:** reputasi faksi ini memberi bonus dialog & quest eksklusif di Arc 3–5, dan memengaruhi ketersediaan ending (§12.5).

#### quest008 — Punggung Pisau
- **Alur:** Kade (bos Serigala Malam) tahu siapa yang membayar tentara bayaran. Ia menawarkan info itu — dengan imbalan reputasi.
- **Requirements:** `talk kade` (crime_den dibuka via flag dari dialog Aria/Lyra) + `flag crime_deal_done`.
- **Hadiah:** 80 XP, 30 emas. **Trade-off:** pilihan dialog:
  1. Terima tawarannya → +10 reputasi crime, tapi −5 reputasi royal_army (mereka tahu kau berurusan dengan penjahat).
  2. Tolak & serang utusannya → pertarungan `thug` ×2, +5 reputasi ancient_order, tanpa info.
  3. Nego harga → skill dialog: hanya bisa jika reputasi merchant_guild ≥ 10 (diskon 30 emas & tanpa reputasi minus).
- **Hasil (semua jalur):** petunjuk bahwa pembayar tentara bayaran adalah kanselir kerajaan (nama Varek pertama disebut).
- **Next:** quest009.

#### quest009 — Dinding Reruntuhan
- **Alur:** Lyra menemukan gerbang reruntuhan (ruins_entrance). Gerbang terkunci — butuh kunci batu berukir (rune_key) yang dipegang pemulung reruntuhan.
- **Requirements:** `map ruins_entrance` + `collect rune_key` ×1 (drop dari `ruins_scavenger`, chance 40%).
- **Hadiah:** 70 XP, 20 emas. **Flags:** `map_ancient_ruins_unlocked`.
- **Next:** quest010.
- **Catatan:** contoh implementasi `collect` di §13.1.

#### quest010 — Reruntuhan Berbisik
- **Alur:** Masuk Reruntuhan Kuno. Roh Penjaga (ancient_spirit) muncul — ia menguji kesungguhanmu dan memainkan **echo pertama** (kilas balik era Kaum Arah). Kalahkan 3 pemulung yang menyerbu saat ritual echo.
- **Requirements:** `map ancient_ruins` + `kill_count ruins_scavenger` ×3 + `talk ancient_spirit`.
- **Hadiah:** 90 XP, 25 emas, kenangan **memory003 "Asal Jangkar"** (via event), +5 reputasi ancient_order.
- **Flags:** `echo_1_collected`.
- **Next:** quest011.
- **Echo 1 (isi):** Kilas balik ke era Kaum Arah saat Jangkar pertama ditempa — lima penjaga bersumpah menjaga rahasianya. Pemain melihat sosok yang *mengenalnya*.

#### quest011 — Kapten Bayaran (BOS Arc 2)
- **Alur:** Pasukan bayaran mengepung tepi hutan menuju desa. Kapten Reiner memimpin; ia mengaku "menertibkan" atas perintah mahkota.
- **Requirements:** `enemy captain_reiner` (pertarungan bos, tidak bisa kabur).
- **Hadiah:** 150 XP, 60 emas, item `steel_sword` atau `chain_armor` (pilihan), +10 reputasi faksi yang kamu pilih di q007.
- **Flags:** `boss_arc2_defeated`, `reiner_info` (ia mengaku diperintah kanselir sebelum mati).
- **Next:** quest012.
- **Scene akhir arc:** banner "ARC 2 SELESAI — JANGKAR WAKTU" + kenangan **memory004 "Nama Varek"**.

---

### 10.2 Arc 3 — "Perang Bayangan" (quest012–quest020)

**Plot:** Gereja mengirim Sister Iris dan pasukan inkuisisi. Kebakaran pertama terjadi. Pemberontak, gilda kriminal, dan akademisi bergerak. Kanselir Varek mulai terlihat sebagai dalang.

| Quest | Judul | Pemberi/Lokasi | Inti |
|-------|-------|----------------|------|
| q012 | **Api di Tepi Hutan** | Tom, village | Kebakaran pertama di rumah pemburu; bukti inkuisisi |
| q013 | **Gereja yang Menghakimi** | Sister Iris, village | Ketegangan dengan inkuisitor; pilihan sikap |
| q014 | **Sarang Serigala Malam** | Kade, crime_den | Infiltrasi sarang; cari arsip pembayaran |
| q015 | **Harga Sebuah Nama** | bebas | Keputusan besar: bocorkan lokasi Jangkar / bungkam |
| q016 | **Kamp Pemberontak** | Sera, rebel_camp | Bantu pemberontak; atau tolak |
| q017 | **Sketsa dari Akademi** | Kael, village | Decode ukiran reruntuhan; kumpulkan gulungan |
| q018 | **Pengkhianatan di Pasar** | Marcus, village | Gilda dagang bocorkan info; selamatkan pedagang |
| q019 | **Malam Serigala** | Erik, village | Serangan malam inkuisisi; pertahankan desa |
| q020 | **Api Hakim** (BOS) | Sister Iris, village | Duel dengan inkuisitor |

#### quest012 — Api di Tepi Hutan
- **Alur:** Rumah Tom (petani) terbakar tengah malam. Tom selamat; istrinya hilang. Jejak menunjukkan minyak api suci — milik gereja.
- **Requirements:** `talk tom` + `map forest_deep` (periksa lokasi).
- **Hadiah:** 80 XP, 20 emas. **Flags:** `first_fire`, `villager_missing`.
- **Next:** quest013.
- **Pilihan:** temani Tom ke hutan (escort mini: `escort tom` forest_deep→village) atau biarkan ia sendiri (kehilangan hadiah kecil). Opsi pertama memberi +5 reputasi village/rakyat.

#### quest013 — Gereja yang Menghakimi
- **Alur:** Sister Iris tiba dengan 12 tentara inkuisisi. Ia menuduh desa menyembunyikan "Batu Iblis" dan memberi ultimatum 5 hari.
- **Requirements:** `talk sister_iris` + `flag ultimatum_received`.
- **Hadiah:** 80 XP. **Flags:** `ultimatum_5_days` (memulai hitung mundur 5 hari game — counter `days_remaining` tampil di HUD sebagai "Api dalam N hari").
- **Next:** quest014.
- **Pilihan penting (reputasi):**
  1. Menantang Iris → +5 rebels, −10 church; tegang.
  2. Menenangkan → +5 church, −3 rebels.
  3. Diam → netral.
- **Catatan desain (terkunci §19):** hitung mundur **5 hari** memakai `rest` (hari game); bila habis sebelum q032 → quest Arc 3 tertentu gagal otomatis (hadiah hilang), alur utama tetap jalan — lihat §12.3.

#### quest014 — Sarang Serigala Malam
- **Alur:** Kade punya arsip pembayaran gereja—siapa menyuap siapa. Infiltrasi sarang (crime_den) secara diam-diam atau lewat pintu depan.
- **Requirements:** `map crime_den` + `talk kade` (atau `enemy thug` ×3 bila memilih jalur paksa).
- **Hadiah:** 90 XP, 35 emas, item `evidence_letter` (surat perintah pembakaran dari ibukota).
- **Flags:** `crime_archive`, `have_evidence_letter`.
- **Next:** quest015.

#### quest015 — Harga Sebuah Nama (keputusan besar #1)
- **Alur:** Salah satu faksi memintamu mengungkap lokasi pasti Jangkar. Pilihan ini mengubah siapa yang datang di Arc 5.
- **Options (3 penyelesaian):**
  1. **Bocorkan ke faksi yang kau percaya** (sesuai aliansi q007) → quest diselesaikan lebih cepat; +15 reputasi faksi itu; faksi itu jadi **sekutu kuat** di Arc 5.
  2. **Rahasiakan** → quest lain (jaga rahasia, lawan interogator `inquisitor_soldier` ×1); +10 reputasi ancient_order; aman tapi lambat.
  3. **Jual info** (hanya jika reputasi merchant_guild ≥ 20) → +100 emas, +10 merchant_guild, tapi −10 ancient_order & gereja mengetahuinya lebih cepat.
- **Hadiah:** 100 XP + varian.
- **Next:** quest016.

#### quest016 — Kamp Pemberontak
- **Alur:** Sera mengundangmu ke kamp. Ia ingin memakai Jangkar untuk menggulingkan raja. Bantu latihan perang atau tolak.
- **Requirements:** `map rebel_camp` + `talk sera` + (opsional) `kill_count rebel_soldier` ×1 (duel latihan).
- **Hadiah:** 100 XP, 30 emas; +10 rebels bila membantu.
- **Next:** quest017.
- **Dialog inti (Sera):** "Mereka membakar rumah rakyat demi batu. Kalau batu itu bisa menulis ulang sejarah... biarkan rakyat yang memegang pena."

#### quest017 — Sketsa dari Akademi
- **Alur:** Prof. Kael berhasil mengartikan sebagian ukiran reruntuhan. Butuh gulungan kuno (old_scroll) yang tersebar di reruntuhan & hutan.
- **Requirements:** `collect old_scroll` ×2 (drop dari `ruins_scavenger` 25%, `time_wraith` 50%) + `talk kael`.
- **Hadiah:** 100 XP, 20 emas, +10 scholar_society. **Flags:** `ancient_script_decoded` (membuka pilihan dialog baru di arc 4).
- **Next:** quest018.

#### quest018 — Pengkhianatan di Pasar
- **Alur:** Marcus ketahuan menjual info lokasi Jangkar ke agen kerajaan. Selamatkan dia dari pengawal gilda yang berbalik.
- **Requirements:** `talk marcus` + `enemy guild_guard` ×1.
- **Hadiah:** 110 XP, 40 emas, +5 merchant_guild (Marcus berhutang budi) ATAU +5 ancient_order (bila kau laporkan ke Aria).
- **Next:** quest019.

#### quest019 — Malam Serigala
- **Alur:** Inkuisisi menyerang desa di malam hari. Pertahankan desa: kalahkan gelombang tentara inkuisisi.
- **Requirements:** `kill_count inquisitor_soldier` ×3.
- **Hadiah:** 120 XP, 30 emas, +5 reputasi village (rakyat). **Flags:** `village_defended`.
- **Next:** quest020.
- **Lore beat:** di tengah serangan, seorang tentara sekarat menyebut "kanselir" — memperkuat bukti Varek.

#### quest020 — Api Hakim (BOS Arc 3)
- **Alur:** Sister Iris menuntut Jangkar. Duel puncak — Iris mengaku hanya alat; nama **Varek** disebut sebagai orang yang memerintahkan pembakaran.
- **Requirements:** `enemy sister_iris`.
- **Hadiah:** 200 XP, 70 emas, `rune_blade` atau `rune_plate` (pilihan), +10 reputasi sesuai pilihan q015.
- **Flags:** `boss_arc3_defeated`, `iris_revealed`.
- **Next:** quest021.
- **Scene akhir arc:** banner "ARC 3 SELESAI — PERANG BAYANGAN" + kenangan **memory005 "Kanselir"**.

---

### 10.3 Arc 4 — "Reruntuhan Waktu" (quest021–quest029)

**Plot:** Dungeon reruntuhan terbuka penuh. Tiga segel harus dipatahkan. Echo besar mengungkap sejarah asli Jangkar. Perjalanan ke ibukota mengungkap pengkhianatan kanselir.

| Quest | Judul | Pemberi/Lokasi | Inti |
|-------|-------|----------------|------|
| q021 | **Gerbang yang Terkunci** | Lyra, ancient_ruins | Buka gerbang dalam (ruins_depth) |
| q022 | **Echo: Hari Pembuat** | ancient_spirit, ancient_ruins | Kilas balik besar era penciptaan |
| q023 | **Segel Darah** | ancient_spirit | Kalahkan penjaga reruntuhan |
| q024 | **Segel Kebijaksanaan** | ancient_spirit | Teka-teki via dialog dengan roh kuno |
| q025 | **Segel Waktu** | anchor_avatar | Ujian menyelaraskan memori |
| q026 | **Koridor yang Berdenyut** | —, ruins_depth | Jebakan & hantu waktu |
| q027 | **Raja yang Terlupakan** | capital | Hadap raja Aldric; pilihan sikap |
| q028 | **Pendengaran Rahasia** | Finn/Lyra, capital | Bukti pengkhianatan Varek |
| q029 | **Penjaga Waktu** (BOS) | anchor_chamber | Konstruk penjaga; Jangkar bicara |

#### quest021 — Gerbang yang Terkunci
- **Alur:** Di ujung reruntuhan L1 ada gerbang besar bertulis tiga segel. Setiap segel butuh ujian.
- **Requirements:** `map ruins_depth` (dibuka event setelah q020).
- **Hadiah:** 100 XP, 20 emas.
- **Next:** quest022.

#### quest022 — Echo: Hari Pembuat
- **Alur:** Roh Penjaga memainkan **echo terbesar**: hari Jangkar ditempa. Kaum Arah menciptakan mesin untuk *memperbaiki* sejarah yang hancur oleh perang — bukan untuk menguasai. Pemain melihat dirinya di masa itu (misteri identitas).
- **Requirements:** `talk ancient_spirit` + `flag echo_2_collected` (diset event saat scene diputar).
- **Hadiah:** 110 XP, kenangan **memory006 "Hari Pembuat"**.
- **Next:** quest023.
- **Catatan:** scene ini memakai mekanik echo (§12.3). Wajib dikumpulkan untuk ending rahasia (F).

#### quest023 — Segel Darah
- **Alur:** Segel pertama dibuka dengan kekuatan: kalahkan `ruin_warden` yang menjaga altar.
- **Requirements:** `enemy ruin_warden` + `kill_count ruin_warden` ×1.
- **Hadiah:** 120 XP, 25 emas, item `seal_of_blood`.
- **Next:** quest024.

#### quest024 — Segel Kebijaksanaan
- **Alur:** Segel kedua dibuka dengan akal: teka-teki pilihan ganda dari Roh Penjaga (3 soal sejarah yang jawabannya ada di memori/echo). Salah menjawab → pertarungan `ruin_warden` ×1.
- **Requirements:** `talk ancient_spirit` + `flag seal_of_wisdom_ok` (diset saat jawaban benar).
- **Hadiah:** 120 XP, item `seal_of_wisdom`.
- **Next:** quest025.

#### quest025 — Segel Waktu
- **Alur:** Segel ketiga adalah ujian waktu: pilih **2 dari 3 memori** untuk diselaraskan (memory001/002/003). Setiap pilihan mengubah hadiah & satu flag kecil (kosmetik/ending).
- **Requirements:** `flag seal_of_time_ok`.
- **Hadiah:** 120 XP, item `seal_of_time`.
- **Next:** quest026.

#### quest026 — Koridor yang Berdenyut
- **Alur:** Jalan menuju ruang Jangkar dipenuhi hantu waktu & jebakan.
- **Requirements:** `map anchor_chamber` + `kill_count time_wraith` ×2.
- **Hadiah:** 130 XP, 30 emas. **Flags:** `map_anchor_chamber_unlocked`.
- **Next:** quest027.

#### quest027 — Raja yang Terlupakan
- **Alur:** Perjalanan ke ibukota (capital dibuka). Hadap raja Aldric — ia tampak bingung dan dimanipulasi. Pilihan menentukan ending C tersedia atau tidak:
  1. **Beri tahu raja tentang Varek** (butuh `have_evidence_letter`) → raja sadar; ending C terbuka; +15 royal_army.
  2. **Rahasiakan** → Varek tak terungkap lebih awal; jalur ending B/D lebih mudah.
  3. *(Khusus `finn_freed`)* Finn membantumu bertemu raja secara rahasia → bonus info +5 royal_army.
- **Requirements:** `map capital` + `talk king_aldric`.
- **Hadiah:** 140 XP, 40 emas.
- **Next:** quest028.

#### quest028 — Pendengaran Rahasia
- **Alur:** Kumpulkan bukti terakhir (evidence_letter + kesaksian Finn/Lyra) bahwa Varek yang memerintahkan pembakaran & penculikan.
- **Requirements:** `collect evidence_letter` ×1 (jika belum dari q014) + `flag conspiracy_proven` (diset dialog).
- **Hadiah:** 140 XP, 20 emas.
- **Next:** quest029.

#### quest029 — Penjaga Waktu (BOS Arc 4)
- **Alur:** Di ruang Jangkar (anchor_chamber), konstruk Penjaga Waktu menyerang. Setelah kalah, Jangkar **bicara** — avatar muncul, memanggilmu "Pejalan Waktu", dan menjelaskan kebenaran penuh.
- **Requirements:** `enemy time_guardian`.
- **Hadiah:** 280 XP, 90 emas, `rune_crown` atau `time_tincture` ×2, +10 ancient_order.
- **Flags:** `boss_arc4_defeated`, `met_anchor_avatar`.
- **Next:** quest030.
- **Scene akhir arc:** banner "ARC 4 SELESAI — RERUNTUHAN WAKTU" + kenangan **memory007 "Suara Jangkar"**.

---

### 10.4 Arc 5 — "Sejarah Baru" (quest030–quest045)

**Plot:** Ultimatum 5 hari habis. Inkuisisi mengepung; desa terbakar. Pemain menyatukan sekutu, mengungkap Varek, dan membuat **keputusan terakhir: nasib Jangkar** → salah satu dari 6 ending, masing-masing dengan rangkaian quest sendiri.

**Aturan Arc 5 (terkunci §19):** 1 NPC gugur permanen per jalur ending (bukan sekutu utama; tokohnya ditentukan pilihan & reputasi, berpengaruh di teks epilog q044) — tanpa mengunci gameplay.

| Quest | Judul | Inti |
|-------|-------|------|
| q030 | **Suara Jangkar** | Avatar menjelaskan kebenaran; pilihan sikap awal |
| q031 | **Persiapan Badai** | Kumpulkan sekutu; reputasi menentukan siapa datang |
| q032 | **Pengepungan Gereja** | Inkuisisi mengepung; pertahankan |
| q033 | **Kanselir Varek** | Kebenaran penuh: Varek merekayasa segalanya |
| q034 | **Api Dimulai** | Desa terbakar; evakuasi warga (escort) |
| q035 | **Menembus Cincin Api** | Terobos blokade menuju ibukota |
| q036 | **Pilihan Terakhir: Nasib Jangkar** | Keputusan menentukan ending (A–F) |
| q037–q043 | **Quest jalur ending** | Rangkaian quest per ending (mutually exclusive) |
| q044 | **Epilog: Pagi di Ashen** | Epilog sesuai ending |
| q045 | **Benih Musim Kedua** | Teaser Season 2 |

#### quest030 — Suara Jangkar
- **Alur:** Avatar Jangkar (anchor_avatar) menjelaskan: ia diciptakan untuk memperbaiki sejarah, dan ditariknya kau ke masa ini bukan kebetulan — darahmu terhubung dengan Kaum Arah.
- **Requirements:** `talk anchor_avatar`.
- **Hadiah:** 130 XP, kenangan **memory008 "Identitas"**.
- **Next:** quest031.
- **Pilihan (kosmetik awal, memengaruhi satu dialog akhir):** percaya / ragu / marah.

#### quest031 — Persiapan Badai
- **Alur:** Kumpulkan sekutu untuk menghadapi pengepungan. **Siapa yang datang tergantung reputasi:**
  - ancient_order ≥ 20 → Lyra & 2 penjaga.
  - rebels ≥ 15 → Sera & regu pemberontak.
  - merchant_guild ≥ 15 → Marcus pasok logistik (diskon toko akhir).
  - scholar_society ≥ 15 → Kael & alat riset.
  - royal_army ≥ 15 (via finn/raja) → pasukan netral dari istana.
  - crime ≥ 15 → Kade kirim pembunuh bayaran.
  - village (rakyat) ≥ 20 → warga ikut bertahan.
- **Requirements:** `talk <≥3 sekutu>` (event mencatat sekutu).
- **Hadiah:** 150 XP + bonus kecil per sekutu.
- **Next:** quest032.
- **Catatan:** jumlah sekutu memengaruhi narasi q032 & q034 (teks varian) dan kesulitan pilihan di q036.

#### quest032 — Pengepungan Gereja
- **Alur:** Inkuisisi mengepung desa. Pertahanan besar — sekutu bertarung di latar, pemain menghadapi gelombang.
- **Requirements:** `kill_count inquisitor_soldier` ×4.
- **Hadiah:** 160 XP, 40 emas. **Flags:** `siege_won`.
- **Next:** quest033.

#### quest033 — Kanselir Varek
- **Alur:** Kebenaran penuh: Varek merekayasa semuanya — mencuri dari perbendaharaan, merekayasa kelaparan, dan memicu konflik gereja vs desa agar Jangkar jatuh ke tangannya. Scene dramatis (dialog + pilihan dukung/lawan).
- **Requirements:** `flag conspiracy_proven` (dari q028) + `talk king_aldric` atau `talk anchor_avatar`.
- **Hadiah:** 170 XP, 50 emas. **Flags:** `varek_unmasked`.
- **Next:** quest034.
- **Pilihan:** umumkan ke raja / ke rakyat / diam — menggeser reputasi faksi.

#### quest034 — Api Dimulai
- **Alur:** Inkuisisi membakar desa. **Quest escort pertama:** evakuasi Tom & warga ke kamp pemberontak (burning_village → rebel_camp).
- **Requirements:** `escort tom` (burning_village → rebel_camp).
- **Hadiah:** 180 XP, kenangan **memory009 "Desa Terbakar"** (versi kini), +10 village.
- **Next:** quest035.

#### quest035 — Menembus Cincin Api
- **Alur:** Blokade api menghalangi jalan ke ibukota. Hancurkan titik lemah atau terobos lewat jalur rahasia (butuh `finn_freed` atau crime ally).
- **Requirements:** `map capital_keep` + `kill_count royal_knight` ×2 ATAU `flag secret_path` (alternatif).
- **Hadiah:** 190 XP, 60 emas.
- **Next:** quest036.

#### quest036 — Pilihan Terakhir: Nasib Jangkar (keputusan besar #2)
- **Alur:** Di ruang Jangkar, dengan api ibukota di kejauhan, kau memegang takdir Jangkar. **Pilihan menentukan ending** — event `event_ending_choice` memvalidasi syarat dan menyetel flag jalur:

| Kode | Pilihan | Syarat | Jalur quest | Ending |
|------|---------|--------|-------------|--------|
| A | Segel bersama Ancient Order | ancient_order ≥ 25 | q037a–q038a | **Penjaga Baru** |
| B | Serahkan ke Pemberontak | rebels ≥ 25 | q037b–q038b | **Fajar Merah** |
| C | Serahkan ke Raja (bersihkan Varek) | royal_army ≥ 20 + `king_informed` | q037c–q038c | **Mahkota Utuh** |
| D | Serahkan ke Akademi | scholar_society ≥ 25 | q037d–q038d | **Menara Ilmu** |
| E | Hancurkan Jangkar | selalu tersedia | q037e–q038e | **Abu yang Tersisa** |
| F | Tulis ulang masa lalu (rahasia) | semua echo (1–5) + `rewrite_key` | q037f–q038f | **Paradoks** |

- Pilihan yang belum memenuhi syarat **tidak muncul** di dialog (memakai `require_reputation` + `require_flags` yang sudah didukung dialog_engine).
- **Hadiah:** 200 XP (jalur mana pun).

#### quest037a–q038a — Jalur A (Penjaga Baru)
- **q037a „Benteng Terakhir"** — pertahankan ruang Jangkar dari serangan `high_inquisitor` (mini-boss) & pasukan gereja. `kill_count inquisitor_soldier` ×3 + `enemy high_inquisitor`.
- **q038a „Sumpah Penjaga"** — ritual penyegelan bersama Aria & Lyra; +250 XP, `guardian_plate`, kenangan memory010.

#### quest037b–q038b — Jalur B (Fajar Merah)
- **q037b „Menyerbu Ibukota"** — bantu pemberontak merebut istana. `enemy royal_knight` ×2 + `enemy elite_guard`.
- **q038b „Pena Rakyat"** — Sera memakai Jangkar untuk menulis ulang dekrit penindasan. +250 XP, `time_edged_blade`, kenangan memory010. (Ending gelap: kerajaan runtuh, waktu goyah.)

#### quest037c–q038c — Jalur C (Mahkota Utuh)
- **q037c „Pembersihan Istana"** — kalahkan pasukan Varek yang setia. `kill_count cult_acolyte` ×2 + `enemy crown_assassin`.
- **q038c „Tahta yang Jujur"** — raja Aldric menyegel Jangkar di bawah istana; Varek dihukum. +250 XP, `anchor_crown`, kenangan memory010.

#### quest037d–q038d — Jalur D (Menara Ilmu)
- **q037d „Menara Terkepung"** — akademi diserang; pertahankan laboratorium. `kill_count time_wraith` ×2 + `enemy time_lord_wraith`.
- **q038d „Halaman Baru"** — Kael membuka sekolah waktu; +250 XP, `rune_crown` + `time_tincture` ×3, kenangan memory010.

#### quest037e–q038e — Jalur E (Abu yang Tersisa)
- **q037e „Memutus Jangkar"** — ritual penghancuran; lawan `anchor_shade` (jelmaan marah Jangkar). `enemy anchor_shade`.
- **q038e „Pagi Tanpa Batu"** — Jangkar hancur; ancaman hilang tapi waktu mulai tak menentu. +250 XP, `time_edged_blade`, kenangan memory010. (Ending pahit-manis.)

#### quest037f–q038f — Jalur F (Paradoks, rahasia)
- **q037f „Malam Kedua"** — gunakan semua echo untuk kembali ke **hari pembuatan Jangkar** dan mencegah penempaan (atau menyelamatkan penciptanya). `enemy ancient_tyrant`.
- **q038f „Sejarah yang Tidak Pernah Ada"** — konflik tak pernah terjadi; desa tak terbakar; kau kehilangan sebagian ingatanmu. +250 XP, kenangan memory010 „Paradoks". (Ending paling tersembunyi; petunjuknya tersebar di echo.)

#### quest039 — Perubahan Akhir (semua jalur)
- **Alur:** Setelah bos jalur, kondisi dunia berubah sesuai ending; satu quest penyelesaian urusan kecil (contoh: A: jaga gerbang; B: distribusi tanah; C: pesta rakyat; D: uji coba mesin; E: kubur Jangkar; F: bangun tanpa ingatan).
- **Requirements:** `flag <ending>_resolved`.
- **Hadiah:** 150 XP + item khusus jalur.

#### quest040 — Perpisahan Sekutu (semua jalur)
- **Alur:** Ucapkan selamat tinggal / hadiahi sekutu yang bertahan; **1 NPC gugur permanen per jalur** (keputusan terkunci §19) — tokoh yang gugur disebut di epilog q044.
- **Requirements:** `talk <2 tokoh sekutu>`.
- **Hadiah:** 100 XP; pengaruh pada teks epilog.

#### quest041 — Kenangan Terakhir (semua jalur)
- **Alur:** Kumpulkan sisa kenangan/echo yang belum dibuka; Lyra menjelaskan makna Pejalan Waktu.
- **Requirements:** `talk lyra` + `flag all_echoes_hinted`.
- **Hadiah:** 100 XP, kenangan **memory011 "Arti Waktu"**.

#### quest042 — Waktu yang Tersisa
- **Alur:** Di ambang perpisahan, avatar Jangkar (atau jejaknya) memberimu pilihan kecil: meninggalkan masa ini atau tinggal. Pilihan memengaruhi baris akhir q044.
- **Requirements:** `talk anchor_avatar` (atau `talk lyra` bila jalur E/F).
- **Hadiah:** 100 XP.

#### quest043 — Catatan Seorang Pejalan Waktu
- **Alur:** Menuliskan catatan perjalananmu ke dalam buku perpustakaan — meta-moment; teksnya bervariasi sesuai ending & keputusan besar (recap otomatis dari flags).
- **Requirements:** `flag recap_prepared` (diset event).
- **Hadiah:** 100 XP.

#### quest044 — Epilog: Pagi di Ashen
- **Alur:** Scene penutup per ending — teks varian + statistik perjalanan (quest selesai, bos dikalahkan, faksi teratas). Banner "TAMAT — SEASON 1".
- **Requirements:** `flag <ending>_done`.
- **Hadiah:** 0 XP; kenangan **memory012 "Pagi di Ashen"**.

#### quest045 — Benih Musim Kedua (teaser)
- **Alur:** Setelah tamat, satu event kecil: tanda anomali waktu muncul di kerajaan lain / langit berubah lagi / surat dari masa depan. Ini benih Season 2.
- **Requirements:** `flag season1_ended`.
- **Hadiah:** kenangan **memory013 "Tanda dari Masa Depan"** (teks berbeda per ending).
- **Catatan:** quest045 memastikan pemain tahu cerita berlanjut — tanpa konten yang dijanjikan di spec ini.

---

## 11. Ringkasan Data Konten Baru

| Tipe | Jumlah baru | Total akhir |
|------|-------------|-------------|
| Quest | 43 (+6 jalur ending) | 45 posisi |
| Peta | 10 | 12 |
| NPC | 22 | 24 |
| Musuh reguler | 20 | 23 |
| Bos | 9 | 9 |
| Item | 19 (tier + konsumabel + quest) | 24 |
| Skill | 10 | 16 |
| Kenangan | 10 (memory003–012 + 1 seed) | 13 (belum dibuat — Phase 1) |
| Dialog | ±40 file | ±50 (belum dibuat — Phase 1) |
| Event | ±15 | ±20 (belum dibuat — Phase 1) |
| Scene | 5 (echo & epilog) | 7 (belum dibuat — Phase 1) |

---

## 12. Mekanik Baru

### 12.1 Kind quest baru (perluasan quest_engine)

Tiga kind baru ditambahkan ke `requirements` quest:

| Kind | Format | Cara selesai |
|------|--------|--------------|
| `collect` | `{"kind":"collect","target":"<item_id>","amount":N}` | Pemain memiliki ≥ N item target di inventaris (dicek saat menambah item & saat perintah inv/use) |
| `kill_count` | `{"kind":"kill_count","target":"<enemy_id>","amount":N}` | Kalahkan musuh target sebanyak N kali (counter disimpan per quest) |
| `escort` | `{"kind":"escort","target":"<npc_id>","from":"<map_id>","to":"<map_id>"}` | Bawa NPC dari map A ke map B (dicek saat tiba di map tujuan) |

**Perubahan state pemain:** `player.quests_active[id]` diperluas dari `{"met": []}` menjadi:
```json
{"met": [0, 1], "progress": {"ruins_scavenger": 2}}
```
- `met`: indeks requirement yang sudah terpenuhi (seperti sekarang).
- `progress`: counter untuk `kill_count` / `collect`.

**Fungsi baru di `quest_engine`:**
- `progress_requirement(game_state, kind, target, amount=1)` — tambah counter, panggil `complete_requirement` bila penuh.
- Hook dipanggil dari: `inventory_system.add_item` (collect), kemenangan pertarungan (kill_count), `travel_system`/`exploration_system` saat tiba di map (escort).

### 12.2 Toko via dialog

- Field baru `shop` di NPC (§7.2).
- Dialog mendapat opsi sistem **"Berbelanja"** bila NPC punya `shop` (ditambahkan di `dialog_view` sebagai aksi paralel — bukan pilihan dialog biasa).
- Sistem baru `src/systems/shop_system.py`:
  - `buy(game_state, npc_id, item_id)` → cek stok, kurangi emas, tambah item (lewat `inventory_system`).
  - `sell(game_state, npc_id, item_id, qty)` → hapus item, tambah emas = harga_jual × `sell_multiplier`.
  - Harga jual item = `price` dari `data/items/<id>.json` (tiap item diberi field `price`).
- Tampilan: daftar beli (harga) / daftar jual (harga jual) / keluar.
- **Diskon/kenaikan harga** bisa dikontrol via reputasi (contoh: merchant_guild ≥ 15 → −15% harga).

### 12.3 Perjalanan waktu (sangat sentral)

1. **Echo (kilas balik):** scene khusus di `data/story/scenes.json` dengan field `"echo": true`; diputar saat quest/event memanggil aksi `play_scene`. Echo menambah kenangan dan flag `echo_N_collected`.
2. **Hitung mundur kebakaran (5 hari, ada konsekuensi — terkunci §19):** flag `ultimatum_5_days` diset di q013; counter `days_remaining` mulai 5 dan tampil di HUD ("Api dalam N hari"). Setiap `rest` → event `event_day_tick` mengurangi 1. Bila mencapai 0 sebelum q032 → event darurat `ultimatum_expired`: desa terbakar lebih cepat, quest Arc 3 yang belum selesai (q014, q016, q018, q019) **gagal otomatis** (hadiah & reputasi hilang, tak bisa diselesaikan), tetapi alur utama q015→q020→q032–q045 tetap bisa dijalankan dengan teks varian. Implementasi: hook di `time_engine`/`game.py` saat `rest` + HUD.
3. **Tulis ulang masa lalu:** kumpulkan semua echo (1–5) → flag `rewrite_key` terbuka → pilihan ending F. Konsekuensi masa lalu memengaruhi masa kini via flag (mis. menyelamatkan pencipta di q037f mengubah teks epilog).
4. **Kenangan tetap jadi jejak keputusan** (sistem yang ada) — diperluas ke 13 kenangan.

### 12.4 Quest eksklusif faksi (reputasi)

Reputasi (per faksi, dari hadiah quest & pilihan) membuka quest/pilihan ekstra (bukan quest terpisah, melainkan **opsi dialog & hadiah bonus** agar beban konten tetap terkendali):

| Ambang | Efek |
|--------|------|
| merchant_guild ≥ 10 | Opsi nego harga q008; diskon toko |
| rebels ≥ 15 | Sekutu Sera di q031; jalur B lebih mulus |
| ancient_order ≥ 25 | Ending A terbuka; info Lyra ekstra |
| scholar_society ≥ 25 | Ending D terbuka; decode penuh |
| royal_army ≥ 20 + raja sadar | Ending C terbuka |
| crime ≥ 15 | Jalur rahasia q035 |
| village ≥ 20 | Warga bertahan di q032 |

### 12.5 Ending (6 variasi)

| Kode | Nama | Ringkas | Syarat | Bos final |
|------|------|---------|--------|-----------|
| A | **Penjaga Baru** | Jangkar disegel; Ancient Order bangkit | ancient_order ≥ 25 | high_inquisitor |
| B | **Fajar Merah** | Kerajaan runtuh; pemberontak menulis ulang | rebels ≥ 25 | general_corvin |
| C | **Mahkota Utuh** | Varek tumbang; raja jujur menyimpan Jangkar | royal_army ≥ 20 + king_informed | chancellor_varek |
| D | **Menara Ilmu** | Akademi menguasai studi waktu | scholar_society ≥ 25 | time_lord_wraith |
| E | **Abu yang Tersisa** | Jangkar dihancurkan; waktu goyah | selalu | anchor_shade |
| F | **Paradoks** (rahasia) | Sejarah ditulis ulang; konflik tak pernah ada | semua echo + rewrite_key | ancient_tyrant |

- **Ending default** bila tidak memenuhi syarat apa pun: E (selalu tersedia) dengan epilog netral.
- Tiap ending memberi **memory012** dengan teks berbeda + **memory013** (benih Season 2) berbeda.

---

## 13. Perubahan Engine (ringkas)

| File | Perubahan | Prioritas |
|------|-----------|-----------|
| `src/engine/quest_engine.py` | Kind baru collect/kill_count/escort; `progress_requirement`; state `progress` | Phase 0 |
| `src/engine/event_engine.py` | Aksi baru: `play_scene`, `unlock_map`, `grant_item`, `set_counter` | Phase 0 |
| `src/engine/dialog_engine.py` | Opsi sistem "Berbelanja" saat NPC punya shop; `require_reputation` sudah ada | Phase 0 |
| `src/ui/dialog_view.py` | Menu toko (beli/jual/keluar) | Phase 0 |
| `src/systems/shop_system.py` | **Baru** — buy/sell, harga, diskon reputasi | Phase 0 |
| `src/systems/inventory_system.py` | Hook `progress_requirement(collect)` di add_item | Phase 0 |
| `src/engine/combat_engine.py` | Hook `kill_count` saat victory; bos tak bisa kabur (`tags: boss`); **self-buff skill (target self)** — terkunci §19 | Phase 0 |
| `src/systems/exploration_system.py` / `travel_system.py` | Hook `escort` saat tiba di map tujuan; cek flag `map_*_unlocked` untuk pilihan `go` | Phase 0 |
| `src/engine/time_engine.py` / `src/core/game.py` | Hook `event_day_tick` (hitung mundur ultimatum) saat `rest` | Phase 0 |
| `src/core/game_context.py` | Muat field `shop` dari NPC; (opsional) field `echo` scene | Phase 0 |
| `src/core/game_state.py` / `src/models/player.py` | Default `progress` di quests_active; save/load backward-compatible | Phase 0 |
| `src/ui/story_view.py` / `scenes.json` | Scene echo & epilog | Phase 0/1 |

**Prinsip:** perubahan engine diminimalkan; semua konten tetap data JSON. Setiap perluasan engine disertai unit test.

---

## 14. Contoh JSON Lengkap

### 14.1 Quest dengan `kill_count` (quest010)

```json
{
  "id": "quest010",
  "title": "Reruntuhan Berbisik",
  "type": "main",
  "description": "Roh Penjaga menguji kesungguhanmu di Reruntuhan Kuno.",
  "objectives": [
    "Bicaralah dengan Roh Penjaga.",
    "Kalahkan 3 pemulung reruntuhan."
  ],
  "requirements": [
    {"kind": "talk", "target": "ancient_spirit"},
    {"kind": "kill_count", "target": "ruins_scavenger", "amount": 3}
  ],
  "rewards": {"xp": 90, "gold": 25, "reputation": {"ancient_order": 5}},
  "flags_on_complete": ["echo_1_collected", "quest010_done"],
  "next": "quest011"
}
```

### 14.2 Quest dengan `collect` (quest009)

```json
{
  "id": "quest009",
  "title": "Dinding Reruntuhan",
  "type": "main",
  "description": "Gerbang reruntuhan terkunci oleh kunci batu berukir.",
  "objectives": ["Kumpulkan 1 Kunci Batu (rune_key) dari pemulung reruntuhan."],
  "requirements": [
    {"kind": "map", "target": "ruins_entrance"},
    {"kind": "collect", "target": "rune_key", "amount": 1}
  ],
  "rewards": {"xp": 70, "gold": 20},
  "flags_on_complete": ["map_ancient_ruins_unlocked", "quest009_done"],
  "next": "quest010"
}
```

### 14.3 Quest dengan `escort` (quest034)

```json
{
  "id": "quest034",
  "title": "Api Dimulai",
  "type": "main",
  "description": "Desa terbakar. Selamatkan warga sebelum semuanya hangus.",
  "objectives": ["Antarkan Tom ke Kamp Pemberontak."],
  "requirements": [
    {"kind": "escort", "target": "tom", "from": "burning_village", "to": "rebel_camp"}
  ],
  "rewards": {"xp": 180, "gold": 20, "reputation": {"village": 10}},
  "flags_on_complete": ["villagers_saved", "quest034_done"],
  "next": "quest035"
}
```

### 14.4 NPC dengan toko (marcus)

```json
{
  "id": "marcus",
  "name": "Marcus",
  "location": "village",
  "role": "merchant",
  "relationship": {"trust": 0, "affinity": 0, "knowledge": 0},
  "faction": "merchant_guild",
  "dialogs": ["dialog_marcus_main"],
  "shop": {
    "buy": [
      {"item": "potion", "price": 25},
      {"item": "steel_sword", "price": 120},
      {"item": "chain_armor", "price": 150},
      {"item": "elixir", "price": 80}
    ],
    "sell_multiplier": 0.5
  }
}
```

### 14.5 Event gate Arc 2 (kompatibilitas save lama)

```json
{
  "id": "event_arc2_gate",
  "trigger": [
    {"kind": "flag", "flag": "quest001_done", "value": true},
    {"kind": "flag", "flag": "quest002_done", "value": true},
    {"kind": "flag", "flag": "arc2_started", "operator": "MISSING"}
  ],
  "actions": [
    {"kind": "log", "text": "═══════════════════════════════════════"},
    {"kind": "log", "text": "ARC 2 — JANGKAR WAKTU"},
    {"kind": "log", "text": "Aria mengetukmu di malam hari: 'Ada sesuatu di bawah perpustakaan.'"},
    {"kind": "start_quest", "id": "quest003"},
    {"kind": "set_flag", "flag": "arc2_started", "value": true}
  ]
}
```

### 14.6 Event pilihan ending (quest036)

```json
{
  "id": "event_ending_choice",
  "trigger": [
    {"kind": "flag", "flag": "quest035_done", "value": true},
    {"kind": "flag", "flag": "ending_chosen", "operator": "MISSING"}
  ],
  "actions": [
    {"kind": "set_flag", "flag": "ending_choice_pending", "value": true}
  ]
}
```

Pilihan di dialog quest036 (`dialog_ending_choice`) memakai `set_flags` untuk menyetel `ending_<a..f>`, lalu event per ending memulai quest jalur:

```json
{
  "id": "event_start_path_a",
  "trigger": [
    {"kind": "flag", "flag": "ending_a", "value": true},
    {"kind": "flag", "flag": "quest037a_started", "operator": "MISSING"}
  ],
  "actions": [
    {"kind": "start_quest", "id": "quest037a"},
    {"kind": "set_flag", "flag": "quest037a_started", "value": true}
  ]
}
```

### 14.7 Kenangan baru (contoh memory003)

```json
{
  "id": "memory003",
  "title": "Asal Jangkar",
  "text": "Lima penjaga bersumpah di depan batu yang berdenyut... dan salah satu dari mereka mengenal wajahmu.",
  "flags_set": ["echo_1_collected"],
  "acquired_by": {"kind": "event", "event": "event_echo_1"}
}
```

---

## 15. Kompatibilitas Save Lama

**Target:** save yang sudah menyelesaikan Arc 1 (quest001+quest002 di `quests_done`) langsung lanjut ke quest003 tanpa reset.

- Event `event_arc2_gate` (14.5) memakai flag `quest001_done` + `quest002_done` → memicu quest003 untuk save lama **dan** save baru (quest002 `next` juga diisi `quest003` untuk save yang menyelesaikan quest002 setelah update).
- `player.quests_active[id]` diperluas dengan `progress` — save lama tanpa field ini tetap valid (default `{}`).
- **Alat bantu:** `tools/validate_saves.py` — memeriksa save lama bisa dimuat & flag/quest konsisten setelah update.
- **Tidak ada migrasi data rumit** — semua state baru berbasis flag yang default-nya MISSING.

---

## 16. Keseimbangan & Kurva Level

Rumus XP naik level tetap `50 × level` (sistem yang ada). Target level akhir **30–35**.

| Arc | Rata-rata XP quest | XP kumulatif quest | +XP pertarungan (perkiraan) | Level perkiraan akhir |
|-----|--------------------|--------------------|----------------------------|------------------------|
| 1 | 45 | 90 | ±150 | 2–3 |
| 2 | 90 | ~800 | ±900 | 8–10 |
| 3 | 130 | ~2000 | ±1600 | 15–17 |
| 4 | 170 | ~3300 | ±2300 | 23–25 |
| 5 | 190 | ~4300 | ±3000 | 30–35 |

- **Skala musuh:** Arc 2 → Lv 5–9 (bos 10); Arc 3 → Lv 10–14 (bos 15); Arc 4 → Lv 15–21 (bos 22); Arc 5 → Lv 22–27 (bos 28–30).
- **Emas:** akumulasi quest + loot + toko jual harus cukup untuk membeli perlengkapan tier sesuai arc. Toko ibukota (Brock/Yara) menjual item rare di harga tinggi sebagai *sink* emas.
- **Angka final wajib diverifikasi lewat playtest otomatis** (`tools/playtest_season1.py`, lihat §17) — bukan asumsi.

---

## 17. Rencana Implementasi (bertahap per arc)

| Phase | Isi | Gate kualitas |
|-------|-----|---------------|
| **0** | Perluasan engine: kind quest baru, toko, hook escort/kill_count/collect, bos no-escape, event_day_tick; unit test semua | `pytest -q` hijau |
| **1** | **Arc 2**: data peta/NPC/musuh/item/skill + quest003–011 + dialog + event + echo 1 | playtest Arc 2 bisa tamat; test konten |
| **2** | **Arc 3**: quest012–020 + boss Iris + hitung mundur ultimatum | playtest Arc 3 |
| **3** | **Arc 4**: dungeon 2 lantai + echo 2–3 + quest021–029 + ibukota | playtest Arc 4 |
| **4** | **Arc 5**: quest030–045 + 6 jalur ending + epilog + benih Season 2 | playtest semua 6 ending |
| **5** | Poles: README, keseimbangan, `tools/validate_saves.py`, full playtest | seluruh suite hijau |

**Cara kerja disepakati:** bertahap per arc, tiap tahap ada tes sebelum lanjut.

---

## 18. Rencana Pengujian

- **Unit test baru:**
  - `tests/test_quest_engine_ext.py` — kind collect/kill_count/escort, `progress_requirement`, state `progress`.
  - `tests/test_shop.py` — beli/jual, emas cukup/tidak, stok, diskon reputasi.
  - `tests/test_escort.py` — selesai saat tiba di map tujuan; gagal bila map salah.
  - `tests/test_ending_gates.py` — syarat reputasi/flag tiap ending (A–F) benar.
  - `tests/test_save_migration.py` — save Arc 1 lama memicu event_arc2_gate.
- **Validasi konten:** `tests/test_season1_content.py` — semua JSON quest/peta/NPC/enemy/item memuat valid (pola `test_arc1_content.py`), graph quest acyclic, referensi target valid.
- **Playtest otomatis:** `tools/playtest_season1.py --arc 2|3|4|5 --all-classes --count N` (perluasan `playtest_arc1.py`) — simulasi berjalan sampai tamat, mendeteksi jalan buntu & ketidakseimbangan.
- **Smoke test CLI:** perpanjang `tools/smoke_menu.sh` untuk toko & dialog ending.

---

## 19. Keputusan yang Dikunci (resolusi pertanyaan terbuka)

Semua pertanyaan terbuka telah diputuskan pada sesi wawancara kedua:

| # | Topik | Keputusan terkunci | Dampak ke spec |
|---|-------|--------------------|----------------|
| 1 | Ultimatum kebakaran | **5 hari game** dengan konsekuensi: bila habis sebelum q032, quest Arc 3 (q014, q016, q018, q019) gagal otomatis (hadiah hilang); alur utama tetap jalan. Counter `days_remaining` tampil di HUD. | §10.2 q013, §10.4, §12.3 |
| 2 | Kematian NPC | **1 NPC gugur permanen per jalur ending** (bukan sekutu utama; tokoh ditentukan pilihan & reputasi); berpengaruh di teks epilog q044, tidak mengunci gameplay. | §10.4 intro & q040 |
| 3 | Multi-phase bos | **Didefer penuh** — bos Season 1 single-phase; fase kedua (HP < 50%) menjadi enhancement terpisah di luar scope. | §8.2, §13 |
| 4 | Self-buff skill | **Masuk Phase 0** — combat_engine diperluas untuk aksi target-self; semua 10 skill baru langsung jadi. | §9.4, §13 |
| 5 | Urutan quest 039–043 | **Rantai berurutan via `next`** (q039→q040→q041→q042→q043) agar HUD `next_objective` tetap jelas. | §10.4 |
| 6 | Judul Season 1 | **"Jangkar Waktu"** (dipertahankan). | seluruh dokumen |
| 7 | Panjang dialog | **Deskriptif semua** — gaya novel ringan (2–5 baris per beat); quest kunci boleh lebih panjang. | §10.0 |

**Catatan:** keputusan #1 dan #2 sengaja tidak menciptakan "game over" permanen, selaras filosofi game (FAQ README: tidak ada game over).

---

## 20. Lampiran: Alur Quest Lengkap (graf)

```
Arc 1           Arc 2                             Arc 3
q001→q002  →  q003→q004→q005→q006→q007→q008→q009→q010→q011  →  q012→q013→q014→q015→q016→q017→q018→q019→q020

Arc 4                                    Arc 5 (climax)
q021→q022→q023→q024→q025→q026→q027→q028→q029  →  q030→q031→q032→q033→q034→q035→[q036 keputusan]

[q036] → jalur ending (pilih satu):
   A: q037a→q038a→q039→q040→q041→q042→q043→q044→q045
   B: q037b→q038b→q039→q040→q041→q042→q043→q044→q045
   C: q037c→q038c→q039→q040→q041→q042→q043→q044→q045
   D: q037d→q038d→q039→q040→q041→q042→q043→q044→q045
   E: q037e→q038e→q039→q040→q041→q042→q043→q044→q045
   F: q037f→q038f→q039→q040→q041→q042→q043→q044→q045
```

## 21. Status Implementasi Data (sesi ini)

File data pendukung yang sudah dibuat (Phase 0 scaffolding, sebelum quest/dialog):

| Tipe | Dibuat | Catatan |
|------|--------|---------|
| Peta | 11 file (`data/maps/*.json`) | termasuk `anchor_vault` (quest004); exits terhubung penuh dari village ke semua peta baru |
| ASCII art | 11 file (`assets/ascii/*.txt`) | dipakai `look`; semua peta kini punya art |
| NPC | 24 file (`data/npc/*.json`) | semua punya dialog (123 file dialog total); merchant punya field `shop` |
| Musuh reguler | 20 file (`data/enemies/*.json`) | skala Lv 5–18; loot merujuk item yang sudah ada |
| Bos | 9 file (`data/enemies/*.json`) | `tags: ["boss"]`; 3 bos arc + 6 bos final |
| Item | 19 file (`data/items/*.json`) | 3 konsumabel, 9 gear tier, 7 quest item; `time_tincture` (heal_mp) & `smoke_bomb` (escape) aktif — Phase 0 selesai |
| Skill | 10 file (`data/skills/*.json`) | 6 damage/status siap dipakai; 4 self-buff (`war_cry`, `arcane_barrier`, `shadow_step`, `time_study`) aktif via field `buff` — combat_engine Phase 0 selesai |
| Quest | 55 file (`data/quests/*.json`) | quest003–045 + quest037a–f/038a–f; requirement kind dibatasi {talk, map, flag, enemy}; kill count via flag `killed_<enemy>_<N>` (dihitung ulang dari flag agar tahan save/load), collect via `have_<item>` |
| Dialog | 123 file (`data/dialogues/*.json`) | intro → main → branch → generic untuk 24 NPC; gating via `require_flags`/`require_not_flags` |
| Event | `data/events/events.json` | gate Arc 2–5, echo, banner, pilihan ending, start quest jalur A–F, alias faksi, `conspiracy_proven`, dan flag penyelesaian jalur ending (q037x_done → q038x) + `recap_prepared` (q043) |
| Kenangan | `data/story/memories.json` | memory001–013 (13 total) |

**Engine hooks baru (sesi ini):**
- `start_quest` kini menandai syarat flag/map yang sudah terpenuhi saat quest mulai (rantai epilog q039–q045 jalan otomatis).
- `complete_requirement` aman tanpa player; hook `map` dipanggil setelah travel (`go`), hook `flag` dipanggil saat event set_flag, pilihan dialog set_flags, kill musuh (`killed_<enemy>_<N>`), dan item quest dari loot (`have_<item>`).
- `GameState.kill_counts` melacak jumlah kill per musuh (tidak ikut disimpan save; flag `killed_*` yang persist).

**Belum dibuat (Phase 2+):** teks scene echo tambahan (baru 2 dari 5 echo yang direncanakan punya scene: `echo_anchor_forged`, `echo_guardian_oath`), varian epilog per ending A–F (baru ada 1 `epilogue_morning` generik, belum 6 varian sesuai §12.5), dan teks recap q043 yang bergantung ending — ketiganya konten naratif Phase 2–4 (§17), di luar scope sesi ini.

**Sesi lanjutan — penyelesaian gap Phase 1 (fail_quest, dialog ending, HUD):**
- `quest_engine.fail_quest(game_state, quest_id)` + `Player.quests_failed` (baru) + `save_manager` (backward-compatible: save lama tanpa field ini tetap valid via default `[]`) — dukungan auto-fail ultimatum §12.3.
- `data/events/events.json`: `event_ultimatum_expired` (menggagalkan otomatis q014/q016/q018/q019 saat `ultimatum_expired` aktif dan belum `ultimatum_resolved`/`ultimatum_failures_applied`) + `event_rewrite_key` (menyalakan `rewrite_key` — gerbang ending F — begitu `echo_1_collected` dan `echo_2_collected` aktif).
- Dialog pilihan ending `dialog_avatar_ending.json`: 6 opsi (A–F) ber-gerbang reputasi/flag sesuai tabel §10.4 quest036, ditautkan ke rantai dialog `anchor_avatar`.
- Dialog flag yatim yang sebelumnya tak tersambung ke pemicu apa pun kini disambungkan: `dialog_lyra_quest015` (set `quest015_resolved`/`quest015_leaked`), `dialog_spirit_seal_wisdom` + `dialog_spirit_seal_time` (set `seal_of_wisdom_ok`/`seal_of_time_ok` untuk quest024/quest025).
- `src/ui/hud.py`: baris hitung mundur ultimatum ("🔥 Api dalam N hari", sembunyi bila `ultimatum_resolved`) dan hint toko per peta ("🛒 Toko tersedia: ...", butuh `npc_catalog` opsional) — melengkapi item "toko terhubung ke HUD" dan "hitung mundur ultimatum" yang sebelumnya tercatat belum dibuat.
- Test baru: `tests/test_phase1_content.py` (15 test — dialog ending & gating reputasi, auto-fail ultimatum + rantai `next`, dialog flag yatim, HUD countdown & shop hint, event `rewrite_key`) serta perbaikan `tests/test_quest_hooks.py::test_talk_no_shop_hint_for_npc_without_shop` (assert sebelumnya keliru membandingkan hint toko level-peta dengan NPC yang sedang diajak bicara).
- Verifikasi penuh sesi ini: `pytest -q` → **525 passed**; `ruff check .` → **All checks passed** (3 pelanggaran gaya di `test_phase1_content.py` — en dash di docstring, import tak terurut, variabel tak terpakai — diperbaiki).

**Perbaikan terbaru (tervalidasi `tests/test_season1_quests.py`):** setiap map yang jadi syarat quest kini punya flag unlock `map_<id>_unlocked` dari quest pendahulunya — quest005 → `map_forest_deep_unlocked`, quest013 → `map_crime_den_unlocked`, quest015 → `map_rebel_camp_unlocked`, quest020 → `map_ruins_depth_unlocked`, quest025 → `map_anchor_chamber_unlocked`, quest026 → `map_capital_unlocked`, quest034 → `map_capital_keep_unlocked`. (Sebelumnya 6 peta tidak pernah bisa dibuka, dan quest026 meng-unlock prasyaratnya sendiri — keduanya diperbaiki.)

**Phase 0 engine selesai (tervalidasi `tests/test_phase0_combat.py`, 13 test):**
- Self-buff skill target-self — `CombatState.buffs` (BuffEffect), `_apply_buff`/`tick_buffs`, stat naik dipakai di `player_stats`, XP bonus (time_study) dipakai saat victory, tampil di combat_view, tahan save/load.
- Bos tak bisa kabur — `_escape` gagal saat `tags: ["boss"]`.
- Item baru aktif — `time_tincture` (heal_mp, MP penuh, combat & luar combat), `smoke_bomb` (escape pasti berhasil di combat; di luar combat ditolak).

**Penyelesaian Phase 1 — verifikasi via Filesystem MCP (2026-08-05):**

Semua TODO Phase 1 dikonfirmasi selesai dengan inspeksi langsung tiap file:

- `quest_engine.fail_quest` + `Player.quests_failed` + `save_manager` backward-compatible (`quests_failed` default `[]` saat load save lama) — mendukung auto-fail ultimatum §12.3.2.
- `data/events/events.json`: `event_ultimatum_expired` (gagalkan otomatis q014/q016/q018/q019 saat `ultimatum_expired` aktif; guard ganda `ultimatum_resolved` + `ultimatum_failures_applied` mencegah duplikasi) + `event_rewrite_key` (nyalakan `rewrite_key` begitu `echo_1_collected` dan `echo_2_collected` keduanya aktif).
- `data/dialogues/dialog_avatar_ending.json`: 6 pilihan ending A–F ber-gerbang reputasi/flag sesuai tabel §10.4; gerbang dialog: `require_flags: ["ending_choice_pending"]` + `require_not_flags: ["ending_chosen"]`; Ending F di index 5 dengan `require_flags: ["rewrite_key"]`; ditautkan ke `anchor_avatar` via `anchor_avatar.json`.
- Dialog flag yatim dikonfirmasi: `dialog_lyra_quest015` (pilihan 0 `"Bocorkan..."` → `quest015_resolved + quest015_leaked`); `dialog_spirit_seal_wisdom` (`require_flags: [arc4_started]`, pilihan jawaban benar → `seal_of_wisdom_ok`); `dialog_spirit_seal_time` (`require_flags: [seal_of_wisdom_ok]`; semua 3 pilihan selaras → `seal_of_time_ok`).
- `src/ui/hud.py`: `_ultimatum_line()` menghasilkan "🔥 Api dalam N hari" (hilang saat `ultimatum_resolved`) + "🔥 Api telah dimulai." saat `ultimatum_expired`; `_shop_hint()` menghasilkan "🛒 Toko tersedia: \<nama\>" dari NPC berfield `shop` di peta saat ini (opsional, butuh `npc_catalog`).
- `tests/test_phase1_content.py`: **15 test** (3 dialog ending, 3 ultimatum, 3 dialog flag yatim, 4 HUD, 2 rewrite_key); lint bersih — docstring pakai `-` bukan en-dash, 2 baris kosong sebelum fungsi pertama, tidak ada variabel tak terpakai atau import unused.
- `tests/test_quest_hooks.py::test_talk_no_shop_hint_for_npc_without_shop`: diperbarui — assert memvalidasi bahwa dialog NPC non-pedagang tidak menawarkan "Ketik 'shop'", bukan hint toko level-peta dari HUD (yang memang boleh muncul per §12.2).
- `data/maps/village.json`: dikonfirmasi memiliki 12 NPC termasuk `marcus`, `kael`, `ben`, `helen` — merchant tersedia untuk test HUD shop hint.

**Verifikasi akhir Phase 1:** `pytest -q` → **527 passed** (510 Phase 0 + 15 test Phase 1 baru + 2 penyesuaian test quest hooks); `ruff check .` bersih; smoke test end-to-end via `Game` asli dikonfirmasi: auto-fail ultimatum (q014/q016/q018/q019), `rewrite_key` dari 2 echo, dialog ending 6 opsi (gating reputasi + `king_informed` + `rewrite_key` bekerja, pilihan menyetel `ending_<x>` + `ending_chosen`), HUD hitung mundur ("🔥 Api dalam N hari" dan status expired), dan dialog flag yatim menyetel flag yang benar.

**Catatan review (2026-08-05):** gerbang ending A–F di `dialog_avatar_ending.json` diverifikasi cocok dengan tabel §10.4 (ancient_order ≥ 25 / rebels ≥ 25 / royal_army ≥ 20 + `king_informed` / scholar_society ≥ 25 / selalu / `rewrite_key`); ending E sengaja tanpa gerbang (ending fallback §10.4). `event_rewrite_key` sengaja digerbani `echo_1_collected` + `echo_2_collected` — dua echo yang sudah punya scene di data (echo 3–5 adalah konten Phase 2–4, §21 "Belum dibuat"); saat echo 3–5 ditambahkan, trigger event diperluas ke `all_echoes_hinted`. `fail_quest` defensif: menolak quest non-aktif, mencegah duplikat di `quests_failed`, dan tidak memulai ulang `next` yang sudah aktif/selesai/gagal. `_ultimatum_line` kini menampilkan status "Api telah dimulai" bahkan tanpa flag `ultimatum_5_days` (defensif terhadap urutan flag). **Phase 1 selesai — siap lanjut ke Phase 2 (Arc 3: data quest012–020, boss Iris, hitung mundur ultimatum di gameplay).**

**Penyelesaian Phase 2 — verifikasi menyeluruh (2026-08-05):**

Seluruh deliverable Arc 3 §22 dikonfirmasi ada dan terverifikasi end-to-end:

- `event_arc3_gate` + `event_arc3_complete` (events.json) — isi persis §22.2.1: gate memicu quest012 + set `arc3_started` + `map_forest_deep_unlocked`; complete meng-grant memory005 + guard `arc3_complete_shown`. (Sebelumnya tercatat "belum ada" di G-05/G-06 — ternyata sudah dibuat.)
- `memory005` "Kanselir" (memories.json) — teks + `flags_set: [iris_revealed]` persis §22.2.2.
- `dialog_marcus_betrayal` (G-08) — file baru + wiring `marcus.json` (`['dialog_marcus_quest', 'dialog_marcus_betrayal', 'dialog_marcus_main']`); choice menyetel `marcus_betrayal_found`/`marcus_helped`.
- `sister_iris.json` loot (G-12) — `rune_blade`/`rune_plate` chance 50% (dari 100%), elixir 50%.
- `dialog_sera_offer` (G-13) — choice 0 set_flags kini `[sera_aligned, aligned_rebels, aligned_any]`.
- `tests/test_arc1_content.py` valid_kinds (G-14) — sudah memuat collect/kill_count/escort sejak Phase 1.
- `tests/test_arc3_content.py` — **18 test** (data integrity 5, quest chain 5, ultimatum countdown 4, reputasi 2, map gate 2) — lulus 18/18.

**Smoke test end-to-end `tools/smoke_arc3.py` (baru, 30 check):** simulasi lengkap Arc 3 via `Game` asli: arc2 selesai → `event_arc3_gate` (quest012 + banner + unlock) → quest012 (talk tom + go forest_deep) → quest013 (dialog iris nyata → ultimatum_received + ultimatum_5_days) → HUD "Api dalam 5 hari" → rest → "Api dalam 4 hari" → quest014 (crime_den + evidence_letter) → quest015 (dialog lyra → quest015_resolved) → quest016 (rebel_camp via forest_deep) → quest017 (hook flag have_old_scrolls + talk kael) → quest018 (dialog marcus betrayal + guild_guard) → quest019 (3× inquisitor_soldier) → quest020 boss sister_iris → `event_arc3_complete` (banner + memory005) → quest021 aktif (Arc 4). **Semua 30 check lulus** — rantai Arc 3 tanpa blokir.

**Verifikasi akhir Phase 2:** `pytest -q` → **545 passed** (527 Phase 1 + 18 test Arc 3), 0 failed; `ruff check .` bersih; playtest Arc 1 250/250 (100%) — regresi nol. **Phase 2 selesai — siap lanjut ke Phase 3 (Arc 4: dungeon 2 lantai, echo 2–3, quest021–029, ibukota).**

**Phase 2 — Arc 3 (quest012–020) selesai (tervalidasi `tests/test_arc3_content.py`, 18 test):** semua gap G-01 s/d G-14 dari §22.1 ditutup dengan nol perubahan engine (`src/`). Data: `data/events/events.json` +`event_arc3_gate` (trigger `boss_arc2_defeated` + guard `arc3_started` MISSING; aksi `start_quest quest012`, set `arc3_started` dan `map_forest_deep_unlocked`) dan +`event_arc3_complete` (trigger `boss_arc3_defeated` + guard `arc3_complete_shown` MISSING; `grant_memory memory005`); `data/story/memories.json` +`memory005` (title "Kanselir", teks menyebut Varek/Iris, flags `iris_revealed`); `data/dialogues/dialog_marcus_betrayal.json` file baru (gate `arc3_started`, anti-duplikat `marcus_betrayal_found`, choice 0 juga set `marcus_helped`) disisipkan ke `marcus.json` sebelum `dialog_marcus_main`; `data/dialogues/dialog_sera_offer.json` choice 0 kini set `aligned_any`; `data/enemies/sister_iris.json` loot `rune_blade`/`rune_plate` turun 100→50. Test: `tests/test_arc3_content.py` 18 test sesuai §22.4 (data integrity 5, quest chain wiring 5, ultimatum countdown 4, reputation/alignment 2, map_forest_deep gate 2); `tests/test_arc1_content.py::test_quest_requirement_kinds` diperluas ke {talk, map, flag, enemy, collect, kill_count, escort}. **Verifikasi akhir Phase 2:** `pytest -q` → **545 passed, 0 failed** (527 Phase 1 + 18 test baru; target absolut ≥555 di §22 tidak tercapai karena baseline repo 527, bukan 537 seperti asumsi spec — seluruh test spec ada, tidak ada yang gagal); `ruff check .` → **All checks passed**.

*— Akhir spesifikasi Season 1. Selanjutnya: persetujuan, lalu implementasi bertahap per arc.*

---

## 22. Rencana Implementasi Terperinci — Phase 2 (Arc 3)

**Lingkup:** Quest012–020, bos Sister Iris, hitung mundur ultimatum di gameplay, dan semua wiring konten Arc 3 yang belum terhubung ke engine.
**Gate kualitas:** `pytest -q` hijau (target ≥ 555 passed, 0 failed); `ruff check .` bersih.

---

### 22.1 Inventaris Gap (temuan dari verifikasi Phase 1)

Berdasarkan inspeksi langsung file data dan engine, berikut gap yang harus diselesaikan di Phase 2.

| Kode | Komponen | Status saat ini | Yang dibutuhkan |
|------|----------|-----------------|-----------------|
| G-01 | `quest012` req `map forest_deep` | Data benar, tapi `forest_deep` butuh `map_forest_deep_unlocked` yang belum diset sebelum Arc 3 | Diset via `event_arc3_gate` setelah `boss_arc2_defeated` |
| G-02 | `quest013` flag `ultimatum_received` | `dialog_iris_intro` semua choices sudah set `ultimatum_received` langsung | Verifikasi via test; tidak perlu perubahan |
| G-03 | `quest017` req `flag have_old_scrolls` | Item `old_scroll` punya `quest_flag: have_old_scrolls`; toko Kael menjual `old_scroll` | Verifikasi bahwa `buy` → `add_item` → `_track_loot_flags` → flag ter-set |
| G-04 | `quest019` req `killed_inquisitor_soldier_3` | Kill-count via flag sudah berjalan; butuh `arc3_started` aktif terlebih dulu | Event `event_arc3_gate` harus ada sebelum quest019 bisa dimulai |
| G-05 | Event `event_arc3_gate` | Belum ada di `events.json` | Tulis event baru (§22.2.1) |
| G-06 | Event `event_arc3_complete` | Belum ada di `events.json` | Tulis event baru (§22.2.1) |
| G-07 | Memory `memory005` | Belum ada di `memories.json` | Tambah entry (§22.2.2) |
| G-08 | Dialog `dialog_marcus_betrayal` | Belum ada — quest018 butuh `talk marcus` sebelum `enemy guild_guard` | File baru (§22.2.3) |
| G-09 | Escort mini quest012 (opsional) | `dialog_tom_escort_go` sudah ada; quest012 tidak punya req escort | Tidak perlu perubahan; konfirmasi via test bahwa dialog berfungsi |
| G-10 | Wiring `process_day_tick` ke `_cmd_rest` | Sudah dipanggil di `_cmd_rest`; `process_events` dipanggil di `run_turn` | Tidak ada perubahan engine; verifikasi via test |
| G-11 | `sister_iris` NPC dialog order | `dialog_iris_defeated` sudah di-list pertama; order benar | Tidak perlu perubahan |
| G-12 | Reward quest020: rune_blade atau rune_plate | Saat ini keduanya chance 100% — keduanya drop | Ubah ke chance 50% masing-masing (§22.2.5) |
| G-13 | `dialog_sera_offer` tidak set `aligned_any` | Pilihan "bekerja sama" hanya set `aligned_rebels` tanpa `aligned_any` | Tambahkan `aligned_any` ke `set_flags` (§22.2.4) |
| G-14 | `test_arc1_content.py` valid_kinds | Set tidak mencakup `collect`, `kill_count`, `escort` — akan gagal di Arc 3+ | Update set valid_kinds (§22.3.1) |

---

### 22.2 Perubahan Data (zero engine change)

#### 22.2.1 `data/events/events.json` — append 2 event

Tambahkan dua objek berikut ke array events.json.

**Event `event_arc3_gate`:**

```json
{
  "id": "event_arc3_gate",
  "trigger": [
    {"kind": "flag", "flag": "boss_arc2_defeated", "value": true},
    {"kind": "flag", "flag": "arc3_started", "operator": "MISSING"}
  ],
  "actions": [
    {"kind": "log", "text": "═══════════════════════════════════════"},
    {"kind": "log", "text": "ARC 3 — PERANG BAYANGAN"},
    {"kind": "log", "text": "Api menyentuh tepi hutan. Inkuisisi sudah bergerak."},
    {"kind": "start_quest", "id": "quest012"},
    {"kind": "set_flag", "flag": "arc3_started", "value": true},
    {"kind": "set_flag", "flag": "map_forest_deep_unlocked", "value": true}
  ]
}
```

Catatan desain: `map_forest_deep_unlocked` diset di event bukan di `quest011.flags_on_complete` agar save lama yang sudah `boss_arc2_defeated=True` langsung mendapat unlock tanpa perlu menyelesaikan quest011 ulang. Guard `arc3_started MISSING` memastikan event hanya terpicu sekali.

**Event `event_arc3_complete`:**

```json
{
  "id": "event_arc3_complete",
  "trigger": [
    {"kind": "flag", "flag": "boss_arc3_defeated", "value": true},
    {"kind": "flag", "flag": "arc3_complete_shown", "operator": "MISSING"}
  ],
  "actions": [
    {"kind": "log", "text": "═══════════════════════════════════════"},
    {"kind": "log", "text": "ARC 3 SELESAI — PERANG BAYANGAN"},
    {"kind": "log", "text": "Sebelum jatuh, Iris menyebut satu nama. Nama itu kini tergantung di udara seperti asap."},
    {"kind": "grant_memory", "id": "memory005"},
    {"kind": "set_flag", "flag": "arc3_complete_shown", "value": true}
  ]
}
```

#### 22.2.2 `data/story/memories.json` — append 1 entry

Tambahkan objek berikut ke array (setelah `memory004`):

```json
{
  "id": "memory005",
  "title": "Kanselir",
  "text": "Sebelum api memadamkan cahaya di matanya, Iris berbisik: 'Varek. Dia yang menyalakan api ini. Waspadalah terhadap mahkota.' Nama itu kini terpatri di dadamu.",
  "flags_set": ["iris_revealed"],
  "acquired_by": {"kind": "event", "event": "event_arc3_complete"}
}
```

#### 22.2.3 `data/dialogues/dialog_marcus_betrayal.json` — file baru

```json
{
  "id": "dialog_marcus_betrayal",
  "require_flags": ["arc3_started"],
  "require_not_flags": ["marcus_betrayal_found"],
  "lines": [
    {"speaker": "marcus", "text": "Pejalan Waktu. Aku... ada yang harus kuakui."},
    {"speaker": "marcus", "text": "Agen kerajaan menemuiku semalam. Mereka menawarkan uang — banyak sekali — untuk tahu di mana letak batu di bawah desa ini."},
    {"speaker": "marcus", "text": "Aku menolak. Tapi mereka tidak pergi dengan tangan kosong — pengawal gilda yang kini berputar di luar itu bukan milik gilda. Mereka dikirim untuk memaksaku."},
    {"speaker": "marcus", "text": "Bantu aku mengusir mereka, dan aku bersumpah tidak akan menjual satu huruf pun tentang desamu."}
  ],
  "choices": [
    {"text": "Kita hadapi mereka bersama.", "require_flags": [], "set_flags": ["marcus_betrayal_found", "marcus_helped"], "next": null},
    {"text": "Aku yang urus ini. Tetaplah di sini.", "require_flags": [], "set_flags": ["marcus_betrayal_found"], "next": null},
    {"text": "Kau harusnya lebih berhati-hati, Marcus.", "require_flags": [], "set_flags": ["marcus_betrayal_found"], "next": null}
  ]
}
```

Setelah membuat file, tambahkan `"dialog_marcus_betrayal"` ke daftar `dialogs` di `data/npc/marcus.json` **sebelum** `"dialog_marcus_main"`:

```json
"dialogs": ["dialog_marcus_quest", "dialog_marcus_betrayal", "dialog_marcus_main"]
```

#### 22.2.4 `data/dialogues/dialog_sera_offer.json` — edit 1 baris

Ubah `set_flags` pilihan pertama (indeks 0) dari:

```json
"set_flags": ["sera_aligned", "aligned_rebels"]
```

menjadi:

```json
"set_flags": ["sera_aligned", "aligned_rebels", "aligned_any"]
```

Flag `aligned_any` bersifat idempoten — bila sudah di-set oleh `event_alias_rebels` (Arc 2), set ulang tidak berpengaruh.

#### 22.2.5 `data/enemies/sister_iris.json` — edit loot chances

Ubah field `loot` dari:

```json
"loot": [
  {"item": "rune_blade", "chance": 100, "amount": 1},
  {"item": "rune_plate", "chance": 100, "amount": 1},
  {"item": "elixir",     "chance": 50,  "amount": 1}
]
```

menjadi:

```json
"loot": [
  {"item": "rune_blade", "chance": 50, "amount": 1},
  {"item": "rune_plate", "chance": 50, "amount": 1},
  {"item": "elixir",     "chance": 50, "amount": 1}
]
```

Rasional: bos langka boleh memberi reward besar, tapi drop keduanya 100% menghilangkan variasi. Chance 50% masing-masing memberi probabilitas ~25% dapat keduanya, ~50% dapat salah satu, ~25% tidak dapat senjata/armor (tetap dapat elixir).

---

### 22.3 Perubahan Engine

Hanya satu perubahan file Python yang diperlukan di Phase 2.

#### 22.3.1 `tests/test_arc1_content.py` — update valid_kinds

Fungsi `test_quest_requirement_kinds` saat ini:

```python
valid_kinds = {"talk", "map", "flag", "enemy"}
```

Perbarui menjadi:

```python
valid_kinds = {"talk", "map", "flag", "enemy", "collect", "kill_count", "escort"}
```

Bukan perubahan logika — hanya menyelaraskan test dengan tiga kind baru yang sudah diimplementasikan di Phase 0 agar suite tidak gagal saat quest Arc 2+ divalidasi.

---

### 22.4 Test Baru: `tests/test_arc3_content.py`

File baru dengan 18 test, semua unit — tidak ada playthrough penuh.

```
tests/test_arc3_content.py

Data integrity (5 test)
  test_arc3_gate_event_exists_and_triggers_quest012
  test_arc3_complete_event_grants_memory005
  test_memory005_exists_with_correct_fields
  test_marcus_betrayal_dialog_exists_and_gated
  test_sister_iris_loot_50_percent_each

Quest chain wiring (5 test)
  test_quest012_completes_via_talk_and_map
  test_quest013_completes_via_iris_talk_and_ultimatum_flag
  test_quest014_unlocks_crime_den_via_quest013_flags
  test_quest019_kill_count_inquisitor_3_via_flags
  test_quest020_boss_iris_completes_arc3

Ultimatum countdown integration (4 test)
  test_rest_advances_day_tick_and_decrements_ultimatum
  test_ultimatum_expires_after_5_rests
  test_expired_ultimatum_fails_arc3_quests_via_process_events
  test_ultimatum_resolved_prevents_auto_fail

Reputation and alignment (2 test)
  test_sera_offer_sets_aligned_any
  test_iris_intro_all_choices_set_ultimatum_received

map_forest_deep gate (2 test)
  test_arc3_gate_sets_map_forest_deep_unlocked
  test_travel_to_forest_deep_blocked_without_unlock
```

#### Spesifikasi tiap test

**Data integrity**

`test_arc3_gate_event_exists_and_triggers_quest012`
Load `ctx.events`; cari objek dengan id `event_arc3_gate`; assert `trigger[0]["flag"] == "boss_arc2_defeated"` dan `trigger[1]["operator"] == "MISSING"` dengan flag `arc3_started`; assert ada action `{"kind": "start_quest", "id": "quest012"}`; assert ada action `set_flag` untuk `arc3_started`.

`test_arc3_complete_event_grants_memory005`
Cari `event_arc3_complete` di `ctx.events`; assert `trigger[0]["flag"] == "boss_arc3_defeated"`; assert ada action `{"kind": "grant_memory", "id": "memory005"}`; assert ada action guard `arc3_complete_shown MISSING`.

`test_memory005_exists_with_correct_fields`
Load `ctx.memories`; cari entry dengan `id == "memory005"`; assert `title` tidak kosong; assert `"Varek"` atau `"Iris"` muncul di field `text`; assert `flags_set` berisi `"iris_revealed"`.

`test_marcus_betrayal_dialog_exists_and_gated`
Load `ctx.dialogues["dialog_marcus_betrayal"]`; assert `require_flags == ["arc3_started"]`; assert `require_not_flags == ["marcus_betrayal_found"]`; assert semua choices memiliki `"marcus_betrayal_found"` di `set_flags`; assert `"dialog_marcus_betrayal"` ada di `ctx.npc["marcus"]["dialogs"]`. **Catatan (koreksi implementasi):** teks draf awal spec keliru menulis `"marcus" in ctx.npc["marcus"]["dialogs"]` — assert itu selalu `False` karena `dialogs` berisi daftar ID *dialog*, bukan ID NPC; assertion yang benar (dan sudah diterapkan) mengecek keanggotaan `"dialog_marcus_betrayal"` seperti di atas.

`test_sister_iris_loot_50_percent_each`
Load `ctx.enemies["sister_iris"]`; untuk item `rune_blade` dan `rune_plate`, assert `entry["chance"] == 50`.

**Quest chain wiring**

`test_quest012_completes_via_talk_and_map`
`make_game()`; set `state.flags["arc3_started"] = True` dan `state.flags["map_forest_deep_unlocked"] = True`; `start_quest(state, "quest012")`; `complete_requirement(state, "talk", "tom")`; `game.run_turn("go forest")` lalu `game.run_turn("go forest_deep")`; assert `"quest012" in state.player.quests_done`; assert `"quest013" in state.player.quests_active`.

`test_quest013_completes_via_iris_talk_and_ultimatum_flag`
`make_game()`; set `state.flags["arc3_started"] = True`; `start_quest(state, "quest013")`; panggil `game.run_turn("talk sister_iris")` (membuka `dialog_iris_intro`); panggil `game.run_turn("1")` (choice 0 intro → lanjut ke `dialog_iris_ultimatum`, set `ultimatum_received`); panggil `game.run_turn("1")` sekali lagi (choice 0 ultimatum → dialog berakhir → syarat `talk` quest013 terpenuhi). **Catatan (koreksi implementasi):** teks draf awal spec ini hanya menyebut 2 `run_turn`; `dialog_iris_intro` choice 0 senyatanya lanjut ke `dialog_iris_ultimatum` (bukan langsung mengakhiri dialog), sehingga dibutuhkan giliran `run_turn` ketiga agar dialog benar-benar berakhir dan syarat `talk` terpenuhi — 3 panggilan `run_turn` di atas sudah mencerminkan alur yang benar. assert `"ultimatum_received" in state.flags`; assert `"quest013" in state.player.quests_done`.

`test_quest014_unlocks_crime_den_via_quest013_flags`
Assert `"map_crime_den_unlocked" in ctx.quests["quest013"]["flags_on_complete"]`; `make_game()`; set `state.flags["map_crime_den_unlocked"] = True`; set `state.current_map = state.world["village"]`; assert `can_travel(state, "crime_den") is True`.

`test_quest019_kill_count_inquisitor_3_via_flags`
`make_game()`; set `state.flags["arc3_started"] = True`; `start_quest(state, "quest019")`; paksa 3 kemenangan `inquisitor_soldier` via `force_victory` (yang memanggil `_track_kills` → set flag `killed_inquisitor_soldier_N`); `clear_level_ups(game)`; assert `"killed_inquisitor_soldier_3" in state.flags`; assert `"quest019" in state.player.quests_done`.

`test_quest020_boss_iris_completes_arc3`
`make_game()`; set `state.flags["arc3_started"] = True`; `start_quest(state, "quest020")`; `force_victory(game, "sister_iris")`; `clear_level_ups(game)`; assert `"boss_arc3_defeated" in state.flags`; `event_engine.process_events(state, game.randomizer)`; assert `"arc3_complete_shown" in state.flags`; assert `memory005_title` muncul di `state.player.memories` (cek field `id == "memory005"`).

**Ultimatum countdown integration**

`test_rest_advances_day_tick_and_decrements_ultimatum`
`make_game()`; set `state.flags["ultimatum_5_days"] = True`; `game.run_turn("rest")`; assert `state.flags.get("ultimatum_days_passed") == 1`; panggil `hud.render(state.player, state)`; assert `"Api dalam 4 hari"` muncul di output HUD.

`test_ultimatum_expires_after_5_rests`
`make_game()`; set `state.flags["ultimatum_5_days"] = True`; loop 5× `game.run_turn("rest")`; assert `"ultimatum_expired" in state.flags`.

`test_expired_ultimatum_fails_arc3_quests_via_process_events`
`make_game()`; `start_quest` untuk q014/q016/q018/q019; set `state.flags["ultimatum_expired"] = True`; `event_engine.process_events(state, game.randomizer)`; assert semua empat quest ada di `state.player.quests_failed`; assert `state.flags.get("ultimatum_failures_applied") is True`.

`test_ultimatum_resolved_prevents_auto_fail`
Sama seperti test di atas tapi tambahkan `state.flags["ultimatum_resolved"] = True` sebelum `process_events`; assert tidak ada quest di `quests_failed` setelah process_events.

**Reputation and alignment**

`test_sera_offer_sets_aligned_any`
Load `ctx.dialogues["dialog_sera_offer"]`; cari choice dengan teks berisi "bekerja sama" atau "pemberontak"; assert `"aligned_any" in choice["set_flags"]`.

`test_iris_intro_all_choices_set_ultimatum_received`
Load `ctx.dialogues["dialog_iris_intro"]`; for tiap choice di `choices`: assert `"ultimatum_received" in choice.get("set_flags", [])` atau `"ultimatum_5_days" in choice.get("set_flags", [])` — membuktikan bahwa setiap jalur percakapan intro Iris mengaktifkan ultimatum.

**map_forest_deep gate**

`test_arc3_gate_sets_map_forest_deep_unlocked`
Load `ctx.events`; cari `event_arc3_gate`; assert ada action `{"kind": "set_flag", "flag": "map_forest_deep_unlocked"}`.

`test_travel_to_forest_deep_blocked_without_unlock`
`make_game()`; set `state.current_map = state.world["forest"]`; assert `travel_system.can_travel(state, "forest_deep") is False` (flag belum ada); set `state.flags["map_forest_deep_unlocked"] = True`; assert `travel_system.can_travel(state, "forest_deep") is True`.

---

### 22.5 Urutan Eksekusi

```
Langkah 1: tests/test_arc1_content.py
  Edit valid_kinds: tambah collect, kill_count, escort.
  Verifikasi: pytest tests/test_arc1_content.py -q

Langkah 2: data/events/events.json
  Append event_arc3_gate dan event_arc3_complete ke array.
  Verifikasi: python3 -c "import json; json.load(open('data/events/events.json'))"

Langkah 3: data/story/memories.json
  Append memory005 ke array (setelah memory004).
  Verifikasi: python3 -c "import json; json.load(open('data/story/memories.json'))"

Langkah 4: data/dialogues/dialog_marcus_betrayal.json + data/npc/marcus.json
  Buat file dialog baru.
  Edit marcus.json: sisipkan dialog_marcus_betrayal sebelum dialog_marcus_main.
  Verifikasi: python3 -c "import json; json.load(open('data/dialogues/dialog_marcus_betrayal.json'))"

Langkah 5: data/dialogues/dialog_sera_offer.json
  Edit set_flags pilihan 0: tambah aligned_any.

Langkah 6: data/enemies/sister_iris.json
  Edit chance rune_blade dan rune_plate dari 100 ke 50.

Langkah 7: tests/test_arc3_content.py
  Tulis 18 test berdasarkan §22.4.

Langkah 8: Validasi akhir
  pytest -q (target >= 555 passed, 0 failed)
  ruff check . (0 violations)
  Update §21 status di spec ini.
```

---

### 22.6 Matriks Dependensi

```
Langkah 1 (test_arc1_content): independen
Langkah 2 (events): independen
Langkah 3 (memories): tidak bergantung ke Langkah 2 tapi Langkah 2 merefer memory005
Langkah 4 (marcus dialog): independen dari 2 dan 3; marcus.json harus diedit setelah file dialog dibuat
Langkah 5 (sera_offer): independen
Langkah 6 (sister_iris loot): independen
Langkah 7 (test_arc3_content): bergantung ke SEMUA langkah 1-6
Langkah 8 (validasi): bergantung ke Langkah 7
```

---

### 22.7 Flag Baru Phase 2

| Flag | Diset oleh | Dibaca oleh |
|------|-----------|-------------|
| `arc3_started` | `event_arc3_gate` | gate dialog Arc 3 (`require_flags`), guard `event_arc3_complete` (MISSING) |
| `arc3_complete_shown` | `event_arc3_complete` | guard idempoten event |
| `map_forest_deep_unlocked` | `event_arc3_gate` | `travel_system.can_travel`, `test_map_requirements_are_unlockable` |
| `marcus_betrayal_found` | `dialog_marcus_betrayal` choices | `require_not_flags` dialog yang sama |
| `marcus_helped` | `dialog_marcus_betrayal` choice 0 | kosmetik — dipakai di epilog q044 |

Flag yang sudah ada dan dipakai Phase 2 (tidak perlu ditulis ulang): `boss_arc2_defeated`, `arc2_started`, `ultimatum_5_days`, `ultimatum_received`, `met_iris`, `boss_arc3_defeated`, `iris_revealed`, `varek_revealed`, `crime_archive`, `have_evidence_letter`, `quest015_resolved`, `sera_aligned`, `aligned_rebels`, `aligned_any`, `ancient_script_decoded`, `village_defended`, `ultimatum_expired`, `ultimatum_resolved`, `ultimatum_failures_applied`.

---

### 22.8 Ringkasan Deliverable Phase 2

| # | File | Aksi | Status |
|---|------|------|--------|
| 1 | `tests/test_arc1_content.py` | Edit 1 baris (valid_kinds) | ✅ selesai (Phase 1) |
| 2 | `data/events/events.json` | Append 2 event | ✅ selesai (event_arc3_gate + event_arc3_complete) |
| 3 | `data/story/memories.json` | Append 1 memory | ✅ selesai (memory005) |
| 4 | `data/dialogues/dialog_marcus_betrayal.json` | File baru | ✅ selesai |
| 5 | `data/npc/marcus.json` | Edit 1 baris (tambah dialog) | ✅ selesai |
| 6 | `data/dialogues/dialog_sera_offer.json` | Edit 1 baris (tambah flag) | ✅ selesai (aligned_any) |
| 7 | `data/enemies/sister_iris.json` | Edit 2 baris (chance 100→50) | ✅ selesai |
| 8 | `tests/test_arc3_content.py` | File baru, 18 test | ✅ selesai (18/18 lulus) |

**Status aktual: 8/8 selesai. Nol perubahan engine Python (src/) — terkonfirmasi.**
**Gate kualitas terpenuhi: `pytest -q` → 545 passed, 0 failed · `ruff check .` 0 violations · smoke `tools/smoke_arc3.py` 30/30 lulus.**
**Phase 2 selesai — lanjut ke Phase 3 (Arc 4).**

