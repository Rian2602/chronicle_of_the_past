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

- 🏰 **Perjalanan waktu** — keputusanmu menciptakan *kenangan* dan mengubah arah cerita, hingga percabangan waktu terbuka di akhir Arc 1.
- ⚔️ **Pertarungan berbasis giliran** — 5 kelas, skill unik, musuh dengan perilaku berbeda (pengecut, agresif, pertahanan).
- 📜 **Cerita & quest** — dialog bernas, quest berjenjang dengan hadiah XP, emas, dan reputasi.
- 🌲 **Eksplorasi** — Desa Ashen dan Hutan Ashen, dengan kemungkinan bertemu musuh (malam hari lebih berbahaya!).
- ⏰ **Siklus waktu** — pagi → siang → sore → malam; bertualang atau beristirahat.
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
Pilihan:
  1. Siapa Anda?
  2. Pergi.
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

- **Windows:** gunakan `py launcher.py`.
- **Tanpa `git`?** Unduh ZIP dari halaman repo, ekstrak, lalu jalankan `python3 launcher.py` dari folder tersebut.
- Virtual environment bersifat opsional — game ini murni pustaka standar Python.

---

## 🎮 Cara Bermain

Navigasi menu utama dengan `W`/`S` (atau `K`/`J`), tekan `Enter` untuk memilih, `Q` untuk keluar.

Selama bermain, ketik perintah dan tekan `Enter`. Jika namamu dibiarkan kosong saat memulai, kamu akan dipanggil **Pejalan Waktu**.

| Menu | Fungsi |
|------|--------|
| Permainan Baru | Mulai petualangan baru (tentukan nama & kelas) |
| Lanjutkan | Muat file save (default `saves/slot1.json`) |
| Pengaturan | Belum tersedia (datang di pembaruan berikutnya) |
| Kredit | Info pembuatan game |
| Keluar | Tutup game |

---

## 🛡️ Kelas

| Kelas | Skill Awal | MP | Gaya |
|-------|-----------|----|------|
| **Warrior** | `slash` (serangan fisik) | 4 | Tangguh, pertahanan tinggi |
| **Assassin** | `backstab` (fisik + pendarahan) | 5 | Cepat, fisik & status |
| **Mage** | `fireball` (sihir 12 dmg) | 8 | Sihir murni, MP besar |
| **Ranger** | `quick_shot` (fisik 7 dmg) | 6 | Seimbang, serba bisa |
| **Scholar** | `inspect` (sihir analisis) | 5 | Bonus XP 1.2× — naik level lebih cepat |

Skill biasa `bite` (bawaan musuh) tidak berbiaya MP. Level-up memulihkan HP/MP penuh dan menambah stat — juga memberi kenangan baru seiring cerita.

---

## ⌨️ Perintah

**Perintah umum:**

| Perintah | Fungsi |
|----------|--------|
| `status` | Lihat stat, perlengkapan, dan XP |
| `look` | Deskripsi lokasi + ASCII art + jalan keluar |
| `go <dest>` | Pindah lokasi (mis. `go forest`) |
| `explore` | Jelajahi lokasi — bisa memicu pertarungan |
| `talk <id>` | Ajak bicara NPC (mis. `talk old_man`) |
| `memories` | Lihat kenangan yang telah terbuka |
| `rest` | Tidur hingga pagi (Hari berikutnya, HP/MP penuh) |
| `inv` / `inventory` | Lihat isi tas |
| `use <item>` | Pakai item (mis. `use potion`) |
| `equip <item>` / `unequip <item>` | Kenakan / lepas perlengkapan |
| `save` / `load` | Simpan / muat permainan (default `saves/slot1.json`) |
| `quit` | Keluar ke menu utama |

**Saat bertarung:**

| Perintah | Fungsi |
|----------|--------|
| `attack` | Serangan fisik dasar |
| `skill` | Gunakan skill kelas |
| `use <item>` | Gunakan item pemulih |
| `flee` | Kabur dari pertarungan |

