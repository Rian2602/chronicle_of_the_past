# Spesifikasi: Perbaikan 5 Bug Terverifikasi (2026-08-04)

## Latar Belakang

Perburuan bug (explore agent + verifikasi runtime) menemukan 4 bug Tier 1 yang
bisa dipicu input keyboard normal + 1 crash jalur "Lanjutkan". Keputusan
pengguna: perbaiki 5 bug ini saja (Tier 1 + crash continue), laporkan sisanya
tanpa diubah.

## Daftar Bug & Perbaikan

### Fix 1 — State musuh bocor antar pertarungan
- **Gejala:** Musuh yang pernah dikalahkan tetap `hp=0, max_hp=0` di
  `state.enemies` → pertarungan berikutnya melawan musuh sama = kemenangan
  instan + XP/emas/loot gratis (farm tanpa risiko).
- **Akar:** `check_encounter` mengembalikan instance `Enemy` bersama dari
  `state.enemies`; `start_combat` & `resolve_hit` menulis langsung ke
  `stats` objek itu.
- **Fix:** `start_combat` beroperasi pada salinan enemy
  (`copy.copy(enemy)` + `stats = dict(enemy.stats)`); `_restore_combat`
  (game.py:83) juga salin sebelum mutasi. `state.enemies` tetap murni.
- **Test:** setelah bertarung (menang/kalah), `check_encounter` berikutnya
  memberi enemy hp penuh.

### Fix 2 — `item` di combat crash
- **Gejala:** `item` tanpa argumen / item tak dimiliki saat bertarung →
  `ValueError` tak tertangkap → traceback → game keluar.
- **Akar:** `use_item` melempar `ValueError`; `_combat_turn` (game.py:353)
  tidak menangkap.
- **Fix:** tangkap `ValueError` di `_combat_turn` → `out.append(str(e))`
  (pola sama dengan `_cmd_use`/`_cmd_go`).
- **Test:** `item` dan `item potion` (tak dimiliki) saat combat → pesan
  ramah, combat berlanjut.

### Fix 3 — Blokir perintah non-combat saat bertarung
- **Aturan (disetujui pengguna):** saat bertarung hanya aksi combat + `save`
  + `help` aktif; sisanya → `"Tidak bisa saat bertarung."`
- **Fix:** perluas routing `run_turn` (game.py:126): saat `_combat` aktif dan
  aksi bukan combat/save/help → blokir sebelum `_dispatch`.
- **Test:** `rest` saat combat → tidak heal, combat utuh; `save <path>` &
  `help` tetap aktif.

### Fix 4 — `save <path buruk>` crash
- **Gejala:** `save /tidak/ada/dir/x.json` → `OSError` (subclass:
  FileNotFoundError/IsADirectoryError/PermissionError) tak tertangkap →
  crash. `load_game` sudah membungkus OSError, `save_game` belum.
- **Fix:** bungkus penulisan di `save_game` dengan `try/except OSError →
  SaveError` (simetris dgn load_game). Launcher sudah menangkap `SaveError`.
- **Test:** `save` ke path invalid → `SaveError`, pesan ramah, tidak crash.

### Fix 5 — "Lanjutkan" file non-save crash
- **Gejala:** memilih Lanjutkan dengan path file JSON valid non-save →
  `AttributeError: 'list' object has no attribute 'get'`; save tanpa `player`
  → `AssertionError` (game.py:71).
- **Fix:** `load_game` cek hasil `json.load` harus dict, jika bukan →
  `SaveError("...bukan file save.")`; jika `player` kosong → `SaveError`.
- **Test:** `continue_game("data/events/events.json")` → `SaveError` ramah,
  tidak crash.

## Metodologi

- TDD: tulis test gagal dulu, lalu fix akar, lalu hijau.
- Satu commit per bug + 1 commit spec. Semua ter-push ke master.
- 345 test yang ada tidak boleh putus.

## Yang Sengaja TIDAK Diperbaiki (diterima sebagai risiko/keputusan desain)

- Tier 2: hardening data — akses dict tanpa `.get()` pada data/save yang
  diedit (crash hanya bila file data/save diedit manual).
- Tier 3: sistem inisiatif/turn_order mati (pemain selalu duluan — keputusan
  desain sah), kekalahan tanpa konsekuensi/game-over, loot hilang diam-diam
  saat inventory penuh, `_hp_bar` kosmetik > 10 karakter.
- Tier 4: MP musuh & `active_events` asimetri save/load, combat dibuang
  diam-diam saat enemy id tidak valid.

## Verifikasi

- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/ -q -p no:cacheprovider` hijau.
- `tools/bench.py` tidak terpengaruh.
- `compileall`, `graphify update .`.
