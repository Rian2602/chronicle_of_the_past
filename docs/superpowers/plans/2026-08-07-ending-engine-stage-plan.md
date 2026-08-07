# Dynamic Ending Engine — Stage Plan (Tahap #1 Prioritas)

> **Untuk pekerja agen:** WAJIB SUB-SKILL: gunakan `superpowers:subagent-driven-development`
> (disarankan) atau `superpowers:executing-plans`. Steps memakai checkbox (`- [ ]`).
> Rencana ini adalah subset Task 1–2 (+ epilog minimal) dari
> `docs/superpowers/plans/2026-08-07-master-plan-penyelesaian.md` — dieksekusi sendiri-sendiri.

**Goal:** Melengkapi Sistem Ending Dinamis (GDD §13 & §21) — memperbaiki suite yang merah,
menambahkan aksi `calculate_ending`, 4 event ending data-driven, dan epilog berbasis reputasi —
sehingga game bisa "tamat" sesuai spesifikasi.

**Architecture:** Aksi event baru `calculate_ending` dibaca dari `state.ending_points`
(dict `defy`/`seal`/`reconcile`), memilih jalur pemenang via `story.calculate_ending()`, lalu
men-set flag `ending_<jalur>_win`. Event ending (JSON) terpicu oleh flag tersebut; epilog
(`build_epilogue`) di-render di `game_loop._run_events` — satu-satunya pemanggil
`process_events`. Semua tetap data-driven; tanpa bump schema save.

**Tech Stack:** Python 3.12+ (perintah `python3`), pytest, ruff, `tools/validate.py`.
Branch aktif: `feature/dynamic-ending-engine` (dari `main` @ 5c44c11, 0 commit — perubahan
`story.py` & `tests/test_story.py` belum di-commit).

## Global Constraints

- Bahasa Indonesia untuk semua teks; nada **grimdark** (GDD §3.6).
- **TDD wajib**: cetak ulang bukti RED di tiap task (jangan andalkan `tdd_proof.md` lama).
- Google style: baris ≤ 80, double quotes, docstring header English + prosa Indonesia.
- Jangan sentuh `src/engine/combat.py`, `src/engine/cultivation.py`, `src/models/player.py`.
- Flag bebas-bentuk di `state.flags` (GDD §19.2) — tanpa bump `schema_version`.
- Verifikasi sebelum commit: `pytest -q`, `ruff check`, `ruff format --check`,
  `python3 tools/validate.py`.
- **Ponytail — scope dilarang melebar**: sistem ritual, bos 2-tahap, layar UI ending mewah
  adalah Task 6/7 master plan — bukan bagian tahap ini.

---

### Task A: Wire aksi `calculate_ending` (engine) — hijaukan suite

**Files:**
- Modify: `src/engine/event.py` (set `ACTION_KINDS` ~baris 29–43; `apply_action` ~baris 127;
  import baru setelah `from src.models.party import load_companion`)
- Modify: `tests/test_story.py` (hapus `import pytest` baris 3; rapikan docstring baris 31)
- Modify: `src/engine/story.py` (jalankan `ruff format` — baris 63)
- Test: `tests/test_story.py` (7 test existing)

**Interfaces:**
- Consumes: `src.engine.story.calculate_ending(state) -> str` (sudah ada, mengembalikan
  `"defy"` / `"seal"` / `"reconcile"`).
- Produces: aksi event `{"kind": "calculate_ending"}` yang men-set
  `state.flags["ending_<jalur>_win"] = True` hanya untuk pemenang.

- [ ] **Step 1: Buktikan RED**
  Jalankan: `pytest tests/test_story.py -q`
  Expected: `1 failed` — `test_apply_action_calculate_ending` dengan
  `ValueError: kind aksi tidak dikenal: calculate_ending`.
  Catat output terminal ini sebagai bukti RED.

- [ ] **Step 2: GREEN — `src/engine/event.py`**
  Tambah `"calculate_ending"` ke `ACTION_KINDS`:
  ```python
      "add_ending_points",
      "calculate_ending",
  ```
  Tambah import di bagian atas:
  ```python
  from src.engine.story import calculate_ending
  ```
  Tambah cabang di akhir rantai `if kind == ...` di `apply_action`:
  ```python
      elif kind == "calculate_ending":
          # GDD §21.1: jalur poin tertinggi menentukan ending; hanya flag
          # pemenang yang diset (test menuntut flag loser None).
          winner = calculate_ending(state)
          state.flags[f"ending_{winner}_win"] = True
  ```

- [ ] **Step 3: Bersihkan `tests/test_story.py`**
  - Hapus baris `import pytest` (F401).
  - Ganti docstring `test_calculate_ending_reconcile_highest` menjadi:
    ```python
    def test_calculate_ending_reconcile_highest():
        """Jalur reconcile poin tertinggi harus mengembalikan 'reconcile'."""
    ```

