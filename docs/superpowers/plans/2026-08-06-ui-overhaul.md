# Textual UI Overhaul — Tema Grimdark & Layout Panel (Rencana FINAL)

> **Status: DISETUJUI SEPENUHNYA (APPROVED)** — evaluasi Antigravity
> (2026-08-06) + evaluasi sendiri. Rekonsiliasi dari rencana ui-overhaul
> lama + rekomendasi visual (ChatGPT). Keputusan user: **zero-dependency**
> — semua fitur memakai Textual 8.2.8 + Rich yang sudah terpasang +
> stdlib `difflib`; **DILARANG** menambah dependency baru
> (`prompt_toolkit`, `pydantic`, `orjson`, `rapidfuzz`, `loguru`,
> `platformdirs`, ekosistem `textual-*` non-inti — semuanya ditolak per
> AGENTS §7 & tangga Ponytail §3.1).
>
> **Hasil verifikasi teknis (diuji terhadap Textual 8.2.8 terpasang):**
> * `RichLog(markup=True)`, `Horizontal`, `Vertical` — tersedia. ✓
> * `Input.BINDINGS` **tidak** memuat `tab` → binding TAB di GameScreen
>   bebas konflik. ✓
> * Asumsi risiko diperbaiki: `tests/test_status.py` menguji **status
>   effect combat**, bukan `status_lines()` HUD. Test yang menyentuh HUD:
>   `test_game_loop.py:253` (`status_lines` saat battle — assert
>   substring "HP"/"Insight" tetap lolos dengan format bar) dan
>   `test_app.py:50,104` (HUD berisi "Akar"/"HP" — tetap lolos). ✓

**Goal:** Menaikkan visual UI terminal dari *teks polos* menjadi *tampilan
RPG modern*: tema dark fantasy, HUD dengan bar HP/Qi, layout panel
(HUD atas + sidebar quest/party + log + input), combat bar visual, warna
semantik konten, dan koreksi ketik perintah — tanpa satu pun library
baru.

**Architecture:**
* `src/ui/app.py` — tema CSS grimdark, `Log` → `RichLog`, layout panel
  (`Horizontal`/`Vertical`), bar musuh, autocomplete TAB.
* `src/core/game_loop.py` — helper `make_bar()` (fungsi modul publik),
  `status_lines()` diperkaya, `quest_lines()`/`party_lines()` publik
  read-only untuk panel (reuse `_cmd_quests`/`_cmd_party`), warna
  semantik di `_cmd_inventory`.
* `src/core/input.py` — koreksi ketik via `difflib.get_close_matches`
  (stdlib) + `complete_command()` untuk autocomplete TAB.
* Tidak menyentuh file stabil §6 (`combat.py`, `cultivation.py`,
  `models/player.py`). `game_loop.py` diperluas (diizinkan §6).

**Tech Stack:** Python 3.12+, Textual 8.2.8, Rich, stdlib. Tanpa dependency baru.

## Global Constraints

- TDD wajib: RED → GREEN → commit per task (AGENTS §2.1).
- `pytest -q` · `ruff check` · `ruff format --check` · `python tools/validate.py` hijau.
- `graphify update .` setelah ubah kode (§4.3).
- Baris ≤ 80; docstring Google-style (header English, isi Indonesia).
- Pesan commit `<lingkup>: <ringkasan>` (lingkup `ui`/`input`/`test`/`docs` —
  **bukan** `style(ui):` — AGENTS §9).
- Kompatibilitas terminal §3.2: karakter `█`/`░` hanya di UI Textual
  (Rich), bukan di output plain yang bisa gagal di terminal sempit.
- Data eksisting **DILARANG** dihapus/diganti (§6) — hanya tampilan yang berubah.

---

### Task 1 — Tema Grimdark + Migrasi `Log` → `RichLog`

**Files:**
- Modify: `src/ui/app.py`
- Modify: `tests/test_app.py`

**Interfaces:**
- Consumes: `GameScreen.compose()` (saat ini `yield Log(...)`), `_refresh()`,
  `_world_command`, `_battle_command` (semua menulis via `#game-log`).
