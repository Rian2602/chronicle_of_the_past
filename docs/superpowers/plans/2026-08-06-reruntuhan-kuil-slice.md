# Reruntuhan Kuil: Vertical Slice Arc 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Menutup dead-end Arc 1 dengan slice data-driven Reruntuhan Kuil — Zombi Kuil + Penjaga Makam (bos) + quest103 + memori "rahasia pertama" (tempat ujian Orde Rahasia) + item `pil_peneguh_fondasi` — dan memindahkan spawn musuh dari hardcode ke data peta (GDD §11).

**Architecture:** Spawn musuh menjadi data-driven: schema `maps.json` diperluas dengan `enemies: [{enemy, requires_flag}]`; `_cmd_look` memunculkan musuh pertama yang syaratnya terpenuhi & belum dikalahkan. Alur naratif via event engine (sudah ada): `shrine_trial_start` (start quest103) → kalahkan Zombi → `ruin_shrine_cleared` membuka Penjaga Makam → `shrine_reveal` (grant memori + item) dipicu quest103_done. `_finish_battle` ditambah `_run_events()` agar reveal mengalir seketika.

**Tech Stack:** Python 3.12+, Rich/Textual (dipakai), stdlib, pytest, ruff (Google style ≤80), JSON data-driven.

## Global Constraints

- TDD wajib: RED → GREEN → REFACTOR → commit (AGENTS §2.1); data JSON diuji dulu sebelum ditambah.
- `pytest -q`, `ruff check`, `ruff format --check`, `python tools/validate.py` wajib hijau sebelum DoD (§1, §12).
- `graphify update .` wajib setelah ubah kode (§4.3).
- Data eksisting **DILARANG** dihapus/diganti; hanya ditambah (§6).
- Bahasa Indonesia untuk semua `name/description/text`; nada **grimdark** (GDD §3.6).
- Elemen siklus Metal→Kayu→Tanah→Air→Api→Metal konsisten (GDD §6.2).
- Flag quest otomatis `quest<id>_done`; bos tak boleh dikaburi (engine sudah menangani, combat.py:410). **DILARANG** flag penyelesaian paralel (§11).
- Baris ≤80 karakter; docstring Google-style (header English, isi Indonesia).
- Tidak ada dependency baru; tidak menyentuh file stabil `combat.py`, `cultivation.py`, `models/player.py` (§6).

---

### Task 1: Data Musuh — Zombi Kuil & Penjaga Makam

**Files:**
- Create: `data/enemies/zombie_temple.json`, `data/enemies/penjaga_makam.json`
- Modify: `tests/test_enemy_data.py:33` (EXPECTED_ENEMIES)
- Test: `tests/test_enemy_data.py`

**Interfaces:**
- Consumes: `load_enemies()` (src/engine/combat.py), schema `Enemy` (src/models/enemy.py), tier `qi_condensation`, teknik `qi_slash`/`flame_strike`.
- Produces: enemy id `zombie_temple` (tag `undead`, elemen `earth`), `penjaga_makam` (tag `boss`+`human`, elemen `metal`) — dipakai Task 2 (maps), Task 3 (quest103), Task 4 (test).

- [ ] **Step 1: Update test (RED)** — `tests/test_enemy_data.py:33` ubah menjadi:
```python
EXPECTED_ENEMIES = {"serigala_qi", "bandit_perbatasan", "zombie_temple", "penjaga_makam"}
```
- [ ] **Step 2: Run test, pastikan GAGAL** — Run: `pytest tests/test_enemy_data.py -q` — Expected: FAIL (`files != expected`, file baru belum ada).

