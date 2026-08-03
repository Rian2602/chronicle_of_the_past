# Chronicle of the Past (MVP Arc 1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a playable vertical slice of Chronicle of the Past: 5 classes, rule-based combat, 2 areas (Ashen Village + Forest), time system, quests, memory fragments, inventory/loot, save/load — all stdlib, deterministic, Bahasa Indonesia.

**Architecture:** Data-driven. Content in `data/*.json`; generic engine in `src/`. Engine/systems/UI communicate via GameState (dependency injection, no globals). UI is read-only. Seeded RNG through `src/core/randomizer.py`.

**Tech Stack:** Python 3.12 stdlib only, pytest (dev only).

## Global Constraints

- All game text in Bahasa Indonesia.
- Runtime deps: stdlib only. pytest is the only dev dependency.
- Box-drawing Unicode with `safe_box` ASCII downgrade in `ui/renderer.py`.
- Determinism: all randomness via `src/core/randomizer.py` seeded RNG. No module-level `random`.
- No globals; GameState passed explicitly. UI never imports engine; engine never imports UI.
- Engine code contains NO specific content names (no "warrior", "goblin", "quest001"). Content strings come from JSON only. Tests may use content IDs.
- 7 combat actions: Attack, Skill, Magic, Item, Observe, Escape, Defend.
- Leveling: auto-growth on level up (F4: max HP +5, max MP +3, full heal) + one manual pick; XP curve `xp_to_next(level) = 50 * level`; damage variance `random(0,5)`; initiative variance `random(0,5)`; combat rewards data-driven from `enemy.reward` (F1).
- Save JSON 3-layer under `saves/`; missing keys → defaults, never crash.
- 6 factions + crime reputation; 8 canonical regions (MVP: Region 1 Village, Region 2 Forest).
- Derived stats always computed, never stored (formulas in spec).

---

### Task 0: Project scaffolding

**Files:**
- Create: `launcher.py`, `requirements.txt`, `README.md`, `.gitignore`, `src/__init__.py` and all subpackage `__init__.py`
- Create: `tests/conftest.py`, `tests/__init__.py`
- Create: `data/config/config.json`, `assets/ui/colors.json`, `assets/ui/borders.json`

**Interfaces:**
- Produces: package layout importable as `from src.core... import ...`; `tests/conftest.py` exposes fixtures `game_state()` (fresh GameState), `randomizer()` (seeded).

- [ ] **Step 1: Write conftest + fixture spec test**

```python
# tests/conftest.py
import pytest
from src.core.game_state import GameState

@pytest.fixture
def randomizer():
    from src.core.randomizer import Randomizer
    return Randomizer(seed=12345)

@pytest.fixture
def game_state():
    return GameState()
```

- [ ] **Step 2: Write `src/core/__init__.py` etc. (empty) + `.gitignore`**

`.gitignore`: `__pycache__/`, `*.pyc`, `saves/*.json`, `logs/*.log`, `.pytest_cache/`, `.venv/`

- [ ] **Step 3: Write minimal `randomizer.py` + `game_state.py` stubs**

```python
# src/core/randomizer.py
import random

class Randomizer:
    def __init__(self, seed: int | None = None):
        self._rng = random.Random(seed)
        self.seed = seed

    def roll(self, low: int, high: int) -> int:
        return self._rng.randint(low, high)

    def chance(self, percent: float) -> bool:
        return self._rng.random() * 100 < percent
```

```python
# src/core/game_state.py
class GameState:
    def __init__(self):
        self.player = None
        self.world = {}
        self.flags = {}
        self.time = "morning"
        self.day = 1
        self.current_map = None
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/ -v`
Expected: PASS (empty suite or 1 trivial test). Add a trivial test to prove fixture wiring if needed.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "chore: scaffold project structure, GameState, Randomizer"
```

---

### Task 1: Config + JSON loader + logger

**Files:**
- Create: `src/utils/json_loader.py`, `src/utils/logger.py`, `src/utils/helpers.py`, `src/utils/dice.py`
- Create: `tests/test_json_loader.py`, `tests/test_dice.py`

**Interfaces:**
- Produces:
  - `json_loader.load_json(path) -> dict` — loads file, raises `ContentError` with path on JSON decode failure.
  - `json_loader.load_dir(dirpath) -> dict[str, dict]` — id → data for all json files in dir.
  - `dice.roll(randomizer, low, high) -> int` — delegate.
  - `logger.get_logger(name) -> logging.Logger` — writes to `logs/game.log`.
  - `helpers.clamp(value, lo, hi)`.

- [ ] **Step 1: Write failing tests**

```python
# tests/test_json_loader.py
import pytest
from src.utils.json_loader import load_json, load_dir, ContentError

def test_load_json_missing_file_raises(tmp_path):
    with pytest.raises(ContentError):
        load_json(str(tmp_path / "nope.json"))

def test_load_json_valid(tmp_path):
    p = tmp_path / "a.json"
    p.write_text('{"a": 1}')
    assert load_json(str(p)) == {"a": 1}

def test_load_dir_keys_are_ids(tmp_path):
    (tmp_path / "warrior.json").write_text('{"id":"warrior","x":1}')
    data = load_dir(str(tmp_path))
    assert data["warrior"]["x"] == 1
```

```python
# tests/test_dice.py
from src.utils.dice import roll

def test_roll_within_range():
    from src.core.randomizer import Randomizer
    r = Randomizer(seed=1)
    for _ in range(100):
        v = roll(r, 0, 5)
        assert 0 <= v <= 5
```

- [ ] **Step 2: Run to verify fail**

Run: `pytest tests/test_json_loader.py tests/test_dice.py -v`
Expected: FAIL (module not found).

- [ ] **Step 3: Implement**

```python
# src/utils/json_loader.py
import json, os

class ContentError(Exception):
    pass

def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        raise ContentError(f"Gagal memuat {path}: {e}") from e

def load_dir(dirpath):
    result = {}
    if not os.path.isdir(dirpath):
        return result
    for name in sorted(os.listdir(dirpath)):
        if name.endswith(".json"):
            data = load_json(os.path.join(dirpath, name))
            result[data["id"]] = data
    return result
