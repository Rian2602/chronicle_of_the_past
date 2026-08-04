# Chronicle of the Past

> **"Sejarah bukan sesuatu yang sudah terjadi. Ia adalah sesuatu yang terus kamu putuskan."**

CLI RPG berbasis teks dalam Bahasa Indonesia — perjalanan melalui waktu, pilihan yang membentuk ulang sejarah, dan kenangan yang tak pernah hilang.

- **5 kelas karakter** (Warrior, Mage, Ranger, Assassin, Scholar) dengan stat & skill awal berbeda
- **3 musuh** berperilaku unik (aggressive, coward) di **2 peta** yang terhubung
- **Quest, event, dan dialog bercabang** yang digerakkan data (semua konten di `data/`)
- **Save / Continue** kapan saja — termasuk di tengah pertarungan
- **Tanpa dependency runtime** — murni stdlib Python 3.12+

---

## Instalasi

**Prasyarat:** Python 3.12+ (game berjalan murni stdlib, tanpa install dependency)

```bash
# Clone atau masuk ke direktori proyek
cd chronicle_of_the_past

# Opsional: virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Opsional (hanya untuk pengembangan/test): pytest
pip install pytest
```

---

## Menjalankan Game

```bash
python3 launcher.py        # atau .venv/bin/python launcher.py
```

Menu utama punya 5 pilihan:

| Pilihan | Fungsi |
|---|---|
| **Permainan Baru** | Mulai permainan baru (minta nama → pilih kelas) |
| **Lanjutkan** | Muat file save (default `saves/slot1.json`) |
| **Pengaturan** | Belum tersedia |
| **Kredit** | Tampilkan kredit |
| **Keluar** | Tutup game |

Navigasi: `w`/`s` (atau `k`/`j`) untuk berpindah, `Enter` untuk memilih, `q` untuk keluar.

Saat **Permainan Baru**, kamu diminta nama (kosongkan → "Pejalan Waktu"), lalu memilih kelas dari 5 opsi.

---

## Kelas

| Kelas | Deskripsi | Skill Awal | XP Bonus |
|---|---|---|---|
| **Warrior** | Spesialis garis depan. | `slash` | 1.0× |
| **Mage** | Pengguna sihir yang mempelajari mantra. | `fireball` | 1.0× |
| **Ranger** | Ahli perburuan dan panah. | `quick_shot` | 1.0× |
| **Assassin** | Pembunuh senyap dari bayangan. | `backstab` | 1.0× |
| **Scholar** | Peneliti yang mencari kebenaran kuno. | `inspect` | **1.2×** |

---

## Perintah dalam Game

| Perintah | Keterangan |
|---|---|
| `status` | Tampilkan status karakter |
| `look` | Lihat deskripsi lokasi saat ini |
| `go <lokasi>` | Berpindah ke lokasi (contoh: `go forest`) |
| `rest` | Istirahat hingga pagi, pulihkan HP/MP penuh |
| `talk <npc>` | Bicara dengan NPC — gunakan **ID**, bukan nama (contoh: `talk old_man`) |
| `explore` | Jelajahi area — mungkin bertemu musuh |
| `inventory` | Tampilkan perlengkapan dan inventaris |
| `use <item>` | Gunakan item konsumabel |
| `equip <item>` | Pasang perlengkapan |
| `unequip <slot>` | Lepas perlengkapan dari slot |
| `quests` | Tampilkan daftar quest aktif (progres X/Y) |
| `save <path>` | Simpan permainan (contoh: `save saves/slot1.json`) |
| `help` | Tampilkan daftar perintah |
| `quit` / `keluar` | Keluar dari game |

**Perintah tempur** (aktif saat pertarungan berlangsung):

| Perintah | Keterangan |
|---|---|
| `attack` | Serangan fisik dasar |
| `skill <id>` | Gunakan skill fisik (contoh: `skill slash`) |
| `magic <id>` | Gunakan skill sihir (contoh: `magic fireball`) |
| `item <id>` | Gunakan item dari inventaris (tidak menghabiskan giliran) |
| `observe` | Amati musuh — ungkap info kelemahan (gratis, 1×) |
| `defend` | Bertahan — kurangi damage setengah ronde ini |
| `escape` | Coba melarikan diri dari pertarungan |
| `1` / `2` / ... | Pilih opsi dialog saat berbicara |

> Saat bertarung, hanya perintah tempur + `save` + `help` yang aktif; perintah lain ditolak dengan pesan "Tidak bisa saat bertarung."

---

