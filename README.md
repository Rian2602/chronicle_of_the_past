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

**Contoh sesi:**

```
╔══════════════════════════════════════════════════════╗
║              CHRONICLE OF THE PAST                   ║
║            Episode 1: Desa Emberfall                 ║
╚══════════════════════════════════════════════════════╝

Kamu terbangun di gubuk bambu yang sempit. Cahaya senja
masuk melalui celah dinding. Tubuhmu terasa aneh — seolah
ada sesuatu yang mengalir di dalam urat nadi, sesuatu yang
seharusnya tidak ada.

> talk elder_mao

Sesepuh Mao menatapmu: "Apa kamu sudah siap memulai jalan
kultivasimu?"

  [1] Saya siap, Guru.
  [2] Beri saya waktu.
```

Navigasi sederhana: ketik perintah (atau nomor pilihan) dan tekan Enter.

---

## ⌨️ Perintah Dasar

### Navigasi & Eksplorasi
| Perintah | Fungsi |
|----------|--------|
| `help` | Tampilkan daftar perintah |
| `status` | Lihat status pemain (HP, Qi, tier) |
| `map` | Lihat peta dunia dan lokasi tersedia |
| `go <lokasi>` | Pindah ke lokasi |
| `look` | Amati lingkungan sekitar |
| `talk <nama>` | Bicara dengan NPC |

### Pertempuran
| Perintah | Fungsi |
|----------|--------|
| `attack` | Serangan fisik dasar |
| `defend` | Bertahan, kurangi damage |
| `technique <nama>` | Gunakan teknik kultivasi |
| `observe` | Analisis musuh |
| `escape` | Melarikan diri |

### Kultivasi & Item
| Perintah | Fungsi |
|----------|--------|
| `cultivate` | Mengumpulkan qi |
| `breakthrough` | Naikkan tingkat kultivasi |
| `rest` | Pulihkan HP |
| `meditate` | Pulihkan Qi |
| `use <item>` | Gunakan item |
| `refine <item>` | Buat item dari resep |
| `shop` | Lihat barang di toko |
| `buy/sell <item>` | Jual beli |

### Party & Tim
| Perintah | Fungsi |
|----------|--------|
| `party` | Lihat anggota party |
| `swap <nama>` | Tukar anggota aktif |
| `formation <id>` | Aktifkan formasi |
| `ritual` | Gelar ritual persiapan (Arc 4) |

### Sistem
| Perintah | Fungsi |
|----------|--------|
| `save [1-3]` | Simpan ke slot |
| `load [1-3]` | Muat dari slot |
| `inventory` | Buka inventaris |
| `quests` | Lihat quest aktif |
| `memories` | Lihat echo memori terkumpul |

> 💡 **Tips:** Gunakan `help` kapan pun kamu bingung. Sebagian besar perintah
> juga punya alias Bahasa Indonesia!

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