- Produces: tema CSS grimdark + log menerima markup Rich (`RichLog`).

- [ ] **Step 1: RED** — `tests/test_app.py`: tambah test bahwa layar game
menyediakan `RichLog` (bukan `Log`) dan CSS berisi palet grimdark:
```python
def test_game_screen_menggunakan_richlog():
    """Layar game memakai RichLog agar narasi bisa diberi markup warna."""
    screen = GameScreen()
    widgets = list(screen.compose())
    assert any(isinstance(w, RichLog) for w in widgets)
    assert not any(isinstance(w, Log) for w in widgets)
```
- [ ] **Step 2: Run test — pastikan GAGAL** (`Log` masih dipakai).
- [ ] **Step 3: GREEN** — `src/ui/app.py`:
  * Import `RichLog` (hapus `Log`); semua pemakaian `#game-log` ganti tipe.
  * `RichLog(id="game-log", markup=True)` — narasi kini menerima warna.
  * CSS `ChronicleApp` → palet grimdark:
```css
    Screen { background: #0F0F0F; color: #E8E8E8; }
    #hud { background: #1a1a1a; padding: 0 1; border-bottom: solid #303030; }
    #enemy { background: #1a0000; padding: 0 1; border-bottom: solid #4a0000;
             color: #ff5555; }
    #game-log { height: 1fr; border: round #D4AF37; background: #0F0F0F; }
    #cmd { border: tall #303030; background: #151515; }
    #cmd:focus { border: tall #D4AF37; }
```
- [ ] **Step 4: Run test + full suite + lint/format — HIJAU.**
- [ ] **Step 5: Commit**
```bash
git commit -am "ui: tema grimdark + migrasi RichLog (GDD 14.1)"
```

---

### Task 2 — HUD: Bar ASCII HP/Qi (`make_bar` + `status_lines`)

**Files:**
- Modify: `src/core/game_loop.py`
- Modify: `tests/test_game_loop.py` (test HUD: `:253` dst. — tetap lolos;
  hanya perbarui bila ada assert teks polos yang berubah, jangan
  dilemahkan)

**Interfaces:**
- Consumes: `GameSession.status_lines()` (dipakai HUD UI & `_cmd_status`).
- Produces: fungsi modul publik `make_bar(current, total, width=20) -> str`
  dan `status_lines()` dengan bar `█`/`░` + markup Rich.

- [ ] **Step 1: RED** — `tests/test_game_loop.py`:
```python
def test_make_bar_proporsional():
    """Bar ASCII mengisi sesuai proporsi (0 -> kosong, penuh -> penuh)."""
    assert make_bar(0, 20, 10) == "░" * 10
    assert make_bar(20, 20, 10) == "█" * 10
    assert make_bar(10, 20, 10).count("█") == 5


def test_status_lines_memuat_bar_hp_qi():
    """HUD menampilkan bar visual HP/Qi, bukan teks polos."""
    session = _session(tmp_path)
    session.new_game("Akar")
    joined = "\n".join(session.status_lines())
    assert "█" in joined and "░" in joined
```
- [ ] **Step 2: Run test — GAGAL.**
- [ ] **Step 3: GREEN** — `src/core/game_loop.py`:
```python
def make_bar(current: int, total: int, width: int = 20) -> str:
    """Bar ASCII proporsional (█ terisi, ░ kosong).

    Args:
        current: Nilai saat ini (>= 0).
        total: Nilai maksimum; 0 menghasilkan bar kosong.
        width: Lebar bar dalam karakter.

    Returns:
        String bar, panjang tepat ``width``.
    """
    if total <= 0:
        return "░" * width
    filled = max(0, min(width, round(current / total * width)))
    return "█" * filled + "░" * (width - filled)
```
`status_lines()`: baris HP/Qi menjadi
`HP [red]{make_bar(...)}[/] {hp}/{hp_max} | Qi [cyan]{bar}[/] {qi}/{qi_max}`
(Insight violet, Gold gold3 — palet §7.)
- [ ] **Step 4: Full suite + lint/format — HIJAU.** Perbarui assert test
status yang formatnya berubah (konten tetap, bukan melemahkan).
- [ ] **Step 5: Commit**
```bash
git commit -am "ui: bar ASCII HP/Qi di HUD status (GDD 14.1)"
```

