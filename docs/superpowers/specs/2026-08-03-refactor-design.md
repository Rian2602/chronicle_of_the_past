# Chronicle of the Past — Refactor Design Spec

> **For agentic workers:** This is the validated design for the refactor pass.
> Scope disetujui pengguna pada 2026-08-03: **bersihkan masalah struktural,
> konsistensi/gaya kode, dan perbaiki bug laten** — TANPA mengubah perilaku game,
> kecuali satu pengecualian eksplisit (xp_bonus, lihat T3).

## Tujuan

Codebase ~2156 baris Python (stdlib only, 339 test lulus) masih membawa dead
code, duplikasi konstanta/formula, dan bug laten. Refactor ini membersihkan
ketiganya dengan diff terkecil dan test tetap hijau di tiap langkah.

## Prinsip (ponytail)

- Hapus, jangan bungkus. Modul mati dihapus, bukan di-"centralize".
- Satu sumber kebenaran per fakta: aksi combat, stat list, stat math, multiplier XP.
- Bug fix = akar masalah (satu helper bersama), bukan tambalan per caller.
- Tidak ada abstraksi baru tanpa pemakai.
- `game.py` (401 baris) **sengaja dibiarkan utuh** — keputusan pengguna.
  Codebase kecil; restrukturisasi penuh berisiko regresi tanpa manfaat terukur.

## Tier 1 — Hapus dead code

Modul tanpa pemanggil produksi (hanya dipakai test-nya sendiri / tidak sama sekali):

- `src/utils/logger.py` — nol pemanggil.
- `src/utils/helpers.py` (`clamp`) — hanya `tests/test_helpers.py`.
- `src/utils/validator.py` — hanya `tests/test_validator.py`.
- `src/core/config.py` (`load_config`) — nol pemanggil.
- `src/models/npc.py`, `skill.py`, `quest.py` — produksi memakai raw dict dari
  ctx; model hanya dipakai `tests/test_models.py` dan `test_dialog.py`.

Field mati:

- `Item.type`, `Enemy.tags`, `Map.time_effects` — nol pemakaian di `src/`.
- `inventory_system.carry_capacity` — nol pemanggil (yang hidup:
  `rule_engine.derived_stats`).
- `constants.CONDITION_OPERATORS` — hanya validator.py + `test_rule_engine.py`.
- `constants.TIMES` — hanya `test_validator.py`.
- `constants.COMBAT_ACTIONS` — nol pemakaian (game.py pakai set lokal).
- Import `memory_system` tak terpakai di `src/core/game.py`.

Test ikut dihapus/diupdate: `test_helpers.py`, `test_validator.py`, section
`Npc`/`Skill`/`time_effects` di `test_models.py`, assert `CONDITION_OPERATORS`
di `test_rule_engine.py`.

## Tier 2 — Konsolidasi duplikasi

- **Aksi combat (3 sumber → 1):** enum `CombatAction` (combat_interfaces) jadi
  satu-satunya; set `_COMBAT_ACTIONS` di game.py diganti set dari enum;
  `constants.COMBAT_ACTIONS` dihapus.
- **Stat list (2 → 1):** `constants.STATS` jadi satu-satunya; `TOTAL_STATS`
  di equipment_system dihapus.
- **Stat math (duplikat → helper bersama di rule_engine):**
  - `accuracy(agility)`, `crit_chance(agility)` dipakai oleh `derived_stats`
    dan `damage_roll`.
  - `player_stats` di combat_engine dibangun via `effective_stat`, bukan
    rebuild manual base+bonus.
  - `magic_resistance` di `resolve_hit` via helper bersama.
- `_hp_bar` (combat_engine) diselaraskan ke `renderer.bar`.

## Tier 3 — Bug laten (perilaku berubah MINIMAL)

- **T3-1 xp_bonus benar-benar berlaku (keputusan pengguna: YA).**
  - Helper baru di `level_system.py`: `award_xp(player, amount)` =
    `int(amount * getattr(player, "xp_bonus", 1.0))`.
  - `_on_victory` (combat_engine) dan `_complete_quest` (quest_engine) memberi
    XP via helper ini, sehingga multiplier class (Scholar +20%) bekerja di
    combat & quest — sebelumnya hanya `gain_xp` yang memakainya, dan reward
    riil menambah `player.xp` langsung tanpa multiplier.
  - `gain_xp` memakai helper yang sama secara internal → satu sumber
    multiplier, tanpa double-apply (alur level-up & pesan "Naik level!"
    di `_finish_combat` tetap utuh karena reward tidak memproses level).
- **T3-2 `_restore_combat`:** guard `CombatResult(combat_data["result"])`
  terhadap nilai tak dikenal (save korup) agar tidak `ValueError`-crash.
- **T3-3 `grant_memory`:** fallback yang membuat Player dummy kosong dihapus
  → `return None` bila tanpa player (periksa test sebelum merubah).

## Verifikasi

Setelah tiap tier:
`PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/ -q -p no:cacheprovider`
harus hijau. Lalu `graphify update .` dan commit per tier ke master (tanpa
branch baru).

## Out of scope

- Restrukturisasi game.py (keputusan: biarkan utuh).
- Perubahan konten JSON, balance, fitur baru.
