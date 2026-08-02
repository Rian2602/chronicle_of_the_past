# Chronicle of the Past — Design Spec (MVP Arc 1)

> **For agentic workers:** This is the validated design. The implementation
> plan lives in `docs/superpowers/plans/`. Every implementation task derives
> its requirements from this spec; the Global Constraints section below is
> binding.

**Goal:** A lightweight, deterministic, rule-based CLI text RPG in Python
(stdlib only) where a person from the future wakes up in a medieval fantasy
past and must decide whether changing history is worth destroying the future.

**Architecture:** Data-driven. All game content (classes, enemies, items,
skills, quests, NPCs, dialogues, events, areas) lives as JSON under `data/`.
Python in `src/` is a generic engine that reads JSON and executes rules.
Engines/systems never reference specific content IDs; they operate on
GameState. UI is read-only and never mutates state.

**Tech Stack:** Python 3.12+ stdlib only. pytest for tests. No third-party
runtime dependencies. No API keys, no LLM, no database.

---

## Global Constraints

- **Language:** All game text (UI, dialog, narration, errors) is Bahasa Indonesia.
- **Dependencies:** stdlib only at runtime. `pytest` is the only dev dependency.
- **Rendering:** ANSI escape codes + box-drawing Unicode (`╔ ═ ╗ ┌ ─ ┐ │ └ ┘ █ ░`).
  A `safe_box` mechanism in `ui/renderer.py` downgrades to ASCII borders
  (`+-+`, `|`, `-`) when the terminal cannot render Unicode (legacy Windows /
  `TERM` not set). Never use heavy Unicode glyphs like emoji or math symbols.
- **Determinism:** All randomness goes through `core/randomizer.py` wrapping a
  seeded `random.Random`. The seed is stored in every save file. No module-level
  `random` calls.
- **No globals:** No module-level mutable game state. GameState is constructed
  once in `core/game.py` and passed explicitly (dependency injection) to
  engines/systems/UI.
- **Dependency direction:** `ui/*` never imports `engine/*`. `engine/*` never
  imports `ui/*`. Everything may depend on `core/*`, `models/*`, `systems/*`.
  Systems communicate through GameState, not by importing each other.
- **Generic engine:** No Python code may contain specific content names
  (e.g., `warrior`, `goblin`, `Ashen Village`, quest IDs). All such strings
  come from JSON via utils/json_loader.py. Tests may use content IDs.
- **Content schema:** Every JSON content file must validate against its schema
  in utils/validator.py; invalid content raises a clear error at load time.
- **Save:** JSON, three logical layers (game_data read-only references,
  player_save, engine_state). Saved under `saves/`. Missing/newer content keys
  fall back to defaults so old saves never crash.
- **Combat actions (7):** Attack, Skill, Magic, Item, Observe, Escape, Defend.
  All 7 must be present and renderable.
- **Factions (6):** Royal Army, Church, Rebels, Merchant Guild, Scholar
  Society, Ancient Order. Reputation tracked per faction plus a `crime` track.
- **Regions (8, canonical):** Village, Forest, Capital, Academy, Ancient Ruins,
  Dungeon, Temple, Forbidden Land. MVP ships Village (Region 1) and Forest
  (Region 2). Arcs map to regions (see Story section).
- **Leveling:** Manual. No auto-upgrade. Player picks one of: +2 Attack,
  +2 Defense, +2 Agility, +2 Intelligence, +15 HP, +10 MP, +1 Skill Point.
- **XP curve:** `xp_to_next(level) = 50 * level` where `level` is the current
  level before the increase (level 1→2 costs 50 XP, 2→3 costs 100 XP, etc.).
- **Random ranges:** Damage variance is `random(0, 5)` inclusive (0–5).
  Initiative variance is `random(0, 5)` inclusive.
- **Stats:** Derived stats are computed only from base stats + level by
  formulas in this spec; never stored, always computed.

---

## Player / Class / Stat System

### Base stats (final numbers, go directly into JSON)

| Stat | Warrior | Ranger | Mage | Assassin | Scholar |
|------|---------|--------|------|----------|---------|
| attack | 12 | 13 | 8 | 15 | 8 |
| defense | 14 | 8 | 6 | 6 | 10 |
| hp | 100 | 75 | 60 | 65 | 75 |
| mp | 10 | 20 | 55 | 12 | 45 |
| agility | 8 | 15 | 9 | 15 | 10 |
| intelligence | 7 | 11 | 15 | 11 | 16 |

Class identity bonuses (enforced by rule engine, not hardcoded per class):
- Warrior: frontline specialist (higher HP/defense already reflected).
- Ranger: mobility.
- Mage: spell damage.
- Assassin: critical and dodge.
- Scholar: XP +20%, bonus dialog options, bonus quest rewards, bonus
  discovery. Scholar's history skills open dialog.

