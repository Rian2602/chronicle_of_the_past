# Arc 2 Systems Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Menyelesaikan fitur-fitur sistem (engine) krusial Fase 2 yang tertinggal (Artefak, Command Eksplorasi, Formasi, Ending Points, dan Evolusi Binatang Roh) untuk merampungkan pondasi mekanik sebelum masuk ke pembuatan konten Fase 3.

**Architecture:** Menerapkan penambahan field pada model item, command statis pada `game_loop.py`, membuat modul baru `src/systems/formation.py`, dan memperluas _schema state/event_ untuk `ending_points`.

**Tech Stack:** Python 3.12+, pytest

## Global Constraints

- Semua konten naratif/pesan UI HARUS menggunakan Bahasa Indonesia.
- ID dan nama berkas HARUS `snake_case`.
- Semua referensi data antar berkas JSON HARUS valid sesuai `tools/validate.py`.
- TDD diwajibkan: Semua kode produksi baru harus diverifikasi dengan tes (`pytest -q` bersih dan lewat).
- Tidak boleh mengubah `combat.py` dan `cultivation.py` kecuali 1 baris yang ditunjuk (jika ada).

---

### Task 1: P1-B Artifact System Completion

**Files:**
- Modify: `src/engine/items.py`
- Modify: `data/items/cermin_bayangan.json`
- Modify: `data/items/liontin_api.json`
- Modify: `data/items/pedang_awan_hitam.json`
- Modify: `tests/test_artifacts.py`

**Interfaces:**
- Consumes: JSON item definitions.
- Produces: `load_items()` returns dict items including `growth_stat` and `max_level`. `add_artifact_xp()` respects `max_level` from item catalog (if provided) instead of hardcoding `5`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_artifacts.py
from src.engine.items import load_items, add_artifact_xp

def test_artifact_loads_growth_and_max_level():
    items = load_items()
    if "cermin_bayangan" in items:
        assert "growth_stat" in items["cermin_bayangan"]
        assert "max_level" in items["cermin_bayangan"]

def test_add_artifact_xp_respects_max_level():
    class DummyState:
        inventory = {"artifacts": {"test_art": {"xp": 0, "level": 1}}}
    
    # We simulate loading max_level by passing a catalog or letting add_artifact_xp fetch it.
    # We will modify add_artifact_xp to accept an optional catalog parameter for testing/lookup.
    catalog = {"test_art": {"max_level": 2}}
    state = DummyState()
    
    add_artifact_xp(state, "test_art", 100, catalog)
    assert state.inventory["artifacts"]["test_art"]["level"] == 2
    add_artifact_xp(state, "test_art", 100, catalog)
    assert state.inventory["artifacts"]["test_art"]["level"] == 2 # Maxed out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_artifacts.py -v`
Expected: FAIL (fields missing, max_level ignored)

- [ ] **Step 3: Write minimal implementation**

Update `src/engine/items.py` in `load_items`:
```python
            "recipe": raw.get("recipe"),
            "growth_stat": raw.get("growth_stat"),
            "max_level": raw.get("max_level"),
```

Update `add_artifact_xp` to accept an optional `catalog` parameter to fetch `max_level` (default 5):
```python
def add_artifact_xp(state: Any, artifact_id: str, amount: int, catalog: dict = None) -> bool:
    """Tambahkan XP ke artefak; kembalikan True jika naik level."""
    if artifact_id not in state.inventory["artifacts"]:
        return False
    artifact = state.inventory["artifacts"][artifact_id]
    artifact["xp"] += amount
    leveled_up = False
    
    if catalog is None:
        catalog = load_items()
        
    max_level = catalog.get(artifact_id, {}).get("max_level", 5)

    while artifact["level"] < max_level and artifact["xp"] >= artifact["level"] * 100:
        artifact["xp"] -= artifact["level"] * 100
        artifact["level"] += 1
        leveled_up = True
    return leveled_up
```