```

```python
# src/utils/dice.py
def roll(randomizer, low, high):
    return randomizer.roll(low, high)
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_json_loader.py tests/test_dice.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: JSON loader, dice, logger, helpers"
```

---

### Task 2: Constants, config, validator

**Files:**
- Create: `src/core/constants.py`, `src/core/config.py`, `src/utils/validator.py`
- Create: `tests/test_validator.py`

**Interfaces:**
- Produces:
  - `constants.STATS = ["attack","defense","hp","mp","agility","intelligence"]`
  - `constants.TIMES = ["morning","afternoon","evening","night"]`
  - `constants.FACTIONS = ["royal_army","church","rebels","merchant_guild","scholar_society","ancient_order","crime"]`
  - `constants.COMBAT_ACTIONS = ["attack","skill","magic","item","observe","escape","defend"]`
  - `config.load_config(data_dir="data") -> dict` — merges `data/config/config.json`.
  - `validator.require_keys(data, keys, path)` — raise `SchemaError` listing missing keys.

- [ ] **Step 1: Write failing test**

```python
# tests/test_validator.py
import pytest
from src.utils.validator import require_keys, SchemaError

def test_require_keys_missing():
    with pytest.raises(SchemaError):
        require_keys({"id": "x"}, ["id", "name"], "data/classes/warrior.json")

def test_require_keys_ok():
    require_keys({"id": "x", "name": "X"}, ["id", "name"], "p")
```

- [ ] **Step 2: Run to verify fail** → FAIL.

- [ ] **Step 3: Implement** constants + config + validator (require_keys raises SchemaError listing missing).

- [ ] **Step 4: Run tests** → PASS.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: constants, config loader, schema validator"
```

---

### Task 3: Models — Player, Item, Skill, Enemy, Npc, Map, Quest

**Files:**
- Create: `src/models/player.py`, `src/models/item.py`, `src/models/skill.py`, `src/models/enemy.py`, `src/models/npc.py`, `src/models/map.py`, `src/models/quest.py`, `src/models/event.py`
- Create: `tests/test_models.py`

**Interfaces:**
- Produces (dataclasses):
  - `Player(name, class_id, level=1, xp=0, gold=0, hp, mp, base_stats: dict, attribute_bonuses: dict, skill_points=0, equipped: dict, inventory: list, reputation: dict, relationship: dict, flags: dict, quests_active: dict, quests_done: list, memories: list, learned_skills: list)`
  - `Item(id, name, type, slot=None, modifiers: dict, price=0, description="")`
  - `Skill(id, name, type, cost, power=0, target, effects: list, requires: dict, description="")`
  - `Enemy(id, name, level, stats: dict, loot: list, skills: list, lore="")`
  - `Npc(id, name, location, role, faction, dialogs: list)`
  - `Map(id, name, region, threat_level, description, ascii_art, exits: list, npcs: list, enemy_pool: list, time_effects: dict)`
  - `Quest(id, title, type, description, requirements: list, rewards: dict, flags_on_complete, next)`
  - Helper `player.max_hp(player) -> int`, `player.max_mp(player) -> int`.

- [ ] **Step 1: Write failing test**

```python
# tests/test_models.py
from src.models.player import Player, max_hp

def test_player_max_hp():
    p = Player(name="Rian", class_id="warrior", hp=100, mp=10,
               base_stats={"hp": 100, "mp": 10})
    assert max_hp(p) == 100
```

- [ ] **Step 2: Run to verify fail** → FAIL.

- [ ] **Step 3: Implement** all dataclasses (stdlib `@dataclass`).

- [ ] **Step 4: Run tests** → PASS.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: content models as dataclasses"
```

---

### Task 4: Rule Engine — conditions, derived stats, damage, xp

**Files:**
- Create: `src/engine/rule_engine.py`, `src/systems/level_system.py`
- Create: `tests/test_rule_engine.py`, `tests/test_level_system.py`

**Interfaces:**
- Produces:
  - `rule_engine.derived_stats(player) -> dict` — computes all 10 derived stats per spec formulas.
  - `rule_engine.evaluate(condition: dict, game_state) -> bool` — supports kinds: `{"kind":"flag","flag":"x","value":True}`, `{"kind":"map","map":"village"}`, `{"kind":"time","time":"night"}`, `{"kind":"level","gte":3}`, `{"kind":"quest_done","quest":"quest001"}`.
  - `rule_engine.damage_roll(attacker_stats, defender_stats, randomizer) -> dict` → `{"damage": int, "critical": bool, "missed": bool}` using physical formula.
  - `level_system.xp_to_next(level) -> int` (`50 * level`).
  - `level_system.gain_xp(player, amount, randomizer) -> list[int]` — returns list of new levels gained; raises LevelUpRequest? No — returns levels gained, caller handles choice.

- [ ] **Step 1: Write failing tests**

```python
# tests/test_rule_engine.py
from src.engine.rule_engine import derived_stats, evaluate, damage_roll
from src.models.player import Player
from src.core.randomizer import Randomizer

def test_derived_stats_critical():
    p = Player("R", "assassin", 65, 12,
               {"attack":15,"defense":6,"hp":65,"mp":12,"agility":15,"intelligence":11})
    ds = derived_stats(p)
    assert ds["critical"] == pytest.approx(6.0)  # 15*0.4

def test_damage_roll_bounds():
    a = {"attack": 10, "defense": 5, "agility": 8, "intelligence": 7}
    d = {"defense": 5, "agility": 5}
    r = Randomizer(seed=7)
    res = damage_roll(a, d, r)
    assert res["missed"] in (True, False)
    if not res["missed"]:
        assert 0 <= res["damage"] <= 15  # 10 - 2 + 0..5, crit ×1.5 (10-2)*1.5=12+5=17 cap
```

```python
# tests/test_level_system.py
from src.systems.level_system import xp_to_next

def test_xp_curve():
    assert xp_to_next(1) == 50
    assert xp_to_next(2) == 100
    assert xp_to_next(3) == 150