### Derived stats (level = L, always computed, never stored)

| Derived stat | Formula |
|---|---|
| critical | agility × 0.4 (percent) |
| dodge | agility × 0.3 (percent) |
| accuracy | 90 + agility × 0.3 (percent) |
| magic_resistance | intelligence × 0.6 |
| physical_resistance | defense × 0.4 |
| mana_regen | intelligence × 0.2 per turn |
| hp_regen | 1 + L per turn |
| casting_speed | intelligence × 0.3 |
| initiative | agility + random(0,5) |
| carry_capacity | 30 + L × 2 |

### Character model fields

`player.json` save layer: name, class_id, level, xp, gold, hp, mp (current),
attribute_bonuses dict, skill_points, equipped {weapon,armor,helmet,accessory},
inventory list, reputation dict (6 factions + crime), relationship dict,
flags dict, quests {active, completed}, memories list, learned_skills list.

---

## Class JSON schema (data/classes/<id>.json)

```json
{
  "id": "warrior",
  "name": "Warrior",
  "description": "Spesialis garis depan.",
  "base_stats": {
    "attack": 12, "defense": 14, "hp": 100, "mp": 10,
    "agility": 8, "intelligence": 7
  },
  "xp_bonus": 1.0,
  "starting_skills": ["slash"],
  "stat_bars": {"attack": 4, "defense": 5, "hp": 5, "mp": 1, "agility": 2, "intelligence": 1}
}
```

---

## Combat System

- Turn-based. Turn order by initiative (descending): `agility + random(0,5)`.
- 7 actions: Attack, Skill, Magic, Item, Observe, Escape, Defend.
- **Attack**: `damage = attack - floor(defense/2) + random(0,5)`.
  Accuracy check: `random(0,100) < accuracy`. Miss → no damage, "seranganmu meleset!".
  Critical: `random(0,100) < critical` → `damage × 1.5`.
- **Skill**: from `data/skills/`, costs MP, may apply status effects.
- **Magic**: `damage = magic_power - magic_resistance`; magic_power derived from
  intelligence + skill power. Costs MP.
- **Item**: use consumable from inventory (heal etc.), consumes one use.
- **Observe**: info revealed scales with intelligence tier:
  - INT < 8: enemy name + HP bar only.
  - INT 8–12: + weakness.
  - INT 13–15: + resistance + lore line.
  - INT ≥ 16: + exact HP number + hidden hint.
  Observe costs no turn (free action, once per combat per enemy).
- **Escape**: `random(0,100) < 50 + agility - enemy_agility` → success.
  On failure the enemy gets one free basic attack.
- **Defend**: halve incoming physical damage for one round; +no attack.
- **Status effects (MVP)**: poison (DoT per turn, stacks as duration),
  bleeding (DoT per turn), burn (DoT per turn). Each has duration in turns;
  effects tick at start of afflicted actor's turn.
- Victory → XP + gold + loot roll. Defeat → game over screen.

### Skill JSON schema (data/skills/<id>.json)

```json
{
  "id": "fireball",
  "name": "Fireball",
  "type": "magic",
  "cost": 12,
  "power": 22,
  "target": "enemy",
  "effects": [
    {"status": "burn", "duration": 3, "power": 4}
  ],
  "requires": {"level": 3, "skill_points": 0},
  "description": "Bola api membakar musuh."
}
```

---

## World / Time / Encounter

### Regions (8 canonical) — MVP ships Region 1 and Region 2

| # | Region | Visual theme | Border |
|---|--------|--------------|--------|
| 1 | Village (Ashen Village) | Hijau, damai | `────` |
| 2 | Forest | Hijau tua, misterius | `~~~~` |
| 3 | Capital | Kuning, megah | `====` |
| 4 | Academy | Cyan, ilmiah | `::::` |
| 5 | Ancient Ruins | Magenta, kuno | `####` |
| 6 | Dungeon | Merah, berbahaya | `!!!!` |
| 7 | Temple | Hijau pucat, sakral | `----` |
| 8 | Forbidden Land | Biru, distorsi waktu | `████` |

### Time system

- Morning → Afternoon → Evening → Night, cycling. 1 day = 8 player "action
  ticks" (each travel / rest / major action advances time; resting advances to
  next period).
- Effects: shop prices shift at Night (+10%); enemy pool changes by time
  (Forest: Night spawns wolves more often); some NPCs only appear at certain
  times.
- Rest action in village: heals full HP/MP and advances to Morning next day.

### Map JSON schema (data/maps/<id>.json)