---

### Task 3 — Layout Panel: HUD + Sidebar (Quest & Party) + Log + Input

**Files:**
- Modify: `src/ui/app.py` (`compose`, `_refresh`, CSS)
- Modify: `src/core/game_loop.py` (metode panel read-only)
- Modify: `tests/test_app.py`, `tests/test_game_loop.py`

**Interfaces:**
- Consumes: `state.quests`, `load_quests`, `check_objective`,
  `objective_label` (engine quest — semua publik).
- Produces: `GameSession.quest_lines()` dan `party_lines()` (publik,
  read-only, reuse `_cmd_quests`/`_cmd_party`) + layout 2 kolom di UI.

- [ ] **Step 1: RED** — `tests/test_game_loop.py`:
```python
def test_quest_lines_menampilkan_quest_aktif(tmp_path):
    """Panel quest memakai data yang sama dengan perintah quests."""
    session = _session(tmp_path)
    session.new_game("Akar")
    _dispatch(session, "cultivate")  # quest101 dimulai via event intro
    joined = "\n".join(session.quest_lines())
    assert "Qi Pertama" in joined
```
`tests/test_app.py`:
```python
def test_layout_memiliki_panel_quest_dan_party(tmp_path):
    """Layar game memuat panel quest & party di sidebar."""
    app = _app(tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("n")
        await pilot.pause()
        app.screen.query_one("#name", Input).value = "Akar"
        await pilot.press("enter")
        await pilot.pause()
        assert app.screen.query_one("#panel-quest") is not None
        assert app.screen.query_one("#panel-party") is not None
```
- [ ] **Step 2: Run test — GAGAL.**
- [ ] **Step 3: GREEN** — `game_loop.py`:
```python
def quest_lines(self) -> list[str]:
    """Ringkasan quest aktif untuk panel UI (read-only, tanpa efek)."""
    return self._cmd_quests(Command(name="quests", args=(), raw="quests"))

def party_lines(self) -> list[str]:
    """Ringkasan tim untuk panel UI (read-only, tanpa efek)."""
    return self._cmd_party(Command(name="party", args=(), raw="party"))
```
`app.py` — `compose()` menjadi 2 kolom:
```python
    with Horizontal():
        with Vertical(id="main-col"):
            yield RichLog(id="game-log", markup=True)
        with Vertical(id="side-col"):
            yield Static("", id="panel-quest")
            yield Static("", id="panel-party")
    yield Static("", id="hud")      # HUD pindah ke atas lewat CSS order
    yield Input(..., id="cmd")
```
  (susun order visual via CSS: HUD di atas, main-col kiri, side-col kanan,
  input di bawah; `_refresh()` mengisi `#panel-quest`/`#panel-party` dari
  `session.quest_lines()`/`party_lines()` — dipanggil di `on_mount` dan
  setelah tiap perintah; `#hud` tetap `status_lines()`.)
- [ ] **Step 4: Full suite + lint/format + validator — HIJAU.**
- [ ] **Step 5: Commit**
```bash
git commit -am "ui: layout panel HUD + sidebar quest/party (GDD 14.1)"
```

---

### Task 4 — Combat: Bar HP Visual Musuh

**Files:**
- Modify: `src/ui/app.py` (`_enemy_lines`, `_battle_command`)
- Modify: `tests/test_app.py`

**Interfaces:**
- Consumes: `BattleFrame.enemies` (dict: name/hp/hp_max/qi/element),
  `make_bar()` (Task 2).
- Produces: panel musuh & amatan dengan bar HP + warna elemen.