- [ ] **Step 3: Tambah data** — `data/enemies/zombie_temple.json`:
```json
{
  "id": "zombie_temple",
  "name": "Zombi Kuil",
  "tier": "qi_condensation",
  "element": "earth",
  "behavior": "aggressive",
  "stats": {
    "attack": 6,
    "defense": 3,
    "agility": 2,
    "intelligence": 1,
    "vitality": 6,
    "spirit": 2,
    "hp": 28,
    "qi": 6
  },
  "skills": ["qi_slash"],
  "tags": ["undead"],
  "rewards": {"insight": 20, "gold": 15}
}
```
`data/enemies/penjaga_makam.json` (stat cukup untuk attack-spam menang, tetap paling kuat tier 1):
```json
{
  "id": "penjaga_makam",
  "name": "Penjaga Makam",
  "tier": "qi_condensation",
  "element": "metal",
  "behavior": "defensive",
  "stats": {
    "attack": 10,
    "defense": 7,
    "agility": 4,
    "intelligence": 5,
    "vitality": 7,
    "spirit": 4,
    "hp": 55,
    "qi": 15
  },
  "skills": ["qi_slash", "flame_strike"],
  "tags": ["boss", "human"],
  "rewards": {"insight": 80, "gold": 50}
}
```

- [ ] **Step 4: Run test, pastikan HIJAU** — Run: `pytest tests/test_enemy_data.py -q && python tools/validate.py` — Expected: PASS, `OK`.

- [ ] **Step 5: Commit**
```bash
git add data/enemies tests/test_enemy_data.py
git commit -m "data: musuh Arc 1 Zombi Kuil & Penjaga Makam (GDD 11)"
```

---

### Task 2: Schema Peta + Spawn Data-Driven di Data

**Files:**
- Modify: `data/maps/ashfall_forest.json`, `data/maps/ruin_shrine.json`
- Modify: `tests/test_map_data.py:8-26` (REQUIRED_KEYS subset + test ref musuh)
- Test: `tests/test_map_data.py`

**Interfaces:**
- Consumes: `load_maps()` (src/engine/maps.py — mengembalikan dict mentah, kunci `enemies` ikut terbawa tanpa ubah loader), musuh dari Task 1.
- Produces: schema baru `enemies: [{enemy: str, requires_flag: str|null}]` di maps.json — dibaca `_cmd_look` (Task 4) dan validator (Task 3).

- [ ] **Step 1: Update test (RED)** — `tests/test_map_data.py`: ubah skema jadi subset, tambah test ref musuh:
```python
REQUIRED_KEYS = {"id", "name", "description", "tier"}  # + opsional "enemies"

def test_semua_peta_memenuhi_skema():
    for path in DATA_DIR.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        assert set(data) >= REQUIRED_KEYS, f"{path.name}: kunci tidak sesuai"
        assert isinstance(data["id"], str) and data["id"] == path.stem
        assert isinstance(data["name"], str) and data["name"]
        assert isinstance(data["description"], str) and data["description"]
        assert isinstance(data["tier"], int) and data["tier"] >= 1

def test_peta_arc1_menyebut_musuh_yang_valid():
    """Ref enemies di peta wajib ter-resolve (GDD §9, §11)."""
    from src.engine.combat import load_enemies
    enemy_ids = {enemy.id for enemy in load_enemies()}
    for path in DATA_DIR.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        for entry in data.get("enemies", []):
            assert entry["enemy"] in enemy_ids, (
                f"{path.name}: musuh {entry['enemy']} tidak dikenal"
            )
            assert isinstance(entry.get("requires_flag", None), (str, type(None)))
```
- [ ] **Step 2: Run test, pastikan GAGAL** — Run: `pytest tests/test_map_data.py::test_peta_arc1_menyebut_musuh_yang_valid -q` — Expected: FAIL (map belum punya `enemies`).

- [ ] **Step 3: Tambah data** — `data/maps/ashfall_forest.json` tambah:
```json
  "enemies": [{"enemy": "bandit_perbatasan"}]
```
`data/maps/ruin_shrine.json` tambah:
```json
  "enemies": [
    {"enemy": "zombie_temple", "requires_flag": "quest102_done"},
    {"enemy": "penjaga_makam", "requires_flag": "ruin_shrine_cleared"}
  ]
```
- [ ] **Step 4: Run test + validator, HIJAU** — Run: `pytest tests/test_map_data.py -q && python tools/validate.py` — Expected: PASS, `OK` (validator belum cek map→enemy; itu Task 3).