```

- [ ] **Step 2: Run to verify fail** → FAIL.

- [ ] **Step 3: Implement** derived_stats (all 10), evaluate (kind dispatch), damage_roll (accuracy, crit ×1.5, variance 0..5), xp_to_next.

- [ ] **Step 4: Run tests** → PASS.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: rule engine (derived stats, damage, conditions) + leveling"
```

---

### Task 4b: Rule engine condition operators (Design Freeze F5)

Follow-up to Task 4: `evaluate` currently treats `flag` conditions as
presence-only. This task adds operator support per F5.

**Files:**
- Extend: `src/engine/rule_engine.py` (`evaluate`), `src/core/constants.py`
  (add `CONDITION_OPERATORS`), `src/utils/validator.py` (validate operator
  membership where relevant)
- Extend: `tests/test_rule_engine.py`

**Interfaces:**
- Produces:
  - `constants.CONDITION_OPERATORS = ("EQ","NE","GT","LT","GTE","LTE","EXISTS","MISSING")`.
  - `rule_engine.evaluate(condition, game_state)` supports operator semantics:
    - no `operator` field → default `EQ` with `value` defaulting to `True`
      (backward compatible with Task 4 behavior / old JSON).
    - `flag` kind: EQ/NE vs `flags[name]` (bool), EXISTS (`name in flags`),
      MISSING (`name not in flags`).
    - `level` kind: numeric comparisons on `player.level` (GT/LT/GTE/LTE/EQ/NE).
    - `map`/`time`: EQ/NE on `current_map` / `time`.
    - `quest_done`: EQ/NE/EXISTS/MISSING on `quests_done`.
    - Unknown kind or operator → `False` (documented).
  - Flag default: `{"kind":"flag","name":"x","value":true}` (no operator)
    must still return True only when `flags["x"] is True`.

- [ ] **Step 1: Write failing tests** — operator EQ false, NE, GT on level,
  EXISTS/MISSING on flags, default (no operator) backward compat, unknown
  operator → False, and that old `{"kind":"flag","flag":"x"}` (legacy key
  `flag`) still works (support both `flag` and `name` keys, `flag` deprecated).

- [ ] **Step 2: Run to verify fail** → FAIL.

- [ ] **Step 3: Implement** per interfaces; keep `flag` key working as alias.

- [ ] **Step 4: Run tests** → PASS (full suite incl. old rule_engine tests).

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: rule engine condition operators (F5)"
```

---

### Task 5: Class loading + player creation (game_context)

**Files:**
- Create: `src/core/game_context.py`
- Create: `data/classes/warrior.json`, `ranger.json`, `mage.json`, `assassin.json`, `scholar.json`
- Create: `tests/test_game_context.py`

**Interfaces:**
- Produces:
  - `game_context.GameContext(data_dir="data")` — loads all content dirs into dicts (classes, enemies, items, skills, maps, npc, quests, dialogues, factions, memories).
  - `game_context.classes -> dict`, `game_context.items -> dict`, etc.
  - `game_context.create_player(name, class_id) -> Player` — applies base_stats, sets current hp/mp to max, starting_skills.

- [ ] **Step 1: Write failing test**

```python
# tests/test_game_context.py
from src.core.game_context import GameContext

def test_create_warrior(tmp_path):
    ctx = GameContext(data_dir="data")
    p = ctx.create_player("Rian", "warrior")
    assert p.base_stats["attack"] == 12
    assert p.hp == 100
```

- [ ] **Step 2: Run to verify fail** → FAIL.

- [ ] **Step 3: Write the 5 class JSON files** per spec schema with final numbers.

- [ ] **Step 4: Implement** GameContext: load_dir each data subdir; create_player applies class base_stats, maxes hp/mp, copies starting_skills.

- [ ] **Step 5: Run tests** → PASS.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat: class JSON content + GameContext + player creation"
```

---

### Task 6: Level up choice (manual upgrade)

**Files:**
- Create: `src/systems/level_system.py` (extend)
- Create: `tests/test_level_up.py`

**Interfaces:**
- Produces:
  - `LEVEL_CHOICES = [("attack",2),("defense",2),("agility",2),("intelligence",2),("hp",15),("mp",10),("skill_point",1)]`
  - `level_system.apply_choice(player, choice_key)` — mutates player.attribute_bonuses / skill_points.
  - `level_system.on_level_up(player)` — +hp_regen? No: auto-increment: hp+10, mp+5 base on level up (documented), increments level, returns choice list.

- [ ] **Step 1: Write failing test**

```python
# tests/test_level_up.py
from src.models.player import Player
from src.systems import level_system

def test_apply_attack_choice():
    p = Player("R", "warrior", 100, 10, {"attack":12,"defense":14,"hp":100,"mp":10,"agility":8,"intelligence":7})
    level_system.apply_choice(p, "attack")
    assert p.attribute_bonuses["attack"] == 2
```

- [ ] **Step 2: Run to verify fail** → FAIL.

- [ ] **Step 3: Implement** apply_choice + on_level_up (level+1, hp+10, mp+5, returns choices).

- [ ] **Step 4: Run tests** → PASS.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: manual level-up choices"
```

---

### Task 6b: Level up growth per F4

Follow-up to Task 6: `on_level_up` currently does `level+1`, `hp+10`, `mp+5`
on current values (clamped). Design Freeze F4 changes the contract.

**Files:**
- Extend: `src/systems/level_system.py` (`on_level_up`)
- Extend: `tests/test_level_up.py` (update old expectations)

**Interfaces:**
- Produces:
  - `level_system.on_level_up(player)` — per F4:
    1. `player.level += 1`
    2. `player.attribute_bonuses["hp"] += 5` and `["mp"] += 3` (raises MAX via
       existing `max_hp`/`max_mp` formulas)
    3. Full heal: `player.hp = max_hp(player)`, `player.mp = max_mp(player)`
    4. returns `LEVEL_CHOICES` (caller presents the single manual pick).
  - `apply_choice` unchanged. `xp_to_next`/`gain_xp` unchanged.

- [ ] **Step 1: Update failing tests** — existing tests asserting old +10/+5
  clamped behavior are replaced: level+1; max_hp/max_mp grow by 5/3; hp/mp
  set to max after (full heal); returns LEVEL_CHOICES; stacking across two
  level-ups accumulates.

- [ ] **Step 2: Run to verify fail** → FAIL (old behavior fails new tests).

- [ ] **Step 3: Implement** the new `on_level_up`.

- [ ] **Step 4: Run tests** → PASS (full suite).

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: level-up auto-growth per design freeze F4"
```