```json
{
  "id": "village",
  "name": "Ashen Village",
  "region": 1,
  "threat_level": 0,
  "description": "Desa kecil di tepi hutan.",
  "ascii_art": "village.txt",
  "exits": ["forest", "village_square"],
  "npcs": ["old_man", "village_chief"],
  "enemy_pool": [],
  "time_effects": {}
}
```

### Encounter

- Rule-based, not random-walk. Entering a dangerous area rolls an encounter
  check influenced by threat_level and time. Formula:
  `encounter_chance = 20 + threat_level*10`, adjusted: Night in Forest +10.
  Roll `random(0,100) < chance` → encounter. Encountered enemy sampled from
  `enemy_pool` (weighted). Reaching village rest spots resets encounter state.

---

## Items / Loot / Inventory

### Slots & types
- Equipment: weapon, armor, helmet, accessory. Consumable. Quest item. Material.
- Modifiers: item may add/subtract stats (e.g., Iron Sword +8 attack −1 agility).
- Carry capacity: `30 + L × 2`. Exceeding blocks pickup.

### Item JSON schema (data/items/<id>.json)

```json
{
  "id": "iron_sword",
  "name": "Iron Sword",
  "type": "weapon",
  "slot": "weapon",
  "modifiers": {"attack": 8, "agility": -1},
  "price": 60,
  "description": "Pedang besi sederhana."
}
```

### Loot table (in enemy JSON)

```json
"loot": [
  {"item": "gold", "chance": 60, "amount": {"min": 5, "max": 15}},
  {"item": "herb", "chance": 25, "amount": 1}
]
```

Roll once per item, in listed order. Deterministic via seeded RNG.

---

## Quest & Memory System

### Quest JSON schema (data/quests/<id>.json)

```json
{
  "id": "quest001",
  "title": "Temui Kepala Desa",
  "type": "main",
  "description": "Bicaralah dengan Kepala Desa.",
  "requirements": [
    {"kind": "talk", "target": "village_chief"}
  ],
  "rewards": {"xp": 50, "gold": 20, "reputation": {"village": 10}},
  "flags_on_complete": "quest001_done",
  "next": "quest002"
}
```

### Memory System
- Player holds Memory Fragments. Each fragment is a JSON entry that sets one
  or more flags (`knows_secret_X = True`) deterministically. Fragments open:
  new dialog options, new quests, new locations, new skills.
- Visual identity: always rendered in cyan with a bordered "MEMORY FRAGMENT
  FOUND" header.
- MVP ships 2 fragments in Arc 1.

### Memory JSON schema (data/story/memories.json entries)

```json
{
  "id": "memory001",
  "title": "Desa Terbakar",
  "text": "Aku pernah membaca... desa ini akan terbakar.",
  "flags_set": ["knows_village_burns"],
  "acquired_by": {"kind": "talk", "target": "old_man", "turn_index": 1}
}
```

---

## NPC / Dialog

### NPC JSON schema (data/npc/<id>.json)

```json
{
  "id": "old_man",
  "name": "Old Man",
  "location": "village",
  "role": "mentor",
  "relationship": {"trust": 0, "affinity": 0},
  "faction": null,
  "dialogs": ["dialog_old_man_main"]
}
```

### Dialog JSON schema (data/dialogues/<id>.json)

```json
{
  "id": "dialog_old_man_main",
  "lines": [
    {"speaker": "old_man", "text": "Kau... Aku belum pernah melihatmu."}
  ],
  "choices": [
    {"text": "Siapa Anda?", "require_flags": [], "set_flags": [], "next": "dialog_old_man_1"},
    {"text": "Saya tersesat.", "require_flags": ["knows_village_burns"], "set_flags": ["told_traveler"], "next": "dialog_old_man_2"},
    {"text": "Pergi.", "next": null}
  ]
}
```

---

## Reputation / Faction

- 6 factions: `royal_army`, `church`, `rebels`, `merchant_guild`,
  `scholar_society`, `ancient_order`. Plus `crime`.
- Reputation ∈ [-100, 100]. Changes are additive, recorded in player save.
- Example: helping merchant → `merchant_guild +15`, `crime -5` (if shady).
- High reputation in one faction may lower trust of opposing factions (rule
  defined in faction JSON: `rival` list with penalty factor).
- MVP: reputation shown in status HUD; reputation gates dialog options.

---

## Story (Arc 1 — "The Stranger")

### Arc ↔ Region mapping (all 10 arcs)

| Arc | Title | Region(s) |
|-----|-------|-----------|
| 1 | The Stranger | 1 Village |
| 2 | Finding Identity | 1–2 Village/Forest |
| 3 | History Begins | 2–3 Forest/Capital |
| 4 | The First Change | 3 Capital |
| 5 | Kingdom in Crisis | 3 Capital |
| 6 | Secrets of Time | 4 Academy |
| 7 | Another Traveler | 5 Ancient Ruins |
| 8 | Broken History | 6 Dungeon |
| 9 | The Origin | 7 Temple |
| 10 | Final Timeline | 8 Forbidden Land |