## Sinopsis Arc 1 — "The Stranger"

Kamu terbangun sebagai orang asing di **Ashen Village** tanpa ingatan. Seorang **Old Man** (Aria, penjaga perpustakaan tua) memperingatkan bahwa desa ini akan terbakar. Kepala Desa meminta bantuanmu memberantas serigala liar di tepi hutan. Semakin dalam kamu menyelidiki, semakin jelas bahwa waktu bukanlah sekadar alur lurus — dan sejarah mulai terbentuk ulang di tanganmu.

---

## Walkthrough Arc 1 (quest001 + quest002)

**Prasyarat:** Permainan Baru → nama → pilih kelas. Kamu mulai di Ashen Village, pagi Hari 1, tanpa item dan emas.

1. **`talk old_man`** → dialog terbuka.
2. Ketik **`1`** ("Siapa Anda?") → dialog berlanjut: Old Man bernama Aria, memperingatkan *"desa ini akan terbakar."* Di akhir giliran ini **dua quest langsung aktif**:
   - **quest001 — "Temui Kepala Desa"**
   - **quest002 — "Bahaya di Hutan"** (kalahkan serigala liar)
3. **`talk village_chief`** → bicara dengan Kepala Desa, pilih opsi mana pun → **quest001 selesai**: +50 XP, +20 emas, +10 reputasi *merchant_guild*.
4. **`go forest`** → tiba di Ashen Forest (waktu maju satu fase).
5. **`explore`** berulang sampai bertemu **Wild Wolf**. Peluang encounter 40% per explore (50% saat malam), dan wolf adalah salah satu dari 3 musuh di pool hutan — bersabarlah. **Hanya Wild Wolf** yang memenuhi syarat quest002. Menang → +40 XP, 8–16 emas, 50% loot *herb* → **quest002 selesai**: +40 XP, +15 emas, +5 reputasi.
6. Di akhir giliran yang sama muncul banner **"PERCABANGAN WAKTU"** → **Arc 1 selesai**. Permainan berlanjut bebas.

> 🧭 **Catatan:** quest002 tidak menunggu quest001 selesai — keduanya aktif bersamaan sejak langkah 2.

---

## Tips Bertarung

- **`observe`** gratis dan mengungkap kelemahan musuh — gunakan di awal.
- **Wild Wolf** berperilaku *coward*: berusaha kabur saat HP-nya rendah. Jangan biarkan ia kabur — kejar dengan `attack`.
- **`defend`** mengurangi damage separuh; berguna saat HP tipis.
- **Menggunakan item tidak menghabiskan giliran** — heal di saat kritis tanpa risiko.
- **Scholar** mendapat **20% XP ekstra** (1.2×) dari semua kemenangan & quest.
- **Tidak ada game over.** Kalah → pesan "Kamu gugur dalam pertarungan...", lalu `rest` untuk pulih penuh dan coba lagi.

---

## Sistem Inti

- **Waktu:** 4 fase — pagi, siang, sore, malam → kembali pagi (bertambah hari). `go <peta>` memajukan waktu; `explore` dan dialog tidak. Malam di hutan meningkatkan peluang bertemu musuh.
- **Level & XP:** butuh `50 × level` XP untuk naik level. Level naik saat **kemenangan combat**; tiap level memberimu +5 HP, +3 MP (otomatis).
- **Ekonomi:** tidak ada toko. Emas & item datang dari quest dan loot musuh. *Herb* memulihkan 20 HP, *Potion* 50 HP.

---

## Save / Continue

- **Simpan:** `save <path>` saat bermain — didukung juga **di tengah pertarungan** (state combat ikut tersimpan).
- **Lanjutkan:** pilih "Lanjutkan" di menu utama; default path `saves/slot1.json`.
- Format JSON 3-layer: `player` + `flags` + `engine_state`. Key yang hilang → default. File yang bukan save, atau save tanpa data pemain, ditolak dengan pesan error ramah (bukan crash).

---

## FAQ & Troubleshooting

**Kenapa `explore` sering tidak ketemu musuh?**
Peluang encounter hanya 40% per explore (50% saat malam di hutan). Coba lagi, atau `rest` dulu sampai malam.

**Kenapa quest002 tidak selesai setelah kalahkan goblin/bandit?**
Quest002 hanya terpenuhi dengan membunuh **Wild Wolf**, musuh yang muncul di pool Ashen Forest.

**Kenapa harus `talk old_man`, bukan `talk "Old Man"`?**
Perintah `talk` memakai **ID** NPC, bukan nama tampilan (`old_man`, `village_chief`).

