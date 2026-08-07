# Fase 4 (Penyelesaian CotP) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mengimplementasikan Arc 4 (Final Arc), Sistem Ending Dinamis, dan melengkapi target akhir data (teknik, artefak, musuh) untuk merampungkan proyek *Chronicle of the Past*.

**Architecture:** Menerapkan logika kalkulasi ending berdasarkan poin di `src/engine/story.py`, memicu event ending dinamis (`ending_defy`, `ending_seal`, `ending_reconcile`), dan mengenerate sisa aset data (quest401-408, bos final). Semua aset mematuhi arsitektur data-driven (JSON) di GDD.

**Tech Stack:** Python 3.12+, pytest, json, pathlib

## Global Constraints

- **TDD:** Wajib menulis tes kegagalan (RED) sebelum implementasi (GREEN) untuk semua engine.
- **Lore & Tone:** Grimdark (tidak ada menang mutlak, konsekuensi abadi), bahasa Indonesia.
- **Data Validation:** Validator `tools/validate.py` dan pytest harus lulus sebelum diklaim selesai.
- **Isolasi Workspace:** Gunakan `superpowers:using-git-worktrees` untuk task ini.

---

### Task 1: Sistem Kalkulasi Ending Dinamis (Engine)

**Files:**
- Create: `src/engine/story.py`
- Modify: `tests/test_story.py` (Create)

**Interfaces:**
- Consumes: `state.ending_points`, `state.reputation`
- Produces: `calculate_ending(state: GameState) -> str` mengembalikan ID dari ending pemenang ("defy", "seal", atau "reconcile").

- [ ] **Step 1: Write the failing test**

```python
# tests/test_story.py
from src.core.state import GameState
from src.engine.story import calculate_ending

def test_calculate_ending_defy_wins():
    state = GameState()
    state.ending_points = {"defy": 50, "seal": 20, "reconcile": 10}
    assert calculate_ending(state) == "defy"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_story.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.engine.story'"

- [ ] **Step 3: Write minimal implementation**

```python
# src/engine/story.py
from src.core.state import GameState

def calculate_ending(state: GameState) -> str:
    points = state.ending_points
    # Cari nilai maksimum
    max_score = max(points.values())
    # Kembalikan key pertama yang mencapai nilai maksimum (tie-break sederhana)
    for path, score in points.items():
        if score == max_score:
            return path
    return "seal"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_story.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_story.py src/engine/story.py
git commit -m "feat: add ending calculation logic"
```

---

### Task 2: Pembuatan Event Ending (Data)

**Files:**
- Create: `data/events/ending_defy.json`
- Create: `data/events/ending_seal.json`
- Create: `data/events/ending_reconcile.json`
- Modify: `tests/test_event_data.py:55` (tambah event ke `EXPECTED_EVENTS`)

**Interfaces:**
- Consumes: Schema event JSON.
- Produces: 3 file event yang menampilkan teks klimaks (log) sesuai jalur.

- [ ] **Step 1: Write the failing test**

Ubah `tests/test_event_data.py` (tambahkan 3 ID ending ke `EXPECTED_EVENTS`).

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_event_data.py::test_terdapat_file_event_yang_diharapkan`
Expected: FAIL karena 3 file JSON belum ada di folder `data/events`.

- [ ] **Step 3: Write minimal implementation**

```json
// data/events/ending_defy.json
{
  "id": "ending_defy",
  "trigger": [
    {"kind": "flag", "flag": "arc4_boss_defeated", "operator": "EQUALS", "value": true},
    {"kind": "flag", "flag": "path_defy_won", "operator": "EQUALS", "value": true}
  ],
  "actions": [
    {"kind": "log", "text": "Kamu menentang entitas kuno, membelah langit, namun dunia terbakar dalam kekacauan murni."}
  ],
  "once": true
}
```
*(Buat hal serupa untuk ending_seal.json dan ending_reconcile.json)*

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_event_data.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add data/events/ending*.json tests/test_event_data.py
git commit -m "feat: add dynamic ending events"
```

---

### Task 3: Peta & Musuh Arc 4 (Data)

**Files:**
- Create: `data/maps/ancient_vault.json`, `data/maps/sky_seal.json`
- Create: `data/enemies/suara.json`, `data/enemies/rasul_langit.json`
- Modify: `tests/test_map_data.py` dan `tests/test_enemy_data.py`

**Interfaces:**
- Consumes: Schema map dan enemy.
- Produces: Akses area final dan bos tier 5/6 (Penantang Surga).

- [ ] **Step 1: Write the failing test**

Tambahkan `ancient_vault` dan `sky_seal` ke `EXPECTED_MAPS`. Tambahkan `suara` dan `rasul_langit` ke `EXPECTED_ENEMIES`.

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_map_data.py tests/test_enemy_data.py -q`
Expected: FAIL karena file belum dibuat.

- [ ] **Step 3: Write minimal implementation**

Tulis `suara.json` (boss, element air/api, tier heaven_challenger) dan `rasul_langit.json` (boss, tier void_breaker).
Tulis `ancient_vault.json` dan `sky_seal.json` menghubungkannya ke musuh-musuh tersebut menggunakan mekanisme `requires_flag`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_map_data.py tests/test_enemy_data.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add data/maps/*.json data/enemies/*.json tests/test_*.py
git commit -m "feat: add arc 4 maps and final bosses"
```

---

### Task 4: Rantai Quest Arc 4 (Data)

**Files:**
- Create: `data/quests/quest401.json` s/d `data/quests/quest408.json`
- Create: `data/events/quest401_intro.json` dll.
- Modify: `tests/test_quest_data.py`

**Interfaces:**
- Produces: Rantai kelanjutan dari `quest308_done` menuju akhir permainan (`quest408_done`).

- [ ] **Step 1: Write the failing test**

Tambahkan `quest401` s/d `quest408` ke `EXPECTED_QUESTS`.

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_quest_data.py -q`
Expected: FAIL.

- [ ] **Step 3: Write minimal implementation**

Gunakan skrip Python sementara (`scratch_create_quests_arc4.py`) untuk menghasilkan 8 quest Arc 4 secara otomatis (mirip dengan Arc 1-3) guna efisiensi. Pastikan quest406 membunuh `rasul_langit` dan quest408 membunuh `suara`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_quest_data.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add data/quests/quest40*.json data/events/*40*.json tests/test_quest_data.py
git commit -m "feat: add arc 4 main quests"
```

---

### Task 5: Pelengkapan Sisa Aset & Polish

**Files:**
- Modify: `data/techniques/`, `data/items/`, `data/companions/`

**Interfaces:**
- Produces: Penambahan kekurangan target aset: ~10 teknik (Fokus: Alkimia/Jiwa), ~9 resep, ~9 artefak, ~2 binatang roh baru (rekrut/telur).

- [ ] **Step 1: Write the failing test**

Buat asersi di file tes terpisah (`tests/test_final_assets.py`) yang memeriksa jumlah file: teknik >= 30, resep >= 14, artefak >= 12, companion >= 4.

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_final_assets.py -q`
Expected: FAIL karena jumlah aset masih di bawah target.

- [ ] **Step 3: Write minimal implementation**

Gunakan skrip Python massal untuk membuat file-file tersebut dengan mengisi parameter JSON sesuai skema `tools/validate.py`. 

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_final_assets.py tools/validate.py -q`
Expected: PASS dan semua referensi OK.

- [ ] **Step 5: Commit**

```bash
git add data/ tests/test_final_assets.py
git commit -m "feat: complete target data generation for final release"
```