---

### Task 7.0: Combat Interfaces (Design Freeze B6 + schema extension)

Contracts only — no game logic. All combat subtasks 7.1–7.7 import these
types so no subtask redefines data structures.

**Files:**
- Create: `src/engine/combat_interfaces.py`
- Extend: `src/models/enemy.py` (new optional fields per Design Freeze B/F1/F3)
- Create: `tests/test_combat_interfaces.py`

**Interfaces:**
- Produces (all in `combat_interfaces`):
  - `class CombatAction(str, Enum)`: `ATTACK, SKILL, MAGIC, ITEM, OBSERVE, ESCAPE, DEFEND`.
  - `class CombatResult(str, Enum)`: `VICTORY, DEFEAT, ESCAPED`.
  - `@dataclass StatusEffect: kind: str, duration: int, power: int` (F2).
  - `@dataclass DamageResult: damage: int, critical: bool, missed: bool`.
  - `LootResolver = Callable[[Enemy, Randomizer], list[dict]]` (F1; stub
    returns `[]`, Task 9 provides real `loot_system.roll_loot`).
  - `@dataclass CombatState` — the shared contract:
    `round_no: int`, `turn_order: list`, `current_index: int`, `over: bool`,
    `result: CombatResult | None`, `log: list[str]`,
    `observe_used: bool`, `player_defending: bool`, `enemy_defending: bool`,
    `statuses: dict[str, list[StatusEffect]]`, `xp: int = 0`, `gold: int = 0`,
    `loot: list = field(default_factory=list)`,
    `observe_info: str | None = None`, `player: Player | None = None`,
    `enemy: Enemy | None = None`, `randomizer: Randomizer | None = None`,
    `skills: dict = field(default_factory=dict)`,
    `loot_resolver: LootResolver | None = None`,
    `max_status_duration: int = 10` (from `config.status.max_duration`, F2/D).
- Produces in `src/models/enemy.py` (backward-compatible defaults):
  `reward: dict = field(default_factory=dict)`,
  `behavior: str = "aggressive"`, `weight: int = 1`,
  `tags: list = field(default_factory=list)`.

- [ ] **Step 1: Write failing test** — constructs CombatState with all fields,
  Enemy with new fields; enums have expected members.

- [ ] **Step 2: Run to verify fail** → FAIL.

- [ ] **Step 3: Implement** contracts + Enemy extension.

- [ ] **Step 4: Run tests** → PASS.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: combat interfaces contract + enemy schema extension"
```

---

### Task 7.1: Status Effect system (F2, cap dari config)

**Files:**
- Create: `src/systems/status_system.py`
- Create: `tests/test_status.py`

**Interfaces:**
- Produces:
  - `apply_status(state, actor_id, kind, power, duration)` — F2 semantics:
    - DoT kinds (`poison`, `burn`, `bleed`): existing same kind → `power`
      unchanged, `duration = min(duration + new, state.max_status_duration)`.
    - Control kinds (`blind`, `silence`, `fear`, `sleep`): existing → refresh
      `duration` (cap applies).
    - New kind → append `StatusEffect`.
    - actor_id `"player"` or enemy id.
  - `tick_statuses(state, actor_id) -> list[str]` — for each status on actor:
    DoT kinds deal `power` damage to current hp (ignores defense, min 0),
    duration `-= 1`, remove expired. Control statuses only decrement duration
    (behavioral penalties out of MVP scope, documented). Returns Bahasa
    Indonesia messages.
  - No randomness, no source tracking (F2).

- [ ] **Step 1: Write failing tests** — DoT reapply keeps power adds duration;
  cap at max_status_duration (use a small cap like 3 to test); control refresh;
  tick deals damage and removes expired; empty → no messages.

- [ ] **Step 2: Run to verify fail** → FAIL.

- [ ] **Step 3: Implement** status_system.

- [ ] **Step 4: Run tests** → PASS.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: status effect system per F2 (doT stacking + control refresh)"
```

---

### Task 7.2: Damage Formula

**Files:**
- Create: `src/engine/combat_engine.py` (damage functions only; loop added in 7.3)
- Create: `tests/test_damage.py`

**Interfaces:**
- Produces (importing CombatState/DamageResult from combat_interfaces):
  - `resolve_hit(state, attacker_stats, defender, power, is_magic, effects) -> DamageResult`:
    - physical: reuse `rule_engine.damage_roll(attacker_stats, defender, randomizer)`;
      if defender defending → halve.
    - magic: `damage = power + int*0.5 - magic_resistance` (int = attacker int;
      enemy magic_res = `defender["intelligence"]*0.6`), min 1, never missed.
    - applies `effects` (list of `{"kind","duration","power"}`) to defender
      via `status_system.apply_status`.
    - returns DamageResult and appends Bahasa Indonesia log line.
- Helper `magic_damage(power, attacker_int, defender_magic_res) -> int`.

- [ ] **Step 1: Write failing tests** — physical vs defend halving, crit/miss
  passthrough, magic formula exact numbers, magic min 1, effects applied.

- [ ] **Step 2: Run to verify fail** → FAIL.

- [ ] **Step 3: Implement**.

