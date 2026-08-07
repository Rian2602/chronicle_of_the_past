# Master Plan Penyelesaian — Chronicle of the Past (Revisi 7 Agustus 2026)

> **Untuk pekerja agen:** WAJIB SUB-SKILL: gunakan `superpowers:subagent-driven-development`
> (disarankan) atau `superpowers:executing-plans` untuk mengimplementasikan rencana ini
> task-by-task. Setiap step memakai checkbox (`- [ ]`) untuk pelacakan.

**Goal:** Menuntaskan sisa proyek *Chronicle of the Past* — stabilisasi suite, sistem ending
dinamis, konten Arc 3 asli, Arc 4 penuh, ritual & epilog — hingga memenuhi target GDD §22 dan
Definisi Selesai AGENTS.md §12.

**Architecture:** Semua gating & narasi lewat event engine data-driven (GDD §15), konten JSON
mengikuti skema GDD §14, engine di `src/` mengikuti pola modul yang sudah ada (event.py,
quest.py, story.py). Perubahan data WAJIB disinkronkan dengan konstanta exact-set di tests.
Tidak menyentuh file stabil Fase 0 (`combat.py`, `cultivation.py`, `models/player.py`).

**Tech Stack:** Python 3.12+ (perintah: `python3`), Rich/Textual, pytest, ruff, `tools/validate.py`.

---

## Koreksi Baseline (elaborasi temuan audit vs `rencana_penyelesaian_cotp.md`)

Rencana sumber ditulis pada kondisi lama. Berikut delta terhadap kondisi **aktual terverifikasi**
(7 Agustus 2026): `pytest` 455 passed + 1 failed (`test_story.py::test_apply_action_calculate_ending`)
+ 1 flaky (`test_app.py`); `ruff check` 2 error; `ruff format` 1 file; `validate.py` OK; branch
`feature/dynamic-ending-engine` aktif, 0 commit, perubahan ending belum di-commit.

| Item rencana lama | Status aktual | Aksi dalam rencana ini |
|---|---|---|
| P1-A fix lint `test_app.py:234` | ✅ Sudah beres | — (lint error sekarang di `test_story.py`; Task 1) |
| P1-B sistem artefak (`growth_stat`) | ✅ Sudah ada (`items.py`, test_artifacts GREEN) | — |
| P1-C command meditate/examine/loot/recall/settings/formation | ✅ Semua `_cmd_*` sudah ada | — |
| P1-D data Arc 2 | ✅ Selesai (NPC, musuh, dialog, teknik, resep, artefak) | — |
| P2-A sistem formasi | ✅ Sudah ada (3 formasi, `formation_skill`) | — |
| P2-B `ending_points` + `add_ending_points` | ✅ state & aksi ada | ⚠️ tinggal aksi `calculate_ending` (Task 1–2) |
| P2-C binatang roh evolusi/menetas/recall | ✅ Sudah ada | — |
| P3 Arc 3 | ⚠️ Scaffolding ada (peta, NPC, bos, teknik), **quest301–308 & fquest_301–303 masih placeholder** | Task 3 |
| P4 Arc 4 + Ending | ❌ 0% (quest401–408, 3 peta, 2 bos final, the_voice, memori, ending) | Task 4–6 |
| P5 Polish | ❌ Belum | Task 7 |

**Kondisi data aktual:** quest 24 file (16 nyata + 8 placeholder) · peta 9 (7 GDD + 2 ekstra) ·
NPC 18 · musuh 20 (15 non-bos, 5 bertag bos) · teknik 30/30 ✓ · resep 12/14 · artefak 8/12 ·
binatang roh 3 (+1 evolusi) · memori 5/9 · event 45.

---

## Global Constraints

- Bahasa Indonesia untuk semua `name`, `description`, `text`; nada **grimdark** (GDD §3.6) —
  tidak ada kemenangan bersih, konsekuensi abadi.
- Python 3.12+, **stdlib dulu**, Rich/Textual boleh dipakai; **DILARANG dependency baru**.
- Google Python Style Guide: baris ≤ 80, double quotes, docstring header English + prosa Indonesia.
- **TDD wajib**: kode produksi tidak boleh mendahului test gagal (RED → GREEN → REFACTOR → COMMIT).
- Data JSON: update konstanta exact-set di tests **dulu** (RED), baru tambah data (GREEN), lalu
  `python3 tools/validate.py` + `pytest`.
- ID `snake_case`; flag quest wajib `quest<id>_done`; gating peta/cerita via event engine
  (`unlock_map`, `map_<id>_unlocked`) — dilarang hardcode.
- Siklus elemen `Metal→Kayu→Tanah→Air→Api→Metal` konsisten.
- **Jangan sentuh** `src/engine/combat.py`, `src/engine/cultivation.py`, `src/models/player.py`
  (AGENTS.md §6) tanpa instruksi eksplisit.
- Save schema tetap **v2**; field baru hanya via backfill (lihat pola `party_active`).
- Verifikasi wajib sebelum commit: `pytest -q`, `ruff check`, `ruff format --check`,
  `python3 tools/validate.py`, `graphify update .`.
- Nama perintah CLI: `python3` (bukan `python`).

---

### Task 1: Stabilisasi — wire aksi `calculate_ending` & hijaukan suite

**Files:**
- Modify: `src/engine/event.py` (set `ACTION_KINDS` baris ~29–43 + fungsi `apply_action` ~127)
- Modify: `tests/test_story.py` (hapus import `pytest` tak terpakai; rapikan baris > 80)
- Modify: `src/engine/story.py` (jalankan `ruff format`)
- Test: `tests/test_story.py` (7 test existing)

