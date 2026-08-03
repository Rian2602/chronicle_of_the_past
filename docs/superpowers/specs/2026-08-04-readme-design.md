# Spesifikasi: Rewrite README sebagai Panduan Pemain (2026-08-04)

## Latar Belakang

README (270 baris) memiliki fakta yang tidak lagi sesuai repo:
- Jumlah test: tertulis "340", aktual **353**.
- Pohon arsitektur menyebut `src/utils/validator.py`, `dice`, `logger` dan
  `src/core/config.py` — semua **dihapus** saat refactor 2026-08-03 (utils/
  kini hanya `json_loader.py`).
- `systems/` tidak mencantumkan `exploration_system` dan `status_system`.
- Klaim "Key yang hilang → default, tidak pernah crash" usang — sejak bugfix
  2026-08-04, file non-save / tanpa player memunculkan `SaveError` ramah.
- Belum mendokumentasikan `tools/bench.py`, alur menu lengkap, daftar kelas,
  save mid-combat, dan perilaku "perintah non-combat diblokir saat bertarung".

Keputusan pengguna: perombakan total menjadi **panduan lengkap untuk pemain
baru** (sinopsis, walkthrough Arc 1, tips bertarung, FAQ, troubleshooting),
tetap mempertahankan panduan authoring konten yang sudah akurat. Bahasa
Indonesia.

## Ruang Lingkup

1. Perbaiki semua fakta yang stale (di atas) agar sesuai kondisi aktual.
2. Tambahkan bagian panduan bermain berdasarkan konten **aktual** yang
   diverifikasi: alur menu, kelas, walkthrough, tips, FAQ.
3. Pertahankan bagian authoring konten (sudah akurat).
4. Catat quirk desain yang diketahui, tanpa memperbaiki kode/konte.

## Struktur README Baru

1. Judul + tagline + pitch + fitur ringkas
2. Instalasi (Python 3.12+, stdlib only; pytest opsional)
3. Menjalankan Game (menu 5 item, navigasi, alur new game)
4. Kelas (tabel 5 kelas + xp_bonus Scholar 1.2)
5. Perintah (non-combat + combat + catatan blokir saat bertarung)
6. Sinopsis Arc 1
7. Walkthrough Arc 1 (6 langkah terverifikasi)
8. Tips Bertarung
9. Sistem Inti (waktu/rest, level, ekonomi)
10. Save / Continue (termasuk mid-combat, format 3-layer, SaveError ramah)
11. FAQ & Troubleshooting
12. Arsitektur (pohon diperbarui)
13. Panduan Authoring Konten (dipertahankan)
14. Testing & Tools (353 test, tools/bench.py)
15. Catatan Pengembangan (quirk diketahui)

## Fakta Kunci yang Harus Tercermin (hasil verifikasi data)

- 5 kelas: warrior, mage, ranger, assassin, scholar (scholar xp_bonus 1.2).
- `talk` memakai ID NPC (`talk old_man`), bukan nama tampilan.
- 3 musuh: goblin (aggressive, 30 XP), wild_wolf (coward, 40 XP), bandit
  (aggressive, 70 XP). Wolf kabur saat HP rendah.
- 2 peta: Ashen Village (threat 0, pool kosong) & Ashen Forest (threat 2).
- Encounter: 40% per explore, 50% saat night. Quest002 hanya dipenuhi
  membunuh Wild Wolf.
- quest001 & quest002 mulai **bersamaan** saat pertama `talk old_man` →
  pilih `1` (bukan berurutan).
- Reward quest001: +50 XP, +20 emas, +10 reputasi merchant_guild.
- Reward quest002: +40 XP, +15 emas, +5 reputasi merchant_guild.
- Kemenangan wolf: +40 XP, 8-16 emas, loot herb 50%.
- Level-up hanya diproses lewat kemenangan combat (threshold 50 × level).
- **Tidak ada game over**; kalah → `rest` → coba lagi.
- Save mid-combat didukung; file non-save/tanpa player → `SaveError` ramah.

## Yang TIDAK Dilakukan

- Tidak menambah badge/lisensi/CI/screenshot.
- Tidak membuat file panduan terpisah.
- Tidak memperbaiki bug konten (quirk hanya dicatat di bagian 15).

## Verifikasi

- Setiap fakta README cocok dengan data aktual (perintah `talk old_man`,
  walkthrough dll. sudah diverifikasi).
- `python3 -c "import README"` tidak relevan; verifikasi manual via catatan
  fakta di atas.
- Test & kode tidak disentuh: `pytest` tetap 353 hijau.

## Deliverable

- Commit 1: `docs/superpowers/specs/2026-08-04-readme-design.md`.
- Commit 2: rewrite README.md.
- Push ke master.