Update the 3 existing JSON artifact files to include `"growth_stat": "intelligence"` (or relevant stat) and `"max_level": 5`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_artifacts.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/engine/items.py tests/test_artifacts.py data/items/*.json
git commit -m "feat(items): add growth_stat and max_level to artifact system"
```

---

### Task 2: P1-C Implement Missing Commands

**Files:**
- Modify: `src/core/game_loop.py`
- Modify: `tests/test_game_loop.py`

**Interfaces:**
- Produces: `_cmd_meditate`, `_cmd_examine`, `_cmd_loot`, `_cmd_recall`, `_cmd_settings` in `GameLoop`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_game_loop.py
def test_missing_exploration_commands(tmp_path):
    from src.core.input import Command
    session = _session(tmp_path)
    session.new_game("Akar")
    
    # settings
    res = session._cmd_settings(Command("settings", []))
    assert "Pengaturan" in res[0]
    
    # loot
    res = session._cmd_loot(Command("loot", []))
    assert "jarahan" in res[0].lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_game_loop.py::test_missing_exploration_commands -v`
Expected: FAIL (missing methods)

- [ ] **Step 3: Write minimal implementation**

Add to `src/core/game_loop.py`:
```python
    def _cmd_meditate(self, command: Command) -> list[str]:
        # Pulihkan qi (versi sederhana dari rest)
        self.state.player.qi = self.state.player.qi_max
        return ["Kamu bermeditasi. Qi pulih sepenuhnya."]

    def _cmd_examine(self, command: Command) -> list[str]:
        return ["Tidak ada objek spesifik untuk diperiksa di sini saat ini."]

    def _cmd_loot(self, command: Command) -> list[str]:
        return ["Tidak ada jarahan di area ini."]

    def _cmd_recall(self, command: Command) -> list[str]:
        return ["Fitur recall binatang roh akan segera hadir."]
        
    def _cmd_settings(self, command: Command) -> list[str]:
        return ["--- Pengaturan ---", "1. Kecepatan Teks: Normal", "(Gunakan command lain untuk mengubah)"]
```
Register them in `_execute_command` logic if needed (usually handled by reflection `getattr(self, f"_cmd_{command.name}")`). Ensure `aliases` in `src/core/input.py` if not already present.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_game_loop.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/core/game_loop.py tests/test_game_loop.py
git commit -m "feat(core): add stubs for meditate, examine, loot, recall, settings"
```

---

### Task 3: P2-B & P2-C System State Extensions (Ending Points & Formations Base)

**Files:**
- Modify: `src/core/state.py`
- Modify: `src/engine/event.py`
- Modify: `src/core/save.py`
- Test: `tests/test_event_actions.py` (create if needed or use `test_game_loop.py`)

**Interfaces:**
- Produces: `ending_points` in `GameState`, `add_ending_points` action in Event Engine, `formations` data map.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_state.py
from src.core.state import GameState

def test_ending_points_initialized():
    state = GameState()
    assert state.ending_points == {"defy": 0, "seal": 0, "reconcile": 0}

# tests/test_game_loop.py (or similar for event action)
def test_add_ending_points_action():
    from src.engine.event import process_actions
    state = GameState()
    process_actions([{"kind": "add_ending_points", "path": "defy", "points": 10}], state)
    assert state.ending_points["defy"] == 10
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest -v`
Expected: FAIL (`GameState` has no `ending_points`)

- [ ] **Step 3: Write minimal implementation**

Update `GameState` in `src/core/state.py`:
```python
@dataclass
class GameState:
    # ... existing fields ...
    ending_points: dict[str, int] = field(default_factory=lambda: {"defy": 0, "seal": 0, "reconcile": 0})
```

Update `process_actions` in `src/engine/event.py`:
```python
    elif kind == "add_ending_points":
        state.ending_points[action["path"]] += action["points"]
```

Update `src/core/save.py` to ensure backfill:
```python
    state.ending_points = raw.get("ending_points", {"defy": 0, "seal": 0, "reconcile": 0})
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/core/state.py src/engine/event.py src/core/save.py tests/
git commit -m "feat(system): add ending_points tracking for Phase 4 foundation"
```