**Interfaces:**
- Consumes: `src/engine/story.calculate_ending(state: GameState) -> str` (sudah ada,
  mengembalikan `"defy"` / `"seal"` / `"reconcile"`), `state.flags`.
- Produces: aksi event baru `{"kind": "calculate_ending"}` yang men-set flag
  `ending_<jalur>_win`; suite hijau penuh.

- [ ] **Step 1: Buktikan kegagalan (RED)**
  Jalankan: `pytest tests/test_story.py -q`
  Expected: 1 failed — `test_apply_action_calculate_ending` dengan
  `ValueError: kind aksi tidak dikenal: calculate_ending`.

- [ ] **Step 2: Implementasi minimal (GREEN) — `src/engine/event.py`**
  Tambahkan `"calculate_ending"` ke set `ACTION_KINDS`:

  ```python
  ACTION_KINDS = {
      "set_flag",
      "clear_flag",
      "unlock_map",
      "start_quest",
      "grant_memory",
      "grant_item",
      "grant_gold",
      "change_reputation",
      "start_dialog",
      "add_companion",
      "log",
      "prompt_choice",
      "add_ending_points",
      "calculate_ending",
  }
  ```

  Tambahkan import di bagian atas (setelah import `load_companion`):

  ```python
  from src.engine.story import calculate_ending
  ```

  Tambahkan cabang di akhir rantai `if kind == ...` pada `apply_action`:

  ```python
      elif kind == "calculate_ending":
          # GDD §21.1: jalur poin tertinggi menentukan ending; flag menang
          # dipakai trigger event ending (Task 2).
          winner = calculate_ending(state)
          state.flags[f"ending_{winner}_win"] = True
  ```

  Catatan: flag LOSER tidak di-set — test menuntut `ending_defy_win is None`.

- [ ] **Step 3: Bersihkan `tests/test_story.py`**
  - Hapus baris `import pytest` (unused — error F401).
  - Ganti docstring baris 31 agar ≤ 80 karakter:
    ```python
    def test_calculate_ending_reconcile_highest():
        """Jalur reconcile poin tertinggi harus mengembalikan 'reconcile'."""
    ```

- [ ] **Step 4: Format `src/engine/story.py`**
  Jalankan: `ruff format src/engine/story.py` (memperbaiki baris 63).

- [ ] **Step 5: Verifikasi (GREEN)**
  Jalankan: `pytest tests/test_story.py -q` → 7 passed.
  Jalankan: `ruff check src launcher.py tools tests` → 0 error.
  Jalankan: `ruff format --check src launcher.py tools tests` → 59 files formatted.
  Jalankan: `python3 tools/validate.py` → OK.

- [ ] **Step 6: Commit**
  ```bash
  git add src/engine/event.py src/engine/story.py tests/test_story.py
  git commit -m "feat(story): wire aksi calculate_ending + hijaukan suite"
  ```

---

### Task 2: Event ending data-driven + perbaiki flaky test

**Files:**
- Create: `data/events/calculate_ending_trigger.json`
- Create: `data/events/ending_defy.json`, `data/events/ending_seal.json`,
  `data/events/ending_reconcile.json`
- Modify: `tests/test_event_data.py` (set `EXPECTED_EVENTS` +4 entri)
- Investigate & fix: `tests/test_app.py::test_pilih_option_serang_melakukan_battle_step` (flaky)
- Test: `tests/test_event_data.py`, `tests/test_story.py`, `tests/test_app.py`

**Interfaces:**
- Consumes: flag `arc4_boss_defeated` (di-set Task 5 saat bos final kalah), flag
  `ending_<jalur>_win` (dari aksi `calculate_ending`, Task 1).
- Produces: 4 event JSON valid + skema terdaftar; suite hijau stabil 5× berturut-turut.

> **Urutan evaluasi** (GDD §15.4): file dievaluasi urut abjad per pass. Nama
> `calculate_ending_trigger` mengurut SEBELUM `ending_*` (`c` < `e`), sehingga dalam satu
> pass yang sama: trigger men-set flag pemenang → event ending langsung terpicu (cascade).

- [ ] **Step 1: Update test (RED) — `tests/test_event_data.py`**
  Tambah ke `EXPECTED_EVENTS` (set persis — file JSON harus cocok 1:1):
  ```python
      "calculate_ending_trigger",
      "ending_defy",
      "ending_seal",
      "ending_reconcile",
  ```
  Jalankan: `pytest tests/test_event_data.py -q`
  Expected: FAIL — keempat file belum ada.

- [ ] **Step 2: Buat `data/events/calculate_ending_trigger.json`**
  ```json
  {
    "id": "calculate_ending_trigger",
    "trigger": [
      {"kind": "flag", "flag": "arc4_boss_defeated", "operator": "EQUALS", "value": true}
    ],
    "actions": [
      {"kind": "calculate_ending"}
    ],
    "once": true
  }
  ```

- [ ] **Step 3: Buat 3 event ending (narasi grimdark, GDD §13/§21.2)**
  `data/events/ending_defy.json`:
  ```json
  {
    "id": "ending_defy",
    "trigger": [
      {"kind": "flag", "flag": "ending_defy_win", "operator": "EQUALS", "value": true}
    ],
    "actions": [
      {"kind": "log", "text": "MENENTANG LANGIT — ..."}
    ],
    "once": true
  }
  ```
  Ulangi pola untuk `ending_seal` (flag `ending_seal_win`) dan `ending_reconcile`
  (flag `ending_reconcile_win`). Teks log: epilog jalur masing-masing, Bahasa Indonesia
  grimdark, 3–6 kalimat (isi faksi selamat/berkuasa mengikuti Task 6 `build_epilogue`).

