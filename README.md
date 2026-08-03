# Chronicle of the Past

> **"Sejarah bukan sesuatu yang sudah terjadi. Ia adalah sesuatu yang terus kamu putuskan."**

CLI RPG berbasis teks dalam Bahasa Indonesia — perjalanan melalui waktu, pilihan yang membentuk ulang sejarah, dan kenangan yang tak pernah hilang.

---

## Instalasi

**Prasyarat:** Python 3.12+

```bash
# Clone atau masuk ke direktori proyek
cd chronicle_of_the_past

# Buat virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install dependensi dev
pip install pytest
```

---

## Menjalankan Game

```bash
python launcher.py
```

Navigasi menu utama dengan `w`/`s` (atau `k`/`j`), `Enter` untuk memilih, `q` untuk keluar.

---

## Perintah dalam Game

| Perintah | Keterangan |
|---|---|
| `status` | Tampilkan status karakter |
| `look` | Lihat deskripsi lokasi saat ini |
| `go <lokasi>` | Berpindah ke lokasi (contoh: `go forest`) |
| `rest` | Istirahat hingga pagi, pulihkan HP/MP |
| `talk <npc>` | Bicara dengan NPC (contoh: `talk old_man`) |
| `explore` | Jelajahi area saat ini — mungkin bertemu musuh |
| `inventory` | Tampilkan perlengkapan dan inventaris |
| `use <item>` | Gunakan item konsumabel |
| `equip <item>` | Pasang perlengkapan |
| `unequip <slot>` | Lepas perlengkapan dari slot |
| `quests` | Tampilkan daftar quest aktif |
| `save <path>` | Simpan permainan (contoh: `save saves/slot1.json`) |
| `help` | Tampilkan daftar perintah |
| `quit` / `keluar` | Keluar dari game |

**Perintah tempur** (aktif saat pertarungan berlangsung):

| Perintah | Keterangan |
|---|---|
| `attack` | Serangan fisik dasar |
| `skill <id>` | Gunakan skill fisik (contoh: `skill slash`) |
| `magic <id>` | Gunakan skill sihir (contoh: `magic fireball`) |
| `item <id>` | Gunakan item dari inventaris |
| `observe` | Amati musuh — ungkap info kelemahan |
| `defend` | Bertahan — kurangi damage setengah ronde ini |
| `escape` | Coba melarikan diri dari pertarungan |
| `1` / `2` / ... | Pilih opsi dialog saat berbicara |

---

## Arsitektur

```
chronicle_of_the_past/
├── launcher.py          # Entry point — menu utama + game loop
├── data/                # Konten game (JSON, data-driven)
│   ├── classes/         # Definisi 5 kelas karakter
│   ├── enemies/         # Data musuh (goblin, wild_wolf, bandit)
│   ├── events/          # Event triggers (Arc 1)
│   ├── factions/        # 7 faksi + matriks oposisi
│   ├── items/           # Item (senjata, armor, konsumabel)
│   ├── maps/            # Peta lokasi (village, forest)
│   ├── npc/             # Data NPC (old_man, village_chief)
│   ├── dialogues/       # Dialog trees
│   ├── quests/          # Quest (quest001, quest002)
│   ├── skills/          # Skill karakter dan musuh
│   └── story/           # Story graph + narasi Arc 1
├── assets/
│   ├── ascii/           # ASCII art per lokasi
│   └── ui/              # Palette warna + border JSON
├── src/
│   ├── core/            # Fondasi — GameState, GameContext, Randomizer, config
│   ├── engine/          # Logika — combat, dialog, event, quest, rule, time, world
│   ├── models/          # Dataclass — Player, Enemy, Item, Map, dll.
│   ├── systems/         # Subsistem — level, inventory, equipment, loot, memory, travel
│   ├── ui/              # Presentasi — renderer, HUD, views (combat/dialog/inventory/menu)
│   └── utils/           # Utilitas — json_loader, validator, dice, logger
└── tests/               # Suite pytest (340 tests)
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

## Lokasi Save

File save disimpan di direktori yang kamu tentukan saat perintah `save`:
```
saves/slot1.json    # default
```

Format JSON 3-layer: `player` + `flags` + `engine_state`. Key yang hilang → default, tidak pernah crash.

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

---

## Testing

```bash
# Jalankan semua test
.venv/bin/pytest tests/ -q

# Test spesifik
.venv/bin/pytest tests/test_arc1_content.py -v   # validasi konten
.venv/bin/pytest tests/test_game_flow.py -v       # integrasi game flow
.venv/bin/pytest tests/test_combat_loop.py -v     # loop pertarungan

# Compile check
python3 -m py_compile src/core/game.py launcher.py
```

**340 tests** covering: JSON loader, dice, constants, models, rule engine, level system, combat (interfaces, status, damage, loop, skills, AI, rewards, integration), time/world/travel, inventory/equipment/loot, quest engine, memory system, dialog engine, event engine, ascii loader, save manager, UI renderer/HUD/views/input, game flow, and Arc 1 content validation.