**Saya kalah bertarung, permainan berakhir?**
Tidak ada game over. Gunakan `rest` untuk pulih penuh, lalu ulangi.

**XP quest tidak menaikkan level langsung?**
Level naik hanya saat kemenangan combat; XP quest tetap terhitung dan akan terproses pada kemenangan berikutnya.

**Error "Bukan file save: <path>"?**
Path menunjuk ke file JSON yang bukan save buatan game. Beri path yang benar.

**Apakah ada toko?**
Tidak. Emas dan item (herb/potion) didapat dari quest dan loot musuh.

---

## Arsitektur

```
chronicle_of_the_past/
├── launcher.py          # Entry point — menu utama + game loop
├── tools/bench.py       # Benchmark performa (stdlib, report-only)
├── data/                # Konten game (JSON, data-driven)
│   ├── classes/         # 5 kelas karakter
│   ├── enemies/         # goblin, wild_wolf, bandit
│   ├── events/          # Event triggers (Arc 1)
│   ├── factions/        # 7 faksi
│   ├── items/           # Senjata, armor, konsumabel
│   ├── maps/            # village, forest
│   ├── npc/             # old_man, village_chief
│   ├── dialogues/       # Dialog trees
│   ├── quests/          # quest001, quest002
│   ├── skills/          # Skill karakter & musuh
│   └── story/           # Narasi kenangan (memories)
├── assets/
│   ├── ascii/           # ASCII art per lokasi
│   └── ui/              # Palette warna + border JSON
├── src/
│   ├── core/            # Game, GameContext, GameState, Randomizer, save_manager, input_handler, constants
│   ├── engine/          # combat, dialog, event, quest, rule, time, world
│   ├── models/          # Dataclass — Player, Enemy, Item, Map, Command, Event
│   ├── systems/         # level, inventory, equipment, loot, memory, travel, exploration, status
│   ├── ui/              # renderer, HUD, views (combat/dialog/inventory/menu), animation, ascii_loader
│   └── utils/           # json_loader
├── docs/superpowers/specs/  # Desain & spesifikasi
└── tests/               # Suite pytest (353 tests)
```

**Arah dependensi (ketat):**
```
data/ → engine/systems → GameState ← ui/
                          ↑
                        core/
```
- `ui/` hanya membaca, tidak pernah mengimpor `engine/` atau `systems/`
- Engine tidak mengandung nama konten spesifik — semua dari JSON
- Tidak ada global state — `GameState` di-pass secara eksplisit

---

## Panduan Authoring Konten

### Menambah Kelas Baru

Buat `data/classes/<id>.json`:
```json
{
  "id": "paladin",
  "name": "Paladin",
  "description": "Ksatria suci yang tahan banting.",
  "base_stats": {"attack": 10, "defense": 16, "hp": 110, "mp": 15, "agility": 6, "intelligence": 9},
  "xp_bonus": 1.0,
  "starting_skills": ["slash"],
  "stat_bars": {"attack": 3, "defense": 6, "hp": 6, "mp": 2, "agility": 1, "intelligence": 2}
}
```

### Menambah Musuh Baru

Buat `data/enemies/<id>.json`:
```json
{
  "id": "skeleton",
  "name": "Skeleton",
  "level": 3,
  "stats": {"attack": 7, "defense": 4, "hp": 15, "mp": 0, "agility": 5, "intelligence": 1},
  "behavior": "aggressive",
  "reward": {"xp": 45, "gold": [5, 15]},
  "skills": ["bite"],
  "loot": [{"item": "herb", "chance": 30, "amount": 1}],
  "weight": 2,
  "tags": ["undead"],
  "lore": "Tulang-belulang yang bangkit kembali."
}
```

### Menambah Skill Baru

Buat `data/skills/<id>.json`:
```json
{
  "id": "thunder_strike",
  "name": "Thunder Strike",
  "type": "magic",
  "cost": 12,
  "target": "single_enemy",
  "power": 15,
  "effects": [{"status": "blind", "power": 1, "duration": 2}],
  "requires": {},
  "description": "Serangan petir yang membutakan musuh."
}
```

### Menambah Event Baru

Tambah ke `data/events/events.json` (pola one-shot dengan self-guard):
```json
{
  "id": "event_my_event",
  "trigger": [
    {"kind": "flag", "flag": "my_condition", "value": true},
    {"kind": "flag", "flag": "my_event_done", "operator": "MISSING"}
  ],
  "actions": [
    {"kind": "log", "text": "Sesuatu terjadi."},
    {"kind": "set_flag", "flag": "my_event_done", "value": true}
  ]
}
```