- [ ] **Step 4: GREEN — validasi**
  Jalankan: `pytest tests/test_event_data.py -q` → pass.
  Jalankan: `python3 tools/validate.py` → OK.

- [ ] **Step 5: Selidiki test flaky (systematic debugging, AGENTS §2.6)**
  1. Reproduksi: jalankan `pytest -q` 5× berurutan, catat berapa kali
     `test_pilih_option_serang_melakukan_battle_step` gagal.
  2. Baca `tests/test_app.py` (test tsb) dan bagian battle di `src/ui/app.py` — cari
     shared state antar test / urutan yang bergantung pada state global.
  3. Hipotesis akar masalah (mis. state UI tidak di-reset antar test), buktikan dengan
     jalankan test tersebut bersama test lain yang dicurigai.
  4. Implementasi fix minimal (biasanya: fixture fresh state / reset di akhir test).
  5. Verifikasi: `pytest -q` 5× berturut-turut → 0 failed.

- [ ] **Step 6: Commit**
  ```bash
  git add data/events/calculate_ending_trigger.json data/events/ending_defy.json \
      data/events/ending_seal.json data/events/ending_reconcile.json \
      tests/test_event_data.py tests/test_app.py
  git commit -m "feat(story): event ending data-driven + fix flaky test_app"
  ```

---

### Task 3: Arc 3 — ganti placeholder quest301–308 & fquest_301–303 dengan konten asli

**Files:**
- Modify: `data/quests/quest301.json` … `quest308.json` (8 file, konten placeholder → asli)
- Modify: `data/quests/fquest_301.json`, `fquest_302.json`, `fquest_303.json`
- Create: `data/story/memory_entitas_pertama.json`, `data/story/memory_arc3_choice.json`
- Create: `data/enemies/tentara_salib.json`, `data/enemies/uskup_muda.json`,
  `data/enemies/mata_gilda.json`, `data/enemies/iblis_formasi.json`
- Create: `data/items/resep_pil_kristal.json`, `data/items/resep_pil_baja_tubuh.json`
  (2 resep → total 14, target GDD §22)
- Create: `data/items/pedang_taring_naga.json` (artefak → total 9)
- Create: `tests/test_arc3_data.py` (guard placeholder + kuota Arc 3)
- Test: `tests/test_quest_data.py`, `tests/test_arc3_data.py`

**Interfaces:**
- Consumes: skema quest GDD §12.3 (`objectives` array objek, `next`, `requires_flag`),
  NPC `sera_ember`/`inquisitor_vega` (sudah ada), musuh `bos_inquisitor_agung` (sudah ada),
  event `fquest_301_intro` dkk (sudah ada, mereferensikan quest id yang sama).
- Produces: 8 quest main Arc 3 + 3 faksi Arc 3 dengan konten naratif asli; memori & musuh
  Arc 3; flag `quest301_done`…`quest308_done` valid.

- [ ] **Step 1: Tulis test guard placeholder (RED) — buat `tests/test_arc3_data.py`**
  ```python
  """Guard konten Arc 3: dilarang placeholder & kuota musuh/artefak (GDD §22)."""

  import json
  from pathlib import Path

  DATA_DIR = Path(__file__).resolve().parents[1] / "data"


  def test_tidak_ada_judul_quest_placeholder():
      """Judul quest tidak boleh berupa template 'Quest questXXX Title'."""
      pattern = ("Quest quest", " Title")
      for path in (DATA_DIR / "quests").glob("quest3*.json"):
          raw = json.loads(path.read_text(encoding="utf-8"))
          assert not raw["title"].startswith(pattern[0]), (
              f"{path.name}: judul masih placeholder: {raw['title']}"
          )


  def test_kuota_artefak_arc3_minimal():
      """Target artefak GDD §22 (12 total) — minimal 9 sudah ada setelah task ini."""
      artifacts = [
          json.loads(p.read_text(encoding="utf-8"))
          for p in (DATA_DIR / "items").glob("*.json")
      ]
      count = sum(1 for a in artifacts if a.get("type") == "artifact")
      assert count >= 9
  ```
  Jalankan: `pytest tests/test_arc3_data.py -q`
  Expected: FAIL (placeholder masih ada, artefak 8 < 9).

- [ ] **Step 2: Tulis ulang quest301–308 dengan konten asli**
  Chain: `quest301.requires_flag = "quest208_done"`, lalu tiap quest
  `requires_flag` quest sebelumnya, `next` quest berikutnya (quest308 `next: null`).
  Contoh lengkap `data/quests/quest301.json`:

  ```json
  {
    "id": "quest301",
    "title": "Panggilan dari Bayang-Bayang",
    "type": "main",
    "category": "main",
    "description": "Sebuah utusan pemberontak menyelipkan petunjuk ke dalam kotamu: Sera Ember menunggu di markas bawah tanah. Orde Suci sudah tahu namamu.",
    "requires_flag": "quest208_done",
    "objectives": [
      {"kind": "map", "target": "rebel_hideout"},
      {"kind": "talk", "target": "sera_ember"}
    ],
    "rewards": {"insight": 60, "gold": 40, "reputation": {"rebels": 10}},
    "flags_on_complete": ["quest301_done"],
    "next": "quest302"
  }
  ```

  Ringkasan konten quest302–308 (tulis lengkap dengan pola di atas; nada grimdark):

  | ID | Judul | Objektif kunci | Reputasi reward |
  |---|---|---|---|
  | quest302 | Infiltrasi Katedral | `map` holy_cathedral → `enemy` penebus_orde_suci ×2 | holy_order −5 |
  | quest303 | Dua Sisi Pedang | `talk` inquisitor_vega + `flag` (`prompt_choice` di event memilih faksi) | sesuai pilihan |
  | quest304 | Martir atau Pejuang | `talk` sera_ember + `enemy` iblis_formasi | rebels +5 |
  | quest305 | Entitas Bergerak | `enemy` kultis_bayangan ×2 + flag `grant_memory` (via event quest305_done) | ancient_order +5 |
  | quest306 | Pengkhianat di Antara Kita | `kill_count` pembunuh_gilda 2 | guilds −5 |
  | quest307 | Segel yang Retak | `flag` quest306_done + `enemy` tentara_salib | holy_order −10 |
  | quest308 | Satu Jalan Tersisa | `enemy` bos_inquisitor_agung | — |

  Rewards tiap quest: `{"insight": 60, "gold": 40, "reputation": {...}}` +
  `flags_on_complete: ["quest<id>_done"]`.