- [ ] **Step 5: Commit**
```bash
git add data/maps tests/test_map_data.py
git commit -m "data: spawn musuh data-driven via schema peta (GDD 9/11)"
```

---

### Task 3: Data Naratif + Loader Item + Validator Map→Enemy & Item

**Files:**
- Create: `src/engine/items.py`, `data/items/pil_peneguh_fondasi.json`
- Create: `data/quests/quest103.json`, `data/story/memory_shrine_trial.json`, `data/events/shrine_trial_start.json`, `data/events/shrine_reveal.json`
- Modify: `tools/validate.py` (maps→dict `map_ids` di 4 titik; cek map→enemy; cek grant_item→item), `tests/test_validate_tool.py`
- Test: `tests/test_validate_tool.py`

**Interfaces:**
- Consumes: event engine action kinds (`start_quest`, `grant_memory`, `grant_item`, `log` — semua sudah ada di src/engine/event.py:27-38), quest kinds `enemy` (src/engine/quest.py:110).
- Produces: `load_items(data_dir=ITEM_DIR) -> dict[str, dict[str,str]]` (kunci `id`+`name`), item `pil_peneguh_fondasi`, `quest103`, `memory_shrine_trial`, `shrine_trial_start`, `shrine_reveal` — dipakai Task 4 (spawn, reveal, display inventory).

**Catatan urutan (K1):** loader item dibuat DI SINI karena validator Task 3 memakainya. Item file wajib ada sebelum validator cek `grant_item` referensi.

- [ ] **Step 1: Tulis test validator map→enemy (RED)** — tambah di `tests/test_validate_tool.py`:
```python
def test_validator_menangkap_ref_map_enemy(tmp_path):
    """Map dengan enemies merujuk musuh tak dikenal wajib dilaporkan."""
    data = _pohon_data(tmp_path)
    (data / "maps" / "map_test.json").write_text(
        json.dumps(
            {
                "id": "map_test",
                "name": "Peta Uji",
                "description": "Tempat uji.",
                "tier": 1,
                "enemies": [{"enemy": "hantu_kuno"}],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    assert any("hantu_kuno" in e for e in collect_errors(data))
```
- [ ] **Step 2: Tulis test validator grant_item→item (RED)** — tambah:
```python
def test_validator_menangkap_ref_item(tmp_path):
    """Event grant_item ke item tak dikenal wajib dilaporkan."""
    data = _pohon_data(tmp_path)
    (data / "events" / "ev_test.json").write_text(
        json.dumps(
            {
                "id": "ev_test",
                "trigger": [],
                "actions": [{"kind": "grant_item", "id": "pil_hantu"}],
                "once": True,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    assert any("pil_hantu" in e for e in collect_errors(data))
```
- [ ] **Step 3: Run kedua test, pastikan GAGAL** — Expected: FAIL (`collect_errors` tidak menemukan temuan).

- [ ] **Step 4: Buat loader item** — `src/engine/items.py`:
```python
"""Item (GDD §14.2) — konten nama item data-driven.

Engine hanya menyimpan item_id di state.inventory; nama tampilan dibaca
dari ``data/items/`` (pola sama dengan story.py).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
ITEM_DIR = DATA_DIR / "items"


def load_items(data_dir: Path = ITEM_DIR) -> dict[str, dict[str, str]]:
    """Muat semua item dari data/items/ keyed by id.

    Args:
        data_dir: Direktori berisi JSON item (default data/items/).

    Returns:
        Mapping item_id -> dict dengan kunci ``id`` dan ``name``.

    Raises:
        KeyError: Jika sebuah file JSON tidak punya kunci ``id``.
    """
    items: dict[str, dict[str, str]] = {}
    for path in sorted(data_dir.glob("*.json")):
        raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        items[raw["id"]] = {"id": raw["id"], "name": raw["name"]}
    return items
```
`data/items/pil_peneguh_fondasi.json`:
```json
{
  "id": "pil_peneguh_fondasi",
  "name": "Pil Peneguh Fondasi"
}
```

- [ ] **Step 5: Perbarui validator** — `tools/validate.py`:
  - Impor: `from src.engine.items import load_items  # noqa: E402`
  - Ganti `maps = set(load_maps(data_dir / "maps"))` jadi:
