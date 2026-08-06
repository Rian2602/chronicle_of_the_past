# Rencana Implementasi — Sistem Alkimia/refine + Fix `_cmd_use`

> **Untuk agentic workers:** eksekusi task-by-task (checkbox). Setiap task:
> RED (tulis test gagal) → GREEN (implementasi minimal) → verifikasi → commit.

**Goal:** Menutup gap target konten Arc 1 (0 dari 3 resep, GDD §22) dengan sistem
alkimia data-driven — pemain **belajar resep** (item `resep_*` → `use`), **meracik**
(`refine`, butuh **Kuali Roh** + bahan), lalu memakai pil hasil racikan. Sekaligus
memperbaiki bug `_cmd_use` (item terkonsumsi sebelum validasi data) dan **menolak
`use` pada bahan** (mencegah bahan terbuang percuma).

**Keputusan desain (disetujui pengguna):**
* 3 resep Arc 1 memakai SEMUA 5 bahan mati: `pil_pemulih` = esensi_api×2 +
  esensi_tanah×1 · `pil_qi` = esensi_air×2 + esensi_kayu×1 · `pil_pemahaman` =
  esensi_kayu×2 + batu_qi×1.
* Resep DIPELAJARI dulu: item `resep_*` (type=recipe, efek `learn_recipe`) → `use`
  → flag `recipe_<item>_known` (di `state.flags`, TANPA bump schema save).
* Alat: item `kuali_roh` (type=tool) wajib di tas saat `refine`.
* Distribusi: `kuali_roh` + 3 `resep_*` ditambah ke stok `pedagang_kelana`.
* `refine <item_id>` → 1 pil, tanpa RNG/kualitas; alias `racik` sudah terdaftar.

**Global Constraints (AGENTS §1–§12):**
- TDD wajib: RED → GREEN → REFACTOR → commit (§2.1). Data JSON diuji dulu.
- `pytest -q` · `ruff check` · `ruff format --check` · `python tools/validate.py`
  wajib hijau sebelum DoD; `graphify update .` setelah ubah kode.
- Tidak menyentuh file stabil: `combat.py`, `cultivation.py`, `models/player.py`.
- Bahasa Indonesia untuk semua teks; docstring Google (header Inggris, isi Indonesia).
- Format commit AGENTS §9: `<lingkup>: <ringkasan>`.
- Pola test pakai helper eksisting (`_session(tmp_path)` + `_dispatch`), bukan
  fixture baru yang tak ada.

---

### Task 1 — Fix `_cmd_use`: validasi sebelum konsumsi + tolak bahan

**Files:** `src/core/game_loop.py` · `tests/test_game_loop.py`

- [ ] **Step 1 (RED):** tambah 2 test:
  - `test_use_item_tak_dikenal_tidak_konsumsi`: injeksi `items["hantu_item"] = 1` →
    `use hantu_item` → pesan "tidak dikenal" + item TETAP di tas (bug saat ini:
    terkonsumsi dulu di `game_loop.py` sebelum cek katalog).
  - `test_use_bahan_ditolak`: injeksi `esensi_api` ×1 → `use esensi_api` → pesan
    "racik dulu" / bahan tak bisa dipakai + item TETAP ada (perangkap: bahan
    terbuang tanpa efek).
- [ ] **Step 2:** jalankan, pastikan GAGAL: `pytest tests/test_game_loop.py -q`.
- [ ] **Step 3 (GREEN):** di `_cmd_use`: pindahkan `catalog = load_items()` dan cek
  `item is None` SEBELUM `items[item_id] -= 1`; tambah guard
  `if item.get("type") == "material": return ["... racik dulu ..."]`.
- [ ] **Step 4:** `pytest tests/test_game_loop.py -q` hijau + full suite.
- [ ] **Step 5 (Commit):** `engine: fix _cmd_use (validasi sebelum konsumsi) + tolak pakai bahan (GDD 7)`

---

### Task 2 — Data: resep, alat, item resep + whitelist efek

**Files:** `data/items/pil_pemulih.json`, `pil_qi.json`, `pil_pemahaman.json`,
`data/items/kuali_roh.json` (baru), `data/items/resep_pemulih.json`,
`resep_qi.json`, `resep_pemahaman.json` (baru) · `data/shops/pedagang_kelana.json`
· `tools/validate.py` (whitelist) · `tests/test_items.py`, `tests/test_shop_data.py`,
`tests/test_validate_tool.py`

- [ ] **Step 1 (RED):**
  - `test_items.py`: `resep_*` & `kuali_roh` ada (skema id/name); pil ber-resep
    wajib punya `recipe` dengan ingredient yang ADA & bertype `material`.
  - `test_shop_data.py`: 4 item baru ada di stok toko & berharga (`price` int ≥ 1).
  - `test_validate_tool.py`: efek `learn_recipe` DITOLAK sebelum masuk whitelist
    (RED) — validasi whitelist `valid_item_effects`.
