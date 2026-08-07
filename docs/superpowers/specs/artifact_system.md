# Spesifikasi Sistem Artefak Roh (Spirit Artifacts)

## 1. Konteks & Tujuan
Sesuai **GDD §7** dan **§21.3**, Artefak Roh adalah *item* khusus (berbeda dengan senjata biasa) yang akan **tumbuh bersama pemiliknya** (bisa naik level) dan merupakan prasyarat mutlak untuk *Ending Dinamis* (melawan Entitas Kuno). 

Mengikuti **Hukum Ponytail**, kita *TIDAK* akan membuat modul raksasa baru. Sistem ini akan didesain secara minimalis menggunakan `state.inventory["artifacts"]` yang sudah ada di `src/core/state.py`. 

## 2. Pendekatan Desain
1. **Definisi Data (JSON):** Artefak akan dibuat di `data/items/` dengan `"type": "artifact"`. Artefak memiliki field baru `growth_stat` (stat mana yang bertambah tiap level) dan `max_level`.
2. **Penyimpanan State:** XP dan Level artefak disimpan di `state.inventory["artifacts"]` dengan format `{"liontin_api": {"level": 1, "xp": 0}}`.
3. **Mekanik XP:** Karena pengguna tidak merinci sumber XP, kita ambil pendekatan paling *lazy* dan logis: **Otomatis dari pertarungan**. Setiap pertarungan yang dimenangkan memberikan *XP artefak* (bisa digabung di fungsi pemberian hadiah di `combat.py` atau `game_loop.py`).
4. **Efek Stat:** Saat bertarung, fungsi perhitungan stat (kemungkinan di `models/player.py` atau `engine/combat.py`) akan membaca level artefak yang sedang di-*equip* (`state.inventory["equipped"]`) dan menambahkan bonusnya secara dinamis.

---

## 3. Rencana Pengerjaan (Langkah demi Langkah)

Tugas dipecah menjadi unit kecil (2-5 menit) sesuai Hukum Superpowers.

### Langkah 1: Persiapan Test (TDD)
- **Tugas:** Buat file `tests/test_artifacts.py`.
- **Aksi:** Tulis test `test_artifact_level_up` dan `test_artifact_stat_bonus`. 
- **Verifikasi:** Jalankan `pytest -q tests/test_artifacts.py`. **Wajib gagal (RED)**.

### Langkah 2: Ekstensi Skema Item
- **File:** `src/engine/items.py`
- **Tugas:** Ubah `load_items` untuk menangani field `growth_stat` dan `max_level` khusus untuk item dengan `"type": "artifact"`.
- **Verifikasi:** Test gagal karena fungsi pemberian XP belum ada.

### Langkah 3: Fungsi Kenaikan Level (Level Up Logic)
- **File:** `src/engine/items.py` atau fungsi mandiri di dalamnya.
- **Tugas:** Buat fungsi `add_artifact_xp(state, artifact_id, amount)`. Jika XP mencapai batas (misal: `level * 100`), naikkan `level` dan reset XP. Modifikasi langsung ke `state.inventory["artifacts"][artifact_id]`.
- **Verifikasi:** `test_artifact_level_up` menjadi **GREEN**.

### Langkah 4: Integrasi Stat Combat
- **File:** `src/models/player.py` atau fungsi penghitung stat akhir.
- **Tugas:** Saat mengambil atribut pemain (misal: stat total), tambahkan bonus dari artefak yang sedang di-*equip*. Bonus = `base_stat + (level * multiplier)`.
- **Verifikasi:** `test_artifact_stat_bonus` menjadi **GREEN**. Semua pengujian di langkah 1 sekarang harus hijau.

### Langkah 5: Penambahan Data JSON (Content)
- **File:** `data/items/liontin_api.json` dan `data/items/cermin_bayangan.json` (2 Artefak Roh pertama untuk Arc 1).
- **Tugas:** Buat JSON valid sesuai skema yang telah diperbarui.
- **Verifikasi:** Jalankan `python tools/validate.py`. Harus sukses.

### Langkah 6: Tweak Game Loop / Combat
- **File:** `src/engine/combat.py` atau `src/core/game_loop.py`
- **Tugas:** Tambahkan baris kode untuk mendistribusikan XP (*insight*) yang didapat dari musuh ke semua artefak yang sedang dipakai (*equipped*).
- **Verifikasi:** *Smoke test* sederhana dengan mensimulasikan satu pertarungan dan melihat status XP artefak.

### Langkah 7: Cleanup & Refactor
- **Tugas:** Rapikan kode, berikan *docstring* Bahasa Indonesia berformat Google (sesuai `AGENTS.md §7`), pastikan tidak melanggar aturan linting.
- **Verifikasi:** `ruff check` dan `ruff format --check` bersih. Semua `pytest` lulus. `graphify update .` dijalankan.

---

## 4. Evaluasi Akhir (Definition of Done)
- [ ] Artefak bisa di-*equip* dan memengaruhi stat.
- [ ] Artefak mendapat XP pasca pertarungan.
- [ ] Naik level berjalan dengan benar.
- [ ] 2 Data JSON artefak masuk ke direktori data.
- [ ] Lulus pengujian otomatis (lint & test).
