# Spesifikasi: Bug-Hunt Pass 2 — Temuan Baru (2026-08-04)

## Latar Belakang

Pass bug-hunt independen kedua setelah `2026-08-04-bugfix-design.md`. Fokus:
area yang belum tereksplorasi di pass 1 (input parsing, exploration, travel,
event, equipment, status, loot selain inventory penuh, save/load, konsistensi
JSON data/ vs kode). Metodologi wajib TDD (test gagal → fix akar → hijau),
satu commit per bug, 354 test yang ada tidak boleh putus.

## Bug Baru Ditemukan

### Bug A — Kondisi `map` di `rule_engine.evaluate` tak pernah cocok (DIPERBAIKI)

- **Gejala:** trigger/kondisi `{"kind": "map", "map": "village"}` selalu
  bernilai False pada alur game nyata → event/quest berbasis map tak pernah
  terpicu.
- **Akar:** `evaluate()` membandingkan `game_state.current_map == target`,
  padahal alur nyata (game.py:45, 62) selalu menyimpan objek `Map` di
  `current_map`; `Map` tak pernah `==` string. Test lama (`test_evaluate_map`)
  lolos karena memakai string `"village"` — kontrak yang tidak pernah terjadi
  di game.
- **Fix:** normalisasi `current = getattr(current_map, "id", current_map)`
  sebelum dibandingkan (satu tempat di `evaluate`). Kompatibel dengan current_map
  berupa objek `Map`, string, atau `None`.
- **Test (RED dulu):** `test_evaluate_map_with_map_object` — `current_map =
  Map(id="village")` → evaluate map EQ True, map lain False.
- **Commit:** `ddcd0cb`

### Bug B — HP pemain tidak penuh setelah naik level (DIPERBAIKI)

- **Gejala:** setelah naik level lewat kemenangan, pemain di HP 105/120
  (harusnya penuh 120); MP justru penuh 13/13 → inkonsisten heal level-up.
- **Akar:** `_apply_level_ups` (game.py) meng-set `p.hp = max_hp(p)` SEBELUM
  `apply_choice(p, "hp")` menambah +15 bonus → `max_hp` naik lagi setelah
  `p.hp` di-set, jadi `p.hp` ketinggalan 15 dari max baru.
- **Fix:** pindah `apply_choice(p, "hp")` sebelum `p.hp = max_hp(p)` /
  `p.mp = max_mp(p)` (reorder minimal, tanpa ubah angka bonus).
- **Test (RED dulu):** `test_level_up_heals_hp_to_full` — menang fight yang
  menaikkan level → `p.hp == max_hp(p)` dan `p.mp == max_mp(p)`.
- **Commit:** `bdec432`

## Yang Dicatat Tapi Sengaja TIDAK Diperbaiki

Kandidat yang tidak memenuhi syarat "repro bug nyata" — atau sudah tercatat /
dianggap keputusan desain sah:

- **Sistem inisiatif/turn_order mati** (`next_turn`/`turn_order`/`current_index`
  hanya dipakai test; pemain selalu duluan) — sudah tercatat Tier 3 di
  `2026-08-04-bugfix-design.md` sebagai keputusan desain.
- **Status kontrol (blind/silence/fear/sleep)** diterapkan oleh
  `apply_status` tapi tidak ada mekanik yang membacanya (tidak ada data
  skill/musuh yang memakainya) — celah fitur, bukan regresi; memperbaikinya =
  fitur baru.
- **`equipment_system.equip(..., items=None)` di slot terisi** meninggalkan
  bonus item lama (bonus menumpuk) — tidak tercapai di game (game.py selalu
  lewat `items=self.state.items`), hanya footgun API langsung.
- **`apply_status` dengan `duration <= 0`** → efek langsung habis di tick
  berikutnya — tidak tercapai (semua duration effect skill ≥ 1 di data/).
- **Heal item tetap terpakai saat HP penuh** (`use_item`/`use_consumable`) —
  keputusan desain/UX minor.
- **`_coward_turn` selalu "mencoba kabur tapi gagal"** (tidak pernah benar
  kabur) — keputusan desain agar pertarungan tetap bisa dimenangkan.
- **XP quest hanya memicu level-up saat kemenangan combat berikutnya**
  (`gain_xp` hanya dipanggil di `_finish_combat`) — level-up tetap terjadi,
  hanya pesannya tertunda; desain UX.

## Metodologi

- TDD: tiap bug = test gagal dulu (RED), fix akar minimal, hijau (GREEN).
- Satu commit per bug, test+fix bareng.
- 354 test baseline; tidak ada yang putus.

## Verifikasi

- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/ -q -p no:cacheprovider`
  → **356 passed** (354 baseline + 2 test baru).
- `tools/bench.py` → semua dimensi di bawah ambang 50 ms (tidak terpengaruh).
- `graphify update .` → selesai (841 node, 35 komunitas); `graphify-out/` di-gitignore.
- `compileall` aman (tidak ada syntax error).