- [ ] **Step 3: Tulis ulang fquest_301–303 (faksi Arc 3)**
  - `fquest_301` — Orde Suci: `requires_flag: "quest303_done"`, objektif
    `enemy` tentara_salib, reward reputasi `holy_order +5`.
  - `fquest_302` — Pemberontak: `requires_flag: "quest303_done"`, objektif
    `enemy` pembelot_pemberontak, reward `rebels +5`.
  - `fquest_303` — Gilda (dari Kestrel): `requires_flag: "quest303_done"`, objektif
    `kill_count` pembunuh_gilda, reward `guilds +5`.
  Pastikan id quest sama dengan yang direferensikan event `fquest_30*_intro` yang sudah ada.

- [ ] **Step 4: Buat data pendukung Arc 3**
  - `data/story/memory_entitas_pertama.json`: id `memory_entitas_pertama`, judul
    "Bisikan di Balik Langit", teks grimdark (entitas kuno pertama menyapa — GDD §3.4).
  - `data/story/memory_arc3_choice.json`: id `memory_arc3_choice`, judul
    "Garis yang Kau Pilih", teks echo saat keputusan faksi.
  - `data/enemies/tentara_salib.json` (tier golden_core, element metal, tags
    `["human","holy_order"]`), `uskup_muda.json` (element fire, holy_order),
    `mata_gilda.json` (element wood, tags `["human","assassin"]`),
    `iblis_formasi.json` (element earth, tags `["ancient","demon"]`) — ikuti skema
    `data/enemies/penebus_orde_suci.json` persis (stats, skills valid, rewards).
  - `data/items/resep_pil_kristal.json` & `resep_pil_baja_tubuh.json`: type `"recipe"`,
    efek `learn_recipe`, ikuti pola `data/items/resep_*.json` existing.
  - `data/items/pedang_taring_naga.json`: type `"artifact"` dengan `growth_stat` +
    `max_level`, ikuti pola `data/items/pedang_awan_hitam.json`.

- [ ] **Step 5: Wire memori ke event**
  Buat `data/events/quest305_done.json` dengan trigger `quest_done: quest305` dan aksi
  `grant_memory: memory_entitas_pertama`; buat `data/events/memory_arc3_choice.json`
  dengan trigger flag pilihan faksi (mis. `arc3_faction_choice_done`) dan aksi
  `grant_memory: memory_arc3_choice`. Daftarkan kedua event di `EXPECTED_EVENTS`.

- [ ] **Step 6: GREEN — verifikasi**
  Jalankan: `pytest tests/test_arc3_data.py tests/test_quest_data.py \
    tests/test_event_data.py tests/test_enemy_data.py tests/test_npc_data.py -q`
  → semua pass. Jalankan: `python3 tools/validate.py` → OK.
  Jalankan: `pytest -q` → 0 failed (total test bertambah).

- [ ] **Step 7: Commit**
  ```bash
  git add data/quests/quest3*.json data/quests/fquest_30*.json data/story/ \
      data/enemies/tentara_salib.json data/enemies/uskup_muda.json \
      data/enemies/mata_gilda.json data/enemies/iblis_formasi.json \
      data/items/resep_pil_kristal.json data/items/resep_pil_baja_tubuh.json \
      data/items/pedang_taring_naga.json data/events/quest305_done.json \
      data/events/memory_arc3_choice.json tests/test_arc3_data.py \
      tests/test_event_data.py
  git commit -m "data(arc3): konten asli quest301-308 + faksi + memori + musuh"
  ```

---

### Task 4: Arc 4 — peta, NPC, musuh, bos, memori

**Files:**
- Create: `data/maps/capital.json`, `data/maps/ancient_vault.json`, `data/maps/sky_seal.json`
- Create: `data/npc/the_voice.json`
- Create: `data/enemies/rasul_langit.json`, `data/enemies/pion_langit.json`,
  `data/enemies/manifestasi_entitas.json`, `data/enemies/penjaga_vault.json`,
  `data/enemies/hantu_langit.json`, `data/enemies/pemberontak_fanatik.json`
- Create: `data/story/memory_arc1_asal.json`, `data/story/memory_arc4_rahasia.json`,
  `data/story/memory_arc4_pengorbanan.json` (memori → total 8)
- Create: `data/items/jimat_roh_liar.json` + `data/items/pil_asar_jiwa.json` (artefak → total 11)
- Modify: `tests/test_map_data.py` (`EXPECTED_MAPS` +3), `tests/test_npc_data.py`
  (`EXPECTED_NPCS` +1), `tests/test_event_data.py` (`EXPECTED_EVENTS` +3 unlock)