- [ ] **Step 2:** jalankan, pastikan GAGAL.
- [ ] **Step 3 (GREEN):** tambah field `recipe` di 3 pil; buat 4 file item baru
  (`kuali_roh` price 150, `resep_*` price 60, efek `{"learn_recipe": "<item>"}`);
  tambah 4 entri ke stok toko; `tools/validate.py` `valid_item_effects` +=
  `"learn_recipe"` (satu commit dengan data agar validator tetap hijau).
- [ ] **Step 4:** `pytest` (3 file) + `python tools/validate.py` hijau.
- [ ] **Step 5 (Commit):** `data: 3 resep pil Arc 1 + kuali roh + item resep + whitelist learn_recipe (GDD 7/22)`

**Catatan perilaku (tulis di commit):** `fquest_pelipur` mengoleksi batu_qi ×3 —
meracik batu_qi bisa membuka ulang objektif (pola sama dengan `sell`, acceptable).

---

### Task 3 — Engine: loader `recipe` + belajar resep + `_cmd_refine`

**Files:** `src/engine/items.py` · `src/core/game_loop.py` · `src/core/input.py` (jika perlu)
· `tests/test_items.py`, `tests/test_game_loop.py`

- [ ] **Step 1 (RED):**
  - `test_items.py`: `load_items` membawa field `recipe` (koreksi evaluasi —
    loader saat ini MEMBUANG field tak dikenal).
  - `test_game_loop.py`:
    - `use resep_pemulih` → flag `recipe_pil_pemulih_known` terset + item resep habis.
    - `refine pil_pemulih` tanpa flag → ditolak "belum mempelajari".
    - `refine` tanpa `kuali_roh` → ditolak.
    - `refine` bahan kurang → ditolak, bahan tak berubah.
    - `refine` sukses → bahan berkurang sesuai resep + pil masuk ×1 + cascade quest/event.
    - `refine` item tanpa resep / tak dikenal → pesan jelas.
- [ ] **Step 2:** jalankan, pastikan GAGAL.
- [ ] **Step 3 (GREEN):**
  - `items.py`: `items[raw["id"]]` += `"recipe": raw.get("recipe")`.
  - `_cmd_use`: cabang efek `learn_recipe` → `self.state.flags[f"recipe_{target}_known"] = True`.
  - `_cmd_refine` (baru): validasi resep ada → flag diketahui → `kuali_roh` di tas →
    bahan cukup → konsumsi bahan → tambah output ×1 → `_run_quests()`+`_run_events()`.
  - `AVAILABLE` += `"refine"`; baris help.
- [ ] **Step 4:** `pytest` scoped + full hijau; `ruff` bersih.
- [ ] **Step 5 (Commit):** `engine: loader recipe + command refine + belajar resep (GDD 18.2)`

---

### Task 4 — Validator: referensi resep

**Files:** `tools/validate.py` · `tests/test_validate_tool.py`

- [ ] **Step 1 (RED):** validator menolak: (a) ingredient `recipe` → item tak dikenal;
  (b) item `type=recipe` dengan `learn_recipe` → target tak ada.
- [ ] **Step 2:** jalankan, pastikan GAGAL.
- [ ] **Step 3 (GREEN):** `validate.py` — loop item ber-`recipe`: tiap `req["item"]` ada
  di `items`; loop item type=recipe: target `learn_recipe` ada.
- [ ] **Step 4:** `pytest tests/test_validate_tool.py` + `python tools/validate.py` OK.
- [ ] **Step 5 (Commit):** `tools: validator cek referensi resep (GDD 25.3)`

---

### Task 5 — Dokumentasi

**Files:** `GDD.md` · `AGENTS.md` · `tests/test_docs.py`

- [ ] **Step 1:** GDD §7 baris Alkimia (`:223`) — sebut mekanik belajar (item resep),
  alat `kuali_roh`, 3 resep Arc 1; GDD §18.2 `refine` (`:639`) — "butuh resep
  dipelajari + kuali roh + bahan"; changelog **v1.2** (di atas `:824`).
- [ ] **Step 2:** AGENTS §6 inventori (`:285`) 21 → **25 item**.
- [ ] **Step 3:** `pytest tests/test_docs.py -q` hijau.
- [ ] **Step 4 (Commit):** `docs: sistem alkimia GDD v1.2 + sinkron AGENTS`

---

### Task 6 — Verifikasi akhir (DoD, AGENTS §12)

- [ ] `pytest -q` · `ruff check src launcher.py tools tests` · `ruff format --check`
- [ ] `python tools/validate.py` · `graphify update .`
- [ ] Smoke test: beli kuali+resep+bahan di toko → `use resep` (flag) → `refine`
      → `use pil` (efek) → save/load (flag persisten) → `rest` (restock).
- [ ] Review dua tahap (kepatuhan GDD → kualitas kode); polish bila ada.

**Sengaja dilewati (catatan `ponytail:`):** kualitas pil (rendah→surgawi), RNG/gagal
racik, `refine` jumlah>1, resep via quest/event Arc 2 (cukup beli toko), lab alkimia
(lokasi khusus), resep sebagai pengetahuan permanen (flag tak dihapus).