```python
    maps = load_maps(data_dir / "maps")
    map_ids = set(maps)
    enemies = load_enemies(data_dir / "enemies")
    enemy_ids = {enemy.id for enemy in enemies}
    items = load_items(data_dir / "items")
```
  - Ganti **4 pemakaian** `maps` jadi `map_ids`: baris quest `objective.kind == "map"`, event `location_entered`, event `unlock_map`, dan lokasi NPC.
  - Tambah cek ref map→enemy (di akhir sebelum `return sorted(errors)`):
```python
    for map_id, raw in maps.items():
        for entry in raw.get("enemies", []):
            if entry["enemy"] not in enemy_ids:
                errors.append(
                    f"{map_id}: enemies -> musuh {entry['enemy']} tidak ada"
                )
```
  - Tambah cabang `grant_item` di loop action event:
```python
            elif kind == "grant_item" and action["id"] not in items:
                errors.append(f"{event.id}: grant_item -> {action['id']} tidak ada")
```

- [ ] **Step 6: Run test validator, HIJAU** — Run: `pytest tests/test_validate_tool.py -q` — Expected: 4 PASS.

- [ ] **Step 7: Tambah data naratif**
`data/quests/quest103.json`:
```json
{
  "id": "quest103",
  "title": "Ujian Orde Kuno",
  "type": "main",
  "description": "Kuil ini tempat ujian. Penjaga Makam menguji mereka yang disebut 'yang ditunggu' — dan setiap nama di dinding sebelumnya gagal.",
  "objectives": [
    {"kind": "enemy", "target": "zombie_temple"},
    {"kind": "enemy", "target": "penjaga_makam"}
  ],
  "rewards": {"insight": 100, "gold": 50, "reputation": {"rebels": 5}},
  "flags_on_complete": [],
  "next": null,
  "category": "main",
  "requires_flag": null
}
```
`data/story/memory_shrine_trial.json`:
```json
{
  "id": "memory_shrine_trial",
  "title": "Tempat Ujian",
  "text": "Gema penjaga terakhir menelusup ke kesadaranmu: kuil ini bukan makam — ia tempat ujian. Sisa Orde Rahasia menunggu 'yang ditunggu' di sini, dan setiap penerus sebelummu tumbang di atas batu ini. Namamu kini terukir di bawah nama-nama yang mati. Kau yang pertama menang. Namun bisikan di dinding tak terdengar seperti pujian — ia terdengar seperti hitung mundur."
}
```
`data/events/shrine_trial_start.json`:
```json
{
  "id": "shrine_trial_start",
  "trigger": [
    {"kind": "location_entered", "map": "ruin_shrine"},
    {"kind": "quest_done", "quest": "quest102"}
  ],
  "actions": [
    {"kind": "start_quest", "id": "quest103"},
    {"kind": "log", "text": "Di dinding ruang bawah, guratan kuno menyala menuliskan deretan nama — semuanya gagal. Dari celah batu, Penjaga Makam bangkit untuk menguji 'yang ditunggu'."}
  ],
  "once": true
}
```
`data/events/shrine_reveal.json`:
```json
{
  "id": "shrine_reveal",
  "trigger": [
    {"kind": "quest_done", "quest": "quest103"}
  ],
  "actions": [
    {"kind": "grant_memory", "memory_id": "memory_shrine_trial"},
    {"kind": "grant_item", "id": "pil_peneguh_fondasi", "count": 1},
    {"kind": "log", "text": "Di balik singgasana batu, pil peneguh fondasi menanti — hadiah bagi yang lulus ujian. Sebuah gema memori tertangkap."}
  ],
  "once": true
}
```
- [ ] **Step 8: Validasi penuh data** — Run: `python tools/validate.py && pytest tests/test_event_data.py tests/test_quest_data.py -q` — Expected: `OK`, PASS.

- [ ] **Step 9: Commit**
```bash
git add src/engine/items.py data/items data/quests data/story data/events tools/validate.py tests/test_validate_tool.py
git commit -m "data: slice kuil quest103, memori, item, loader item, validator (GDD 5.3/11/12/25.3)"
```

