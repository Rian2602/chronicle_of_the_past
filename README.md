<div align="center">

# 🕰️ Chronicle of the Past

*RPG berbasis teks (CLI) tentang perjalanan waktu — di desa yang tak lama lagi akan terbakar.*

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white)
![100% stdlib](https://img.shields.io/badge/100%25-stdlib-4EA94B?style=flat-square)
![Bahasa](https://img.shields.io/badge/Bahasa-Indonesia-1f6feb?style=flat-square)
[![Tests](https://img.shields.io/github/actions/workflow/status/Rian2602/chronicle_of_the_past/ci.yml?style=flat-square&label=tests)](https://github.com/Rian2602/chronicle_of_the_past/actions)
[![License](https://img.shields.io/github/license/Rian2602/chronicle_of_the_past?style=flat-square)](LICENSE)

**Tanpa instalasi tambahan. Tanpa dependensi eksternal. Hanya Python 3.12+.**

</div>

---

Kamu terbangun di tempat asing. Langit tak seperti yang kau kenal. Seorang tua berbisik: *desa ini akan terbakar.* Sebagai Pejalan Waktu, kau harus menulis ulang sejarah — satu pertarungan, satu percakapan, satu kenangan pada satu waktu.

---

## ✨ Fitur Utama

- 🏰 **Perjalanan waktu** — keputusanmu menciptakan *kenangan* dan mengubah arah cerita; **5 arc + 6 ending** berbeda di Season 1.
- ⚔️ **Pertarungan berbasis giliran** — 5 kelas, skill unik (termasuk self-buff: `war_cry`, `arcane_barrier`, `shadow_step`, `time_study`), musuh dengan perilaku berbeda (pengecut, agresif, pertahanan), dan **bos yang tak bisa kabur**.
- 📜 **Cerita & quest** — **45+ quest utama** berjenjang dengan hadiah XP, emas, dan reputasi; quest eksklusif faksi & pilihan yang mengubah alur.
- 🗺️ **Eksplorasi** — **12 peta**: Desa Ashen, Hutan, Reruntuhan 4 lantai, Kamp Pemberontak, Sarang Kriminal, Ibukota, dan Benteng Kerajaan — dengan kemungkinan bertemu musuh (malam lebih berbahaya!).
- 🛒 **Toko** — beli/jual lewat NPC pedagang (diskon berdasar reputasi merchant_guild).
- ⏰ **Siklus waktu & ultimatum** — pagi → siang → sore → malam; di Arc 3, hitung mundur **5 hari** sebelum desa terbakar.
- 💾 **Simpan kapan saja** — bahkan saat bertarung.

---

## 🖼️ Cuplikan Layar

Menu utama:

```
CHRONICLE OF THE PAST
==========================

> Permainan Baru
  Lanjutkan
  Pengaturan
  Kredit
  Keluar
```

Pilih kelas:

```
Warrior
Attack        ████████░░
Defense       ██████████
Hp            ██████████
Mp            ██░░░░░░░░
Agility       ████░░░░░░
Intelligence  ██░░░░░░░░
```

Memulai perjalanan:

```
Kau membuka mata. Langit tampak asing.

Rian — Warrior (Lv 1)
HP 100/100 ██████████████
MP 10/10 ██████████████
Emas: 0   XP: 0
Lokasi: Ashen Village   Waktu: morning
```

Jelajahi desa:

```
    ####
   # @  #
  #  /\  #
 #__/  \__#
 |   ##   |
 | *    * |
  \______/

Desa kecil yang hangat. Orang-orang memandangmu dengan curiga.
Jalan keluar: forest
Di sini ada: Aria, Kepala Desa
```

Bertemu Aria, penjaga perpustakaan tua:

```
Aria:
+------------------------------------+
| Kau... Aku belum pernah melihatmu. |
+------------------------------------+

Aksi:
> Siapa Anda?
  Pergi.
```

...dan jalannya sejarah mulai terbentuk:

```
Quest dimulai: Temui Kepala Desa.
Kenangan terbuka: Desa Terbakar.
Quest dimulai: Bahaya di Hutan.
```

Bertarung dan menangkan Arc 1:

```
Quest selesai: Bahaya di Hutan. Hadiah: 40 XP, 15 emas, 5 reputasi merchant_guild.
Kamu menyerang Wild Wolf, -13 HP.
Kamu mendapat 40 XP dan 13 emas.
Kemenangan!
═══════════════════════════════════════
PERCABANGAN WAKTU — Kamu merasakan sesuatu bergeser.
Sejarah mulai terbentuk ulang di tanganmu, Pejalan Waktu.
Arc 1 selesai. Jalanmu selanjutnya menanti...
═══════════════════════════════════════
Kenangan terbuka: Sihir Terlarang.
```

---

## 🚀 Cara Menjalankan

```bash
git clone https://github.com/Rian2602/chronicle_of_the_past.git
cd chronicle_of_the_past
python3 launcher.py
```

**Windows** (Terminal / PowerShell / cmd):
```bash
py launcher.py
```

**macOS / Linux** (Terminal):
```bash
python3 launcher.py
```

- **Belum punya Python 3.12+?** Unduh dari [python.org](https://www.python.org/downloads/). Saat instalasi di Windows, centang **"Add Python to PATH"**. Verifikasi dengan `python3 --version` (atau `py --version` di Windows).
- **Tanpa `git`?** Unduh ZIP dari halaman repo, ekstrak, lalu jalankan `launcher.py` dari folder tersebut.
- Virtual environment bersifat opsional — game ini **murni pustaka standar Python**, tanpa instalasi paket tambahan.

### 🖥️ Kompatibilitas & Persyaratan

| Kebutuhan | Detail |
|-----------|--------|
| Python | **3.12 atau lebih baru** (wajib; versi lama tidak didukung) |
| Sistem | Windows 10/11, macOS, atau Linux (semua distro) |
| Terminal | Jendela terminal/console apa pun; **minimal lebar ±60 kolom** untuk tampilan terbaik |
| Keyboard | Arrow key (↑/↓) *atau* tombol `w`/`s` untuk navigasi — dua-duanya didukung |
| Tampilan karakter | Di Windows otomatis memakai **ASCII** (kompatibel semua console); di macOS/Linux otomatis Unicode bila terminal mendukung. Ganti manual kapan saja di menu **Pengaturan → Tampilan** |

> 💡 **Laptop jadul / terminal aneh?** Buka **Pengaturan** di menu utama, set **Tampilan** ke `ASCII` dan **Animasi** ke `Mati` — game tetap berjalan mulus di mana pun.

---

## 🎮 Cara Bermain

Navigasi menu utama dengan `W`/`S` (atau `K`/`J`), tekan `Enter` untuk memilih, `Q` untuk keluar.

Selama bermain, ketik perintah dan tekan `Enter`. Jika namamu dibiarkan kosong saat memulai, kamu akan dipanggil **Pejalan Waktu**.

| Menu | Fungsi |
|------|--------|
| Permainan Baru | Mulai petualangan baru (tentukan nama & kelas) |
| Lanjutkan | Muat file save (default `saves/slot1.json`) |
| Pengaturan | Atur karakter UI (Auto/Unicode/ASCII) dan animasi startup (Normal/Cepat/Mati) |
| Kredit | Info pembuatan game |
| Keluar | Tutup game |

Pengaturan berlaku untuk semua slot dan disimpan di `saves/settings.json`. Pilih **Reset ke Default** untuk mengembalikan Tampilan ke `Auto` dan Animasi ke `Normal`.

---

## 🛡️ Kelas

| Kelas | Skill Awal | Biaya MP Skill | HP | MP | Gaya |
|-------|-----------|----------------|-----|-----|------|
| **Warrior** | `slash` (fisik) | 4 | 100 | 10 | Tangguh, pertahanan tinggi |
| **Assassin** | `backstab` (fisik + pendarahan) | 5 | 65 | 12 | Cepat, fisik & status |
| **Mage** | `fireball` (sihir 12 dmg) | 8 | 60 | 55 | Sihir murni, MP besar |
| **Ranger** | `quick_shot` (fisik 7 dmg) | 6 | 75 | 20 | Seimbang, serba bisa |
| **Scholar** | `inspect` (sihir analisis) | 5 | 75 | 45 | Bonus XP 1.2× — naik level lebih cepat |

Skill biasa `bite` (bawaan musuh) tidak berbiaya MP. Level-up memulihkan HP/MP penuh dan menambah stat — bonus stat **dipilih sendiri oleh pemain** (Serangan/Pertahanan/Kelincahan/Kecerdasan/HP/MP/Skill Point) — juga memberi kenangan baru seiring cerita.

---

## ⌨️ Perintah

**Perintah umum:**

| Perintah | Fungsi |
|----------|--------|
| `status` | Lihat stat, perlengkapan, dan XP |
| `look` | Deskripsi lokasi + ASCII art + jalan keluar |
| `go <dest>` | Pindah lokasi (mis. `go forest`) |
| `explore` | Jelajahi lokasi — bisa memicu pertarungan |
| `talk <nama>` | Ajak bicara NPC — ID *atau* nama (mis. `talk Aria`) |
| `memories` | Lihat kenangan yang telah terbuka |
| `rest` | Tidur hingga pagi (Hari berikutnya, HP/MP penuh) |
| `inv` / `inventory` | Lihat isi tas |
| `use <item>` | Pakai item (mis. `use potion`) |
| `equip <item>` / `unequip <item>` | Kenakan / lepas perlengkapan |
| `save <path>` | Simpan permainan (mis. `save saves/slot1.json`) |
| `load <path>` | Muat permainan (tanpa path → default `saves/slot1.json`) |
| `quit` | Keluar ke menu utama |

**Saat bicara dengan pedagang:**

| Perintah | Fungsi |
|----------|--------|
| `shop` | Buka toko NPC (menu beli/jual) — atau pilih **Berbelanja** di dialog |
| `buy <item> [jumlah]` | Beli item dari toko (mis. `buy potion 3`) |
| `sell <item> [jumlah]` | Jual item ke NPC dengan harga × `sell_multiplier` (mis. `sell herb`) |

> Semua perintah di atas juga bisa dipilih lewat **menu** — tidak wajib mengetik.
> Hint toko muncul di HUD: **"🛒 Toko tersedia: ..."** saat kamu berada di peta yang punya pedagang.

**Saat bertarung:**

| Perintah | Fungsi |
|----------|--------|
| `attack` | Serangan fisik dasar |
| `skill <id>` / `magic <id>` | Gunakan skill / sihir kelas |
| `item <id>` | Gunakan item pemulih |
| `observe` | Amati musuh (buka kelemahan & lore) |
| `defend` | Bertahan — kurangi damage giliran ini |
| `escape` | Kabur dari pertarungan |

**Selama dialog**, ketik angka pilihan (mis. `1`) untuk merespons. Angka di luar dialog akan membalas *"Tidak ada dialog aktif."*

> 💡 **Harga jual** = harga dasar item × `sell_multiplier` NPC (biasanya 0.5). **Diskon beli** naik bersama reputasi merchant_guild — makin tinggi reputasimu, makin murah belanjamu.

---

## 📖 Cerita — Season 1: "Jangkar Waktu"

Desa Ashen dibangun di atas **Jangkar Waktu** — artefak kuno yang mampu *menulis ulang sejarah*. Kebakaran yang diramalkan Aria bukan sekadar bencana: itu **Pembersihan** yang dikirim dari ibukota kerajaan Ashenfeld, didalangi **Kanselir Varek**, penasihat raja yang mengincar kekuatan Jangkar.

Kamu, sang **Pejalan Waktu**, terseret lintas waktu ke masa ini karena Jangkar terganggu. Di tengah intrik **7 faksi** — kerajaan, gereja, pemberontak, gilda dagang, akademisi, penjaga kuno, dan kriminal — kau harus mengungkap sejarah asli Jangkar lewat **echo** (kilas balik), lalu **memutuskan nasibnya**: 6 ending berbeda menantimu.

| Arc | Judul | Quest | Inti |
|-----|-------|-------|------|
| 1 | Prolog | q001–q002 | Bangun di Desa Ashen; desa akan terbakar |
| 2 | **Jangkar Waktu** | q003–q011 | Ruang rahasia perpustakaan; mata-mata kerajaan; reruntuhan kuno; bos **Kapten Reiner** |
| 3 | **Perang Bayangan** | q012–q020 | Gereja memberi ultimatum **5 hari**; pemberontak & gilda bergerak; bos **Sister Iris** |
| 4 | **Reruntuhan Waktu** | q021–q029 | Tiga segel dibuka; echo besar; ibukota; bos **Penjaga Waktu** |
| 5 | **Sejarah Baru** | q030–q045 | Pengepungan, Varek terungkap, **6 ending** (A–F) |

**7 faksi aktif:** royal_army, church, rebels, merchant_guild, scholar_society, ancient_order, crime — reputasimu dengan mereka membuka quest eksklusif, sekutu, dan menentukan ending.

---

### 📖 Cerita — Arc 1

Kau bangun di **Desa Ashen** tanpa ingatan. Di sana, **Aria** — penjaga perpustakaan tua — memperingatkanmu bahwa desa akan terbakar. **Kepala Desa** khawatir serigala liar mulai berani mendekati tepi hutan. Dua pertanyaan menggantung: siapa dirimu, dan apa yang menantimu di dalam Hutan Ashen?

---

## 🧭 Walkthrough Arc 1

> Hint: angka di dalam dialog dijawab dengan mengetik nomornya.

1. **`talk old_man`** → pilih **1** ("Siapa Anda?") — kenali Aria; lanjutkan pilihan **1** hingga ia mengingatkan soal kebakaran. → *Quest "Temui Kepala Desa" dimulai* & *Kenangan "Desa Terbakar" terbuka.*
2. **`talk village_chief`** → pilih **1** ("Aku akan berusaha..."). → *Quest "Temui Kepala Desa" selesai*: **+50 XP, +20 emas, +10 reputasi merchant_guild** — dan level up! *Quest "Bahaya di Hutan" dimulai.*
3. **`go forest`** — perjalanan memajukan waktu ke siang.
4. **`explore`** — bertarunglah melawan **Wild Wolf** (Lv 3, HP 18; hadiah 40 XP & 8–16 emas; drop umum herb 50%, kadang leather_armor 10%).
   - Lawan lain: **Goblin** (Lv 2, HP 10; 30 XP, 6–12 emas; drop herb 25%, wooden_helmet 5%) dan **Bandit** (Lv 4, HP 28; 70 XP, 15–30 emas; drop potion 30%, iron_sword 15%) — bandit agresif, jangan meremehkannya.
5. Kalahkan serigala → *"Bahaya di Hutan" selesai*: **+40 XP, +15 emas, +5 reputasi** → banner **PERCABANGAN WAKTU** muncul, dan *Kenangan "Sihir Terlarang" terbuka.* Arc 1 tuntas.

---

## 🧭 Walkthrough Arc 2 — Jangkar Waktu (q003–q011)

> Setelah banner **PERCABANGAN WAKTU**, event `arc2_gate` otomatis memulai q003. Level target: Lv 8–10.

1. **`talk old_man`** (Aria) → pilih **1** → q003 *"Gema di Bawah Perpustakaan"* dimulai. Kalahkan **royal_scout** (explore di village/forest) → selesai, **+60 XP, +20 emas, +5 ancient_order**. `anchor_vault` terbuka.
2. **`go anchor_vault`** → q004 *"Batu yang Berdenyut"* selesai (**+50 XP**). Kembali ke village.
3. **`talk finn`** → pilih tangkap (**1**) atau lepas (**2**) → q005 *"Utusan dari Ibukota"* selesai (**+60 XP**); `forest_deep` terbuka. *(Keputusan ini memengaruhi Arc 4: `finn_freed` → bantuan Finn; `finn_arrested` → info dari Lyra.)*
4. **`go forest` → `go forest_deep`** → kalahkan **mercenary_soldier** ×2 → q006 *"Darah di Hutan Dalam"* selesai (**+80 XP, +25 emas**).
5. **q007 *"Pilihan Aliansi"*** — pilih satu faksi untuk diajak kerja sama: `talk lyra` (ancient_order) / `talk sera` di forest_deep (rebels) / `talk marcus` (merchant_guild) / `talk kael` (scholar_society). **+70 XP, +10 reputasi** faksi pilihan.
6. **`go crime_den`** (atau `talk kade` via dialog) → q008 *"Punggung Pisau"*: terima tawaran / tolak & serang `thug` ×2 / nego harga. **+80 XP, +30 emas**, dan nama **Varek** pertama kali disebut.
7. **`go ruins_entrance`** → q009 *"Dinding Reruntuhan"*: kalahkan **ruins_scavenger** sampai dapat `rune_key` (drop 40%). **+70 XP**; `ancient_ruins` terbuka.
8. **`go ancient_ruins`** → `talk ancient_spirit` → kalahkan **ruins_scavenger** ×3 → q010 *"Reruntuhan Berbisik"* selesai (**+90 XP**) + **Echo 1** terbuka (memory003).
9. **BOS Arc 2:** kalahkan **captain_reiner** (Lv 10, tak bisa kabur) → q011 selesai (**+150 XP, +60 emas**, pilih `steel_sword` / `chain_armor`). Banner **ARC 2 SELESAI** + Kenangan *"Nama Varek"* (memory004).

---

## 🧭 Walkthrough Arc 3 — Perang Bayangan (q012–q020)

> Event `arc3_gate` otomatis memulai q012 setelah `boss_arc2_defeated`. **Level target: Lv 15–17.**
> ⚠️ **Ultimatum 5 hari** dimulai di q013 — setiap `rest` menghabiskan 1 hari. Kalau habis sebelum q032, quest yang belum selesai (q014/q016/q018/q019) **gagal otomatis**.

1. **`talk tom`** → pilih temani (1) → q012 *"Api di Tepi Hutan"*; lalu **`go forest` → `go forest_deep`** → selesai (**+80 XP**).
2. **`talk sister_iris`** → pilih sikap → **ultimatum 5 hari aktif** (HUD: *"🔥 Api dalam N hari"*) → q013 *"Gereja yang Menghakimi"* selesai (**+80 XP**). `crime_den` terbuka.
3. **`go crime_den`** → `talk kade` → q014 *"Sarang Serigala Malam"* selesai (**+90 XP, +35 emas**) + item bukti `evidence_letter`.
4. **q015 *"Harga Sebuah Nama"*** — keputusan besar #1: `talk lyra` → pilih bocorkan / rahasiakan. Selesai (**+100 XP**); `rebel_camp` terbuka.
5. **`go forest` → `go forest_deep` → `go rebel_camp`** → `talk sera` → q016 *"Kamp Pemberontak"* selesai (**+100 XP, +10 rebels**).
6. **q017 *"Sketsa dari Akademi"*** — kumpulkan **2× `old_scroll`** (drop `ruins_scavenger` 25% / `time_wraith` 50%, atau beli di toko Kael 30g) → `talk kael` → selesai (**+100 XP, +10 scholar_society**).
7. **`talk marcus`** → dialog pengkhianatan → kalahkan **guild_guard** → q018 *"Pengkhianatan di Pasar"* selesai (**+110 XP, +40 emas**).
8. **q019 *"Malam Serigala"*** — kalahkan **inquisitor_soldier** ×3 (di village/forest) → selesai (**+120 XP**).
9. **BOS Arc 3:** kalahkan **sister_iris** (Lv 15, tak bisa kabur) → q020 *"Api Hakim"* selesai (**+200 XP, +70 emas**, pilih `rune_blade` / `rune_plate`). Banner **ARC 3 SELESAI** + Kenangan *"Kanselir"* (memory005); `ruins_depth` terbuka.

---

## 🛒 Toko

Buka toko dengan **`shop`** saat bicara dengan pedagang, atau pilih **Berbelanja** di dialog. HUD menampilkan *"🛒 Toko tersedia"* di peta berpedagang.

| Pedagang | Lokasi | Jual |
|----------|--------|------|
| **Marcus** | village | potion 25g, elixir 80g, steel_sword 120g, chain_armor 150g |
| **Helen** | village | herb 10g, potion 25g, elixir 80g |
| **Ben** | village | iron_sword 60g, steel_sword 120g, leather_armor 45g, chain_armor 150g, iron_helmet 70g |
| **Prof. Kael** | village | old_scroll 30g, time_tincture 60g |
| **Mira** | capital | potion 25g, elixir 80g |
| **Brock** | capital | steel_sword 120g, rune_blade 320g, chain_armor 150g, rune_plate 380g, rune_crown 260g |
| **Yara** | capital | potion 25g, elixir 80g, time_tincture 60g, smoke_bomb 40g |

**Diskon reputasi:** merchant_guild ≥ 10 → opsi nego harga di q008; merchant_guild ≥ **15** → diskon beli **−15%** di semua toko berfaksi merchant_guild (Marcus saja — Kael berfaksi scholar_society, tanpa diskon).

---

## ⚔️ Tips Bertarung

- **Wild Wolf itu pengecut.** Saat HP-nya < 20%, ia *mencoba kabur tapi gagal* — gilirannya terbuang percuma. Manfaatkan momen itu untuk menyerang gratis.
- **Scholar** naik level 20% lebih cepat — pilihan tepat untuk eksplorasi santai.
- **Mage** kuat melawan musuh ber-defence rendah, tapi MP-nya habis cepat — bawa potion.
- **Istirahat** memulihkan segalanya dan memajukan satu hari; jangan ragu `rest` sebelum menantang bandit.
- Musuh punya **kelemahan**: pertahanan rendah → rentan fisik; kecerdasan rendah → rentan sihir. Cek dengan skill `inspect`.

---

## ⚙️ Sistem Inti

- **Waktu:** pagi → siang → sore → malam, lalu berulang. `go` memajukan satu fase; `rest` melompat ke pagi hari berikutnya.
- **Level:** butuh `50 × level` XP. Saat naik level, kamu **memilih sendiri bonus stat** (Serangan/Pertahanan/Kelincahan/Kecerdasan/HP/MP/Skill Point) — baik dari quest maupun kemenangan bertarung — lalu HP/MP dipulihkan penuh.
- **Ekonomi:** kumpulkan emas dari hadiah & jarahan, belanjakan di **toko** (7 pedagang). Harga jual = harga dasar × 0.5; diskon beli naik bersama reputasi merchant_guild.
- **Item:** konsumabel — Herb (20 HP), Potion (50 HP), Elixir (500 HP), **Time Tincture** (MP penuh), **Smoke Bomb** (kabur pasti berhasil); gear bertier — Iron → **Steel** (+12 atk) → **Rune** (+18 atk) → **Epic** (`time_edged_blade` +25 atk).
- **Skill baru (lewat Skill Point / level-up):** `shield_bash` & `war_cry` (Warrior), `frost_bolt` & `arcane_barrier` (Mage), `poison_blade` & `shadow_step` (Assassin), `multishot` & `snare` (Ranger), `lore_strike` & `time_study` (Scholar).
- **Reputasi faksi:** hadiah quest & pilihan dialog menaikkan reputasi per faksi; ambang tertentu membuka quest eksklusif, sekutu di Arc 5, dan ending (A: ancient_order ≥ 25, B: rebels ≥ 25, C: royal_army ≥ 20 + raja sadar, D: scholar_society ≥ 25, E: selalu, F: semua echo + `rewrite_key`).
- **Echo & ultimatum:** scene echo memberi kenangan + flag `echo_N_collected`; kumpulkan semua echo → `rewrite_key` → ending F (rahasia).
- **Menyimpan:** `save <path>` menulis ke file (menu **Simpan** memakai `saves/slot1.json`); `load <path>` memuatnya kembali (default `saves/slot1.json`). Save saat bertarung juga didukung — keadaan pertarungan ikut dipulihkan.

---

## ❓ FAQ

- **Bisa kalah permanen?** Tidak ada *game over*. Jika gugur, kamu kembali ke peta dengan HP 0 — cukup `rest` untuk pulih sepenuhnya.
- **Kenapa aku dapat kenangan?** Kenangan adalah jejak keputusanmu sebagai Pejalan Waktu. Setiap kenangan membentuk ulang jalan cerita — dan echo yang terkumpul bisa membuka ending rahasia.
- **XP quest tidak langsung menaikkan level?** Sudah tidak berlaku — XP dari quest maupun pertarungan kini langsung memicu level-up saat itu juga.
- **Bagaimana cara berbelanja?** Bicaralah dengan pedagang (`marcus`, `helen`, `ben`, `kael` di desa; `mira`, `brock`, `yara` di ibukota) lalu ketik `shop` atau pilih **Berbelanja** di dialog. HUD menampilkan hint *"🛒 Toko tersedia"*.
- **Apa itu hitung mundur "Api dalam N hari"?** Ultimatum gereja (q013): 5 hari game sebelum desa terbakar. Setiap `rest` mengurangi 1 hari — selesaikan quest Arc 3 sebelum habis.
- **Berapa banyak ending?** **6 ending** (A–F) di Arc 5, ditentukan reputasi faksi & keputusan besar.
- **Kredit?** Pilih "Kredit" di menu utama.

---

## 🛠️ Pengembangan

- **Persyaratan:** Python 3.12+ (pustaka standar saja).
- **Gaya kode:** mengikuti [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html) — baris ≤ 80 karakter, docstring berformat Google, import terurut.
- **Lint & format:** `ruff check src launcher.py tools tests` dan `ruff format --check src launcher.py tools tests` (konfigurasi di `pyproject.toml`).
- **Uji:** `pytest -q` (uji dijalankan otomatis oleh CI pada setiap push/PR).
- **Smoke test CLI (tmux):** `bash tools/smoke_menu.sh` — memverifikasi menu "Muat" & level-up interaktif di terminal nyata (butuh `tmux` di sistem lokal).
- **Playtest Arc 1:** `python3 tools/playtest_arc1.py --count 20 --all-classes` — simulasi playthrough otomatis untuk memastikan keseimbangan tetap memungkinkan menyelesaikan Arc 1.
- **Smoke test Arc 3:** `PYTHONPATH=. python3 tools/smoke_arc3.py` — verifikasi end-to-end rantai quest q012–q020 (gate → ultimatum → boss Iris → memory005).
- **Lisensi:** [MIT](LICENSE) © 2026 Rian2602.

*Dibuat dengan Python dan semangat bercerita. Selamat berkelana, Pejalan Waktu.* 🕰️
