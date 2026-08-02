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
- Leveling manual; XP curve `xp_to_next(level) = 50 * level`; damage variance `random(0,5)`; initiative variance `random(0,5)`.
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

### Task 7: Combat Engine — turn loop + 7 actions

**Files:**
- Create: `src/engine/combat_engine.py`, `src/systems/status_system.py`
- Create: `tests/test_combat.py`, `tests/test_status.py`

**Interfaces:**
- Produces:
  - `status_system.Status(duration, power, source)` and `status_system.tick_statuses(actor, randomizer) -> list[str]` (returns messages).
  - `combat_engine.CombatState(round_no, turn_order, current_index, over, result, log: list[str], observe_used)`
  - `combat_engine.start_combat(player, enemy, randomizer) -> CombatState`
  - `combat_engine.player_action(state, action, choice=None)` — dispatch:
    - attack/skill/magic → `combat_engine.resolve_hit(state, attacker_stats, defender, power, is_magic, effects)`
    - item → `combat_engine.use_item(state, item)` — consumes, heals.
    - observe → fills `state.observe_info` (intel-tier text), free action.
    - escape → roll `50 + agility - enemy_agility`; fail → enemy free attack.
    - defend → sets `state.defending=True`.
  - `combat_engine.enemy_turn(state)` — enemy uses basic attack or skill from pool.
  - `combat_engine.next_turn(state)` — advance, apply status ticks, check end.
  - Victory result contains `xp`, `gold`, `loot` items list.
  - Magic damage: `power + intelligence*0.5 - magic_resistance`; enemy magic_resistance = int*0.6.

- [ ] **Step 1: Write failing tests** (physical attack miss/crit, defend halves, escape success/fail, poison ticks, magic formula, observe tiers, victory loot).

```python
# tests/test_combat.py
from src.engine.combat_engine import start_combat, player_action, enemy_turn, next_turn
from src.models.player import Player
from src.models.enemy import Enemy
from src.core.randomizer import Randomizer

def test_victory_gives_rewards():
    p = Player("R", "warrior", 100, 10, {"attack":12,"defense":14,"hp":100,"mp":10,"agility":8,"intelligence":7})
    e = Enemy("goblin", "Goblin", 2, {"attack":5,"defense":2,"hp":5,"mp":0,"agility":6,"intelligence":3},
              loot=[], skills=[], lore="")
    r = Randomizer(seed=3)
    st = start_combat(p, e, r)
    for _ in range(20):
        if st.over: break
        player_action(st, "attack")
        if not st.over:
            enemy_turn(st)
        next_turn(st)
    assert st.result == "victory"
    assert st.xp > 0
```

- [ ] **Step 2: Run to verify fail** → FAIL.

- [ ] **Step 3: Implement** status_system + combat_engine per interfaces.

- [ ] **Step 4: Run tests** → PASS.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: turn-based combat engine with 7 actions and statuses"
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
  - `exploration_system.check_encounter(game_state, randomizer) -> Enemy | None` — formula `20 + threat*10` (+10 night in Forest).

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
  - `loot_system.roll_loot(enemy, randomizer, game_state) -> list[dict]` — per spec loot table; `gold` amounts via `{"min","max"}`.

- [ ] **Step 1: Write failing test**

```python
# tests/test_loot.py
from src.models.enemy import Enemy
from src.systems.loot_system import roll_loot
from src.core.randomizer import Randomizer

def test_loot_gold_range():
    e = Enemy("g", "Goblin", 2, {"attack":5,"defense":2,"hp":5,"mp":0,"agility":6,"intelligence":3},
              loot=[{"item":"gold","chance":100,"amount":{"min":5,"max":15}}], skills=[], lore="")
    r = Randomizer(seed=9)
    drops = roll_loot(e, r, None)
    gold = next(d for d in drops if d["item"]=="gold")
    assert 5 <= gold["amount"] <= 15
```

- [ ] **Step 2: Run to verify fail** → FAIL.

- [ ] **Step 3: Write item/enemy JSON** files per spec schema.

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