- [ ] **Step 4: Format `story.py`**
  Jalankan: `ruff format src/engine/story.py`

- [ ] **Step 5: Verifikasi GREEN**
  Jalankan: `pytest tests/test_story.py -q` → 7 passed.
  Jalankan: `ruff check src launcher.py tools tests` → 0 error.
  Jalankan: `ruff format --check src launcher.py tools tests` → OK.
  Jalankan: `python3 tools/validate.py` → OK.

- [ ] **Step 6: Commit**
  ```bash
  git add src/engine/event.py src/engine/story.py tests/test_story.py
  git commit -m "feat(story): wire aksi calculate_ending + hijaukan suite"
  ```

---

### Task B: Event ending data-driven (data)

**Files:**
- Create: `data/events/calculate_ending_trigger.json`
- Create: `data/events/ending_defy.json`, `data/events/ending_seal.json`,
  `data/events/ending_reconcile.json`
- Modify: `tests/test_event_data.py` (set `EXPECTED_EVENTS` +4 entri)
- Test: `tests/test_event_data.py`

**Interfaces:**
- Consumes: flag `arc4_boss_defeated` (di-set quest Arc 4 kelak — Task 5 master plan;
  saat ini cukup dibuktikan lewat unit test), flag `ending_<jalur>_win` (Task A).
- Produces: 4 event JSON valid; urutan abjad menjamin cascade satu-pass
  (`calculate_ending_trigger` < `ending_*` karena `c` < `e`, GDD §15.4).

- [ ] **Step 1: RED — update `tests/test_event_data.py`**
  Tambah ke `EXPECTED_EVENTS` (set persis 1:1 dengan file):
  ```python
      "calculate_ending_trigger",
      "ending_defy",
      "ending_seal",
      "ending_reconcile",
  ```
  Jalankan: `pytest tests/test_event_data.py -q`
  Expected: FAIL — 4 file belum ada.

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

- [ ] **Step 3: Buat `data/events/ending_defy.json`**
  ```json
  {
    "id": "ending_defy",
    "trigger": [
      {"kind": "flag", "flag": "ending_defy_win", "operator": "EQUALS", "value": true}
    ],
    "actions": [
      {"kind": "log", "text": "MENENTANG LANGIT — Kau menaiki langit yang retak dan menggenggam kilat. Aturan-aturan lama runtuh satu per satu. Kerajaan dibangun ulang di atas abu para dewa, dan namamu diukir bukan sebagai penguasa, melainkan sebagai peringatan. Di kejauhan, sesuatu yang baru mulai bernapas. Kau tidak tahu apakah kau menyelamatkan dunia — atau menggantikan penjaganya."}
    ],
    "once": true
  }
  ```

- [ ] **Step 4: Buat `data/events/ending_seal.json`**
  ```json
  {
    "id": "ending_seal",
    "trigger": [
      {"kind": "flag", "flag": "ending_seal_win", "operator": "EQUALS", "value": true}
    ],
    "actions": [
      {"kind": "log", "text": "MENYEGEL DIRI — Kau memilih mundur. Segel itu kau pasang dengan tangan sendiri, menutup pintu yang tak boleh terbuka. Dunia memilih jalannya sendiri: tanpa kau, faksi-faksi saling menghancurkan, dan langit tertidur sekali lagi. Di antara reruntuhan, orang-orang mengingat seorang kultivator yang menolak menjadi pahlawan. Mungkin itu juga cara untuk menang."}
    ],
    "once": true
  }
  ```

- [ ] **Step 5: Buat `data/events/ending_reconcile.json`**
  ```json
  {
    "id": "ending_reconcile",
    "trigger": [
      {"kind": "flag", "flag": "ending_reconcile_win", "operator": "EQUALS", "value": true}
    ],
    "actions": [
      {"kind": "log", "text": "REKONSILIASI — Kau berdiri di antara faksi-faksi yang saling membunuh dan entitas yang mulai bangkit. Ritual pengorbanan dijalankan setengah, darahmu jadi jembatan. Orde Suci dan pemberontak belajar berbagi bayangan yang sama. Langit tetap retak — tapi kini ada yang menjaganya. Bukan sebagai dewa: sebagai penjaga perbatasan antara dua dunia."}
    ],
    "once": true
  }
  ```

