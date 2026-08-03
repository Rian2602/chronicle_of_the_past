# Chronicle of the Past — Phase 2 (Playable Vertical Slice) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the engine-only codebase (Tasks 1–10, frozen baseline) into a playable vertical slice of Arc 1: dialog engine, NPC/faction content, maps + ASCII art, event engine, save/load, terminal UI (renderer/HUD/menu/views), game orchestration + launcher, and complete Arc 1 content in Bahasa Indonesia.

**Architecture:** Data-driven. Content in `data/*.json`; generic engine/systems in `src/`. Engine/systems/UI communicate via GameState (dependency injection, no globals). UI is read-only (`ui` never imports `engine`/`systems`). Seeded RNG through `src/core/randomizer.py`. Per MASTER_CONCEPT §6.3, the command parser is `src/core/input_handler.py` + `src/models/command.py` (NOT `engine/command_parser.py`).

**Tech Stack:** Python 3.12 stdlib only, pytest (dev only). **Divergence from MASTER_CONCEPT:** Rich, Pydantic v2, and uv are SKIPPED per user decision — visual stack remains stdlib (ANSI + box-drawing with ASCII fallback); models stay dataclasses; `requirements.txt` stays, no `pyproject.toml`.

## Context & Scope

This plan is **Phase 2** of the existing project. The old plan
`docs/superpowers/plans/2026-08-02-chronicle-of-the-past.md` remains the frozen
baseline for Tasks 0–10 (all complete, 280 tests green, HEAD `ceecf03`).
This plan **restructures the old Tasks 11–18 into 8 flat tasks** (NO subtasks),
renumbered 1–8, and folds in the Claude MASTER_CONCEPT roadmap items that map
to that remaining work.

### Task remap (old plan task → this plan task)

| Old task | New task | Claude roadmap items absorbed |
|---|---|---|
| 11 Dialog + NPC + factions | **Task 1** | T3 NPC Framework, T4 Faction/Reputation, T5 Dialogue |
| 12 Maps + ascii + event engine | **Task 2** | T6 Event Engine, T7 Maps/Assets |
| 13 Save Manager | **Task 3** | T10 Save |
| 14 UI Renderer | **Task 4** | T11 UI Renderer |
| 15 UI Views + command parser | **Task 5** | T12 UI Views + Command parsing |
| 16 Game orchestration + launcher | **Task 6** | T8 Registry, T14 Orchestration |
| 17 Full Arc 1 content | **Task 7** | T2 Story Graph `arcs.json`, T13 Bestiary, T15 Arc 1 content, T9 Regression |
| 18 Docs + polish | **Task 8** | T17 Docs, T16 Regression |

Claude roadmap item **T1 (Reconciliation of Task 1–10) is DROPPED** per user
decision — the frozen Task 1–10 output already matches the original plan.

### Corrections to Claude's roadmap claims (verified against repo)

- **No save foundation exists.** `src/core/save_manager.py` does not exist — Task 3 is net-new.
- **No `parse_input()` exists.** `engine/command_parser.py` does not exist; parser is net-new in `core/input_handler.py` + `models/command.py` (per MASTER_CONCEPT §6.3).
- **`assets/ui/borders.json` and `assets/ui/colors.json` exist but are EMPTY `{}`** — Task 4 must populate them (semantic palette per MASTER_CONCEPT §5.2).
- **No `data/skills/` directory** — classes reference `starting_skills` (`slash`, `backstab`, `fireball`, `quick_shot`, `inspect`) but no skill JSON exists. Task 7 creates them (and enemy skills).
- **No `data/npc`, `data/dialogues`, `data/factions`, `data/maps`, `data/events`** yet — Tasks 1/2 create them.

### Divergences from MASTER_CONCEPT (user-approved, recorded)