---

### Task 4: Engine — Spawn Data-Driven, Reveal Setelah Kemenangan, Display Inventory

**Files:**
- Modify: `src/core/game_loop.py:50-57` (hapus const `FOREST_ID`/`FOREST_ENEMY`), `:301-315` (`_cmd_look`), `:556-588` (`_finish_battle`), `:203-207` (`_cmd_inventory`)
- Test: `tests/test_game_loop.py` (2 test baru)

**Interfaces:**
- Consumes: `load_maps()` (key `enemies` dari Task 2), `load_items()` (Task 3), `state.kills`, `state.flags` (`ruin_shrine_cleared` diset `_finish_battle`), data Task 1 & 3.
- Produces: perilaku spawn per lokasi (data-driven) + display nama item — menjadi dasar test alur.

- [ ] **Step 1: Tulis test (RED)** — tambah di `tests/test_game_loop.py`:
```python
def test_look_kuil_sebelum_quest102_tidak_memicu_battle(tmp_path):
    """Gating §11: kuil tanpa quest102_done tidak memunculkan musuh."""
    session = _session(tmp_path)
    session.new_game("Akar")
    session.state.player.add_insight(100)
    _dispatch(session, "breakthrough")
    _dispatch(session, "go ruin_shrine")
    lines = _dispatch(session, "look")
    assert session.in_battle is False
    assert any("Reruntuhan Kuil" in line for line in lines)


def test_slice_kuil_lengkap_quest103_dan_rahasia(tmp_path):
    """Alur Arc 1: zombi -> bos -> quest103 -> memori + pil."""
    session = _session(tmp_path)
    session.new_game("Akar")
    _dispatch(session, "talk elder_mao")
    session.state.player.add_insight(100)
    _dispatch(session, "breakthrough")
    _dispatch(session, "talk lin_wei")
    _dispatch(session, "go ruin_shrine")
    assert "quest102_done" in session.state.flags
    assert "quest103" in session.state.quests.started
    _dispatch(session, "look")
    assert session.in_battle is True
    frame = session.battle_frame()
    while not frame.over:
        frame = session.battle_step("attack")
    assert frame.victory is True
    _dispatch(session, "look")
    assert session.in_battle is True
    frame = session.battle_frame()
    while not frame.over:
        frame = session.battle_step("attack")
    assert frame.victory is True
    assert "quest103_done" in session.state.flags
    assert "memory_shrine_trial" in session.state.memories
    assert session.state.inventory["items"]["pil_peneguh_fondasi"] == 1
    lines = _dispatch(session, "inventory")
    assert any("Pil Peneguh Fondasi" in line for line in lines)
```
- [ ] **Step 2: Run test, pastikan GAGAL** — Expected: FAIL (spawn masih hardcode hanya untuk hutan; `look` di kuil mengembalikan deskripsi).

- [ ] **Step 3: Implement `_cmd_look` data-driven** — `src/core/game_loop.py:301-315` ganti jadi:
```python
    def _cmd_look(self, _command: Command) -> list[str]:
        """Amati lokasi saat ini: deskripsi dari data/maps (GDD §9).

        Musuh per peta didefinisikan di data (enemies + requires_flag);
        yang pertama memenuhi syarat dan belum dikalahkan memicu
        pertarungan (GDD §11).
        """
        location = self.state.location
        data = load_maps().get(location)
        if data is not None:
            for entry in data.get("enemies", []):
                enemy_id = entry["enemy"]
                requires = entry.get("requires_flag")
                if requires and not self.state.flags.get(requires):
                    continue
                if self.state.kills.get(enemy_id, 0) >= 1:
                    continue
                return self._start_battle(enemy_id)
        if data is None:
            return [f"Kamu di {location}. Tempat ini sunyi."]
        return [f"{data['name']}: {data['description']}"]
```
Hapus const `FOREST_ID`/`FOREST_ENEMY` beserta komentarnya (`:50-57`). Tambah impor `from src.engine.items import load_items` (kelompok impor engine, setelah `src.engine.event`).