**Interfaces:**
- Consumes: skema peta GDD §9 (`enemies` dengan `requires_flag`), skema enemy §14.3,
  tier `void_breaker`/`heaven_challenger` dari `data/cultivation/`, event `unlock_map`.
- Produces: 3 peta Arc 4, NPC `the_voice`, bos `rasul_langit`, 5 musuh non-bos Arc 4,
  3 memori, 2 artefak — semua ter-resolve validator.

- [ ] **Step 1: Update test exact-set (RED)**
  - `tests/test_map_data.py` → tambah ke `EXPECTED_MAPS`:
    `"capital", "ancient_vault", "sky_seal"` (test memakai `assert files == expected`
    — set harus persis sama jumlahnya).
  - `tests/test_npc_data.py` → tambah `"the_voice"` ke `EXPECTED_NPCS`.
  - `tests/test_event_data.py` → tambah `"unlock_capital", "unlock_ancient_vault",
    "unlock_sky_seal"` ke `EXPECTED_EVENTS`.
  Jalankan ketiga test → FAIL.

- [ ] **Step 2: Buat peta (skema GDD §9, ikuti `data/maps/rebel_hideout.json`)**
  `data/maps/capital.json` — Ibukota Ashenfeld, tier 4, `"enemies": []` (politik):
  ```json
  {
    "id": "capital",
    "name": "Ibukota Ashenfeld",
    "description": "Menara marmer menyentuh awan kotor. Di balik gerbangnya, takhta memunggungi langit yang mulai retak.",
    "tier": 4,
    "enemies": []
  }
  ```
  `data/maps/ancient_vault.json` — Ruang Rahasia Kuno, tier 5, enemies:
  `penjaga_vault` (requires_flag `quest402_done`), `manifestasi_entitas`
  (requires_flag `quest403_done`).
  `data/maps/sky_seal.json` — Segel Langit, tier 6, enemies:
  `rasul_langit` (requires_flag `quest406_done`), `suara` (requires_flag
  `ritual_complete`), `suara_ganas` (requires_flag `quest407_done`) — lihat Task 6.

- [ ] **Step 3: Buat NPC `the_voice` (GDD §10 — entitas kuno)**
  `data/npc/the_voice.json` — `location: "sky_seal"`, `greeting` + `dialog` array
  Bahasa Indonesia grimdark, `requires_flag` pembuka (mis. `quest407_done`). Ikuti
  skema `data/npc/warden_kai.json`.

- [ ] **Step 4: Buat musuh Arc 4**
  `data/enemies/rasul_langit.json` — bos Arc 4, tier `void_breaker`, element `fire`,
  tags `["boss", "ancient"]`, stats tinggi (attack ~55, hp ~900), skills valid dari
  `data/techniques/`, `requires_flag: "quest406_done"`, rewards besar.
  Non-bos (tier `void_breaker`/`golden_core`): `pion_langit` (metal),
  `manifestasi_entitas` (shadow/ancient), `penjaga_vault` (earth, guardian),
  `hantu_langit` (undead), `pemberontak_fanatik` (rebels). Semua mengikuti skema
  `test_enemy_data.py` (REQUIRED_KEYS: id, name, tier, element, behavior, stats,
  skills, tags, rewards).

- [ ] **Step 5: Buat 3 memori Arc 4** (`data/story/`, skema id/title/text):
  `memory_arc1_asal` ("Asal yang Hilang"), `memory_arc4_rahasia`
  ("Rahasia Penuh Terungkap"), `memory_arc4_pengorbanan` ("Harga dari Langit").

- [ ] **Step 6: Buat 2 artefak** (`data/items/`, type artifact + growth_stat/max_level):
  `jimat_roh_liar`, `pil_asar_jiwa` — material ritual ending (dipakai Task 6).

- [ ] **Step 7: Buat event unlock peta** — `data/events/unlock_capital.json`,
  `unlock_ancient_vault.json`, `unlock_sky_seal.json` (pola `unlock_ruin_shrine.json`:
  trigger quest_done arc sebelumnya → action `unlock_map` + `set_flag`
  `map_<id>_unlocked`). Trigger: unlock_capital ← `quest308_done`;
  unlock_ancient_vault ← `quest401_done`; unlock_sky_seal ← `quest405_done`.

- [ ] **Step 8: GREEN — verifikasi**
  Jalankan: `pytest tests/test_map_data.py tests/test_npc_data.py \
    tests/test_event_data.py tests/test_enemy_data.py -q` → pass.
  Jalankan: `python3 tools/validate.py` → OK. `pytest -q` → 0 failed.

- [ ] **Step 9: Commit**
  ```bash
  git add data/maps/capital.json data/maps/ancient_vault.json data/maps/sky_seal.json \
      data/npc/the_voice.json data/enemies/rasul_langit.json data/enemies/pion_langit.json \
      data/enemies/manifestasi_entitas.json data/enemies/penjaga_vault.json \
      data/enemies/hantu_langit.json data/enemies/pemberontak_fanatik.json \
      data/story/memory_arc1_asal.json data/story/memory_arc4_rahasia.json \
      data/story/memory_arc4_pengorbanan.json data/items/jimat_roh_liar.json \
      data/items/pil_asar_jiwa.json data/events/unlock_capital.json \
      data/events/unlock_ancient_vault.json data/events/unlock_sky_seal.json \
      tests/test_map_data.py tests/test_npc_data.py tests/test_event_data.py
  git commit -m "data(arc4): peta capital/vault/seal + the_voice + rasul_langit + memori"
  ```