- [ ] **Step 4: Run tests** → PASS.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: combat damage resolution (physical + magic)"
```

---

### Task 7.3: Combat Loop

**Files:**
- Extend: `src/engine/combat_engine.py`
- Create: `tests/test_combat_loop.py`

**Interfaces:**
- Produces:
  - `start_combat(player, enemy, randomizer, skills=None, loot_resolver=None, max_status_duration=10) -> CombatState` — builds state per contract; turn order by initiative descending: player via `rule_engine.derived_stats` initiative, enemy `agility + roll(0,5)`.
  - `player_action(state, action, choice=None)` — dispatch:
    - `ATTACK`: `resolve_hit` physical (choice=None); if enemy defending → halved.
    - `OBSERVE`: once per combat (`observe_used`); fills `observe_info` per INT tier (INT<8 name+HP bar; 8–12 +weakness; 13–15 +resistance+lore; ≥16 +exact HP+hint). **Free action** — caller skips enemy_turn.
    - `ESCAPE`: `roll(0,100) < 50 + player_agility - enemy_agility` → `result=ESCAPED`, `over=True`; failure → enemy free basic attack.
    - `DEFEND`: `player_defending = True`; no attack.
    - SKILL/MAGIC/ITEM: NotImplementedError (implemented in 7.4).
  - `enemy_turn(state)` — basic attack only (skill/AI in 7.4/7.5): `resolve_hit` physical, halved if `player_defending` (then reset).
  - `next_turn(state)` — tick statuses for acting actor (7.1), apply hp_regen/mana_regen (derived_stats, clamped) at actor turn start, advance `current_index`/`round_no`, check death → `result` set (reward computation in 7.6).
  - Helpers `enemy_stats(state) -> dict`, `player_stats(state) -> dict`.

- [ ] **Step 1: Write failing tests** — turn order by initiative; full basic-attack combat reaches victory/defeat; defend halves then resets; escape success/failure; observe tiers + once-only; status tick at turn start.

- [ ] **Step 2: Run to verify fail** → FAIL.

- [ ] **Step 3: Implement**.

- [ ] **Step 4: Run tests** → PASS.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: combat turn loop, defend/observe/escape, basic attacks"
```

---

### Task 7.4: Skill & Item Execution

**Files:**
- Extend: `src/engine/combat_engine.py`
- Create: `tests/test_combat_skills.py`

**Interfaces:**
- Produces:
  - `player_action` SKILL/MAGIC/ITEM now implemented:
    - `SKILL` / `MAGIC`: `choice` = skill dict (id resolved via `state.skills`); costs MP (`skill["cost"]`); `skill["type"]` `"magic"` → magic path, `"physical"` → physical path; `skill["power"]`; `skill["effects"]` applied to enemy; log. Insufficient MP → log, turn consumed without action.
    - `ITEM`: `use_item(state, item_id)` — find in `player.inventory` (dict with `id`/`qty`), decrement qty, remove at 0, `heal` → hp + heal clamped to max, log; not owned → ValueError.
  - `use_item(state, item_id)` — as above.

- [ ] **Step 1: Write failing tests** — skill costs MP and applies effects; magic skill uses magic formula; not enough MP; item heal consumes qty, clamps, removes at 0; unknown item raises.

- [ ] **Step 2: Run to verify fail** → FAIL.

- [ ] **Step 3: Implement**.

- [ ] **Step 4: Run tests** → PASS.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: skill/magic execution and item use in combat"
```

---

### Task 7.5: Enemy AI (F3)

**Files:**
- Extend: `src/engine/combat_engine.py`
- Extend: `tests/test_combat_loop.py` (or new `tests/test_enemy_ai.py`)

**Interfaces:**
- Produces:
  - `enemy_turn(state)` now runs deterministic behavior tree from
    `state.enemy.behavior` (F3), no RNG for decisions:
    - `aggressive`: first skill in `enemy.skills` order with cost ≤ enemy mp
      (resolved via `state.skills`) → use it; else basic attack.
    - `defensive`: enemy hp < 30% → heal skill if present; else if
      `enemy_defending` already → attack; else set `enemy_defending=True`.
    - `mage`: first magic-type skill affordable → use; else first skill; else
      attack.
    - `coward`: enemy hp < 20% → attempt escape (fails, combat continues);
      else defend; else attack.
  - Enemy skills use `resolve_hit` (physical/magic per skill type) and apply
    effects; consumes enemy mp.

- [ ] **Step 1: Write failing tests** — aggressive uses highest-priority
  affordable skill; defensive heals below 30%, defends, attacks; mage prefers
  magic; coward tries escape then defends; deterministic across runs (same
  seed → same outcome).

- [ ] **Step 2: Run to verify fail** → FAIL.

- [ ] **Step 3: Implement**.

- [ ] **Step 4: Run tests** → PASS.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: deterministic enemy AI per F3 (behavior + skill priority)"
```

---

### Task 7.6: Victory & Reward (F1 + LootResolver stub)

**Files:**
- Extend: `src/engine/combat_engine.py`
- Create: `tests/test_combat_rewards.py`

**Interfaces:**
- Produces:
  - On victory (`result = VICTORY`): read `state.enemy.reward`
    (`xp` int, `gold` = `[min, max]` inclusive range):
    - `state.xp = reward["xp"]`
    - `state.gold = randomizer.roll(reward["gold"][0], reward["gold"][1])`
    - `state.loot = state.loot_resolver(state.enemy, state.randomizer)`
      (stub default returns `[]`; Task 9 implements `loot_system.roll_loot`
      and wires it — **no duplicate loot implementation**).
    - Mutate player: `player.xp += state.xp`, `player.gold += state.gold`,
      append loot item dicts to `player.inventory` (via inventory_system in
      Task 9; until then simple list append).
    - Level-up flow stays caller/UI-side (gain_xp/on_level_up unchanged here).
  - On defeat: `result = DEFEAT`, `over = True`, no rewards.

- [ ] **Step 1: Write failing tests** — victory applies xp/gold to player from
  reward (exact numbers), gold within range (seeded), loot via resolver
  (mock resolver returns items → appended to inventory), no reward mutation on
  defeat.

- [ ] **Step 2: Run to verify fail** → FAIL.

- [ ] **Step 3: Implement**.

