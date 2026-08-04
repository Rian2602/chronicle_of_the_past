# Spesifikasi: Perburuan Bug Independen Putaran 2 (2026-08-04)

## Latar Belakang

Sesi bug-hunt independen setelah pass refactor + perbaikan 5 bug. Metodologi
TDD: tulis test gagal dulu untuk setiap dugaan bug, verifikasi merah, lalu
fix akar minimal (ponytail), lalu hijau. Hanya bug yang bisa direproduksi
melalui input keyboard normal yang diperbaiki.

## Daftar Bug & Perbaikan

### Fix 1 — `max_hp` musuh hilang saat save/load di tengah combat
- **Gejala:** simpan di tengah combat setelah musuh terluka → load → HP bar
  musuh jadi `5/5` padahal seharusnya `5/50`; `stats["max_hp"]` memicu
  `KeyError`; rasio HP musuh untuk AI salah.
- **Akar:** `_engine_state` (save_manager.py) hanya menulis `enemy_hp`,
  bukan `max_hp`; `_restore_combat` (game.py) me-restore stats mentah tanpa
  `max_hp`. `start_combat` menambahkan `max_hp` hanya saat combat dimulai,
  tidak saat restore.
- **Fix:** di `_restore_combat`, tambah `stats.setdefault("max_hp", hp penuh)`
  sebelum meng-overwrite `hp` (simetris dengan `start_combat`).
- **Test:** save tengah combat setelah musuh terluka → load → `max_hp` musuh
  benar & HP bar penuh.

### Fix 2 — Efek status skill fisik tetap diterapkan saat meleset
- **Gejala:** skill fisik (mis. poison/bleed) yang meleset tetap memberi efek
  status ke musuh — HP tidak berubah tapi status diterapkan.
- **Akar:** `resolve_hit` (combat_engine.py) menerapkan `effects` di luar
  cabang hit/miss; guard `if effects:` tidak memeriksa `missed`. Test lama
  `test_damage.py` meng-enkode perilaku salah ini (roll miss di slot
  `miss_roll` namun mengharapkan efek tetap terpasang).
- **Fix:** `if effects and not missed:` — efek status hanya terpasang saat
  hit. Dua test lama dikoreksi jadi memakai roll hit (intensi aslinya:
  efek menuju defender yang benar) + tambah test miss-does-not-apply.
- **Test:** skill fisik dengan efek status dipaksa miss → status tidak
  terpasang, log `"Seranganmu meleset!"`.

## Pemeriksaan Tanpa Temuan (tidak ada fix)

- Konsistensi referensi silang seluruh data JSON (map exits, enemy_pool,
  starting_skills, skills musuh, dialog choices `next`, quest requirements
  `talk`/`enemy`, `next` quest, loot item, event grant_memory/start_quest,
  field wajib tiap entitas, stats hp/mp, base_stats semua STATS) — bersih.
- `dialog .index()` aman (equality dict berbasis konten).
- `apply_status` menerima duration <= 0 — hardening data, bukan bug runtime.
- `parse_input` menangani huruf kapital/spasi ganda dengan benar.

## Yang Sengaja TIDAK Diperbaiki (diterima sebagai risiko/keputusan desain)

- Path save dibersihkan menjadi huruf kecil (efek desain input
  case-insensitive; konvensi path default semua huruf kecil).
- Duplikasi kode `_mid_combat_game` vs flow uji — pembantu khusus test.

## Verifikasi

- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/ -q -p no:cacheprovider` hijau (354 test).
- `graphify update .` berjalan tanpa error.