> ⚠️ **Penting:** Jangan gunakan `"type": "location"` untuk trigger event — `rule_engine` menggunakan `"kind": "map"` dengan perbandingan string, dan `game.py` menyimpan `Map` object (bukan string). Gunakan flag triggers untuk semua event konten.

### Menambah Dialog NPC

Buat `data/dialogues/<id>.json`:
```json
{
  "id": "dialog_my_npc_main",
  "lines": [
    {"speaker": "my_npc", "text": "Halo, pengembara!"}
  ],
  "choices": [
    {"text": "Siapa kamu?", "require_flags": [], "set_flags": ["met_my_npc"], "next": null},
    {"text": "Pergi.", "require_flags": [], "set_flags": [], "next": null}
  ]
}
```

**Kunci choice opsional:** `require_not_flags: []`, `require_reputation: {"merchant_guild": 10}`.

### Menambah Quest Baru

Buat `data/quests/<id>.json`:
```json
{
  "id": "quest003",
  "title": "Judul Quest",
  "type": "side",
  "description": "Deskripsi quest.",
  "requirements": [
    {"kind": "enemy", "target": "goblin"},
    {"kind": "talk", "target": "village_chief"}
  ],
  "rewards": {"xp": 60, "gold": 25, "reputation": {"merchant_guild": 5}},
  "flags_on_complete": ["quest003_done"],
  "next": null
}
```

**Kind requirement valid:** `talk`, `enemy`, `flag`, `map`.

**Faksi valid (frozen):** `royal_army`, `church`, `rebels`, `merchant_guild`, `scholar_society`, `ancient_order`, `crime`.

---

## Testing & Tools

```bash
# Jalankan semua test (353 test)
.venv/bin/python -m pytest tests/ -q

# Test spesifik
.venv/bin/python -m pytest tests/test_arc1_content.py -v   # validasi konten
.venv/bin/python -m pytest tests/test_game_flow.py -v       # integrasi game flow
.venv/bin/python -m pytest tests/test_combat_loop.py -v     # loop pertarungan

# Compile check
python3 -m compileall src launcher.py tools/bench.py

# Benchmark performa (startup, save/load, combat, render, memori)
python3 tools/bench.py
```

**353 tests** covering: JSON loader, constants, models, rule engine, level system, combat (interfaces, status, damage, loop, skills, AI, rewards, integration), time/world/travel, inventory/equipment/loot, quest engine, memory system, dialog engine, event engine, ascii loader, save manager, UI renderer/HUD/views/input, launcher, game flow, dan Arc 1 content validation.

---

## Catatan Divergensi dari MASTER_CONCEPT

Proyek ini menyimpang dari MASTER_CONCEPT v1.0 dalam beberapa hal yang sudah disetujui:

| Aspek | MASTER_CONCEPT | Implementasi |
|---|---|---|
| **Stack** | Rich, Pydantic v2, uv | stdlib only, dataclasses, requirements.txt |
| **Faksi** | `{kingdom, church, rebels, merchant_guild, scholar_society, village, ancient_order}` | `{royal_army, church, rebels, merchant_guild, scholar_society, ancient_order, crime}` (frozen) |
| **Region ID** | `snake_case` | Numerik string (`"1"`, `"2"`) |
| **Event trigger lokasi** | `{"type": "location", "equals": "village"}` | `{"kind": "map", "name": ..., "operator": "EQ"}` — perbandingan string; live `Game` menyimpan Map object → konten Arc 1 menggunakan flag trigger saja |
| **Reputation bleed-over** | Matriks oposisi aktif | Matriks disimpan sebagai data (`opposes`/`aligns`) tapi tidak dievaluasi engine |
| **Save versioning** | — | `schema_version` + `content_version` (backward-compatible load) |

## Catatan Pengembangan (Diketahui)

Quirk konten yang tercatat, bukan untuk diperbaiki di sini:

- `data/story/arc1_text.json` **tidak dimuat** engine — semua narasi hardcoded di `events.json`.
- **memory001** ("Desa Terbakar") diberikan **senyap** — tidak ada log di layar maupun perintah untuk melihat kenangan.
- **quest002 aktif bersamaan** quest001 (tidak menunggu quest001 selesai).
- Field `weight` di file `enemies/*.json` **diabaikan** engine — yang dipakai bobot `enemy_pool` di peta.
- `data/config/` dan `data/timeline/` ada tapi belum terpakai.