- [ ] **Step 4: Run tests** → PASS.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: data-driven combat rewards per F1 (reward.xp/gold + loot resolver)"
```

---

### Task 7.7: Combat integration tests

**Files:**
- Create: `tests/test_combat.py` (integration)
- Extend: none (fix issues if found)

**Interfaces:**
- Verifies end-to-end combat through `start_combat` + `player_action` +
  `enemy_turn` + `next_turn`:
  - full fight reaches `victory` with `xp > 0` and player mutated (original
    Task 7 brief example test, updated for F1/F3: Enemy built with
    `reward={"xp":30,"gold":[6,12]}`).
  - defeat path when player dies.
  - status effect applied via skill persists across turns and resolves.
  - All 7 actions exercised (attack/skill/magic/item/observe/escape/defend).
- Run **full suite** → all green.

- [ ] **Step 1: Write failing integration tests** → FAIL.

- [ ] **Step 2: Implement** (fix integration gaps discovered).

- [ ] **Step 3: Run full suite** → PASS.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "feat: combat integration tests (7 actions, victory, defeat)"
```

---

### Task 8: Time Engine + World Engine + travel

**Files:**
- Create: `src/engine/time_engine.py`, `src/engine/world_engine.py`, `src/systems/travel_system.py`
- Create: `tests/test_time.py`, `tests/test_world.py`

**Interfaces:**
- Produces:
  - `time_engine.advance_time(game_state, ticks=1)` — cycles morning→afternoon→evening→night; `day+1` on wrap to morning.
  - `time_engine.rest(game_state)` — advance to morning next day, heal player to full.
  - `world_engine.get_map(game_state, map_id)` / `world_engine.current_map(game_state)`.
  - `travel_system.can_travel(game_state, target)` — checks exits.
  - `travel_system.travel(game_state, target)` — moves current_map, advances time 1 tick, logs arrival.
  - `exploration_system.check_encounter(game_state, randomizer) -> Enemy | None` — formula `20 + threat*10` (+10 night in Forest). Enemy sampled from `enemy_pool` weighted by each enemy's `weight` field (default 1, Design Freeze B); pool entries may be enemy ids or `{"id": ..., "weight": ...}`.

- [ ] **Step 1: Write failing tests**

```python
# tests/test_time.py
from src.core.game_state import GameState
from src.engine.time_engine import advance_time

def test_time_cycle():
    gs = GameState()
    gs.time = "evening"
    advance_time(gs)
    assert gs.time == "night"

def test_day_wraps():
    gs = GameState()
    gs.time = "night"
    gs.day = 1
    advance_time(gs)
    assert gs.time == "morning"
    assert gs.day == 2
```

- [ ] **Step 2: Run to verify fail** → FAIL.

- [ ] **Step 3: Implement** time_engine, world_engine, travel_system, exploration_system (encounter formula).

- [ ] **Step 4: Run tests** → PASS.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: time, world, travel, rule-based encounters"
```

---

### Task 9: Inventory, Equipment, Loot

**Files:**
- Create: `src/systems/inventory_system.py`, `src/systems/equipment_system.py`, `src/systems/loot_system.py`
- Create: `tests/test_inventory.py`, `tests/test_loot.py`
- Create: `data/items/iron_sword.json`, `herb.json`, `potion.json`, `leather_armor.json`, `wooden_helmet.json`
- Create: `data/enemies/goblin.json`, `wild_wolf.json`, `bandit.json`

**Interfaces:**
- Produces:
  - `inventory_system.add_item(player, item_id, qty=1) -> bool` (False if over carry capacity `30 + L*2`).
  - `inventory_system.remove_item(player, item_id, qty=1)`.
  - `inventory_system.use_consumable(player, item, game_state) -> str` (potion restores hp).
  - `equipment_system.equip(player, item)` / `unequip(player, slot)` — applies modifiers into attribute_bonuses; returns log.
  - `equipment_system.total_stats(player)` — base + bonuses + equipment.
  - `loot_system.roll_loot(enemy, randomizer) -> list[dict]` — **implements the
    `LootResolver` contract from Task 7.0** (items only, per loot table;
    gold is NOT in loot — it comes from `enemy.reward.gold`, F1). Combat
    wiring: Task 16 passes this as `loot_resolver` to `start_combat`; Task 7.6
    stub default remains `[]` until then.

- [ ] **Step 1: Write failing test**

```python
# tests/test_loot.py
from src.models.enemy import Enemy
from src.systems.loot_system import roll_loot
from src.core.randomizer import Randomizer

def test_loot_item_chance():
    e = Enemy("g", "Goblin", 2, {"attack":5,"defense":2,"hp":5,"mp":0,"agility":6,"intelligence":3},
              loot=[{"item":"herb","chance":100,"amount":1}], skills=[], lore="",
              reward={"xp":30,"gold":[6,12]})
    r = Randomizer(seed=9)
    drops = roll_loot(e, r)
    assert any(d["item"] == "herb" for d in drops)
```

- [ ] **Step 2: Run to verify fail** → FAIL.

- [ ] **Step 3: Write item/enemy JSON** files per spec schema. Enemy JSON uses
  the full schema (Design Freeze B): `id, name, level, stats, behavior,
  reward{xp,gold}, skills, loot, weight, tags, lore`.

- [ ] **Step 4: Implement** the three systems.

- [ ] **Step 5: Run tests** → PASS.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat: inventory, equipment, loot systems + item/enemy content"
```

---

### Task 10: Quest Engine + Memory System

**Files:**
- Create: `src/engine/quest_engine.py`, `src/systems/memory_system.py`
- Create: `tests/test_quests.py`, `tests/test_memory.py`
- Create: `data/quests/quest001.json` ("Temui Kepala Desa", main), `data/quests/quest002.json` (side quest "Bahaya di Hutan")
- Create: `data/story/memories.json`

**Interfaces:**
- Produces:
  - `quest_engine.start_quest(game_state, quest_id)` / `quest_engine.complete_requirement(game_state, kind, target)` → checks active quests, marks done when all met, applies rewards (xp/gold/reputation), sets `flags_on_complete`, triggers `next`.
  - `memory_system.grant_memory(game_state, memory_id)` — sets flags, appends to player.memories, returns memory dict.
  - `memory_system.has_memory(game_state, memory_id) -> bool`.

- [ ] **Step 1: Write failing test**

```python
# tests/test_memory.py
from src.core.game_state import GameState
from src.systems.memory_system import grant_memory, has_memory

def test_grant_sets_flags():
    gs = GameState()
    memory = {"id":"memory001","flags_set":["knows_village_burns"]}
    grant_memory(gs, "memory001", memory)
    assert has_memory(gs, "memory001")
    assert gs.flags.get("knows_village_burns") is True
```