- [ ] **Step 1: RED** — `tests/test_app.py` (dalam battle, panel `#enemy`
memuat `█`):
```python
@pytest.mark.asyncio
async def test_panel_musuh_memuat_bar_hp(tmp_path):
    app = _app(tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("n")
        await pilot.pause()
        app.screen.query_one("#name", Input).value = "Akar"
        await pilot.press("enter")
        await pilot.pause()
        cmd = app.screen.query_one("#cmd", Input)
        cmd.value = "go ashfall_forest"
        await pilot.press("enter")
        await pilot.pause()
        cmd.value = "look"
        await pilot.press("enter")
        await pilot.pause()
        enemy = app.screen.query_one("#enemy", Static).content
        assert "█" in str(enemy)
```
- [ ] **Step 2: Run test — GAGAL** (panel musuh masih teks polos).
- [ ] **Step 3: GREEN** — `_enemy_lines`:
```python
bar = make_bar(enemy["hp"], enemy["hp_max"], 12)
lines.append(
    f"[bold red]{enemy['name']}[/] HP [red]{bar}[/] "
    f"{enemy['hp']}/{enemy['hp_max']} | Qi {enemy['qi']} "
    f"| Elemen {enemy['element']}"
)
```
- [ ] **Step 4: Full suite + lint/format — HIJAU.**
- [ ] **Step 5: Commit**
```bash
git commit -am "ui: bar HP visual musuh saat bertarung (GDD 6)"
```

---

### Task 5 — Inventory: Warna Semantik Item

**Files:**
- Modify: `src/core/game_loop.py` (`_cmd_inventory`)
- Modify: `tests/test_game_loop.py`

**Interfaces:**
- Consumes: `load_items()` (type/name per item).
- Produces: output inventory dengan warna per tipe (material cyan, resep
  violet, tool gold3, consumable default).

- [ ] **Step 1: RED** — `tests/test_game_loop.py`:
```python
def test_inventory_mewarnai_per_tipe(tmp_path):
    """Inventory menampilkan warna semantik sesuai tipe item."""
    session = _session(tmp_path)
    session.new_game("Akar")
    session.state.inventory.setdefault("items", {})["esensi_api"] = 2
    session.state.inventory.setdefault("items", {})["kuali_roh"] = 1
    joined = "\n".join(_dispatch(session, "inventory"))
    assert "[cyan]" in joined   # material
    assert "[gold3]" in joined  # tool
```
- [ ] **Step 2: Run test — GAGAL.**
- [ ] **Step 3: GREEN** — `_cmd_inventory`: warna per `item["type"]`
(`material`→cyan, `recipe`→violet, `tool`→gold3, `consumable`→default).
  Baris: `f"  [{color}]{name}[/] x{count}"`.
- [ ] **Step 4: Full suite + lint/format — HIJAU.**
- [ ] **Step 5: Commit**
```bash
git commit -am "ui: pewarnaan semantik item di inventory (GDD 7)"
```
> **ponytail:** DataTable interaktif + tooltip item (saran visual) ditunda —
> upgrade saat panel tim (party system) tiba, agar satu pola panel untuk
> semua.

---

### Task 6 — Input: Koreksi Ketik (difflib) + Autocomplete TAB

**Files:**
- Modify: `src/core/input.py` (`parse_command` + `complete_command` baru)
- Modify: `src/ui/app.py` (binding TAB)
- Modify: `tests/test_input.py`, `tests/test_app.py`

**Interfaces:**
- Consumes: `ALIASES` (kanonik), `difflib` (stdlib).
- Produces: koreksi ketik aman (cutoff tinggi, hanya bila unik) +
  `complete_command(raw) -> str | None` untuk TAB.