**Selama dialog**, ketik angka pilihan (mis. `1`) untuk merespons. Angka di luar dialog akan membalas *"Tidak ada dialog aktif."*

---

## 📖 Cerita — Arc 1

Kau bangun di **Desa Ashen** tanpa ingatan. Di sana, **Aria** — penjaga perpustakaan tua — memperingatkanmu bahwa desa akan terbakar. **Kepala Desa** khawatir serigala liar mulai berani mendekati tepi hutan. Dua pertanyaan menggantung: siapa dirimu, dan apa yang menantimu di dalam Hutan Ashen?

---

## 🧭 Walkthrough Arc 1

> Hint: angka di dalam dialog dijawab dengan mengetik nomornya.

1. **`talk old_man`** → pilih **1** — kenali Aria. Lanjutkan pilihan **1** hingga ia mengingatkan soal kebakaran. → *Quest "Temui Kepala Desa" dimulai* & *Kenangan "Desa Terbakar" terbuka.*
2. **`talk village_chief`** → pilih **1** ("Aku bisa membantu..."). → *Quest "Temui Kepala Desa" selesai*: **+50 XP, +20 emas, +10 reputasi merchant_guild** — dan level up! *Quest "Bahaya di Hutan" dimulai.*
3. **`go forest`** — perjalanan memajukan waktu ke siang.
4. **`explore`** — bertarunglah melawan **Wild Wolf** (Lv 3, HP 18; hadiah 40 XP & 8–16 emas; drop umum herb 50%, kadang leather_armor 10%).
   - Lawan lain: **Goblin** (Lv 2, HP 10; 30 XP, 6–12 emas; drop herb 25%, wooden_helmet 5%) dan **Bandit** (Lv 4, HP 28; 70 XP, 15–30 emas; drop potion 30%, iron_sword 15%) — bandit agresif, jangan meremehkannya.
5. Kalahkan serigala → *"Bahaya di Hutan" selesai*: **+40 XP, +15 emas, +5 reputasi** → banner **PERCABANGAN WAKTU** muncul, dan *Kenangan "Sihir Terlarang" terbuka.* Arc 1 tuntas.

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
- **Level:** butuh `50 × level` XP. Naik level = HP/MP penuh, stat naik, dan berlaku langsung — baik dari quest maupun kemenangan bertarung.
- **Ekonomi:** kumpulkan emas dari hadiah & jarahan. Toko belum tersedia — tabung untuk pembaruan berikutnya.
- **Item:** Herb (pulihkan 20 HP), Potion (pulihkan 50 HP), Iron Sword, Leather Armor, Wooden Helmet.
- **Menyimpan:** `save` menulis ke `saves/slot1.json` (bisa diganti via `load`). Save saat bertarung juga didukung — keadaan pertarungan ikut dipulihkan.

---

## ❓ FAQ

- **Bisa kalah permanen?** Tidak ada *game over*. Jika gugur, kamu kembali ke peta dengan HP 0 — cukup `rest` untuk pulih sepenuhnya.
- **Kenapa aku dapat kenangan?** Kenangan adalah jejak keputusanmu sebagai Pejalan Waktu. Setiap kenangan membentuk ulang jalan cerita.
- **XP quest tidak langsung menaikkan level?** Sudah tidak berlaku — XP dari quest maupun pertarungan kini langsung memicu level-up saat itu juga.
- **Di mana tokonya?** Belum ada di versi ini. Simpan emasmu untuk pembaruan berikutnya.
- **Kredit?** Pilih "Kredit" di menu utama.

---

## 🛠️ Pengembangan

- **Persyaratan:** Python 3.12+ (pustaka standar saja).
- **Uji:** `pytest -q` (uji dijalankan otomatis oleh CI pada setiap push/PR).
- **Lisensi:** [MIT](LICENSE) © 2026 Rian2602.

*Dibuat dengan Python dan semangat bercerita. Selamat berkelana, Pejalan Waktu.* 🕰️
