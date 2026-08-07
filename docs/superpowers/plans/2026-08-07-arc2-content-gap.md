# Arc 2 Content Gap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create 13 new JSON data files (1 enemy, 3 techniques, 3 consumable pills, 3 pill recipes, 2 artifacts, 1 companion) to satisfy the GDD §22 content targets for Arc 2, bringing Fase 2 to 100% completion.

**Architecture:** Pure data additions (JSON) in the `data/` folder following established schemas. No Python code changes needed. We will use the existing `tools/validate.py` to ensure schema integrity and referential validity.

**Tech Stack:** JSON, pytest, Python (for validation script)

## Global Constraints

All content MUST be in Bahasa Indonesia.
All file names and IDs MUST be in `snake_case`.
All references between files MUST be valid.
Target tier for these additions is `golden_core` (Kristal Emas - Arc 2 tier).

---

### Task 1: Pembunuh Gilda (Enemy)

**Files:**
- Create: `data/enemies/pembunuh_gilda.json`

**Interfaces:**
- Produces: `pembunuh_gilda` (id)

- [ ] **Step 1: Write the JSON implementation**

```json
{
  "id": "pembunuh_gilda",
  "name": "Pembunuh Bayaran Gilda",
  "tier": "golden_core",
  "element": "metal",
  "behavior": "aggressive",
  "stats": {
    "attack": 32,
    "defense": 18,
    "hp": 220,
    "qi": 45
  },
  "skills": [
    "qi_slash"
  ],
  "tags": ["human", "assassin"],
  "requires_flag": "map_guild_city_unlocked"
}
```

- [ ] **Step 2: Run validator to verify schema**

Run: `python3 tools/validate.py`
Expected: PASS (OK: semua data valid...)

- [ ] **Step 3: Run tests to verify logic**

Run: `pytest -q tests/test_enemy_data.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add data/enemies/pembunuh_gilda.json
git commit -m "data(enemy): tambah pembunuh_gilda untuk Arc 2"
```

---

### Task 2: Teknik Baru (3 Teknik)

**Files:**
- Create: `data/techniques/jaring_jiwa.json`
- Create: `data/techniques/jarum_racun.json`
- Create: `data/techniques/perisai_cahaya.json`

**Interfaces:**
- Produces: `jaring_jiwa`, `jarum_racun`, `perisai_cahaya`

- [ ] **Step 1: Write `data/techniques/jaring_jiwa.json`**

```json
{
  "id": "jaring_jiwa",
  "name": "Jaring Jiwa",
  "path": "soul",
  "element": "water",
  "type": "technique",
  "qi_cost": 12,
  "power": 0,
  "effects": [
    {"type": "status", "status": "stun", "chance": 100}
  ],
  "requires": {
    "tier": "golden_core"
  }
}
```

- [ ] **Step 2: Write `data/techniques/jarum_racun.json`**

```json
{
  "id": "jarum_racun",
  "name": "Jarum Racun",
  "path": "alchemy",
  "element": "wood",
  "type": "technique",
  "qi_cost": 10,
  "power": 15,
  "effects": [
    {"type": "status", "status": "poison", "chance": 80}
  ],
  "requires": {
    "tier": "golden_core"
  }
}
```

- [ ] **Step 3: Write `data/techniques/perisai_cahaya.json`**

```json
{
  "id": "perisai_cahaya",
  "name": "Perisai Cahaya",
  "path": "formation",
  "element": "metal",
  "type": "technique",
  "qi_cost": 15,
  "power": 0,
  "effects": [
    {"type": "status", "status": "barrier", "chance": 100}
  ],
  "requires": {
    "tier": "golden_core"
  }
}
```

- [ ] **Step 4: Run validator to verify schema**

Run: `python3 tools/validate.py`
Expected: PASS

- [ ] **Step 5: Run tests**

Run: `pytest -q tests/test_technique_data.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add data/techniques/*.json
git commit -m "data(technique): tambah 3 teknik baru untuk Arc 2"
```

---

### Task 3: Item Baru (Artefak & Pil Konsumsi)

**Files:**
- Create: `data/items/pil_racun_meridian.json`
- Create: `data/items/pil_baja_tubuh.json`
- Create: `data/items/pil_langkah_angin.json`
- Create: `data/items/jubah_bayangan.json`
- Create: `data/items/gelang_qi.json`

**Interfaces:**
- Produces: 3 consumable pills, 2 artifacts (needed for Task 4 recipes)

- [ ] **Step 1: Write `data/items/pil_racun_meridian.json`**

```json
{
  "id": "pil_racun_meridian",
  "name": "Pil Racun Meridian",
  "type": "consumable",
  "description": "Racun pekat yang merusak aliran qi.",
  "price": 100,
  "effect": {
    "status_inflict": "poison"
  }
}
```