- [ ] **Step 2: Run to verify fail** → FAIL.

- [ ] **Step 3: Implement** quest_engine (requirement kinds: talk/map/flag; rewards) + memory_system.

- [ ] **Step 4: Write quest + memory JSON** per spec schema (2 memories).

- [ ] **Step 5: Run tests** → PASS.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat: quest engine, memory system + content"
```

---

### Task 11: Dialog Engine + NPC content

**Files:**
- Create: `src/engine/dialog_engine.py`
- Create: `tests/test_dialog.py`
- Create: `data/npc/old_man.json`, `village_chief.json`
- Create: `data/dialogues/dialog_old_man_main.json`, `dialog_old_man_1.json`, `dialog_village_chief.json`
- Create: `data/factions/factions.json`

**Interfaces:**
- Produces:
  - `dialog_engine.get_dialog(context, dialog_id) -> dict` (dialogue file).
  - `dialog_engine.available_choices(dialog, game_state) -> list[dict]` — filters by `require_flags` and (optional) `require_not_flags`.
  - `dialog_engine.choose(game_state, dialog, choice_index)` — applies `set_flags`, returns `next` dialog id (or None).
  - Dialog choice schema per spec.

- [ ] **Step 1: Write failing test**

```python
# tests/test_dialog.py
from src.engine.dialog_engine import available_choices, choose
from src.core.game_state import GameState

def test_choice_flag_gating():
    gs = GameState()
    dialog = {"id":"d","lines":[],"choices":[
        {"text":"A","require_flags":["knows_village_burns"],"set_flags":[],"next":None},
        {"text":"B","require_flags":[],"set_flags":["told"],"next":None}]}
    opts = available_choices(dialog, gs)
    assert len(opts) == 1 and opts[0]["text"] == "B"
```

- [ ] **Step 2: Run to verify fail** → FAIL.

- [ ] **Step 3: Implement** dialog_engine (flag gating).

- [ ] **Step 4: Write NPC + dialog + factions JSON** per spec.

- [ ] **Step 5: Run tests** → PASS.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat: dialog engine with flag-gated choices + NPC/faction content"
```

---

### Task 12: Maps content + ascii art + exploration content

**Files:**
- Create: `data/maps/village.json`, `forest.json`
- Create: `assets/ascii/village.txt`, `assets/ascii/forest.txt`
- Create: `src/ui/ascii_loader.py` + test
- Create: `data/events/events.json` (Arc1 events: wake, first memory, quest hints)

**Interfaces:**
- Produces:
  - `ascii_loader.load(name) -> str` from assets/ascii.
  - `event_engine.process_events(game_state, randomizer)` — checks `data/events/events.json` triggers (kind: map/time/flag/level/quest_done) via rule_engine.evaluate; applies actions (set flags, grant memory, log).

- [ ] **Step 1: Write failing test**

```python
# tests/test_events.py
from src.core.game_state import GameState
from src.engine.event_engine import process_events

def test_event_fires_on_flag():
    gs = GameState()
    gs.flags["trigger_me"] = True
    events = [{"id":"e1","trigger":[{"kind":"flag","flag":"trigger_me","value":True}],
               "actions":[{"kind":"set_flag","flag":"e1_fired","value":True}]}]
    process_events(gs, None, events)
    assert gs.flags.get("e1_fired") is True
```

- [ ] **Step 2: Run to verify fail** → FAIL.

- [ ] **Step 3: Implement** ascii_loader + event_engine.

- [ ] **Step 4: Write map JSON + ascii art + events JSON.**

- [ ] **Step 5: Run tests** → PASS.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat: map content, ascii art, event engine"
```

---

### Task 13: Save Manager

**Files:**
- Create: `src/core/save_manager.py`
- Create: `tests/test_save.py`

**Interfaces:**
- Produces:
  - `save_manager.save_game(game_state, path, version=1) -> str` — serializes player/engine_state; returns path.
  - `save_manager.load_game(path, game_context) -> GameState` — validates version, fills missing keys with defaults, seeds Randomizer from saved seed, returns state with `game_state.rng`.
  - `save_manager.default_player(context)` for corrupt/missing saves.
  - Corruption → `SaveError`; Game loop catches and offers new game.
  - Note (Design Freeze B6): combat statuses are transient (live in
    `CombatState`, never in Player) — no status serialization needed.

- [ ] **Step 1: Write failing test**

```python
# tests/test_save.py
import json
from src.core.game_state import GameState
from src.core.save_manager import save_game, load_game

def test_save_roundtrip(tmp_path):
    gs = GameState()
    gs.day = 3
    gs.flags["x"] = True
    p = tmp_path / "s.json"
    save_game(gs, str(p))
    gs2 = load_game(str(p), None)
    assert gs2.day == 3
    assert gs2.flags.get("x") is True
```

- [ ] **Step 2: Run to verify fail** → FAIL.

- [ ] **Step 3: Implement** save_manager (player serialization, defaults, rng seed).

- [ ] **Step 4: Run tests** → PASS.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: JSON save/load with defaults and seed persistence"
```

---

### Task 14: UI Renderer — palette, safe_box, HUD, bars

**Files:**
- Create: `src/ui/renderer.py`, `src/ui/hud.py`, `src/ui/animation.py`
- Create: `tests/test_renderer.py`

**Interfaces:**
- Produces:
  - `renderer.ANSI = {"white":"\033[37m","cyan":"\033[36m","green":"\033[32m","red":"\033[31m","yellow":"\033[33m","magenta":"\033[35m","blue":"\033[34m","gray":"\033[90m","reset":"\033[0m"}`
  - `renderer.supports_unicode()` -> bool (TERM set and not "dumb", plus legacy windows heuristic).
  - `renderer.box(text, border_style="normal") -> str` — box-drawing if supported else `+-+`/`|`.
  - `renderer.bar(current, total, width=14) -> str` (`████░░` style, fill = `█`).
  - `hud.render(player, game_state) -> str`.
  - `animation.progress(label, duration_seconds)` — print `label` + progressive `█` bar (no sleep in tests; keep pure: accepts frame callback).

