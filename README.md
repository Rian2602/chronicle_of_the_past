╔══════════════════════════════════════════════════════════════╗
║              CHRONICLE OF THE PAST                          ║
║        ───  RPG Kultivasi Fantasi Gelap  ───               ║
╚══════════════════════════════════════════════════════════════╝

[![]()]()
> **Petualangan teks CLI yang mencekam.** Sebuah dunia fantasi gelap tempat
> kekuatan kultivasi disalahgunakan untuk menindas, dan takdir seluruh benua
> bergantung pada pilihanmu.

---

## 📜 Daftar Isi

- [Tentang Game](#-tentang-game)
- [Kisah & Latar](#-kisah--latar)
- [Fitur Utama](#-fitur-utama)
- [Persyaratan Sistem](#-persyaratan-sistem)
- [Instalasi](#-instalasi)
- [Memulai](#-memulai)
- [Perintah Dasar](#-perintah-dasar)
- [Konten Game](#-konten-game)
- [Struktur Proyek](#-struktur-proyek)
- [Pengembangan](#-pengembangan)
- [Lisensi](#-lisensi)

---

## 🎮 Tentang Game

**Chronicle of the Past** adalah RPG teks (*text-based RPG*) bertema kultivasi
fantasi gelap (*grimdark cultivation fantasy*). Berjalan sepenuhnya di terminal
(CLI), game ini menggabungkan narasi bercabang yang mendalam dengan sistem
kultivasi kompleks terinspirasi dari genre *xianxia/wuxia*.

Dikembangkan dengan **Python 3.12+** dan diperkaya oleh **Rich** + **Textual**
untuk pengalaman terminal yang hidup — tanpa perlu GPU, tanpa instalasi berat,
cukup terminal dan imajinasi.

> "Di dunia ini, tidak ada pemenang yang bersih. Hanya yang bertahan — dan
> yang diingat."

---

## 📖 Kisah & Latar

Ashenfeld, sebuah dunia di mana kekuatan kultivasi — *qi* — adalah segalanya.
Namun alih-alih membebaskan umat manusia, kekuatan ini justru menjadi alat
penindasan. Orde Suci menguasai kerajaan dengan tangan besi, Pemberontak
berjuang dengan cara yang tak kalah kejam, dan di balik semua itu, *sesuatu*
yang lebih tua dari peradaban telah menunggu — sejak sebelum desa pertama
berdiri.

Kau adalah **Akar**, seorang pemuda dari Desa Emberfall yang terbangun dengan
kekuatan aneh di dalam tubuhmu. Kekuatan yang tidak diundang. Kekuatan yang
membuatmu menjadi buruan. Kekuatan yang mungkin — hanya mungkin — cukup untuk
mengubah segalanya.

Perjalananmu membawamu melewati **4 babak (Arc)**:

| Arc | Judul | Wilayah | Level |
|-----|-------|---------|-------|
| 1 | *Desa Emberfall & Hutan Ashfall* | Hutan kelabu, makam kuno, reruntuhan kuil | Pengumpul Qi |
| 2 | *Sekte Azure & Kota Guild* | Kota bawah tanah, markas penyelundup, jurang abyssal | Pendiri Fondasi |
| 3 | *Antara Dua Langit* | Katedral Orde Suci, markas Pemberontak, gua abyssal | Pemecah Kehampaan |
| 4 | *Penyegelan Langit & Epilog* | Ibu kota, ruang bawah tanah kuno, puncak penyegelan | Penantang Surga |

**Setiap keputusanmu akan menentukan akhir dunia ini.**

---

## ✨ Fitur Utama

### 🗺️ Dunia yang Hidup
- **12 peta** unik — dari Desa Emberfall hingga Puncak Penyegelan Langit
- **45 quest** (32 utama + 13 faksi) dengan narasi bercabang
- **21 NPC** dengan dialog mendalam dan konsekuensi nyata

### ⚔️ Sistem Pertarungan
- **Turn-based** dengan 4 anggota party (termasuk binatang roh)
- **Siklus 5 elemen** (Metal → Kayu → Tanah → Air → Api → Metal) — damage multiplier 0.7×/1.5×
- **36 teknik** kultivasi yang bisa dipelajari dan dikombinasikan
- **28 musuh** termasuk 7 bos unik dengan mekanik spesial

### 🧘 Kultivasi & Progresi
- **6 tingkatan** (Pengumpul Qi → Penantang Surga)
- **Breakthrough** berbasis insight + material langka
- **Alkimia:** 14 resep pil, ramuan, dan eliksir

### 🐉 Binatang Roh & Formasi
- Rekrut, rawat, dan evolusikan binatang roh
- **Formasi pertempuran** dengan buff tim & skill spesial
- Sistem ikatan (*bond*) yang tumbuh seiring pertempuran

### 🏛️ Faksi & Reputasi
- 5 faksi dengan reputasi dinamis
- Pilihan faksi memengaruhi quest yang tersedia dan ending
- Tidak ada pilihan yang benar — hanya konsekuensi

### 🏁 Ending Dinamis
- **7 keputusan kunci** yang mengumpulkan poin ending
- **3 jalur akhir:** *Defy* (menentang), *Seal* (menyegel), *Reconcile* (rekonsiliasi)
- Epilog yang mencerminkan seluruh perjalananmu dan status faksi
- Setiap keputusan berarti — tidak ada *true ending*, hanya *ending-mu*

---

## 💻 Persyaratan Sistem

| Komponen | Minimal |
|----------|---------|
| **OS** | Linux, macOS, Windows (WSL/Cygwin/cmder) |
| **Python** | ≥ 3.12 |
| **Terminal** | Mendukung Unicode & 256 warna (xterm-256color) |
| **RAM** | ≥ 64 MB |
| **Penyimpanan** | ~5 MB |
| **Koneksi** | Tidak perlu (offline penuh) |

### Dependensi
- `rich>=13.0` — rendering terminal kaya
- `textual>=0.50` — antarmuka terminal interaktif
- `pytest>=8.0` (opsional, untuk development)

---

## 📦 Instalasi

### 1. Clone repositori

```bash
git clone https://github.com/Rian2602/chronicle_of_the_past.git
cd chronicle_of_the_past
```

### 2. Buat dan aktifkan environment (disarankan)

```bash
# Menggunakan venv
python3 -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows
```

### 3. Instal dependensi

```bash
# Dengan pip
pip install -e .

# Atau dengan uv (lebih cepat)
pip install uv
uv sync
```

### 4. Jalankan game!

```bash
python3 launcher.py
```

---

## 🚀 Memulai

Setelah meluncurkan game, kamu akan disambut oleh layar judul. Pilih **Mulai
Baru** untuk memulai petualangan sebagai **Akar**, pemuda dari Desa Emberfall.

**Antarmuka layar permainan:**

```
┌─────────────────────────────────────────────────────────┐
│ 🔖 Chronicle of the Past                      ⏰ 12:34 │
├────┬──────────────────────────────────────────┬─────────┤
│🎒  │ Akar — Desa Emberfall             ⚡QC Lv.1 │📜Quest  │
│📜  │ [████████████████░░░░] HP    17/20    │ [Quest] │
│👥  │ [████████████████████] Qi     20/20    │ ...     │
│⚡  │                                          │         │
│💥  │ ── Tab: 📖 Story ──                     │👥Party  │
│💾  │ Kamu terbangun di gubuk bambu...         │ Akar    │
│    │                                          │ Lin Wei │
│    │ ┌──────────────────────────────────┐     │         │
│    │ │ 🗣 Bicara dgn Sesepuh Mao     ▸  │     │         │
│    │ │ ⚡ Mulai kultivasi               │     │         │
│    │ │ 🌙 Istirahat                     │     │         │
│    │ │ 🗺 Buka peta                     │     │         │
│    │ └──────────────────────────────────┘     │         │
│    │ [⚡ Kultivasi] [🌙 Istirahat] [🗺 Peta]  │         │
├────┴──────────────────────────────────────────┴─────────┤
│ 🔤 N: Mulai Baru  L: Muat  Q: Keluar  Esc: Menu        │
└─────────────────────────────────────────────────────────┘
```

**Cara bermain — tanpa mengetik:**

| Yang ingin kamu lakukan | Caranya |
|-------------------------|---------|
| Berjalan ke lokasi lain | Klik 🗺 Peta / menu "Jelajahi" → pilih lokasi |
| Bicara dengan NPC | Klik "🗣 Bicara" → pilih NPC dari daftar |
| Pilih opsi dialog | Klik opsi yang muncul di panel dialog (atau ↑↓ Enter) |
| Bertarung | Klik ⚔ Serang / 🧘 Teknik / 🛡 Bertahan dari menu battle |
| Buka tas/inventaris | Klik tombol 🎒 Tas di sidebar kiri |
| Cek quest | Klik 📜 Quest di sidebar kiri atau panel kanan |
| Atur tim | Klik 👥 Tim di sidebar kiri |
| Kultivasi | Klik ⚡ Kultiv atau 💥 Break di sidebar / baris bawah |
| Simpan permainan | Klik 💾 Simpan di sidebar kiri |
| Cek peta | Klik 🗺 Peta di baris tombol bawah |
| Gunakan formasi | Klik menu "Formasi" dari daftar aksi |
| Gelar ritual | Klik menu "Ritual" dari daftar aksi (Arc 4) |

> 💡 **Navigasi:** Gunakan **mouse** untuk klik tombol, atau **panah ↑↓**
> untuk memilih opsi lalu **Enter** untuk konfirmasi. Tidak perlu mengetik
> perintah — cukup klik dan pilih. Satu-satunya saat kamu perlu mengetik
> adalah saat memasukkan nama kultivatormu di awal permainan.

---

## 🎮 Menu & Kontrol

Permainan dikendalikan sepenuhnya via **klik** + **panah ↑↓ Enter** —
tanpa perlu mengetik perintah (kecuali nama karakter di awal).

### Sidebar Kiri (Tombol Cepat)

| Tombol | Fungsi |
|--------|--------|
| 🎒 Tas | Buka inventaris & kelola item |
| 📜 Quest | Lihat quest aktif & progres |
| 👥 Tim | Lihat & atur anggota party |
| ⚡ Kultiv | Mulai kultivasi (kumpulkan qi) |
| 💥 Break | Coba naikkan tingkat kultivasi |
| 💾 Simpan | Simpan permainan ke slot |

### Menu Aksi Utama (Panel Tengah)

Daftar opsi yang muncul di panel tengah berubah sesuai situasi:

**Mode Jelajah (dunia):**
```
🗣 Bicara dgn Sesepuh Mao   ▸
⚡ Mulai kultivasi
🌙 Istirahat
🗺 Buka peta
🔧 Gunakan item             ▸
🔄 Atur formasi             ▸
📖 Echo memori
⏳ Ritual persiapan          ▸
```

**Mode Pertarungan:**
```
⚔ Serang
🧘 Teknik                   ▸
🛡 Bertahan
🔍 Amati musuh
🏃 Melarikan diri
🧪 Gunakan item             ▸
```

**Mode Percakapan:**
Panel dialog muncul dengan pilihan bernomor — klik salah satu
atau gunakan ↑↓ + Enter untuk memilih.

### Baris Tombol Bawah

```
[⚡ Kultivasi] [🌙 Istirahat] [🗺 Peta]
```

### Pintasan Keyboard

| Tombol | Fungsi |
|--------|--------|
| `↑` `↓` | Navigasi opsi di menu/aksi |
| `Enter` | Pilih opsi yang disorot |
| `Esc` | Kembali ke sub-menu / ke menu utama |
| `N` | Mulai baru (dari menu utama) |
| `L` | Muat save (dari menu utama) |
| `Q` | Keluar game |

> 💡 **Tips:** Cukup gunakan mouse untuk klik tombol, atau keyboard
> dengan ↑↓ Enter. Tidak ada perintah yang perlu dihapal atau diketik.

---

## 📊 Konten Game

| Kategori | Jumlah | Detail |
|----------|--------|--------|
| **Arc** | 4 | Desa Emberfall → Sekte Azure → Katedral → Langit |
| **Quest Utama** | 32 | quest101–108, quest201–208, quest301–308, quest401–408 |
| **Quest Faksi** | 13 | Gilda, Pemberontak, Orde Suci, Abyssal, Pelipur |
| **Peta** | 12 | 4 arc × 3 peta per arc |
| **NPC** | 21 | Dari Sesepuh Mao hingga The Voice |
| **Musuh** | 28 | Termasuk 7 bos (Penjaga Makam → Suara) |
| **Teknik** | 36 | Tersebar di 6 tier kultivasi & 5 elemen |
| **Item** | 53 | Pil, bahan, resep, artefak, senjata |
| **Resep** | 14 | Alkimia: ramuan, pil, eliksir |
| **Artefak** | 12 | Dengan sistem growth & max level |
| **Formasi** | 3 | Jaring Naga, Benteng Bumi, Langit Pecah |
| **Echo Memori** | 10 | Kilas balik naratif yang membuka lore |
| **Tingkatan** | 6 | Qi Condensation → Heaven Challenger |
| **Faksi** | 5 | Court, Holy Order, Rebels, Guild, Abyssal Cult |

---

## 🏗️ Struktur Proyek

```
chronicle_of_the_past/
├── src/                    # Kode sumber game
│   ├── core/               # Game loop, state, save, input
│   ├── engine/             # Event, combat, dialog, maps, story
│   ├── models/             # Data model (Player, Enemy, Item, dll.)
│   ├── systems/            # Sistem: cultivation, ritual, formation
│   └── ui/                 # Antarmuka Textual
├── data/                   # Konten game (data-driven JSON)
│   ├── events/             # Event naratif & unlock
│   ├── quests/             # Definisi quest
│   ├── npc/                # Karakter non-pemain
│   ├── enemies/            # Musuh & bos
│   ├── maps/               # Definisi peta
│   ├── items/              # Item, pil, resep, artefak
│   ├── techniques/         # Teknik kultivasi
│   ├── formations/         # Formasi pertempuran
│   ├── cultivation/        # Tingkatan kultivasi
│   ├── story/              # Echo memori naratif
│   └── dialogues/          # Percakapan NPC
├── launcher.py             # Entry point
├── pyproject.toml          # Metadata & tooling config
├── README.md               # ← Kamu di sini
└── .gitignore              # File yang diabaikan git
```

---

## 🛠️ Pengembangan

### Menjalankan Test

```bash
# Semua test
pytest -q

# Test spesifik
pytest tests/test_dialog.py -q
pytest tests/test_game_loop.py::test_quest408_selesai_memantik_ending -q
```

### Lint & Validasi

```bash
# Linting
ruff check src launcher.py tools tests

# Format check
ruff format --check src launcher.py tools tests

# Validasi data game (referensi antar entity)
python3 tools/validate.py
```

### Smoke Test

```bash
python3 tools/smoke_playthrough.py
```

### Catatan Pengembangan

- **Python 3.12+** — memanfaatkan fitur terkini (type alias, pattern matching)
- **Data-driven JSON** — seluruh konten game ada di `data/`, bukan hardcode
- **Modular** — engine, sistem, UI dipisah dengan antarmuka jelas
- **TDD** — setiap fitur baru wajib didahului test gagal (RED → GREEN)
- **Grimdark tone** — tidak ada kemenangan bersih, konsekuensi permanen

---

## 📄 Lisensi

**Chronicle of the Past** © 2026 Rian2602. Seluruh hak cipta dilindungi.

Dilarang mendistribusikan, memodifikasi, atau menggunakan kode sumber ini
untuk tujuan komersial tanpa izin tertulis dari pemegang hak cipta.

Untuk keperluan lisensi, silakan hubungi pemilik repositori.

---

<p align="center">
  <i>"Dunia ini dibangun di atas satu keputusan yang diambil seribu tahun lalu.</i><br>
  <i>Sekarang giliranmu: mau menulis ulang, menyegel, atau berdiri di antara keduanya?"</i>
</p>

<p align="center">
  <sub>— The Voice, Chronicle of the Past</sub>
</p>