- [ ] **Step 2: Write `data/items/pil_baja_tubuh.json`**

```json
{
  "id": "pil_baja_tubuh",
  "name": "Pil Baja Tubuh",
  "type": "consumable",
  "description": "Mengeraskan kulit seperti baja.",
  "price": 150,
  "effect": {
    "status_inflict": "strengthen"
  }
}
```

- [ ] **Step 3: Write `data/items/pil_langkah_angin.json`**

```json
{
  "id": "pil_langkah_angin",
  "name": "Pil Langkah Angin",
  "type": "consumable",
  "description": "Membuat tubuh seringan bulu.",
  "price": 150,
  "effect": {
    "status_inflict": "haste"
  }
}
```

- [ ] **Step 4: Write `data/items/jubah_bayangan.json`**

```json
{
  "id": "jubah_bayangan",
  "name": "Jubah Bayangan",
  "type": "artifact",
  "description": "Jubah tenunan benang roh gelap yang sulit dideteksi mata.",
  "price": 400,
  "effect": {
    "resist_dark": 10,
    "buff_agility": 5
  }
}
```

- [ ] **Step 5: Write `data/items/gelang_qi.json`**

```json
{
  "id": "gelang_qi",
  "name": "Gelang Qi",
  "type": "artifact",
  "description": "Membantu menstabilkan kapasitas qi penggunanya.",
  "price": 500,
  "effect": {
    "buff_qi_max": 20
  }
}
```

- [ ] **Step 6: Run validator to verify schema**

Run: `python3 tools/validate.py`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add data/items/pil_*.json data/items/jubah_bayangan.json data/items/gelang_qi.json
git commit -m "data(item): tambah 3 pil dan 2 artefak baru Arc 2"
```

---

### Task 4: Resep Pil

**Files:**
- Create: `data/items/resep_pil_racun.json`
- Create: `data/items/resep_pil_baja.json`
- Create: `data/items/resep_pil_angin.json`

**Interfaces:**
- Consumes: `pil_racun_meridian`, `pil_baja_tubuh`, `pil_langkah_angin`, `herb_qi`
- Produces: 3 recipe items

- [ ] **Step 1: Write `data/items/resep_pil_racun.json`**

```json
{
  "id": "resep_pil_racun",
  "name": "Resep Pil Racun Meridian",
  "type": "recipe",
  "description": "Mengajarkan cara meracik Pil Racun Meridian.",
  "price": 200,
  "effect": {
    "learn_recipe": "pil_racun_meridian"
  },
  "recipe": [
    {"item": "herb_qi", "qty": 3},
    {"item": "beast_core_1", "qty": 1}
  ]
}
```

- [ ] **Step 2: Write `data/items/resep_pil_baja.json`**

```json
{
  "id": "resep_pil_baja",
  "name": "Resep Pil Baja Tubuh",
  "type": "recipe",
  "description": "Mengajarkan cara meracik Pil Baja Tubuh.",
  "price": 250,
  "effect": {
    "learn_recipe": "pil_baja_tubuh"
  },
  "recipe": [
    {"item": "ore_iron", "qty": 2},
    {"item": "herb_qi", "qty": 2}
  ]
}
```

- [ ] **Step 3: Write `data/items/resep_pil_angin.json`**

```json
{
  "id": "resep_pil_angin",
  "name": "Resep Pil Langkah Angin",
  "type": "recipe",
  "description": "Mengajarkan cara meracik Pil Langkah Angin.",
  "price": 250,
  "effect": {
    "learn_recipe": "pil_langkah_angin"
  },
  "recipe": [
    {"item": "dew_morning", "qty": 3},
    {"item": "herb_qi", "qty": 1}
  ]
}
```

- [ ] **Step 4: Run validator to verify schema**

Run: `python3 tools/validate.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add data/items/resep_*.json
git commit -m "data(recipe): tambah 3 resep pil baru Arc 2"
```

---

### Task 5: Binatang Roh

**Files:**
- Create: `data/companions/macan_baja.json`

**Interfaces:**
- Consumes: `qi_slash` (technique id)
- Produces: `macan_baja` companion

- [ ] **Step 1: Write `data/companions/macan_baja.json`**

```json
{
  "id": "macan_baja",
  "name": "Macan Baja",
  "tier": "golden_core",
  "element": "metal",
  "stats": {
    "attack": 25,
    "defense": 30,
    "hp": 300,
    "qi": 20
  },
  "skills": [
    "qi_slash"
  ],
  "bond_xp": 0,
  "rank": 1
}
```

- [ ] **Step 2: Run validator to verify schema**

Run: `python3 tools/validate.py`
Expected: PASS

- [ ] **Step 3: Run full test suite**

Run: `pytest -q`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add data/companions/macan_baja.json
git commit -m "data(companion): tambah Macan Baja untuk Arc 2"
```

---