- [ ] **Step 6: GREEN — verifikasi**
  Jalankan: `pytest tests/test_event_data.py -q` → pass.
  Jalankan: `python3 tools/validate.py` → OK.
  Tambahkan unit test smoke di `tests/test_event.py` bahwa cascade satu-pass bekerja:
  ```python
  def test_ending_events_terpicu_setelah_bos_kalah():
      """Set arc4_boss_defeated -> calculate_ending -> ending event (cascade)."""
      from src.engine.event import load_events, process_events
      from src.core.state import GameState
      from src.models.player import Player

      state = GameState(player=Player(name="Akar"))
      state.ending_points = {"defy": 2, "seal": 7, "reconcile": 3}
      state.flags["arc4_boss_defeated"] = True
      result = process_events(state, load_events())
      assert state.flags.get("ending_seal_win") is True
      assert any(event_id.startswith("ending_") for event_id in result.fired)
      # Seal menang -> teks ending reconcile TIDAK boleh muncul.
      assert all("REKONSILIASI" not in line for line in result.logs)
  ```
  Jalankan: `pytest tests/test_event.py -q` → pass.

- [ ] **Step 7: Commit**
  ```bash
  git add data/events/calculate_ending_trigger.json data/events/ending_defy.json \
      data/events/ending_seal.json data/events/ending_reconcile.json \
      tests/test_event_data.py tests/test_event.py
  git commit -m "feat(story): event ending data-driven + cascade test"
  ```

---

### Task C: Epilog minimal — `build_epilogue` + wiring di game_loop

**Files:**
- Modify: `src/engine/story.py` (tambah `build_epilogue`)
- Modify: `tests/test_story.py` (tambah test epilog)
- Modify: `tests/test_game_loop.py` (tambah test wiring `_run_events`)
- Modify: `src/core/game_loop.py` (modifikasi `_run_events` ~baris 1524)
- Test: `tests/test_story.py`, `tests/test_game_loop.py`

**Interfaces:**
- Consumes: `state.reputation` (dict 5 faksi), flag `ending_<jalur>_win`, flag baru
  `ending_epilogue_shown` (free-form, GDD §19.2).
- Produces: `build_epilogue(state) -> list[str]` — satu baris status per faksi; epilog
  tampil sekali setelah ending memicu.

- [ ] **Step 1: RED — tulis test epilog di `tests/test_story.py`**
  ```python
  from src.engine.story import build_epilogue  # tambah ke import baris atas


  def test_build_epilogue_menyebut_status_faksi():
      """Epilog menyebut tiap faksi dengan status dari reputasi (GDD §21.2)."""
      state = _state()
      state.reputation = {
          "court": 40, "holy_order": -60, "rebels": 10,
          "guilds": 0, "ancient_order": 70,
      }
      lines = build_epilogue(state)
      joined = "\n".join(lines)
      assert "ancient_order" in joined and "berkuasa" in joined
      assert "holy_order" in joined and "hancur" in joined
      assert len(lines) == 5
  ```
  Jalankan: `pytest tests/test_story.py::test_build_epilogue_menyebut_status_faksi -q`
  Expected: FAIL — `build_epilogue` belum ada (ImportError/AttributeError).