- [ ] **Step 1: Write failing test**

```python
# tests/test_renderer.py
from src.ui.renderer import bar

def test_bar_fraction():
    assert bar(50, 100, width=4) == "██░░"
```

- [ ] **Step 2: Run to verify fail** → FAIL.

- [ ] **Step 3: Implement** renderer (ANSI, supports_unicode, box with fallback, bar), hud, animation.

- [ ] **Step 4: Run tests** → PASS.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: UI renderer, HUD, bars, safe_box ASCII fallback"
```

---

### Task 15: UI Views — menu, combat, inventory, dialog

**Files:**
- Create: `src/ui/menu.py`, `src/ui/combat_view.py`, `src/ui/inventory_view.py`, `src/ui/dialog_view.py`
- Create: `tests/test_views.py`
- Create: `src/engine/command_parser.py`

**Interfaces:**
- Produces:
  - `command_parser.parse_input(text) -> str` — trims, lowercases; maps number→action name for combat menu (e.g. "1"→"attack").
  - `menu.render_main(selection) -> str` (New Game / Continue / Settings / Credits / Exit), `menu.arrow(idx, total) -> int` (prev/next).
  - `menu.render_class_card(class_data) -> str` (ASCII stat bars from `stat_bars`).
  - `combat_view.render(state) -> str` (enemy block, player block, 7 actions, observe info).
  - `inventory_view.render(player) -> str` (equipment, consumables, materials).
  - `dialog_view.render(dialog, game_state) -> str` (speaker + boxed lines + numbered choices).

- [ ] **Step 1: Write failing test**

```python
# tests/test_views.py
from src.engine.command_parser import parse_input

def test_parse_number_to_action():
    assert parse_input("1") == "1"
    assert parse_input(" attack ") == "attack"
```

- [ ] **Step 2: Run to verify fail** → FAIL.

- [ ] **Step 3: Implement** command_parser + 4 views.

- [ ] **Step 4: Run tests** → PASS.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: UI views (menu/combat/inventory/dialog) + command parser"
```

---

### Task 16: Game orchestration + launcher

**Files:**
- Create: `src/core/game.py`, `launcher.py`
- Create: `tests/test_game_flow.py`
- Modify: `src/core/game_context.py` (load dialogues, factions, memories)

**Interfaces:**
- Produces:
  - `game.Game(game_context)` — owns GameState; method `run_turn(command) -> str` (renders result + next prompt); handles save/load, rest, travel, talk, combat loop, quest updates, memory grants.
  - `game.Game.new_game(name, class_id)` / `game.Game.continue_game(save_path)`.
  - `launcher.py` — main menu loop, calls Game; catches SaveError, ContentError, KeyboardInterrupt (exit cleanly).
  - Boot sequence text + name input + class selection via views.

- [ ] **Step 1: Write failing test** (happy path: new game → travel to forest → encounter → victory → save).

```python
# tests/test_game_flow.py
from src.core.game_context import GameContext
from src.core.game import Game

def test_new_game_and_save(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    out = g.run_turn("status")
    assert "Rian" in out
```

- [ ] **Step 2: Run to verify fail** → FAIL.

- [ ] **Step 3: Implement** Game orchestration wiring all systems + launcher loop.

- [ ] **Step 4: Run full test suite** → all PASS.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: game orchestration + launcher, MVP vertical slice playable"
```

---

### Task 17: Full Arc 1 content integration

**Files:**
- Create: `data/story/arc1_text.json` (narration strings in Bahasa Indonesia)
- Modify: `data/npc/*`, `data/dialogues/*`, `data/quests/*`, `data/events/*`, `assets/ascii/*`
- Create: `tests/test_arc1_content.py`

**Interfaces:**
- Produces: playable Arc 1 — intro boot, name/class, wake scene, mentor, quest001, side quest002, memory001 from old_man, forest encounters, quest completions, Timeline Divergence hint at end.

- [ ] **Step 1: Write failing test** — assert every content JSON validates (all require_keys) and every cross-reference resolves (quest rewards, dialog `next`, map exits, npc dialogs, class starting_skills point to existing skills).

```python
# tests/test_arc1_content.py
def test_content_references_resolve():
    from src.core.game_context import GameContext
    ctx = GameContext(data_dir="data")
    for cid, cls in ctx.classes.items():
        for s in cls.get("starting_skills", []):
            assert s in ctx.skills, f"{cid} missing skill {s}"
    for mid, m in ctx.maps.items():
        for e in m.get("exits", []):
            assert e in ctx.maps, f"{mid} bad exit {e}"
```

- [ ] **Step 2: Run to verify fail** → FAIL until content complete.

- [ ] **Step 3: Write all Arc 1 content** (Indonesian text) + fix any schema gaps surfaced.

- [ ] **Step 4: Run full suite** → PASS.

- [ ] **Step 5: Manual smoke** — `python launcher.py` plays through Arc 1.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat: complete Arc 1 content in Bahasa Indonesia"
```

---

### Task 18: Docs + final polish

**Files:**
- Create: `README.md` (full), `requirements.txt` (pytest marker)
- Modify: `.gitignore` (ensure saves/logs ignored)

- [ ] **Step 1: Write README** — install, run, controls, architecture summary, content-authoring guide.
- [ ] **Step 2: Full test run + lint smoke** — `pytest tests/ -v`, `python -m py_compile src/**/*.py launcher.py`.
- [ ] **Step 3: Final commit** — `git add -A && git commit -m "docs: README + final polish"`.

---

## Self-Review Notes

- Spec coverage: Tasks 0–18 map to all 8 milestones; every Global Constraint is enforced by a dedicated test (determinism via Randomizer fixture, safe_box in Task 14, 7 actions in Task 7, manual leveling in Task 6, XP curve in Task 4).
- Type consistency: `player.attribute_bonuses` is the single mutation point for leveling (Task 6) AND equipment (Task 9) AND is consumed by `total_stats`/`derived_stats`. Keep that key name stable.
- `enemy_turn` is imported in the Task 7 test (see Step 1 import line).