### MVP story beat sheet

1. Boot sequence ("CHRONICLE OF THE PAST", temporal error) → name input → class
   selection (5 class cards) → fade to waking up.
2. Waking scene: sounds, sky different. Mentor (Old Man) finds player.
3. Main quest `quest001`: "Temui Kepala Desa". Tutorial via gameplay: move,
   talk, inventory, save, observe.
4. Side quest: help a villager (e.g., kill wolves at Forest edge) → reputation
   + loot reward.
5. First Memory Fragment (from Old Man talk): `knows_village_burns`.
6. Forest exploration with encounters (Goblin, Wild Wolf, Bandit).
7. Arc 1 ends after `quest001` complete + side quest complete → cliffhanger
   hint of `knows_village_burns` consequence (Timeline Divergence alert).

### Endings
MVP does not ship endings; the Timeline Divergence alert system is present and
visible. Full timeline endings (Alpha/Beta/Gamma/Delta/Omega) are future arcs.

---

## UI System

### Palette (semantic, defined in assets/ui/colors.json)

| Color | Meaning |
|-------|---------|
| White | main text |
| Cyan | system info / memory |
| Green | normal status |
| Red | danger |
| Yellow | quest |
| Magenta | magic |
| Blue | timeline |
| Gray | narration |

### Components (ui/)
- renderer.py: ANSI helpers, safe_box border (auto ASCII downgrade), box, bar.
- hud.py: name/class/Lv/HP/MP/Gold/location/time header + HP/MP/EXP bars.
- menu.py: main menu + arrow navigation + class cards.
- combat_view.py: combat layout (enemy block / player block / 7 actions).
- inventory_view.py: equipment + consumables + materials.
- dialog_view.py: NPC name + boxed line + numbered choices.
- ascii_loader.py: loads assets/ascii/*.txt, prints on first visit / Observe.
- animation.py: simple progressive bar animations (init, saving, level up).
- borders.json / colors.json: per-region border style + color mapping.

### Layout
Header (game title bar) → narrative block (center) → action choices (bottom).
Narrative always separated by blank lines, not too dense.

---

## Save System

`core/save_manager.py`. Save JSON structure:

```json
{
  "version": 1,
  "player": {...},
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

- Save on demand (menu) and auto-save after major milestones (quest complete,
  level up, rest).
- Load: validate version; missing keys → defaults (player attributes, flags,
  reputation) so old/new content never crashes.
- Game data (`data/*.json`) is read-only at runtime; never written by game.

---

## Project Structure

```
chronicle_of_the_past/
├── launcher.py
├── requirements.txt        # empty (stdlib) — dev: pytest
├── README.md
├── assets/ascii/ village.txt forest.txt
├── assets/ui/ borders.json colors.json
├── data/ classes/ enemies/ items/ skills/ maps/ npc/ quests/ events/
│        story/ dialogues/ factions/ timeline/ config/
├── saves/
├── logs/
├── tests/
├── docs/superpowers/specs/  (this file)
├── docs/superpowers/plans/
└── src/
    ├── core/ game.py game_state.py game_context.py constants.py
    │         config.py randomizer.py save_manager.py
    ├── engine/ world_engine.py combat_engine.py story_engine.py
    │           event_engine.py dialog_engine.py quest_engine.py
    │           rule_engine.py time_engine.py command_parser.py
    ├── systems/ inventory_system.py equipment_system.py level_system.py
    │            reputation_system.py relationship_system.py memory_system.py
    │            travel_system.py exploration_system.py loot_system.py
    │            status_system.py
    ├── ui/ renderer.py menu.py combat_view.py inventory_view.py
    │        dialog_view.py hud.py ascii_loader.py animation.py
    ├── models/ player.py enemy.py npc.py item.py quest.py map.py
    │           event.py skill.py
    └── utils/ json_loader.py validator.py logger.py dice.py helpers.py
```

Note: `command_parser.py` lives in `src/engine/` (input → intent mapping used
by views).

---

## Error Handling & Testing

- Invalid JSON content → raises `ContentError` at load with file path and key.
- JSON schema violations → `SchemaError` at load (validator.py).
- Save corruption → friendly error, offers "start new game", never crashes.
- Unknown command in UI → re-prompt with hint.
- Tests: pytest, one test file per system/engine under tests/. Deterministic
  tests use fixed seeds via randomizer. TDD: write failing test, run, implement
  minimal, run pass, commit per step.

---

## Out of Scope (future arcs)

Endings/Timelines, New Game+, full skill trees, crafting, weather system,
full faction conflict events, all regions beyond Forest. The engine is built
generically so these are content additions only.