1. **Factions (R2):** MASTER_CONCEPT canonical list is `{kingdom, church, rebels, merchant_guild, scholar_society, village(local), ancient_order}`. This repo pins `constants.FACTIONS = [royal_army, church, rebels, merchant_guild, scholar_society, ancient_order, crime]` (frozen, `test_validator.py:40-42`). **Kept frozen.** `data/factions/*.json` uses the frozen IDs (one file per faction). The `village` local faction maps to `merchant_guild` in content.
2. **Bug fix:** `data/quests/quest001.json` and `quest002.json` reward `reputation: {"village": ...}` — invalid faction key (not in FACTIONS). Fixed in Task 7 → `{"merchant_guild": ...}`.
3. **Stack:** stdlib vs Rich/Pydantic/uv (see Tech Stack).
4. **Region IDs:** stay numeric strings (`"1"`, `"2"`); `exploration_system.FOREST_REGIONS = ("2", 2)` is frozen (MASTER_CONCEPT prefers `snake_case`).
5. **Frozen formulas kept:** `xp_to_next = 50*level`, damage variance `random(0,5)`, carry capacity `30 + level*2`, level-up auto-growth + manual pick. MASTER_CONCEPT v1 numbers are "subject to playtest" (Open Q #2) — NOT re-implemented.
6. **Reputation bleed-over (opposition matrix §3.13.1):** the matrix is stored as DATA in `data/factions/*.json` (`opposes`/`aligns`) but NO `reputation_system.py` engine is built in this plan. Existing `quest_engine` applies reputation deltas additively (frozen). Bleed-over is future work.
7. **Map/location trigger caveat:** MASTER_CONCEPT §6.12 Event conditions use `{"type": "location", "equals": "village"}`; the frozen `rule_engine.evaluate` uses `{"kind": "map", "name": "village", "operator": "EQ"}` and compares `game_state.current_map == target` as a STRING. The live `Game` (`_wire`, Task 6) holds a `Map` OBJECT, so a map-triggered event would never fire there. **Content events therefore use FLAG triggers only**; map/time triggers are exercised in unit tests against string-valued `current_map`. This is a KNOWN CONSTRAINT for Arc 1 content writers (do NOT author `type: location` event conditions). Recorded as divergence in MASTER_CONCEPT PART 11 Changelog.

### Global Constraints

- All game text (UI, dialog, narration, errors) in Bahasa Indonesia.
- Runtime deps: stdlib only. pytest is the only dev dependency.
- Box-drawing Unicode with ASCII downgrade in `ui/renderer.py`.
- Determinism: all randomness via `src/core/randomizer.py` seeded RNG. No module-level `random`.
- No globals; GameState passed explicitly. UI never imports engine; engine never imports UI.
- Engine code contains NO specific content names (no "warrior", "goblin", "quest001"). Content strings come from JSON only. Tests may use content IDs.
- 7 combat actions: Attack, Skill, Magic, Item, Observe, Escape, Defend (frozen, `CombatAction`).
- Save JSON 3-layer under `saves/`; missing keys → defaults, never crash.
- Factions pinned: `royal_army, church, rebels, merchant_guild, scholar_society, ancient_order, crime`.
- Derived stats always computed, never stored.
- **RNG rule:** whole-loop outcome asserts only. NEVER assert exact roll sequences (gold roll in `_on_victory` shifts the stream; `player_stats()` re-rolls initiative each call).
- **Wiring pins:** (a) every `equip`/`unequip` call MUST pass `game_state.items` (ledger Task 9 Important); (b) `grant_memory` call sites MUST assert `game_state.player` exists before calling (ledger Task 10 latent — `memory_system.grant_memory` creates a synthetic Player if None).
- **Frozen baseline:** `src/core/{constants,game_state,randomizer,config}.py`, all `src/engine/*`, all `src/systems/*`, `src/models/*`, `src/utils/*`, and all Task 1–10 tests are UNCHANGED except the two additive extensions declared below (Npc.relationship in Task 1, GameState.events/rng_seed in Tasks 2/3). All other new code lives in new files.

---

### Task 1: Dialog engine + NPC content + factions

**Files:**
- Create: `src/engine/dialog_engine.py`
- Create: `tests/test_dialog.py`
- Modify: `src/models/npc.py` (add `relationship` field — additive, default keeps Task 3 tests green)
- Create: `data/npc/old_man.json`, `data/npc/village_chief.json`
- Create: `data/dialogues/dialog_old_man_main.json`, `data/dialogues/dialog_old_man_1.json`, `data/dialogues/dialog_village_chief.json`
- Create: `data/factions/royal_army.json`, `church.json`, `rebels.json`, `merchant_guild.json`, `scholar_society.json`, `ancient_order.json`, `crime.json` (one file per faction — `load_dir` is keyed by each file's `data["id"]`, so a single `factions.json` list would not load)

**Interfaces:**
- Consumes: `GameContext.dialogues` (dict id→dialog dict, from `load_dir`), `GameContext.factions` (dict id→faction dict), `GameState` (`flags`, `player.reputation`). `rule_engine.evaluate` NOT used here (dialog gating is flag/reputation equality only).
- Produces:
  - `dialog_engine.get_dialog(context, dialog_id) -> dict` — returns `context.dialogues[dialog_id]`; raises `KeyError` if unknown.
  - `dialog_engine.available_choices(dialog, game_state) -> list[dict]` — filters `dialog["choices"]` keeping a choice when ALL `require_flags` present AND ALL `require_not_flags` (optional) absent AND ALL `require_reputation` satisfied (`player.reputation[f] >= v`). Choices without a condition key pass that filter.
  - `dialog_engine.choose(game_state, dialog, choice_index) -> str | None` — sets `game_state.flags[f] = True` for each `f` in the choice's `set_flags`; returns the choice's `next` dialog id (or `None`). Invalid `choice_index` → `None`.
- **Dialog JSON schema** (`data/dialogues/<id>.json`, per design spec):

```json
{
  "id": "dialog_old_man_main",
  "lines": [{"speaker": "old_man", "text": "Kau... Aku belum pernah melihatmu."}],
  "choices": [
    {"text": "Siapa Anda?", "require_flags": [], "set_flags": ["met_old_man"], "next": "dialog_old_man_1"},
    {"text": "Aku tersesat.", "require_flags": ["knows_village_burns"], "set_flags": ["met_old_man"], "next": "dialog_old_man_1"},
    {"text": "Pergi.", "require_flags": [], "set_flags": [], "next": null}
  ]
}
```
  Optional choice keys: `require_not_flags: []`, `require_reputation: {"merchant_guild": 10}`.
- **NPC JSON schema** (`data/npc/<id>.json`, design spec §NPC/Dialog):

```json
{
  "id": "old_man",
  "name": "Old Man",
  "location": "village",
  "role": "mentor",
  "relationship": {"trust": 0, "affinity": 0, "knowledge": 0},
  "faction": "ancient_order",
  "dialogs": ["dialog_old_man_main"]
}
```
- **Faction JSON** (`data/factions/<id>.json`, one file per faction) — the 7 FROZEN ids + opposition matrix as data (`opposes`/`aligns`, never evaluated by code this plan). Each file:

```json
{
  "id": "royal_army",
  "name": "Royal Army",
  "pov": "Menjaga stabilitas kerajaan.",
  "opposes": {"rebels": -0.3},
  "aligns": {"church": 0.1}
}
```
  Per-faction `opposes`/`aligns` (adapted from MASTER_CONCEPT §3.13.1 to the frozen ids):
  - `church`: opposes `scholar_society` −0.3, aligns `royal_army` +0.1
  - `rebels`: opposes `royal_army` −0.3, aligns `merchant_guild` +0.1
  - `merchant_guild`: opposes `{}`, aligns `rebels` +0.1, `scholar_society` +0.1 (netral/transaksional)
  - `scholar_society`: opposes `church` −0.3, aligns `merchant_guild` +0.1
  - `ancient_order`: opposes all six main factions −0.3, aligns `{}`
  - `crime`: opposes `{}`, aligns `{}` (no canonical matrix entry; neutral)

- [ ] **Step 1: Write failing tests** (`tests/test_dialog.py`)

```python
from src.engine.dialog_engine import available_choices, choose, get_dialog
from src.core.game_context import GameContext
from src.core.game_state import GameState
from src.models.npc import Npc
from src.models.player import Player


def test_choice_flag_gating():
    gs = GameState()
    dialog = {"id": "d", "lines": [], "choices": [
        {"text": "A", "require_flags": ["knows_village_burns"], "set_flags": [], "next": None},
        {"text": "B", "require_flags": [], "set_flags": ["told"], "next": None}]}
    opts = available_choices(dialog, gs)
    assert len(opts) == 1 and opts[0]["text"] == "B"


def test_choice_require_not_flags_blocks():
    gs = GameState()
    gs.flags["already_spoken"] = True
    dialog = {"id": "d", "lines": [], "choices": [
        {"text": "A", "require_not_flags": ["already_spoken"], "set_flags": [], "next": None},
        {"text": "B", "require_flags": [], "set_flags": [], "next": None}]}
    opts = available_choices(dialog, gs)
    assert len(opts) == 1 and opts[0]["text"] == "B"


def test_choice_reputation_gate():
    gs = GameState()
    gs.player = Player(name="R", class_id="warrior", hp=10, mp=10,
                       base_stats={}, reputation={"merchant_guild": 15})
    dialog = {"id": "d", "lines": [], "choices": [
        {"text": "A", "require_reputation": {"merchant_guild": 20}, "set_flags": [], "next": None},
        {"text": "B", "require_reputation": {"merchant_guild": 10}, "set_flags": [], "next": None}]}
    opts = available_choices(dialog, gs)
    assert len(opts) == 1 and opts[0]["text"] == "B"


def test_choose_applies_flags_and_returns_next():
    gs = GameState()
    dialog = {"id": "d", "lines": [], "choices": [
        {"text": "A", "require_flags": [], "set_flags": ["met_old_man"], "next": "dialog_old_man_1"}]}
    assert choose(gs, dialog, 0) == "dialog_old_man_1"
    assert gs.flags.get("met_old_man") is True


def test_choose_invalid_index_returns_none():
    gs = GameState()
    dialog = {"id": "d", "lines": [], "choices": []}
    assert choose(gs, dialog, 0) is None


def test_get_dialog_from_context():
    ctx = GameContext(data_dir="data")
    dlg = get_dialog(ctx, "dialog_old_man_main")
    assert dlg["id"] == "dialog_old_man_main"


def test_npc_model_has_relationship():
    npc = Npc(id="x", name="X", location="village", role="mentor",
              faction="merchant_guild", dialogs=[])
    assert npc.relationship == {}


def test_factions_json_uses_frozen_ids():
    from src.core.constants import FACTIONS
    ctx = GameContext(data_dir="data")
    assert set(ctx.factions) == set(FACTIONS)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_dialog.py -v`
Expected: FAIL — `ModuleNotFoundError: src.engine.dialog_engine`, plus missing content dirs (empty `data/npc`, `data/dialogues`, `data/factions` → `ctx.factions == {}`).

- [ ] **Step 3: Implement `dialog_engine.py`**

```python
def get_dialog(context, dialog_id):
    return context.dialogues[dialog_id]


def available_choices(dialog, game_state):
    result = []
    player = game_state.player
    for choice in dialog["choices"]:
        if any(f not in game_state.flags for f in choice.get("require_flags", [])):
            continue
        if any(f in game_state.flags for f in choice.get("require_not_flags", [])):
            continue
        rep = choice.get("require_reputation", {})
        if player is not None and any(player.reputation.get(f, 0) < v for f, v in rep.items()):
            continue
        result.append(choice)
    return result


def choose(game_state, dialog, choice_index):
    if choice_index < 0 or choice_index >= len(dialog["choices"]):
        return None
    choice = dialog["choices"][choice_index]
    for flag in choice.get("set_flags", []):
        game_state.flags[flag] = True
    return choice.get("next")
```

- [ ] **Step 4: Add `relationship` field to `Npc`**

Modify `src/models/npc.py`:

```python
from dataclasses import dataclass, field

@dataclass
class Npc:
    id: str
    name: str
    location: str
    role: str
    faction: str
    dialogs: list
    relationship: dict = field(default_factory=dict)
```

- [ ] **Step 5: Write NPC + dialog + factions JSON content** (schemas above; old_man and village_chief with Indonesian dialog; both NPCs `location: "village"`; factions = the 7 frozen ids above).

- [ ] **Step 6: Run full test suite**

Run: `pytest tests/ -q`
Expected: all PASS (280 baseline + new dialog tests).

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "feat: dialog engine with flag/reputation-gated choices + NPC/faction content"
```

- [ ] **Step 8: Review gate** — dispatch code reviewer; fix any `Important` findings; commit fixes.

---

### Task 2: Maps content + ascii art + event engine

**Files:**
- Create: `data/maps/village.json`, `data/maps/forest.json`
- Create: `assets/ascii/village.txt`, `assets/ascii/forest.txt`
- Create: `src/ui/ascii_loader.py`
- Create: `tests/test_ascii_loader.py`
- Create: `src/engine/event_engine.py`
- Create: `tests/test_events.py`
- Create: `data/events/events.json`
- Modify: `src/core/game_state.py` (add additive field `events: list = []`)

**Interfaces:**
- Consumes: `rule_engine.evaluate(condition, game_state)`, `memory_system.grant_memory(game_state, memory_id)`, `quest_engine.start_quest(game_state, quest_id)`, `GameState` (`flags`, `memories`, `player`), `GameContext.events` (list from `data/events/events.json`).
- Produces:
  - `ascii_loader.load(name, assets_dir="assets/ascii") -> str` — reads `<assets_dir>/<name>.txt`, UTF-8; raises `ContentError` (from `utils/json_loader`) if missing.
  - `event_engine.process_events(game_state, randomizer=None, events=None) -> list[str]` — for each event (default `game_state.events`), if ALL `trigger` conditions pass `rule_engine.evaluate`, apply `actions`; returns narration log lines. Action kinds: `set_flag` (`flag`, `value`), `grant_memory` (`id`), `start_quest` (`id`), `log` (`text`).
- **Map JSON schema** (`data/maps/<id>.json`) — `ascii_art` is the asset stem name (resolved by `ascii_loader` at render):

```json
{
  "id": "village",
  "name": "Ashen Village",
  "region": "1",
  "threat_level": 0,
  "description": "Desa kecil yang hangat. Orang-orang memandangmu dengan curiga.",
  "ascii_art": "village",
  "exits": ["forest"],
  "npcs": ["old_man", "village_chief"],
  "enemy_pool": []
}
```
  `forest.json`: `name "Ashen Forest"`, `region "2"`, `threat_level 2`, `exits ["village"]`, `npcs []`, `enemy_pool [{"id": "goblin", "weight": 2}, {"id": "wild_wolf", "weight": 2}, {"id": "bandit", "weight": 1}]` (pool format per `exploration_system`).
- **Event JSON** (`data/events/events.json`) — list; trigger condition kinds use `rule_engine.evaluate` (flag/map/time/level/quest_done); one-shot is achieved by flag self-guard (trigger MISSING + action set flag), NOT an engine `one_time` flag:

```json
[
  {
    "id": "event_intro_wake",
    "trigger": [{"kind": "flag", "flag": "intro_wake_done", "operator": "MISSING"}],
    "actions": [
      {"kind": "log", "text": "Kau membuka mata. Langit tampak asing."},
      {"kind": "set_flag", "flag": "intro_wake_done", "value": true}
    ]
  },
  {
    "id": "event_first_memory",
    "trigger": [{"kind": "flag", "flag": "met_old_man", "value": true}],
    "actions": [
      {"kind": "grant_memory", "id": "memory001"},
      {"kind": "set_flag", "flag": "memory001_granted", "value": true}
    ]
  }
]
```
  Note: `grant_memory` action MUST be guarded — only fire when `game_state.player is not None` (assert at call site, per wiring pin).
  **Map-trigger caveat:** `rule_engine.evaluate` kind `map` compares `game_state.current_map == target` as a STRING, but the live `Game` (`_wire`, Task 6) holds a `Map` OBJECT — a map-triggered event would never fire there. Content events (this task and Task 7) therefore use FLAG triggers only; map/time triggers are exercised in unit tests against string-valued `current_map`. Recorded divergence (frozen `rule_engine`).

- [ ] **Step 1: Write failing tests**

`tests/test_ascii_loader.py`:

```python
import pytest
from src.utils.json_loader import ContentError
from src.ui.ascii_loader import load


def test_load_returns_file_text(tmp_path):
    (tmp_path / "village.txt").write_text("#..\n...", encoding="utf-8")
    assert load("village", assets_dir=str(tmp_path)) == "#..\n..."


def test_load_missing_raises(tmp_path):
    with pytest.raises(ContentError):
        load("tidak_ada", assets_dir=str(tmp_path))
```

`tests/test_events.py`:

```python
from src.engine.event_engine import process_events
from src.core.game_state import GameState


def test_event_fires_on_flag():
    gs = GameState()
    gs.flags["trigger_me"] = True
    events = [{"id": "e1",
               "trigger": [{"kind": "flag", "flag": "trigger_me", "value": True}],
               "actions": [{"kind": "set_flag", "flag": "e1_fired", "value": True}]}]
    process_events(gs, None, events)
    assert gs.flags.get("e1_fired") is True


def test_event_does_not_fire_when_condition_missing():
    gs = GameState()
    events = [{"id": "e1",
               "trigger": [{"kind": "flag", "flag": "nope", "value": True}],
               "actions": [{"kind": "set_flag", "flag": "e1_fired", "value": True}]}]
    process_events(gs, None, events)
    assert gs.flags.get("e1_fired") is None


def test_event_log_action_returned():
    gs = GameState()
    gs.current_map = "village"
    events = [{"id": "e1",
               "trigger": [{"kind": "map", "name": "village", "operator": "EQ"}],
               "actions": [{"kind": "log", "text": "Selamat datang di desa."}]}]
    assert process_events(gs, None, events) == ["Selamat datang di desa."]


def test_event_grant_memory_skips_without_player():
    gs = GameState()
    gs.memories = [{"id": "memory001", "title": "Desa Terbakar",
                    "text": "Aku pernah membaca... desa ini akan terbakar.",
                    "flags_set": ["knows_village_burns"]}]
    events = [{"id": "e1",
               "trigger": [{"kind": "flag", "flag": "x", "value": True}],
               "actions": [{"kind": "grant_memory", "id": "memory001"}]}]
    gs.flags["x"] = True
    process_events(gs, None, events)
    assert gs.player is None
    assert "knows_village_burns" not in gs.flags
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_ascii_loader.py tests/test_events.py -v`
Expected: FAIL — `ModuleNotFoundError` for both new modules.

- [ ] **Step 3: Implement `ascii_loader.py` and `event_engine.py`**

```python
# src/ui/ascii_loader.py
import os
from src.utils.json_loader import ContentError


def load(name, assets_dir="assets/ascii"):
    path = os.path.join(assets_dir, f"{name}.txt")
    if not os.path.isfile(path):
        raise ContentError(f"Ascii art tidak ditemukan: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()
```

```python
# src/engine/event_engine.py
from src.engine import rule_engine
from src.systems import memory_system
from src.engine import quest_engine


def process_events(game_state, randomizer=None, events=None):
    if events is None:
        events = getattr(game_state, "events", [])
    log_lines = []
    for event in events:
        if not all(rule_engine.evaluate(c, game_state) for c in event["trigger"]):
            continue
        for action in event["actions"]:
            kind = action["kind"]
            if kind == "set_flag":
                game_state.flags[action["flag"]] = action.get("value", True)
            elif kind == "grant_memory":
                if game_state.player is not None:
                    memory_system.grant_memory(game_state, action["id"])
            elif kind == "start_quest":
                if game_state.player is not None:
                    log_lines.append(quest_engine.start_quest(game_state, action["id"]))
            elif kind == "log":
                log_lines.append(action["text"])
    return log_lines
```

- [ ] **Step 4: Add `events` field to `GameState`** — `self.events = []` in `__init__` (additive; existing `game_state` fixture tests unaffected).

- [ ] **Step 5: Write map JSON + ascii art + events JSON** (schemas above). `assets/ascii/village.txt` and `forest.txt`: pure ASCII `# @ | / \ _ . * =` illustrations (MASTER_CONCEPT §5.3), ≥ 3 lines each.

- [ ] **Step 6: Run full test suite**

Run: `pytest tests/ -q`
Expected: all PASS.

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "feat: map content, ascii art, event engine"
```

- [ ] **Step 8: Review gate** — dispatch code reviewer; fix any `Important` findings; commit fixes.

---

### Task 3: Save Manager

**Files:**
- Create: `src/core/save_manager.py`
- Create: `tests/test_save.py`
- Modify: `src/core/game_state.py` (add additive field `rng_seed: int | None = None`)

**Interfaces:**
- Consumes: `GameState` (player, flags, time, day, current_map, memories, quests, rng_seed), `Player` (dataclass → `dataclasses.asdict`), `game_context.create_player(name, class_id)` when context is provided.
- Produces:
  - `save_manager.save_game(game_state, path, version=1) -> str` — serializes player (via `asdict`), `flags`, `engine_state` (`current_map`, `current_time`, `day`, `random_seed`, `active_events`), `saved_at` ISO timestamp; writes JSON; returns `path`.
  - `save_manager.load_game(path, game_context=None) -> GameState` — validates `schema_version == 1` else `SaveError`; fills missing keys with defaults (never crash); player restored via `game_context.create_player` + overlay when context given, else constructed directly from saved dict; sets `game_state.rng_seed`; corrupt/missing file → `SaveError`.
  - `save_manager.default_player(game_context) -> Player` — fresh player for corrupt saves / new game.
  - `class SaveManagerError(Exception)` (alias `SaveError`).
  - Save versioning: `schema_version` = save-format version (bumps on incompatible format change); `content_version` = content/game version (bumps when data content evolves, e.g. new Arc). Both written on save, validated/backward-compatible on load (missing key → treated as v0, still loads).
- **Design Freeze B6:** combat statuses are transient (live in `CombatState`, never in `Player`) — NO status serialization.
- **Save JSON shape** (design spec §Save System):

```json
{
  "schema_version": 1,
  "content_version": 1,
  "player": {},
  "flags": {},
  "engine_state": {
    "current_map": "village",
    "current_time": "morning",
    "day": 1,
    "random_seed": 12345,
    "active_events": []
  },
  "saved_at": "ISO timestamp"
}
```

- [ ] **Step 1: Write failing tests** (`tests/test_save.py`)

```python
import json
import pytest
from src.core.game_state import GameState
from src.core.save_manager import save_game, load_game, default_player, SaveError
from src.models.player import Player


def test_save_roundtrip(tmp_path):
    gs = GameState()
    gs.day = 3
    gs.flags["x"] = True
    p = tmp_path / "s.json"
    save_game(gs, str(p))
    gs2 = load_game(str(p), None)
    assert gs2.day == 3
    assert gs2.flags.get("x") is True


def test_save_player_roundtrip(tmp_path):
    gs = GameState()
    gs.player = Player(name="Rian", class_id="warrior", hp=80, mp=10,
                       base_stats={"hp": 100, "mp": 10}, level=2, gold=50,
                       inventory=[{"id": "potion", "qty": 3}],
                       reputation={"merchant_guild": 10})
    p = tmp_path / "s.json"
    save_game(gs, str(p))
    gs2 = load_game(str(p), None)
    assert gs2.player.name == "Rian"
    assert gs2.player.level == 2
    assert gs2.player.inventory == [{"id": "potion", "qty": 3}]
    assert gs2.player.reputation["merchant_guild"] == 10


def test_save_restores_rng_seed(tmp_path):
    gs = GameState()
    gs.rng_seed = 12345
    p = tmp_path / "s.json"
    save_game(gs, str(p))
    gs2 = load_game(str(p), None)
    assert gs2.rng_seed == 12345


def test_load_missing_keys_use_defaults(tmp_path):
    p = tmp_path / "s.json"
    p.write_text(json.dumps({"version": 1}), encoding="utf-8")
    gs = load_game(str(p), None)
    assert gs.day == 1
    assert gs.time == "morning"
    assert gs.flags == {}
    assert gs.player is None


def test_load_wrong_version_raises(tmp_path):
    p = tmp_path / "s.json"
    p.write_text(json.dumps({"version": 99}), encoding="utf-8")
    with pytest.raises(SaveError):
        load_game(str(p), None)


def test_load_corrupt_file_raises(tmp_path):
    p = tmp_path / "s.json"
    p.write_text("{not json", encoding="utf-8")
    with pytest.raises(SaveError):
        load_game(str(p), None)


def test_load_missing_file_raises(tmp_path):
    with pytest.raises(SaveError):
        load_game(str(tmp_path / "nope.json"), None)


def test_default_player(tmp_path):
    from src.core.game_context import GameContext
    from src.core.constants import FACTIONS
    ctx = GameContext(data_dir="data")
    p = default_player(ctx)
    assert p.name == "Pejalan Waktu"
    assert p.class_id == "warrior"
    assert set(p.reputation) == set(FACTIONS)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_save.py -v`
Expected: FAIL — `ModuleNotFoundError: src.core.save_manager`.

- [ ] **Step 3: Implement `save_manager.py`**

```python
import dataclasses
import datetime
import json
import os

from src.core.game_state import GameState
from src.models.player import Player

SCHEMA_VERSION = 1
CONTENT_VERSION = 1

class SaveError(Exception):
    pass


def default_player(game_context=None):
    if game_context is not None:
        return game_context.create_player("Pejalan Waktu", "warrior")
    return Player(name="Pejalan Waktu", class_id="warrior", hp=0, mp=0, base_stats={})


def _engine_state(game_state):
    current_map = game_state.current_map
    return {
        "current_map": current_map.id if hasattr(current_map, "id") else current_map,
        "current_time": game_state.time,
        "day": game_state.day,
        "random_seed": game_state.rng_seed,
        "active_events": [],
    }


def save_game(game_state, path, schema_version=SCHEMA_VERSION):
    data = {
        "schema_version": schema_version,
        "content_version": CONTENT_VERSION,
        "player": dataclasses.asdict(game_state.player) if game_state.player else None,
        "flags": game_state.flags,
        "engine_state": _engine_state(game_state),
        "saved_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return path


def load_game(path, game_context=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        raise SaveError(f"Save tidak dapat dimuat: {path}") from e
    schema_version = data.get("schema_version", data.get("version", 0))
    if schema_version > SCHEMA_VERSION:
        raise SaveError(f"Versi save tidak didukung: {schema_version}")
    gs = GameState()
    player_data = data.get("player") or {}
    if player_data:
        gs.player = _restore_player(player_data, game_context)
    gs.flags = data.get("flags", {})
    engine = data.get("engine_state", {})
    gs.current_map = engine.get("current_map")
    gs.time = engine.get("current_time", "morning")
    gs.day = engine.get("day", 1)
    gs.rng_seed = engine.get("random_seed")
    return gs


def _restore_player(player_data, game_context):
    if game_context is not None and player_data.get("class_id") in game_context.classes:
        p = game_context.create_player(
            player_data.get("name", "Pejalan Waktu"),
            player_data["class_id"],
        )
        overlay = dict(player_data)
        for key in ("base_stats", "attribute_bonuses", "equipped", "reputation",
                    "relationship", "flags", "quests_active"):
            overlay[key] = player_data.get(key, getattr(p, key))
        overlay["inventory"] = player_data.get("inventory", [])
        overlay["quests_done"] = player_data.get("quests_done", [])
        overlay["memories"] = player_data.get("memories", [])
        overlay["learned_skills"] = player_data.get("learned_skills", [])
        for field_name in ("hp", "mp", "level", "xp", "gold", "skill_points"):
            setattr(p, field_name, player_data.get(field_name, getattr(p, field_name)))
        for key, value in overlay.items():
            if hasattr(p, key):
                setattr(p, key, value)
        return p
    defaults = dict(
        name="Pejalan Waktu", class_id="warrior", hp=0, mp=0, base_stats={},
        attribute_bonuses={}, level=1, xp=0, gold=0, skill_points=0,
        equipped={}, inventory=[], reputation={}, relationship={}, flags={},
        quests_active={}, quests_done=[], memories=[], learned_skills=[],
    )
    defaults.update(player_data)
    return Player(**defaults)
```

- [ ] **Step 4: Add `rng_seed` field to `GameState`** — `self.rng_seed = None` in `__init__` (additive).

- [ ] **Step 5: Run full test suite**

Run: `pytest tests/ -q`
Expected: all PASS. Note: `test_save_player_roundtrip` requires `current_map` handling — save writes `None` when current_map is a Map object; keep `_engine_state` guard (only store strings).

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat: JSON save/load with defaults and seed persistence"
```

- [ ] **Step 7: Review gate** — dispatch code reviewer; fix any `Important` findings; commit fixes.

---

### Task 4: UI Renderer — palette, safe_box, HUD, bars

**Files:**
- Create: `src/ui/renderer.py`, `src/ui/hud.py`, `src/ui/animation.py`
- Create: `tests/test_renderer.py`
- Modify: `assets/ui/colors.json`, `assets/ui/borders.json` (populate from `{}`)

**Interfaces:**
- Produces:
  - `renderer.ANSI = {"white":"\033[37m","cyan":"\033[36m","green":"\033[32m","red":"\033[31m","yellow":"\033[33m","magenta":"\033[35m","blue":"\033[34m","gray":"\033[90m","reset":"\033[0m"}`
  - `renderer.supports_unicode() -> bool` — True unless `TERM` unset or `"dumb"` (plus `NO_COLOR`/legacy-windows heuristic per safe_box).
  - `renderer.box(text, border_style="normal") -> str` — wraps multi-line text in a border; Unicode `┌─┐│└┘` when supported else ASCII `+-+|`.
  - `renderer.bar(current, total, width=14) -> str` — `"█"*filled + "░"*(width-filled)`, filled = `round(current/total*width)`; total ≤ 0 → all empty.
  - `hud.render(player, game_state) -> str` — one block: `name` / class / Lv / HP / MP / Gold / location / time + HP/MP bars (design spec §UI). Location `"—"` when `current_map` is None.
  - `animation.progress(label, frames=10) -> list[str]` — pure: returns progressive bar frame strings (no sleep). `animation.animate(frames, delay=0.05, sleep=time.sleep)` — prints frames (launcher-only; tests never call `animate`).
- `assets/ui/colors.json` — semantic palette (MASTER_CONCEPT §5.2): `white, cyan, green, red, yellow, magenta, blue, gray` (+ `reset`). `assets/ui/borders.json` — `normal` / `double` / `ascii` border char sets.

- [ ] **Step 1: Write failing tests** (`tests/test_renderer.py`)

```python
from src.models.player import Player
from src.models.map import Map
from src.core.game_state import GameState
from src.ui.renderer import bar, box, ANSI
from src.ui import hud
from src.ui import animation


def test_bar_fraction():
    assert bar(50, 100, width=4) == "██░░"


def test_bar_full_and_empty():
    assert bar(100, 100, width=4) == "████"
    assert bar(0, 100, width=4) == "░░░░"


def test_bar_zero_total():
    assert bar(5, 0, width=4) == "░░░░"


def test_box_ascii_fallback(monkeypatch):
    from src.ui import renderer
    monkeypatch.setattr(renderer, "supports_unicode", lambda: False)
    out = box("hai")
    assert out.splitlines()[0] == "+-----+"
    assert "| hai |" in out


def test_box_contains_lines():
    out = box("baris satu\nbaris dua")
    assert "baris satu" in out and "baris dua" in out


def test_hud_shows_core_info():
    p = Player(name="Rian", class_id="warrior", hp=80, mp=5, gold=30,
               base_stats={"hp": 100, "mp": 10})
    gs = GameState()
    gs.player = p
    gs.current_map = Map(id="village", name="Ashen Village", region="1",
                         threat_level=0, description="", ascii_art="",
                         exits=[], npcs=[], enemy_pool=[])
    out = hud.render(p, gs)
    assert "Rian" in out
    assert "Warrior" in out
    assert "Ashen Village" in out
    assert "morning" in out


def test_hud_no_map_shows_dash():
    p = Player(name="Rian", class_id="warrior", hp=80, mp=5,
               base_stats={"hp": 100, "mp": 10})
    gs = GameState()
    gs.player = p
    assert "—" in hud.render(p, gs)


def test_progress_returns_frames():
    frames = animation.progress("Menyimpan", frames=3)
    assert frames == ["Menyimpan █░░", "Menyimpan ██░", "Menyimpan ███"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_renderer.py -v`
Expected: FAIL — `ModuleNotFoundError: src.ui.renderer`.

- [ ] **Step 3: Implement `renderer.py`, `hud.py`, `animation.py`**

```python
# src/ui/renderer.py
import os

ANSI = {
    "white": "\033[37m", "cyan": "\033[36m", "green": "\033[32m",
    "red": "\033[31m", "yellow": "\033[33m", "magenta": "\033[35m",
    "blue": "\033[34m", "gray": "\033[90m", "reset": "\033[0m",
}

_UNICODE_BORDER = {
    "normal": ("┌", "─", "┐", "│", "└", "┘"),
    "double": ("╔", "═", "╗", "║", "╚", "╝"),
}
_ASCII_BORDER = ("+", "-", "+", "|", "+", "+")


def supports_unicode():
    term = os.environ.get("TERM", "")
    if not term or term == "dumb":
        return False
    return os.name != "nt"


def _border(border_style):
    if supports_unicode():
        return _UNICODE_BORDER.get(border_style, _UNICODE_BORDER["normal"])
    return _ASCII_BORDER


def box(text, border_style="normal"):
    tl, h, tr, v, bl, br = _border(border_style)
    lines = text.split("\n")
    width = max((len(line) for line in lines), default=0)
    out = [f"{tl}{h * (width + 2)}{tr}"]
    for line in lines:
        out.append(f"{v} {line}{' ' * (width - len(line))} {v}")
    out.append(f"{bl}{h * (width + 2)}{br}")
    return "\n".join(out)


def bar(current, total, width=14):
    if total <= 0:
        return "░" * width
    filled = round(current / total * width)
    return "█" * filled + "░" * (width - filled)
```

```python
# src/ui/hud.py
from src.models.player import max_hp, max_mp
from src.ui.renderer import ANSI, bar


def render(player, game_state):
    location = game_state.current_map.name if game_state.current_map else "—"
    hp_bar = bar(player.hp, max_hp(player))
    mp_bar = bar(player.mp, max_mp(player))
    lines = [
        f"{player.name} — {player.class_id.title()} (Lv {player.level})",
        f"HP {player.hp}/{max_hp(player)} {hp_bar}",
        f"MP {player.mp}/{max_mp(player)} {mp_bar}",
        f"Emas: {player.gold}   XP: {player.xp}",
        f"Lokasi: {location}   Waktu: {game_state.time}",
    ]
    return "\n".join(lines)
```

```python
# src/ui/animation.py
import time


def progress(label, frames=10):
    return [f"{label} {'█' * i}{'░' * (frames - i)}" for i in range(1, frames + 1)]


def animate(frames, delay=0.05, sleep=time.sleep):
    for frame in frames:
        print(f"\r{frame}", end="", flush=True)
        sleep(delay)
    print()
```

- [ ] **Step 4: Populate `assets/ui/colors.json` and `borders.json`**

`colors.json`:
```json
{
  "white": "\u001b[37m",
  "cyan": "\u001b[36m",
  "green": "\u001b[32m",
  "red": "\u001b[31m",
  "yellow": "\u001b[33m",
  "magenta": "\u001b[35m",
  "blue": "\u001b[34m",
  "gray": "\u001b[90m",
  "reset": "\u001b[0m"
}
```
`borders.json`:
```json
{
  "normal": {"tl": "\u250c", "h": "\u2500", "tr": "\u2510", "v": "\u2502", "bl": "\u2514", "br": "\u2518"},
  "double": {"tl": "\u2554", "h": "\u2550", "tr": "\u2557", "v": "\u2551", "bl": "\u255a", "br": "\u255d"}
}
```

- [ ] **Step 5: Run full test suite**

Run: `pytest tests/ -q`
Expected: all PASS. (Note: `test_hud_no_map_shows_dash` uses `—` em dash in the header line; keep `location = "—"`.)

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat: UI renderer, HUD, bars, safe_box ASCII fallback"
```

- [ ] **Step 7: Review gate** — dispatch code reviewer; fix any `Important` findings; commit fixes.

---

### Task 5: UI Views — menu, combat, inventory, dialog + input handler

**Files:**
- Create: `src/core/input_handler.py`
- Create: `src/models/command.py`
- Create: `src/ui/menu.py`, `src/ui/combat_view.py`, `src/ui/inventory_view.py`, `src/ui/dialog_view.py`
- Create: `tests/test_views.py`

**Interfaces:**
- Produces:
  - `models/command.Command` — `@dataclass` with `action: str`, `args: list[str] = field(default_factory=list)`, `index: int | None = None`.
  - `input_handler.parse_input(text) -> Command` — strips, lowercases; if first token is a number → `Command(action="select", index=int(token), args=rest)`; else `Command(action=first_token, args=rest_tokens)`.
  - `menu.render_main(selection=0) -> str` — items `["New Game", "Continue", "Settings", "Credits", "Exit"]`, `"> "` prefix on the selected item.
  - `menu.arrow(idx, total) -> int` — next/prev with wrap (`(idx+1)%total`, `(idx-1)%total`).
  - `menu.render_class_card(class_data) -> str` — class name + ASCII stat bars from `class_data["stat_bars"]` (value × 2 blocks of 10; MASTER_CONCEPT §3.2.1).
  - `combat_view.render(state) -> str` — enemy block (name, HP bar, observe info), player block, 7 action list (from `CombatAction`), last 5 log lines. Uses `renderer.bar` and `rule_engine` NOT needed — reads `state.player`, `state.enemy`, `state.log`.
  - `inventory_view.render(player, items=None) -> str` — equipment (slot → name via `items` registry), consumables/materials (inventory entries with name/desc via `items` registry, fallback `entry["id"]`).
  - `dialog_view.render(dialog, game_state) -> str` — speaker + boxed lines + numbered choices (from `dialog_engine.available_choices`).

- [ ] **Step 1: Write failing tests** (`tests/test_views.py`)

```python
from src.core.game_state import GameState
from src.core.input_handler import parse_input
from src.models.command import Command
from src.models.player import Player
from src.models.enemy import Enemy
from src.models.item import Item
from src.ui import menu, combat_view, inventory_view, dialog_view
from src.engine.combat_engine import start_combat
from src.core.randomizer import Randomizer


def test_parse_number_to_command():
    c = parse_input("1")
    assert c.action == "select"
    assert c.index == 1


def test_parse_action_trimmed():
    c = parse_input("  attack  ")
    assert c.action == "attack"
    assert c.index is None


def test_parse_action_with_args():
    c = parse_input("go forest")
    assert c.action == "go"
    assert c.args == ["forest"]


def test_command_defaults():
    c = Command(action="rest")
    assert c.args == []
    assert c.index is None


def test_menu_main_highlight():
    out = menu.render_main(0)
    assert "> New Game" in out
    assert "\n  Continue" in out


def test_menu_arrow_wrap():
    assert menu.arrow(0, 5) == 1
    assert menu.arrow(4, 5) == 0


def test_class_card_bars():
    card = menu.render_class_card({"id": "warrior", "name": "Warrior",
                                   "stat_bars": {"attack": 4, "defense": 5}})
    assert "Warrior" in card
    assert "Attack" in card
    assert "█" in card


def test_combat_view_contains_actions():
    p = Player(name="Rian", class_id="warrior", hp=100, mp=10,
               base_stats={"hp": 100, "mp": 10, "attack": 12, "defense": 14,
                           "agility": 8, "intelligence": 7})
    e = Enemy(id="goblin", name="Goblin", level=2,
              stats={"attack": 5, "defense": 2, "hp": 5, "mp": 0,
                     "agility": 6, "intelligence": 3},
              loot=[], skills=[])
    state = start_combat(p, e, Randomizer(seed=1))
    out = combat_view.render(state)
    assert "Goblin" in out
    assert "Attack" in out
    assert "Escape" in out


def test_inventory_view_shows_equipment():
    p = Player(name="Rian", class_id="warrior", hp=100, mp=10, base_stats={},
               equipped={"weapon": "iron_sword"},
               inventory=[{"id": "herb", "qty": 2}])
    items = {
        "iron_sword": Item(id="iron_sword", name="Iron Sword", type="weapon",
                           slot="weapon", modifiers={"attack": 8}),
        "herb": Item(id="herb", name="Herb", type="consumable", heal=20),
    }
    out = inventory_view.render(p, items)
    assert "Iron Sword" in out
    assert "weapon" in out
    assert "Herb" in out


def test_dialog_view_numbers_choices():
    gs = GameState()
    dialog = {"id": "d", "lines": [{"speaker": "old_man", "text": "Halo."}],
              "choices": [{"text": "Siapa Anda?", "require_flags": [], "set_flags": [], "next": None}]}
    out = dialog_view.render(dialog, gs)
    assert "old_man" in out
    assert "1. Siapa Anda?" in out
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_views.py -v`
Expected: FAIL — `ModuleNotFoundError` for `input_handler`, `command`, and the four view modules.

- [ ] **Step 3: Implement `Command`, `input_handler`, and the four views**

```python
# src/models/command.py
from dataclasses import dataclass, field

@dataclass
class Command:
    action: str
    args: list = field(default_factory=list)
    index: int | None = None
```

```python
# src/core/input_handler.py
from src.models.command import Command


def parse_input(text):
    tokens = text.strip().lower().split()
    if not tokens:
        return Command(action="")
    first = tokens[0]
    rest = tokens[1:]
    if first.isdigit():
        return Command(action="select", args=rest, index=int(first))
    return Command(action=first, args=rest)
```

```python
# src/ui/menu.py
from src.ui.renderer import ANSI, bar

MAIN_ITEMS = ["New Game", "Continue", "Settings", "Credits", "Exit"]


def render_main(selection=0):
    lines = ["CHRONICLE OF THE PAST", "=" * 26, ""]
    for idx, item in enumerate(MAIN_ITEMS):
        marker = "> " if idx == selection else "  "
        lines.append(marker + item)
    return "\n".join(lines)


def arrow(idx, total):
    if total <= 0:
        return 0
    return (idx + 1) % total if total > 1 else idx


def render_class_card(class_data):
    lines = [f"{class_data['name']}"]
    for stat, value in class_data.get("stat_bars", {}).items():
        lines.append(f"{stat.title():<14}{bar(value * 2, 10, width=10)}")
    return "\n".join(lines)
```

```python
# src/ui/combat_view.py
from src.engine.combat_interfaces import CombatAction
from src.ui.renderer import ANSI, bar


def render(state):
    lines = []
    enemy = state.enemy
    max_hp = enemy.stats.get("max_hp", enemy.stats.get("hp", 1))
    lines.append(f"{enemy.name} — Lv {enemy.level}")
    lines.append(f"HP {enemy.stats['hp']}/{max_hp} {bar(enemy.stats['hp'], max_hp, width=10)}")
    if state.observe_info:
        lines.append(state.observe_info)
    lines.append("")
    p = state.player
    lines.append(f"{p.name} — HP {p.hp}  MP {p.mp}")
    lines.append("")
    lines.append("Aksi:")
    for action in CombatAction:
        lines.append(f"  {action.value.title()}")
    lines.append("")
    lines.extend(state.log[-5:])
    return "\n".join(lines)
```

```python
# src/ui/inventory_view.py
def render(player, items=None):
    items = items or {}
    lines = ["Perlengkapan:"]
    for slot, item_id in player.equipped.items():
        name = items[item_id].name if item_id in items else item_id
        lines.append(f"  {slot}: {name}")
    lines.append("Inventaris:")
    for entry in player.inventory:
        item = items.get(entry["id"])
        name = item.name if item else entry["id"]
        lines.append(f"  {name} x{entry['qty']}")
    return "\n".join(lines)
```

```python
# src/ui/dialog_view.py
from src.ui.renderer import box
from src.engine.dialog_engine import available_choices


def render(dialog, game_state):
    lines = []
    for line in dialog["lines"]:
        lines.append(f"{line['speaker']}:")
        lines.append(box(line["text"]))
    lines.append("Pilihan:")
    for idx, choice in enumerate(available_choices(dialog, game_state), start=1):
        lines.append(f"  {idx}. {choice['text']}")
    return "\n".join(lines)
```

- [ ] **Step 4: Run full test suite**

Run: `pytest tests/ -q`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: UI views (menu/combat/inventory/dialog) + command parser"
```

- [ ] **Step 6: Review gate** — dispatch code reviewer; fix any `Important` findings; commit fixes.

---

### Task 6: Game orchestration + launcher

**Files:**
- Create: `src/core/game.py`
- Modify: `launcher.py`
- Create: `tests/test_game_flow.py`

**Interfaces:**
- Consumes: everything — `GameContext` (classes/enemies/items/skills/maps/npc/dialogues/factions/events/memories), `combat_engine.start_combat/player_action/enemy_turn`, `rule_engine.derived_stats`, `quest_engine.start_quest/complete_requirement`, `memory_system.grant_memory/has_memory`, `exploration_system.check_encounter`, `travel_system.travel/can_travel`, `time_engine.rest`, `inventory_system.{add_item,use_consumable,count_items}`, `equipment_system.{equip,unequip,total_stats}`, `level_system.{gain_xp,on_level_up,apply_choice}`, `loot_system.roll_loot`, `save_manager.{save_game,load_game,SaveError}`, `dialog_engine`, `event_engine.process_events`, `ascii_loader`, all UI views.
- Produces:
  - `game.Game(game_context, rng_seed=None)` — owns `GameState` + `Randomizer(rng_seed)`; sets `game_state.rng_seed`.
  - `game.Game.new_game(name, class_id) -> str` — `create_player`, wire `world` (Map objects), `enemies` (Enemy objects), `items` (Item objects), `quests`, `memories`, `events`; set `current_map` to `"village"` Map; `rng_seed` fixed; run initial `process_events`; return intro text.
  - `game.Game.continue_game(save_path) -> str` — `save_manager.load_game(path, game_context)`; re-wire registries (world/enemies/items/quests/memories/events) from context (saves store only state); recreate `Randomizer(game_state.rng_seed)`. NOTE: `_engine_state` stores `current_map` as the Map's **id string** — after re-wiring, set `s.current_map = s.world[s.current_map]` (falls back to village if id unknown).
  - `game.Game.run_turn(text) -> str` — parse via `input_handler.parse_input`, dispatch, return rendered text (HUD + result). Commands: `status`, `help`, `go <map>`, `rest`, `talk <npc>`, `look`, `explore`, `inventory`, `use <item>`, `equip <item>`, `unequip <slot>`, `save <path>`, `quests`, plus combat actions (`attack`, `skill <id>`, `magic <id>`, `item <id>`, `observe`, `escape`, `defend`). Unknown command → help hint.
  - `launcher.py` — main menu loop: render_main, arrow navigation, name input, class selection (class cards), new/continue; catches `SaveError`, `ContentError`, `KeyboardInterrupt` (clean exit).

- **Wiring pins (MANDATORY):**
  - `equip(player, item, items=game_state.items)` / `unequip(player, slot, items=game_state.items)` — ALWAYS pass registry (ledger Task 9 Important).
  - Before any `grant_memory` call: `assert game_state.player is not None`.
  - Combat victory → `quest_engine.complete_requirement(game_state, "enemy", state.enemy.id)` after loot/xp (for quest002 "kalahkan wild_wolf"); defeat of enemy sets `game_state.flags[f"defeated_{state.enemy.id}"] = True` before complete_requirement.
  - After talk completes a dialog, call `complete_requirement(game_state, "talk", npc_id)` (for quest001).
  - After each turn, run `event_engine.process_events(game_state, randomizer)` and append returned logs.

- [ ] **Step 1: Write failing tests** (`tests/test_game_flow.py`)

```python
from src.core.game_context import GameContext
from src.core.game import Game


def test_new_game_and_status(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    out = g.run_turn("status")
    assert "Rian" in out
    assert "Ashen Village" in out


def test_travel_to_forest(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    out = g.run_turn("go forest")
    assert "Forest" in out
    assert g.state.current_map.id == "forest"


def test_travel_invalid_destination(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    out = g.run_turn("go capital")
    assert "Tidak ada jalan" in out


def test_save_and_continue(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    path = str(tmp_path / "s.json")
    g.run_turn(f"save {path}")
    g2 = Game(ctx)
    g2.continue_game(path)
    assert g2.state.player.name == "Rian"
    assert g2.state.day == g.state.day


def test_talk_npc_sets_dialog_flag(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    out = g.run_turn("talk old_man")
    assert "Old Man" in out
    g.run_turn("1")  # pick "Siapa Anda?" -> next dialog_old_man_1
    assert g.state.flags.get("met_old_man") is True


def test_rest_heals(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    g.state.player.hp = 10
    out = g.run_turn("rest")
    assert "morning" in out
    assert g.state.player.hp >= 50
```

  NOTE: `run_turn` must thread a current dialog state (`game_state`-side, e.g. `Game._current_dialog`) so `"1"` selects a choice of the active dialog. Dialog display is 1-based (`dialog_view` numbers `1..N`) but `dialog_engine.choose(game_state, dialog, choice_index)` is 0-based — when `Command.action == "select"`, pass `Command.index - 1` to `choose`. `test_travel_invalid_destination` uses map id `"capital"` which is NOT in village exits. The `talk <npc>` handler renders a header `f"{npc['name']}:"` (from `ctx.npc`) above the `dialog_view` output — so `test_talk_npc_sets_dialog_flag`'s `"Old Man" in out` matches the NPC display name. Also, on entering a map run `process_events` once (intro/wake narration), and after `talk` completes render the dialog lines so `"Old Man"` appears.

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_game_flow.py -v`
Expected: FAIL — `ModuleNotFoundError: src.core.game`.

- [ ] **Step 3: Implement `game.py`**

Key skeleton (full orchestration in the implementer's task; all logic content-free — ids/names come from registries):

```python
from src.core.game_state import GameState
from src.core.randomizer import Randomizer
from src.core import input_handler
from src.core import save_manager
from src.models.enemy import Enemy
from src.models.item import Item
from src.models.map import Map
from src.engine import event_engine, quest_engine
from src.engine.combat_interfaces import CombatAction, CombatResult
from src.engine.combat_engine import start_combat, player_action, enemy_turn
from src.systems import (equipment_system, exploration_system, inventory_system,
                         level_system, loot_system, memory_system, travel_system)
from src.engine.time_engine import rest
from src.ui import ascii_loader, hud


class Game:
    def __init__(self, game_context, rng_seed=None):
        self.ctx = game_context
        self.state = GameState()
        self.state.rng_seed = rng_seed if rng_seed is not None else 20260803
        self.randomizer = Randomizer(self.state.rng_seed)
        self._current_dialog = None
        self._combat = None

    def _wire(self):
        s = self.state
        s.world = {mid: Map(**data) for mid, data in self.ctx.maps.items()}
        s.enemies = {eid: Enemy(**data) for eid, data in self.ctx.enemies.items()}
        s.items = {iid: Item(**data) for iid, data in self.ctx.items.items()}
        s.quests = dict(self.ctx.quests)
        s.memories = list(self.ctx.memories)
        s.events = list(self.ctx.events)
        if s.current_map is None:
            s.current_map = s.world["village"]

    def new_game(self, name, class_id):
        self._wire()
        self.state.player = self.ctx.create_player(name, class_id)
        lines = event_engine.process_events(self.state, self.randomizer)
        return "\n".join(lines) or "Kamu terbangun di Ashen Village."
```

  `run_turn(text)`: parse → if `self._combat` active and action is a combat action → `player_action(self._combat, action, choice=...)`; then `enemy_turn` if not over; on over → apply rewards via `_finish_combat`. Non-combat dispatch per command list above. `_finish_combat` implements the wiring pins (rewards already applied by `_on_victory`; then `complete_requirement`, flags, `level_system.gain_xp` → `on_level_up` pick, `process_events`).

  Combat commands (`attack/skill/magic/item/observe/escape/defend`) only valid while `self._combat` is not None. `explore` → `exploration_system.check_encounter(self.state, self.randomizer)`; if enemy found → `start_combat(player, enemy, self.randomizer, skills=self.ctx.skills, loot_resolver=loot_system.roll_loot, items=self.state.items)` and `self._combat = ...`, return combat view.

- [ ] **Step 4: Implement `launcher.py`**

Main menu loop with `menu.render_main`/`menu.arrow`; name input; class selection via `render_class_card` over `ctx.classes`; `Game.new_game`/`Game.continue_game`; wraps every command in try/except `(save_manager.SaveError, ContentError, KeyboardInterrupt)` → friendly Indonesian message + clean exit. `animate(progress("Menghubungkan..."))` boot sequence.

- [ ] **Step 5: Run full test suite**

Run: `pytest tests/ -q`
Expected: all PASS (280 baseline + new flow tests). Then manual smoke: `python launcher.py` plays through: new game → status → talk old_man → go forest → explore → save.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat: game orchestration + launcher, MVP vertical slice playable"
```

- [ ] **Step 7: Review gate** — dispatch code reviewer; fix any `Important` findings; commit fixes.

---

### Task 7: Full Arc 1 content + regression

**Files:**
- Create: `data/story/arc1_text.json` (narration strings, Bahasa Indonesia)
- Create: `data/story/arcs.json` (story graph — Claude T2)
- Create: `data/skills/slash.json`, `backstab.json`, `fireball.json`, `quick_shot.json`, `inspect.json` (+ `bite.json` for enemies)
- Modify: `data/enemies/goblin.json`, `wild_wolf.json` (add `skills: ["bite"]`), `bandit.json` (add `skills: ["backstab"]`)
- Modify: `data/npc/*`, `data/dialogues/*`, `data/quests/*`, `data/events/*`, `assets/ascii/*`
- Fix: `data/quests/quest001.json` + `quest002.json` — `"reputation": {"village": ...}` → `"merchant_guild"`; quest002 requirement `{"kind": "flag", "target": "wolves_defeated"}` → `{"kind": "enemy", "target": "wild_wolf"}`
- Create: `tests/test_arc1_content.py`

**Interfaces:**
- Consumes: all Task 1–6 content loaders; `GameContext` loads `skills` via `_load_dir("skills")`, `story/memories.json` via `_load_file_list`.
- Produces: playable Arc 1 (design spec §MVP story beat sheet) — boot intro, name/class, wake scene (`event_intro_wake`), mentor (old_man dialog), quest001 (talk village_chief), side quest002 (defeat wild_wolf), memory001 from old_man (via `event_first_memory` on `met_old_man`), forest encounters, quest completions, Timeline Divergence hint at end.
- **Skill JSON schema** (matches `Skill` model + `combat_engine` expectations: `cost`, `type` `"magic"`|`"physical"`, `power`, `effects` list of `{"status","power","duration"}`):

```json
{
  "id": "slash",
  "name": "Slash",
  "type": "physical",
  "cost": 0,
  "target": "single_enemy",
  "power": 0,
  "effects": [],
  "requires": {},
  "description": "Serangan pedang dasar."
}
```
  `backstab` (assassin, physical, cost 0, power 0), `fireball` (mage, magic, cost 8, power 12), `quick_shot` (ranger, physical, cost 0, power 0), `inspect` (scholar, physical, cost 0, power 0, effects `[{"status": "observe", ...}]` — or simply power 0), `bite` (enemy, physical, cost 0, power 0).
- **arcs.json** (story graph):

```json
[
  {"id": "arc_01_the_stranger", "title": "Arc 1 — The Stranger",
   "region": "village", "beats": ["boot", "wake", "meet_old_man", "quest001", "quest002", "forest", "divergence_hint"]}
]
```
- **arc1_text.json** — narration strings dict: `boot_sequence`, `wake`, `village_enter`, `forest_enter`, `divergence_alert`, `quest001_start`, `quest001_done`, `quest002_done`, `memory001_obtained`, `ending_hint`. All Bahasa Indonesia.

- [ ] **Step 1: Write failing content test** (`tests/test_arc1_content.py`) — validates every content JSON and every cross-reference; MUST fail before the quest `"village"` fix and missing skills:

```python
import json
import os
from src.core.game_context import GameContext
from src.core.constants import FACTIONS


def _load_all_jsons(root):
    results = []
    for dirpath, _dirs, files in os.walk(root):
        for name in files:
            if name.endswith(".json"):
                results.append(os.path.join(dirpath, name))
    return results


def test_class_starting_skills_exist():
    ctx = GameContext(data_dir="data")
    for cid, cls in ctx.classes.items():
        for s in cls.get("starting_skills", []):
            assert s in ctx.skills, f"{cid} missing skill {s}"


def test_map_exits_resolve():
    ctx = GameContext(data_dir="data")
    for mid, m in ctx.maps.items():
        for e in m.get("exits", []):
            assert e in ctx.maps, f"{mid} bad exit {e}"


def test_map_npc_and_enemy_pool_resolve():
    ctx = GameContext(data_dir="data")
    for mid, m in ctx.maps.items():
        for n in m.get("npcs", []):
            assert n in ctx.npc, f"{mid} bad npc {n}"
        for entry in m.get("enemy_pool", []):
            eid = entry if isinstance(entry, str) else entry.get("id")
            assert eid in ctx.enemies, f"{mid} bad enemy {eid}"


def test_npc_dialogs_resolve():
    ctx = GameContext(data_dir="data")
    for nid, npc in ctx.npc.items():
        for d in npc.get("dialogs", []):
            assert d in ctx.dialogues, f"{nid} bad dialog {d}"


def test_dialog_next_and_flags_resolve():
    ctx = GameContext(data_dir="data")
    for did, dlg in ctx.dialogues.items():
        for choice in dlg.get("choices", []):
            nxt = choice.get("next")
            if nxt is not None:
                assert nxt in ctx.dialogues, f"{did} bad next {nxt}"


def test_quest_reputation_uses_valid_factions():
    ctx = GameContext(data_dir="data")
    for qid, quest in ctx.quests.items():
        for faction in quest.get("rewards", {}).get("reputation", {}):
            assert faction in FACTIONS, f"{qid} bad reputation faction {faction}"


def test_quest_requirement_kinds():
    ctx = GameContext(data_dir="data")
    valid_kinds = {"talk", "map", "flag", "enemy"}
    for qid, quest in ctx.quests.items():
        for req in quest.get("requirements", []):
            assert req.get("kind") in valid_kinds, f"{qid} bad requirement kind {req.get('kind')}"


def test_enemy_skills_exist():
    ctx = GameContext(data_dir="data")
    for eid, enemy in ctx.enemies.items():
        for s in enemy.get("skills", []):
            assert s in ctx.skills, f"{eid} missing skill {s}"


def test_enemy_loot_items_exist():
    ctx = GameContext(data_dir="data")
    for eid, enemy in ctx.enemies.items():
        for entry in enemy.get("loot", []):
            assert entry.get("item") in ctx.items, f"{eid} bad loot {entry.get('item')}"


def test_event_actions_resolve():
    ctx = GameContext(data_dir="data")
    memory_ids = {m["id"] for m in ctx.memories}
    for ev in ctx.events:
        for action in ev.get("actions", []):
            if action.get("kind") == "grant_memory":
                assert action["id"] in memory_ids, f"{ev['id']} bad memory {action['id']}"
            if action.get("kind") == "start_quest":
                assert action["id"] in ctx.quests, f"{ev['id']} bad quest {action['id']}"


def test_ascii_art_files_exist():
    for map_id, _ in GameContext(data_dir="data").maps.items():
        path = os.path.join("assets", "ascii", f"{map_id}.txt")
        assert os.path.isfile(path), f"missing ascii art {path}"


def test_all_json_files_parse():
    for path in _load_all_jsons("data"):
        with open(path, encoding="utf-8") as f:
            json.load(f)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_arc1_content.py -v`
Expected: FAIL — `ctx.skills == {}` (no skills dir), quest reputation `"village"` not in FACTIONS, missing maps/npc/dialogues/events content.

- [ ] **Step 3: Write all Arc 1 content** (schemas above, Indonesian text per design spec story beat sheet + MASTER_CONCEPT Arc 1 "The Stranger" / Stranger Without History):
  - `data/skills/*.json` (5 class skills + `bite`).
  - `data/quests/quest001.json` / `quest002.json` — fix `"village"` → `"merchant_guild"`; quest002 requirement `{"kind": "enemy", "target": "wild_wolf"}`.
  - `data/events/events.json` — extend Task 2 events to cover: wake scene, first memory, quest002 completion hint (`defeated_wild_wolf` flag), Timeline Divergence alert at Arc 1 end.
  - `data/dialogues/*` — complete old_man tree (memory001 hint via `set_flags: ["met_old_man"]`) and village_chief dialog (quest001).
  - `data/story/arcs.json`, `data/story/arc1_text.json`.
  - `assets/ascii/*` — finish art if needed; `data/maps/*` — finalize descriptions.
- [ ] **Step 4: Fix any schema gaps surfaced** by the content test (validator/schemas must stay consistent with existing `utils/validator.py` if it grows).

- [ ] **Step 5: Run full test suite**

Run: `pytest tests/ -q`
Expected: all PASS (including `test_arc1_content.py`).

- [ ] **Step 6: Manual smoke** — `python launcher.py` plays through Arc 1: boot → new game → talk old_man (memory001) → talk village_chief (quest001) → go forest → explore (encounter) → defeat wild_wolf (quest002) → quest completions + divergence alert.

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "feat: complete Arc 1 content in Bahasa Indonesia + content regression tests"
```

- [ ] **Step 8: Review gate** — dispatch code reviewer; fix any `Important` findings; commit fixes.

---

### Task 8: Docs + final polish

**Files:**
- Create: `README.md` (full)
- Modify: `requirements.txt` (pytest dev marker comment)
- Modify: `.gitignore` (ensure `saves/`, `logs/`, `*.log`, `.pytest_cache/` ignored — already present, verify)

- [ ] **Step 1: Write README.md** — project intro (Chronicle of the Past, Arc 1 vertical slice), install (`python -m venv .venv`, `pip install pytest`), run (`python launcher.py`), controls/commands, architecture summary (layers + dependency direction), content-authoring guide (JSON schemas for classes/enemies/skills/maps/npc/dialogues/quests/events/factions + how to add an event or dialog), save locations, MASTER_CONCEPT divergence notes (stdlib stack, frozen factions, numeric regions, map/location-trigger constraint, save versioning).

- [ ] **Step 1b: Optional regression test** (`tests/test_regression.py`, OPTIONAL deliverable — user-approved) — deterministic integration test: fixed seed, run a full-playthrough scenario (battle → loot → xp → level) 100 times via the same `Game` flow, assert identical final state each run. Respects RNG whole-loop rule (asserts final outcome, never roll sequences). Skip if it proves flaky/noisy — record the decision in the task report.

- [ ] **Step 1c: Record MASTER_CONCEPT PART 11 Changelog** — append a row to the changelog table in `/mnt/c/Users/dienk/Downloads/MASTER_CONCEPT.md` (PART 11, after v1.0 row): document the divergence that §6.12 Event conditions use `{"type": "location", "equals": "village"}` while the frozen `rule_engine` uses `{"kind": "map", "name", "operator"}` comparing a string — and that Arc 1 content uses FLAG triggers only (map/time triggers exercised in unit tests only). Title it version 1.1.

- [ ] **Step 2: Full test run + lint smoke**

Run: `pytest tests/ -v && python -m py_compile src/**/*.py launcher.py`
Expected: all PASS, no compile errors.

- [ ] **Step 3: Final commit**

```bash
git add -A
git commit -m "docs: README + final polish"
```

- [ ] **Step 4: Review gate** — dispatch code reviewer; fix any `Important` findings; commit fixes.

---

## Self-Review Notes

- **Spec coverage:** Tasks 1–8 cover the old plan Tasks 11–18 AND all Claude roadmap items T2–T17 (T1 dropped by user). Every Global Constraint is enforced by a dedicated test (frozen FACTIONS in `test_quest_reputation_uses_valid_factions` + existing `test_validator`; determinism via seeded `Randomizer` fixtures; no-content-names in engine code — all names from JSON; save defaults in `test_save.py`; equip registry pin in Task 6 wiring; RNG whole-loop rule respected in all flow tests).
- **Placeholder scan:** All interfaces are fully specified with exact signatures, schemas, and test code. The only "TODO"-like spot is Task 6 `game.py` orchestration detail, which is bounded by the explicit command dispatch list + wiring pins in the task body.
- **Type consistency:** `input_handler.parse_input -> Command(action, args, index)` is consumed only by Task 6 `Game.run_turn`. `process_events(game_state, randomizer=None, events=None) -> list[str]` signature is used identically in Tasks 2, 6, 7. `Npc.relationship` added in Task 1 is used by content (not consumed by engine) — additive, keeps `test_models.py` green. `GameState.events`/`GameState.rng_seed` added in Tasks 2/3 and read in Tasks 3/6. `Map.ascii_art` = asset stem, resolved by `ascii_loader.load` at render — consistent across Tasks 2, 4, 6.
- **Frozen-baseline guard:** the only files modified outside new-file tasks are `src/models/npc.py` (additive field, Task 1), `src/core/game_state.py` (two additive fields, Tasks 2/3), `launcher.py` (stub → full, Task 6), content JSONs (Task 7), and README/requirements/.gitignore (Task 8). No frozen engine/system logic is altered.
- **Self-review corrections applied (inline):**
  - Faction JSON is **one file per faction** (`data/factions/<id>.json`) — `load_dir` keys by each file's `data["id"]`; a single list file would not load. Task 1 creates 7 files.
  - `save_game` writes `flags` (added to data dict + shape) — `test_save_roundtrip` depends on it.
  - `_engine_state` stores `current_map.id` (not `None`) so saves preserve location; `continue_game` re-maps id → Map object.
  - `Game._wire` only sets `current_map` when `None` (continue_game must not be clobbered back to village).
  - `combat_view` renders `action.value.title()` ("Attack"/"Escape") to match the test; `render_class_card` uses `stat.title()` ("Attack"/"Defense") to match the test.
  - `test_box_ascii_fallback` corrected to `+-----+` (width 3 + 2 border chars); `test_event_does_not_fire_when_condition_missing` changed from `operator: MISSING` (which fires) to `value: True` on an absent flag (which doesn't).
  - `dialog_old_man_main` first choice sets `met_old_man` (was on a gated choice) so the Task 6 flow `talk old_man` → `"1"` works; `talk` handler renders an NPC-name header (`Old Man:`) for the test assertion.
  - `test_default_player` replaced weak `or True` assertion with factual asserts (name/class/reputation keys).
  - `forest.json` named **"Ashen Forest"** so Task 6 `"Forest" in out` matches the HUD location line.
  - Recorded map-trigger caveat (frozen `rule_engine` compares string ids; live Game holds Map objects → content events use flag triggers only).
- **User-approved amendments (post-review, before execution):**
  - Divergence #7 added (map/location-trigger caveat, explicit entry) — content events use flag triggers only.
  - Save Versioning: `schema_version`/`content_version` added to Task 3 save shape + implementation (backward-compatible load: legacy `version` key → treated as v0, still loads).
  - Task 8 Step 1b: optional regression test (100 deterministic runs, RNG whole-loop respected).
  - Task 8 Step 1c: MASTER_CONCEPT PART 11 Changelog entry (v1.1) recording the condition-schema divergence.
  - EventBus NOT in this plan (user decision; MASTER_CONCEPT §6.6 deems it overkill for CLI scale). Registry deferred to next phase (user decision).