- [ ] **Step 1: RED** — `tests/test_input.py`:
```python
def test_koreksi_ketik_dekat():
    """Typo ringan diperbaiki otomatis (rapidfuzz -> difflib stdlib)."""
    assert parse_command("brakthrough").name == "breakthrough"
    assert parse_command("inventroy").name == "inventory"


def test_typo_jauh_tetap_error():
    """Typo jauh tidak dikoreksi (tetap CommandError)."""
    with pytest.raises(CommandError):
        parse_command("flying_sword")


def test_complete_command_menyarankan():
    """Autocomplete mengembalikan perintah terdekat untuk awalan/typo."""
    from src.core.input import complete_command
    assert complete_command("bre") == "breakthrough"
    assert complete_command("invent") == "inventory"
```
- [ ] **Step 2: Run test — GAGAL.**
- [ ] **Step 3: GREEN** — `input.py`:
```python
def _kanonik() -> list[str]:
    """Daftar nama kanonik untuk koreksi & autocomplete."""
    return sorted({v for v in ALIASES.values()})

def _close_match(token: str, cutoff: float = 0.82) -> str | None:
    matches = difflib.get_close_matches(token, _kanonik(), n=1, cutoff=cutoff)
    return matches[0] if matches else None

def complete_command(raw: str) -> str | None:
    """Kata pertama input: nama kanonik terdekat, atau None."""
    token = raw.strip().split()[0].lower() if raw.strip() else ""
    if not token:
        return None
    return _close_match(token)
```
  Di `parse_command`, saat nama tidak dikenal: coba `_close_match(name)` —
  bila ada, pakai kanonik itu; bila tidak, tetap `CommandError` (pesan lama
  dipertahankan, `flying_sword` tetap error). `app.py`: binding
  `("tab", "complete", "Lengkapi")` → isi `#cmd` dengan
  `complete_command(value)` bila ada, kursor di akhir.
- [ ] **Step 4: Run test_input + test_app (TAB) + full suite + lint/format — HIJAU.**
- [ ] **Step 5: Commit**
```bash
git commit -am "input: koreksi ketik difflib + autocomplete TAB (GDD 18)"
```

---

### Task 7 — Verifikasi Akhir & Dokumentasi

**Files:**
- Modify: `GDD.md` (changelog **v1.3**), `AGENTS.md` bila perlu
- Jalankan: semua gerbang + smoke test + review + graphify

- [ ] **Step 1: Dokumentasi** — GDD changelog v1.3 (UI overhaul:
  RichLog, tema grimdark, layout panel, bar HP/Qi, warna item, koreksi
  ketik — semua zero-dependency; `difflib` sebagai pengganti rapidfuzz).
  Commit: `docs: UI overhaul GDD v1.3 (GDD 14.1)`.
- [ ] **Step 2: Gerbang akhir** — `pytest -q` · `ruff check` ·
  `ruff format --check` · `python tools/validate.py` · `graphify update .`.
- [ ] **Step 3: Smoke test alur nyata** (tmux/script): mulai → nama →
  status (bar HP) → go/look (battle bar musuh) → quests → inventory →
  TAB autocomplete → typo "statis" → save/load.
- [ ] **Step 4: Review dua tahap** (§2.7): kepatuhan desain (zero-dep,
  tidak sentuh §6) lalu kualitas kode; terapkan temuan Critical/Important.
- [ ] **Step 5: Lapor ringkas** — perubahan, bukti, hal yang dilewati
  (`ponytail:`: minimap ASCII, animasi/spinner, DataTable tooltip,
  settings menu — ditunda ke polish Fase 5).

---

## Sengaja dilewati (`ponytail:`)

* Minimap ASCII & animasi progress/spinner — polish Fase 5 (GDD §23).
* DataTable inventory + tooltip — saat party system (satu pola panel).
* Semua dependency baru ChatGPT — ditolak (AGENTS §7, §3.1 rung 3–5).
* `settings` menu — belum ada state settings di save (YAGNI).
* Branch isolasi §2.3 tidak dipakai: tidak menyentuh file stabil §6, TDD
  per task, tiap task bisa di-revert terpisah.

## Catatan perilaku

* `status_lines()` berubah format (bar ASCII) — output perintah `status`
  ikut berubah. Test HUD eksisting (`test_game_loop.py:253`,
  `test_app.py:50,104`) assert substring "HP"/"Insight"/"Akar" yang
  tetap ada di format baru — tidak perlu diubah. `tests/test_status.py`
  (status effect combat) tidak terpengaruh sama sekali.
* `parse_command` kini mengoreksi typo dekat — perilaku "perintah tak
  dikenal" berubah hanya untuk typo ringan yang unik; `flying_sword`
  tetap error (test lama dipertahankan).
* Semua perubahan tampilan murni; engine combat/kultivasi/quest tidak
  disentuh — suite 323 test harus tetap hijau tanpa melemahkan satu pun.