- [ ] **Step 2: GREEN — tambah `build_epilogue` di `src/engine/story.py`**
  ```python
  def build_epilogue(state: GameState) -> list[str]:
      """Susun epilog dari reputasi 5 faksi (GDD §21.2).

      Status per faksi: >= 70 "berkuasa", >= 30 "kuat", > -30 "lemah",
      lainnya "hancur". Dipanggil game_loop saat flag ending memicu.

      Args:
          state: GameState permainan saat ini.

      Returns:
          Daftar baris epilog, satu baris per faksi.
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
  Jalankan: `pytest tests/test_story.py -q` → 8 passed.

- [ ] **Step 3: RED — tulis test wiring di `tests/test_game_loop.py`**
  ```python
  def test_run_events_menampilkan_epilog_sekali():
      """Setelah flag ending diset, _run_events memuat epilog satu kali saja."""
      session = GameSession()
      session.new_game("Akar")
      session.state.flags["ending_defy_win"] = True
      first = session._run_events()
      assert any("EPILOG" in line for line in first)
      second = session._run_events()
      assert not any("EPILOG" in line for line in second)
  ```
  Jalankan: `pytest tests/test_game_loop.py::test_run_events_menampilkan_epilog_sekali -q`
  Expected: FAIL — `_run_events` belum memuat epilog.

- [ ] **Step 4: GREEN — modifikasi `_run_events` di `src/core/game_loop.py`**
  Tambah import:
  ```python
  from src.engine.story import build_epilogue, load_memories
  ```
  Ganti body `_run_events` (~baris 1524):
  ```python
      def _run_events(self) -> list[str]:
          """Proses event data-driven setelah momen mutasi state (GDD §15.4).

          Dipanggil setelah go / cultivate / rest / breakthrough / talk —
          sekali per momen. Kembalikan baris narasi event untuk UI.
          Bila event ending memicu flag ending_<jalur>_win, tambahkan
          epilog dari reputasi faksi (GDD §21.2) — sekali per playthrough
          (flag ending_epilogue_shown).
          """
          if self.state is None:
              return []
          lines = list(process_events(self.state, load_events()).logs)
          if (
              any(
                  self.state.flags.get(f"ending_{path}_win")
                  for path in ("defy", "seal", "reconcile")
              )
              and not self.state.flags.get("ending_epilogue_shown")
          ):
              # ponytail: alur keluar setelah ending (kembali ke menu)
              # menyusul Fase polish (master plan Task 7).
              self.state.flags["ending_epilogue_shown"] = True
              lines.append("— EPILOG —")
              lines.extend(build_epilogue(self.state))
          return lines
  ```

- [ ] **Step 5: Verifikasi GREEN**
  Jalankan: `pytest tests/test_game_loop.py tests/test_story.py -q` → pass.
  Jalankan: `ruff check src launcher.py tools tests` → 0 error.
  Jalankan: `ruff format --check src launcher.py tools tests` → OK.

- [ ] **Step 6: Commit**
  ```bash
  git add src/engine/story.py src/core/game_loop.py tests/test_story.py \
      tests/test_game_loop.py
  git commit -m "feat(story): epilog reputasi + tampil sekali via _run_events"
  ```

---

### Task D: Selidiki test flaky + verifikasi penuh

**Files:**
- Investigate: `tests/test_app.py::test_pilih_option_serang_melakukan_battle_step`
  (pernah gagal 1× dari 4 run penuh; lulus saat dijalankan terpisah)
- Modify: `tests/test_app.py` (bila fix ditemukan)
- Test: seluruh suite

**Interfaces:**
- Consumes: semua perubahan Task A–C.
- Produces: suite hijau stabil (5× berturut-turut), lint/format/validator bersih,
  graph ter-update, semua perubahan ter-commit.

- [ ] **Step 1: Reproduksi flaky**
  Jalankan: `for i in 1 2 3 4 5; do pytest -q 2>&1 | tail -1; done`
  Catat berapa kali `test_pilih_option_serang_melakukan_battle_step` gagal.

- [ ] **Step 2: Investigasi akar masalah (AGENTS §2.6 — dilarang guess-and-check)**
  Baca `tests/test_app.py` (test tsb) dan alur battle di `src/ui/app.py` (fungsi yang
  dipanggil test). Periksa: apakah test memakai state global/class-level yang bocor
  antar test, atau bergantung pada urutan collection? Cari perbedaan saat dijalankan
  sendiri vs bersama suite (mis. fixture, mock, atau `random` tanpa seed).

- [ ] **Step 3: Hipotesis & fix minimal**
  Tulis hipotesis satu kalimat + bukti (jalankan subset test yang dicurigai bersamaan).
  Fix minimal (contoh umum: reset state di akhir test / fixture `autouse` / seed rng).
  JANGAN melemahkan test lain atau menambah dependency.

- [ ] **Step 4: Verifikasi stabilitas**
  Jalankan: `for i in 1 2 3 4 5; do pytest -q 2>&1 | tail -1; done` → 0 failed tiap run.
  Jalankan: `pytest -q` → seluruh suite pass (jumlah test = 456 + test baru Task B–C).

- [ ] **Step 5: Verifikasi lengkap (Definisi Selesai)**
  ```bash
  ruff check src launcher.py tools tests
  ruff format --check src launcher.py tools tests
  python3 tools/validate.py
  graphify update .
  ```

- [ ] **Step 6: Commit**
  ```bash
  git add tests/test_app.py
  git commit -m "test(app): perbaiki flaky test battle step"
  ```

---

## Self-Review (writing-plans)

**1. Cakupan spek:** Rekomendasi tahap #1 = Task A (engine) + Task B (data ending) + Task C
(epilog). Task D (flaky) adalah cacat yang sudah diketahui dan masuk scope tahap yang sama.
Ritual, bos 2-tahap, keputusan kunci 7, quest Arc 4 → master plan Task 3–6 (di luar tahap ini,
sesuai batas Ponytail).

**2. Scan placeholder:** Semua step memuat kode/JSON lengkap — tidak ada "TBD". Teks epilog
ditulis penuh dalam file JSON.

**3. Konsistensi tipe:** `calculate_ending(state)` → `ending_<jalur>_win` → trigger
`ending_*` events → `build_epilogue(state) -> list[str]` → `_run_events`. Nama fungsi &
flag konsisten antar task. `ending_epilogue_shown` bebas-bentuk (GDD §19.2), tanpa bump
schema v2.

---

*Rencana tahap ini diturunkan dari `2026-08-07-master-plan-penyelesaian.md` (Task 1–2 +
epilog), dengan elaborasi hasil audit aktual repo 7 Agustus 2026. Perubahan yang bertentangan
GDD §24.1 wajib didiskusikan dulu (AGENTS.md §11).*