---

### Task 5: Arc 4 — quest401–408, faksi, keputusan kunci & flag bos final

**Files:**
- Create: `data/quests/quest401.json` … `quest408.json` (8 file)
- Create: `data/quests/fquest_401.json`, `fquest_402.json` (2 faksi Arc 4)
- Create: event intro/done quest401–408 + fquest_401/402 (mengikuti pola `fquest_301_intro`)
- Modify: `tests/test_quest_data.py` (`EXPECTED_QUESTS` +10), `tests/test_event_data.py`
  (`EXPECTED_EVENTS` +event baru)
- Test: `tests/test_quest_data.py`, `tests/test_event_data.py`

**Interfaces:**
- Consumes: flag `quest308_done`, peta capital/ancient_vault/sky_seal (Task 4), NPC
  `warden_kai`/`the_voice`, musuh `rasul_langit`/`suara` variants, aksi
  `add_ending_points` + `calculate_ending` (Task 1).
- Produces: chain quest401–408 lengkap; **7 keputusan kunci** (GDD §21.1) ter-wire ke
  `add_ending_points`; flag `arc4_boss_defeated` di-set saat quest408 selesai
  (memicu `calculate_ending_trigger`, Task 2).

- [ ] **Step 1: Update test exact-set (RED)**
  `tests/test_quest_data.py` → tambah ke `EXPECTED_QUESTS`: `quest401`…`quest408`,
  `fquest_401`, `fquest_402`. `tests/test_event_data.py` → tambah event yang dibuat.
  Jalankan → FAIL.

- [ ] **Step 2: Buat quest401–408 (chain, skema GDD §12.3)**

  | ID | Judul | Objektif kunci | `requires_flag` |
  |---|---|---|---|
  | quest401 | Gerbang Rahasia Kuno | `map` ancient_vault | quest308_done |
  | quest402 | Penjaga Terakhir | `talk` warden_kai + `enemy` penjaga_vault | quest401_done |
  | quest403 | Rahasia yang Tersegel | `flag` grant_memory `memory_arc4_rahasia` | quest402_done |
  | quest404 | Tujuh Garis Takdir | `talk` warden_kai + prompt keputusan final | quest403_done |
  | quest405 | Mempersiapkan Ritual | `collect` artefak ritual (jimat_roh_liar, pedang_taring_naga, pil_asar_jiwa) | quest404_done |
  | quest406 | Rasul Langit | `enemy` rasul_langit | quest405_done |
  | quest407 | Pintu Langit Terbuka | `flag` ritual_complete (set event ritual Task 6) + `talk` the_voice | quest406_done |
  | quest408 | Suara | `enemy` suara (atau suara_ganas via `requires_flag` peta) | quest407_done |

  Contoh lengkap `data/quests/quest401.json`:
  ```json
  {
    "id": "quest401",
    "title": "Gerbang Rahasia Kuno",
    "type": "main",
    "category": "main",
    "description": "Warden Kai menyerahkan kunci batu. Di bawah ibukota, pintu yang menunggu dua ratus tahun mulai berbisik namamu.",
    "requires_flag": "quest308_done",
    "objectives": [
      {"kind": "map", "target": "ancient_vault"}
    ],
    "rewards": {"insight": 80, "gold": 60, "reputation": {"ancient_order": 10}},
    "flags_on_complete": ["quest401_done"],
    "next": "quest402"
  }
  ```

- [ ] **Step 3: Buat fquest_401 & fquest_402** — `fquest_401` (Orde Suci: lawan
  pemberontak_fanatik, reward holy_order +10), `fquest_402` (Pemberontak: bantu
  rebut ibukota, reward rebels +10). `requires_flag: "quest403_done"`.

- [ ] **Step 4: Wire 7 keputusan kunci → `add_ending_points` (GDD §21.1)**
  Distribusi: 1 di Arc 1, 2 di Arc 2, 2 di Arc 3, 2 di Arc 4. Minimal yang WAJIB di-wire
  (quest/dialog/event yang SUDAH ADA — cukup tambah aksi, bukan quest baru):
  - `quest108_done` (Arc 1) — aksi `add_ending_points` (mis. `seal +1`).
  - `quest207_done` & `quest208_done` (Arc 2) — masing-masing 1 jalur.
  - `quest303_done` & `quest306_done` (Arc 3, Task 3) — sesuai pilihan faksi
    (di event intro/prompt choice, bukan di quest JSON reward).
  - `quest404` (Arc 4) — prompt final 3 opsi: `defy +1` / `seal +1` / `reconcile +1`
    via event `quest404_choice` dengan aksi `add_ending_points` per opsi.
  Contoh aksi di event:
  ```json
  {"kind": "add_ending_points", "path": "defy", "points": 1}
  ```

- [ ] **Step 5: Set `arc4_boss_defeated`** — di event `quest408_done.json`, aksi:
  ```json
  [
    {"kind": "set_flag", "flag": "arc4_boss_defeated", "value": true}
  ]
  ```
  (memantik `calculate_ending_trigger` → ending events, Task 2).

- [ ] **Step 6: Buat event wiring quest** — `quest40X_intro` (trigger quest sebelumnya
  done → `start_quest`) dan `quest40X_done` (log + memori + keputusan) mengikuti pola
  `data/events/quest101_intro.json` / `quest108_done.json`. Daftarkan di `EXPECTED_EVENTS`.