- [ ] **Step 4: Tambah `_run_events` di `_finish_battle`** — di cabang kemenangan, setelah loop quest:
```python
            for line in self._run_quests():
                battle.log.append(line)
            for line in self._run_events():
                battle.log.append(line)
```

- [ ] **Step 5: Display inventory** — `_cmd_inventory` ganti jadi:
```python
    def _cmd_inventory(self, _command: Command) -> list[str]:
        """Tampilkan isi tas dengan nama item dari data (GDD §14.2)."""
        items = self.state.inventory.get("items", {})
        if not items:
            return ["Tasmu kosong."]
        names = load_items()
        lines = ["Isi tas:"]
        for item_id, count in sorted(items.items()):
            # ponytail: item tanpa data (save lama) -> id mentah; validator
            # §25.3 menjamin event->item ter-resolve.
            name = names.get(item_id, {}).get("name", item_id)
            lines.append(f"  {name} x{count}")
        return lines
```

- [ ] **Step 6: Full suite, HIJAU** — Run: `pytest -q` — Expected: semua PASS. Lalu:
```bash
ruff check src tests tools && ruff format --check src tests tools
```

- [ ] **Step 7: Commit**
```bash
git add src/core/game_loop.py tests/test_game_loop.py
git commit -m "engine: spawn musuh data-driven, reveal pasca kemenangan, display item (GDD 9/11)"
```

---

### Task 5: Sinkronisasi Dokumen

**Files:**
- Modify: `GDD.md` (§9 — schema peta + `enemies`), `AGENTS.md` (§6 — inventori data)

- [ ] **Step 1: GDD §9** — tambahkan blok skema peta setelah paragraf gating:
```markdown
**Skema peta (data-driven):**
```json
{
  "id": "ruin_shrine",
  "name": "Reruntuhan Kuil",
  "description": "...",
  "tier": 1,
  "enemies": [
    {"enemy": "zombie_temple", "requires_flag": "quest102_done"},
    {"enemy": "penjaga_makam", "requires_flag": "ruin_shrine_cleared"}
  ]
}
```
* `enemies` (opsional): daftar musuh; saat `look`, musuh pertama yang
  `requires_flag`-nya terpenuhi dan belum dikalahkan (`kills >= 1`) memicu
  pertarungan. Ini mekanisme gating kemunculan bos (§11). Gating diletakkan
  di level peta, bukan field `Enemy.requires_flag`, agar satu musuh bisa
  muncul di beberapa peta dengan syarat berbeda.
```
- [ ] **Step 2: AGENTS §6** — perbarui baris inventori data eksisting: `(6 tier, 3 teknik, 2 musuh, 3 event)` → `(6 tier, 3 teknik, 4 musuh, 8 event, 3 peta, 3 quest, 2 memori)`.

- [ ] **Step 3: Commit**
```bash
git add GDD.md AGENTS.md
git commit -m "docs: schema peta + enemies di GDD, sinkronkan inventori AGENTS.md"
```

---

### Task 6: Verifikasi Akhir (Definition of Done, AGENTS §12)

- [ ] `pytest -q` — semua lulus
- [ ] `ruff check src launcher.py tools tests` — bersih
- [ ] `ruff format --check src launcher.py tools tests` — bersih
- [ ] `python tools/validate.py` — `OK`
- [ ] Smoke test alur nyata: jalankan permainan, mainkan quest101→102→103→bos→memori (verifikasi output UI terminal, bukan hanya unit test)
- [ ] `graphify update .` (ada perubahan kode)
- [ ] Review dua tahap: kepatuhan GDD (spawn gating §11, flag quest §24.1, grimdark §3.6) lalu kualitas kode
- [ ] Ringkasan: apa yang diubah, bukti, hal yang sengaja dilewati

**Sengaja dilewati:** rekrut Lin Wei (§20.2), schema item lengkap (description/effect — pil hanya nama, YAGNI sampai ada engine item), teknik baru, dan field `Enemy.requires_flag` di dataclass tetap tak terpakai (gating ditangani level peta; keputusan terdokumentasi di GDD §9).