- [ ] **Step 7: GREEN — verifikasi**
  Jalankan: `pytest tests/test_quest_data.py tests/test_event_data.py -q` → pass.
  Jalankan: `python3 tools/validate.py` → OK. `pytest -q` → 0 failed.

- [ ] **Step 8: Commit**
  ```bash
  git add data/quests/quest40*.json data/quests/fquest_40*.json data/events/quest40*.json \
      data/events/fquest_40*.json tests/test_quest_data.py tests/test_event_data.py
  git commit -m "data(arc4): chain quest401-408 + keputusan kunci ending_points"
  ```

---

### Task 6: Ending — ritual, pertarungan 2-tahap Suara, epilog reputasi

**Files:**
- Create: `data/events/ritual_prep.json` (cek komponen ritual → set `ritual_complete`)
- Create: `data/enemies/suara.json` (heaven_challenger, stat normal) &
  `data/enemies/suara_ganas.json` (heaven_challenger, stat +25% — versi tanpa ritual,
  GDD §21.3)
- Modify: `src/engine/story.py` — tambah `build_epilogue(state) -> list[str]`
- Modify: `tests/test_story.py` — tambah test epilog (RED dulu)
- Modify: `data/maps/sky_seal.json` — enemies memakai `suara`/`suara_ganas`
  (sudah direncanakan di Task 4 Step 2)
- Test: `tests/test_story.py`, `tests/test_event_data.py`

**Interfaces:**
- Consumes: `state.reputation` (5 faksi), `state.memories`, flag `ritual_complete`,
  `state.ending_points`; event `calculate_ending_trigger` (Task 2).
- Produces: `build_epilogue(state)` — teks status per faksi (hancur/lemah/kuat/berkuasa,
  GDD §21.2); ritual flag; 2 varian bos final; epilog tampil via event ending (Task 2).

- [ ] **Step 1: Tulis test epilog (RED) — `tests/test_story.py`**
  ```python
  def test_build_epilogue_menyebut_faksi_berkuasa():
      """Epilog menyebut faksi dengan reputasi tertinggi (GDD §21.2)."""
      state = _state()
      state.reputation = {"court": 40, "holy_order": -60, "rebels": 10,
                          "guilds": 0, "ancient_order": 70}
      lines = build_epilogue(state)
      joined = "\n".join(lines)
      assert "ancient_order" in joined
      assert "holy_order" in joined
  ```
  Jalankan: `pytest tests/test_story.py::test_build_epilogue_menyebut_faksi_berkuasa -q`
  Expected: FAIL — `build_epilogue` belum ada.

- [ ] **Step 2: Implementasi `build_epilogue` di `src/engine/story.py`**
  ```python
  def build_epilogue(state: GameState) -> list[str]:
      """Susun epilog dari reputasi 5 faksi (GDD §21.2).

      Status per faksi: >= 70 "berkuasa", >= 30 "kuat", > -30 "lemah",
      lainnya "hancur". Dikompilasi sebagai baris teks Bahasa Indonesia.

      Args:
          state: GameState permainan saat ini.

      Returns:
          Daftar baris epilog (satu baris per faksi).
      """
      lines: list[str] = []
      for faction, score in state.reputation.items():
          if score >= 70:
              status = "berkuasa"
          elif score >= 30:
              status = "kuat"
          elif score > -30:
              status = "lemah"
          else:
              status = "hancur"
          lines.append(f"{faction}: {status} ({score})")
      return lines
  ```
  (Nama faksi tampil pakai id internal; label Indonesia boleh ditambahkan lewat
  mapping kecil bila perlu — jangan over-engineering.)

- [ ] **Step 3: GREEN — verifikasi epilog**
  Jalankan: `pytest tests/test_story.py -q` → semua pass (8 test).
  Jalankan: `ruff format src/engine/story.py && ruff check src/engine/story.py` → bersih.

- [ ] **Step 4: Buat varian bos final (GDD §21.3)**
  `data/enemies/suara.json` — tier `heaven_challenger`, element `metal`, tags
  `["boss", "ancient"]`, stats ~ attack 70 / hp 1500, skills terkuat, rewards besar.
  `data/enemies/suara_ganas.json` — salinan suara dengan **semua stat ×1.25**
  (bos mendapat bonus per komponen ritual yang hilang — dimodelkan varian tanpa ritual).
  Pastikan keduanya lolos `test_enemy_data.py`.

- [ ] **Step 5: Event ritual — `data/events/ritual_prep.json`**
  Trigger: `quest405_done` (Task 5). Actions: cek kepemilikan artefak ritual lewat
  trigger flag (`collect` quest405 menjamin item), lalu
  ```json
  [
    {"kind": "set_flag", "flag": "ritual_complete", "value": true},
    {"kind": "log", "text": "Artefak berbaris di altar. Formasi menyala. Langit mengaduh."}
  ]
  ```
  Daftarkan di `EXPECTED_EVENTS`.

- [ ] **Step 6: Pastikan `sky_seal` memilih varian bos via flag (data-driven)**
  `data/maps/sky_seal.json` enemies (sudah dibuat Task 4) — urutan seleksi `look`:
  ```json
  "enemies": [
    {"enemy": "rasul_langit", "requires_flag": "quest406_done"},
    {"enemy": "suara", "requires_flag": "ritual_complete"},
    {"enemy": "suara_ganas", "requires_flag": "quest407_done"}
  ]
  ```
  (suara_ganas hanya muncul bila ritual tidak lengkap — mekanisme gating peta GDD §9.)

- [ ] **Step 7: Sambungkan epilog ke event ending**
  Update `data/events/ending_defy.json`, `ending_seal.json`, `ending_reconcile.json`
  (Task 2) — tambah action `log` yang memuat hasil `build_epilogue(state)` tidak bisa
  lewat JSON (state dinamis), jadi epilog di-render di `game_loop` saat event ending
  memicu: tambahkan di `src/core/game_loop.py` handler `_cmd_*` pasca event pass,
  cek flag `ending_<jalur>_win` → panggil `build_epilogue` dan log baris-barisnya.
  (Pola: lihat bagaimana `_cmd_choose`/event result.logs diproses; tambahkan blok kecil
  setelah `process_events` di alur pasca-aksi.)

- [ ] **Step 8: Verifikasi penuh & commit**
  Jalankan: `pytest -q` → 0 failed · `ruff check` → 0 · `ruff format --check` → OK ·
  `python3 tools/validate.py` → OK.
  ```bash
  git add src/engine/story.py src/core/game_loop.py tests/test_story.py \
      data/enemies/suara.json data/enemies/suara_ganas.json \
      data/events/ritual_prep.json data/maps/sky_seal.json tests/test_event_data.py
  git commit -m "feat(story): ritual + bos final 2 varian + epilog reputasi"
  ```

---

### Task 7: Fase 5 — polish, smoke test & rilis

**Files:**
- Modify: `README.md` (status & instruksi main)
- Modify: `data/*` (tuning keseimbangan GDD §24.2 bila ada anomali)
- Create: `tests/test_smoke_playthrough.py` (smoke per arc)
- Test: seluruh suite

**Interfaces:**
- Consumes: semua sistem Task 1–6.
- Produces: game playable end-to-end 4 arc + 3 ending; laporan rilis.

- [ ] **Step 1: Smoke test playthrough (TDD) — `tests/test_smoke_playthrough.py`**
  Tulis test yang menjalankan urutan perintah inti (mulai → cultivate → rest →
  quest arc1 → battle → breakthrough → save/load) memakai pola `tests/test_game_loop.py`
  (fake input, cap jumlah langkah). Verifikasi tidak ada exception di alur Arc 1–2.
  (Smoke penuh 4 arc opsional bila waktu memungkinkan — utamakan Arc 1–2 + verifikasi
  event ending terpicu dengan state buatan: set `arc4_boss_defeated` + jalankan
  `process_events` → assert log ending muncul.)

- [ ] **Step 2: Balancing cepat (GDD §24.2)**
  Jalankan ulang `python3 tools/validate.py`; cek anomali angka (mis. reward insight
  quest Arc 3–4 sejalan kurva tier §4.1: quest301+ insight ~60, quest408 ~120).

- [ ] **Step 3: Update README.md** — status "Fase 0–4 selesai, rilis v1.0", instruksi
  install (`pip install -e .` atau `python3 launcher.py`), daftar perintah.

- [ ] **Step 4: Bersihkan artefak sesi**
  - Hapus `.agents/` dari tracking (tambahkan ke `.gitignore`) — artefak orchestration
    bukan bagian repo.
  - Putuskan nasib file yang belum ter-commit: `audit_report.md` (pertahankan),
    `tdd_proof.md` (pertahankan sebagai bukti), `docs/superpowers/plans/*` (commit
    rencana-rencana yang valid).

- [ ] **Step 5: Verifikasi final (Definisi Selesai AGENTS.md §12)**
  Jalankan: `pytest -q` → 0 failed · `ruff check src launcher.py tools tests` → 0 ·
  `ruff format --check src launcher.py tools tests` → OK · `python3 tools/validate.py`
  → OK · `graphify update .` → graph mutakhir.

- [ ] **Step 6: Commit & merge**
  ```bash
  git add -A
  git commit -m "docs: polish fase 5 + smoke test + README rilis v1.0"
  git checkout main && git merge feature/dynamic-ending-engine
  ```

---

## Self-Review (writing-plans)

**1. Cakupan spek:** Setiap gap GDD §22 terpetakan ke task: teknik 30/30 (sudah, tanpa
task) · resep 14 (Task 3) · artefak 12 (Task 3–4) · musuh 30 + bos 5 (Task 3–4, 6) · NPC 25
(Task 4) · peta 10 (Task 4) · memori 9 (Task 3–4) · quest 32 (Task 3, 5) · ending + ritual +
epilog (Task 1–2, 6) · polish (Task 7). Rencana lama yang sudah usang didaftar di bagian
"Koreksi Baseline" — tidak dibuat task duplikat.

**2. Scan placeholder:** Semua step memuat konten konkret (kode/JSON/chain quest). Data
naratif (teks grimdark per quest) didefinisikan judul + objektif + reward persis; prosa
adalah tugas penulis mengikuti tone GDD §3.6.

**3. Konsistensi tipe:** Aksi `calculate_ending` (Task 1) → flag `ending_<jalur>_win`
(Task 2 trigger) → `calculate_ending_trigger` diurutkan sebelum `ending_*` (cascade)
· flag `arc4_boss_defeated` (Task 5 Step 5) → trigger (Task 2) · `ritual_complete`
(Task 6) → `suara`/`suara_ganas` di `sky_seal` (Task 4 Step 2 / Task 6 Step 6) ·
`build_epilogue(state) -> list[str]` konsisten di story.py & game_loop (Task 6 Step 7).

---

*Rencana ini menyatukan `rencana_penyelesaian_cotp.md` (dengan koreksi terhadap baseline
yang usang) dan temuan audit aktual repo (7 Agustus 2026). Keputusan desain mengikuti
GDD.md; perubahan yang bertentangan GDD §24.1 wajib didiskusikan dulu (AGENTS.md §11).*
