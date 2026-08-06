# Variasi Data Arc 1 + Fondasi Arc 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Memperkaya data game dengan variasi tinggi (musuh, teknik, item, quest, NPC, peta) mengikuti GDD & arsitektur yang ada, ter-integrasi penuh ke alur Arc 1 aktif + fondasi Arc 2, siap di-merge agent lain.

**Architecture:** Perluas loader item + command `use` (luar combat, tanpa sentuh `combat.py`/`cultivation.py`/`player.py`). Semua data baru (musuh/teknik/item/quest/NPC/peta) memakai skema & mekanisme integrasi yang sudah ada: map `enemies` spawn, `event` chain (`start_quest`/`grant_item`/`unlock_map`), quest reward, NPC `talk`, teknik otomatis dari tier.

**Tech Stack:** Python 3.12+, Rich/Textual (dipakai), stdlib, pytest, ruff (Google style ≤80), JSON data-driven.

## Global Constraints

- TDD wajib: RED → GREEN → REFACTOR → commit (AGENTS §2.1); data JSON diuji dulu sebelum ditambah.
- `pytest -q`, `ruff check`, `ruff format --check`, `python tools/validate.py` wajib hijau sebelum DoD (§1, §12).
- `graphify update .` wajib setelah ubah engine (§4.3).
- Data eksisting **DILARANG** dihapus/diganti; hanya ditambah (§6).
- Bahasa Indonesia untuk semua `name/description/text`; nada **grimdark** (GDD §3.6).
- Siklus elemen Metal→Kayu→Tanah→Air→Api→Metal konsisten (GDD §6.2); jalur `spirit` = GDD `soul`.
- Flag quest otomatis `quest<id>_done`; **DILARANG** flag paralel (§11).
- Teknik `type` hanya `physical`/`technique` (test membatasi; tidak ada `buff`).
- Baris ≤80; docstring Google-style (header English, isi Indonesia).
- Tidak ada dependency baru; **TIDAK menyentuh** `combat.py`, `cultivation.py`, `models/player.py` (stabil, §6).
- Tidak mengubah GDD §24.1; tidak mengubah schema save.

---

### Task 1: Loader Item Diperluas (schema type/description/effect)

**Files:**
- Modify: `src/engine/items.py:17-33`
- Test: `tests/test_items.py` (BARU)

**Interfaces:**
- Consumes: file JSON `data/items/*.json` (schema lama: `id`+`name`; skema baru opsional `type`/`description`/`effect`).
- Produces: `load_items(data_dir=ITEM_DIR) -> dict[str, dict[str, Any]]` — tiap item berisi `id`, `name` (wajib) + `type`/`description`/`effect` (default). Dipakai validator (sudah), `_cmd_inventory`, dan `_cmd_use` (Task 2).

- [ ] **Step 1: Write the failing test** — buat `tests/test_items.py`:

```python
"""Validasi loader item & skema effect (GDD §14.2, §7)."""

import json
from pathlib import Path

from src.engine.items import load_items


def test_load_items_membaca_field_effect(tmp_path):
    """Loader item wajib membawa field type/description/effect."""
    item_dir = tmp_path / "items"
    item_dir.mkdir()
    (item_dir / "pil_uji.json").write_text(
        json.dumps(
            {
                "id": "pil_uji",
                "name": "Pil Uji",
                "type": "consumable",
                "description": "Uji.",
                "effect": {"heal_hp": 20},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    items = load_items(item_dir)
    assert items["pil_uji"]["name"] == "Pil Uji"
    assert items["pil_uji"]["type"] == "consumable"
    assert items["pil_uji"]["description"] == "Uji."
    assert items["pil_uji"]["effect"] == {"heal_hp": 20}


def test_load_items_item_tanpa_effect_tetap_lolos(tmp_path):
    """Item lama (id+name saja) tidak boleh rusak (kompatibilitas)."""
    item_dir = tmp_path / "items"
    item_dir.mkdir()
    (item_dir / "pil_lama.json").write_text(
        json.dumps({"id": "pil_lama", "name": "Pil Lama"}),
        ensure_ascii=False,
    )
    items = load_items(item_dir)
    assert items["pil_lama"]["name"] == "Pil Lama"
    assert items["pil_lama"].get("effect") is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_items.py -q`
Expected: FAIL — `load_items` mengembalikan hanya `id`/`name` (type/effect hilang).

- [ ] **Step 3: Write minimal implementation** — ganti `src/engine/items.py`:

```python
DEFAULT_TYPE = "consumable"


def load_items(data_dir: Path = ITEM_DIR) -> dict[str, dict[str, Any]]:
    """Muat semua item dari data/items/ keyed by id.

    Skema item: ``id`` dan ``name`` wajib; ``type`` (default
    "consumable"), ``description``, dan ``effect`` opsional. ``effect``
    siap dipakai combat nanti tanpa menyentuh combat.py (stabil).

    Args:
        data_dir: Direktori berisi JSON item (default data/items/).

    Returns:
        Mapping item_id -> dict berisi ``id``, ``name``, ``type``,
        ``description`` (default ""), dan ``effect`` (default None).

    Raises:
        KeyError: Jika sebuah file JSON tidak punya kunci ``id``.
    """
    items: dict[str, dict[str, Any]] = {}
    for path in sorted(data_dir.glob("*.json")):
        raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        items[raw["id"]] = {
            "id": raw["id"],
            "name": raw["name"],
            "type": raw.get("type", "consumable"),
            "description": raw.get("description", ""),
            "effect": raw.get("effect"),
        }
    return items
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_items.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/engine/items.py tests/test_items.py
git commit -m "items: perluas loader item schema type/description/effect (GDD 7)"
```

---

### Task 2: Data Item Baru (10 item, efek bervariasi)

**Files:**
- Create: 10 file di `data/items/`
- Test: `tests/test_items.py` (tambah test data dir)

**Interfaces:**
- Consumes: loader item Task 1 (field `effect`).
- Produces: item id dipakai command `use` (Task 3) dan event `grant_item` (Task 6).

- [ ] **Step 1: Write the failing test (data schema)** — tambah di `tests/test_items.py`:

```python
REQUIRED_ITEM_KEYS = {"id", "name"}


def test_data_item_semua_memenuhi_skema():
    """Item data memiliki minimal id+name; type/description/effect opsional."""
    data_dir = Path(__file__).resolve().parents[1] / "data" / "items"
    for path in data_dir.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        assert set(data) >= REQUIRED_ITEM_KEYS, f"{path.name}: kunci kurang"
        assert isinstance(data["id"], str) and data["id"] == path.stem
        assert isinstance(data["name"], str) and data["name"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_items.py::test_data_item_semua_memenuhi_skema -q`
Expected: FAIL — belum ada file item selain yang ada (skema strict belum teruji semua), atau PASS bila item ada — lanjutkan.

- [ ] **Step 3: Create the data** — contoh konten grimdark (efek bervariasi):

`data/items/pil_uji_heal.json`:
```json
{
  "id": "pil_uji_heal",
  "name": "Pil Uji Heal",
  "type": "consumable",
  "description": "Pil uji untuk test.",
  "effect": {"heal_hp": 20}
}
```
`data/items/pil_uji_buff.json`:
```json
{
  "id": "pil_uji_buff",
  "name": "Pil Uji Buff",
  "type": "consumable",
  "description": "Pil uji combat-ready.",
  "effect": {"buff_attack": 5}
}
```
`data/items/pil_pemulih_kecil.json`:
```json
{
  "id": "pil_pemulih_kecil",
  "name": "Pil Pemulih Kecil",
  "type": "consumable",
  "description": "Remasan akar purba memulihkan luka ringan. Rasa pahit takdir.",
  "effect": {"heal_hp": 25}
}
```
`data/items/pil_pemulih_besar.json`:
```json
{
  "id": "pil_pemulih_besar",
  "name": "Pil Pemulih Besar",
  "type": "consumable",
  "description": "Menyambung daging dan tulang yang hancur. Darahnya menolak.",
  "effect": {"heal_hp": 60}
}
```
`data/items/pil_qi_tenang.json`:
```json
{
  "id": "pil_qi_tenang",
  "name": "Pil Qi Tenang",
  "type": "consumable",
  "description": "Menenangkan aliran qi yang bergolak. Bisikan dalam darah mereda.",
  "effect": {"restore_qi": 20}
}
```
`data/items/pil_insight_sharif.json`:
```json
{
  "id": "pil_insight_sharif",
  "name": "Pil Pencerahan Sharif",
  "type": "consumable",
  "description": "Pecahan kesadaran yang ditinggalkan peziarah mati. Pemahaman datang dengan harga.",
  "effect": {"add_insight": 30}
}
```
`data/items/pil_buka_meridian.json`:
```json
{
  "id": "pil_buka_meridian",
  "name": "Pil Pembuka Meridian",
  "type": "consumable",
  "description": "Meridian terbakar lalu menganga. Jalan baru membuka — dan rasa sakit itu nyata.",
  "effect": {"add_meridian": 1}
}
```
`data/items/elixir_empedu_api.json`:
```json
{
  "id": "elixir_empedu_api",
  "name": "Eliksir Empedu Api",
  "type": "consumable",
  "description": "Cairan mendidih yang membuat tubuh muak terhadap racun. Combat-ready.",
  "effect": {"resist_poison": 30}
}
```
`data/items/pil_besi_hitam.json`:
```json
{
  "id": "pil_besi_hitam",
  "name": "Pil Besi Hitam",
  "type": "consumable",
  "description": "Mengeraskan kulit menjadi baja sementara. Combat-ready.",
  "effect": {"buff_defense": 30}
}
```
`data/items/pil_asar_jiwa.json`:
```json
{
  "id": "pil_asar_jiwa",
  "name": "Pil Asar Jiwa",
  "type": "consumable",
  "description": "Ditenun dari jiwa-jiwa yang padam. Memperkuat tekad — dipakai penjahat dan pahlawan.",
  "effect": {"buff_attack": 20}
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_items.py -q`
Expected: PASS.

- [ ] **Step 5: Validate + commit**

Run: `python tools/validate.py` (item baru belum di-grant — tetap valid).
```bash
git add data/items tests/test_items.py
git commit -m "data: 10 item baru skema effect (GDD 7)"
```

---

### Task 3: Command `use <item>` (luar combat)

**Files:**
- Modify: `src/core/game_loop.py` (tambah `_cmd_use`; tambah `use` di `AVAILABLE`; tambah di `_cmd_help`)
- Test: `tests/test_game_loop.py` (3 test baru)

**Interfaces:**
- Consumes: `load_items()` (Task 1, key `effect`), `state.inventory["items"]`, `state.player` (`hp`/`qi` mutable, `add_insight(amount)`, `meridian_buka`).
- Produces: handler `_cmd_use(command)` — efek non-combat diterapkan: `heal_hp`, `restore_qi`, `add_insight`, `add_meridian`; efek combat-ready diparse tapi tak dieksekusi. `dispatch` memanggil `_cmd_use` untuk perintah `use`.

- [ ] **Step 1: Write the failing test** — tambah di `tests/test_game_loop.py` (item Task 2 sudah ada di data):

```python
def test_use_pil_pemulih_memulihkan_hp(tmp_path):
    """use pil heal_hp menambah HP pemain dan mengonsumsi item."""
    session = _session(tmp_path)
    session.new_game("Akar")
    player = session.state.player
    player.hp = 10
    session.state.inventory.setdefault("items", {})["pil_uji_heal"] = 1
    lines = _dispatch(session, "use pil_uji_heal")
    assert player.hp > 10
    assert any("Pil Uji Heal" in line for line in lines)


def test_use_item_tanpa_efek_eksekusi_tetap_mengonsumsi(tmp_path):
    """Item dengan effect combat-ready konsumsi tapi tak ada stat berubah."""
    session = _session(tmp_path)
    session.new_game("Akar")
    player = session.state.player
    before = (player.hp, player.qi, player.insight, player.meridian_buka)
    session.state.inventory.setdefault("items", {})["pil_uji_buff"] = 1
    _dispatch(session, "use pil_uji_buff")
    after = (player.hp, player.qi, player.insight, player.meridian_buka)
    assert after == before
    assert session.state.inventory["items"].get("pil_uji_buff", 0) == 0


def test_use_item_tidak_ada_di_tas_memberi_error(tmp_path):
    """use item yang tidak dimiliki harus memberi pesan jelas."""
    session = _session(tmp_path)
    session.new_game("Akar")
    lines = _dispatch(session, "use pil_tidak_ada")
    assert any("tidak" in line.lower() for line in lines)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_game_loop.py -q -k use`
Expected: FAIL — tidak ada command `use` (dispatch kembalikan `UNAVAILABLE`).

- [ ] **Step 3: Write minimal implementation**

Tambah `"use"` ke set `AVAILABLE` (line ~60). Perbarui `_cmd_help` (tambah `use <item>`). Tambah handler:

```python
    def _cmd_use(self, command: Command) -> list[str]:
        """Pakai item konsumabel di luar combat (GDD §18.2).

        Efek non-combat yang didukung: heal_hp, restore_qi, add_insight,
        add_meridian. Efek lain (buff payload) diparse tapi tidak
        dieksekusi.
        """
        if not command.args:
            return ["Pakai apa? Contoh: use <nama_item>."]
        item_id = command.args[0]
        items = self.state.inventory.get("items", {})
        if items.get(item_id, 0) <= 0:
            return [f"Kamu tidak punya {item_id} di tas."]
        items[item_id] -= 1
        if items[item_id] == 0:
            del items[item_id]
        catalog = load_items()
        item = catalog.get(item_id)
        if item is None:
            return [f"Item '{item_id}' tidak dikenal di data."]
        lines = [f"Kamu memakai {item['name']}."]
        effect = item.get("effect")
        player = self.state.player
        if effect:
            if effect.get("heal_hp"):
                player.hp = min(player.hp_max, player.hp + effect["heal_hp"])
                lines.append(f"HP pulih {effect['heal_hp']}.")
            if effect.get("restore_qi"):
                player.qi = min(player.qi_max, player.qi + effect["restore_qi"])
                lines.append(f"Qi pulih {effect['restore_qi']}.")
            if effect.get("add_insight"):
                player.add_insight(effect["add_insight"])
                lines.append(f"Insight +{effect['add_insight']}.")
            if effect.get("add_meridian"):
                player.meridian_buka = min(
                    8, player.meridian_buka + effect["add_meridian"]
                )
                lines.append(
                    f"Meridian terbuka ({player.meridian_buka}/8)."
                )
            # ponytail: effect combat (buff_*) diparse tapi tak dieksekusi;
            # eksekusi saat engine combat diperluas (Fase 2).
        return lines
```

Jalankan quest/event setelah penggunaan bila perlu (pola `_cmd_cultivate`): tambahkan `+ self._run_quests() + self._run_events()` di akhir return.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_game_loop.py -q -k use`
Expected: PASS (item Task 2 sudah tersedia di data).

- [ ] **Step 5: ruff + format**

Run: `ruff check src tests && ruff format --check src tests`
Expected: bersih.

- [ ] **Step 6: Commit**

```bash
git add src/core/game_loop.py tests/test_game_loop.py
git commit -m "engine: command use item luar combat (GDD 18.2)"
```

---


---

### Task 4: Data Musuh Baru (6) + Teknik Baru (6)

**Files:**
- Create: 6 file di `data/enemies/`
- Create: 6 file di `data/techniques/`
- Modify: `tests/test_enemy_data.py` (EXPECTED_ENEMIES), `tests/test_technique_data.py` (EXPECTED_TECHNIQUES)

**Interfaces:**
- Consumes: tier `qi_condensation`/`foundation_establishment`, teknik yang dijadikan `skills`.
- Produces: enemy id + technique id — dipakai map `enemies` (Task 5/6), quest target (Task 6), dan `_get_player_techniques` (otomatis dari `requires.tier`).

- [ ] **Step 1: Update test (RED)** — `tests/test_enemy_data.py:33` tambah musuh baru:

```python
EXPECTED_ENEMIES = {
    "serigala_qi",
    "bandit_perbatasan",
    "zombie_temple",
    "penjaga_makam",
    "penjaga_arsip",
    "babi_hutan_qi",
    "pembelot_pemberontak",
    "penebus_orde_suci",
    "ular_racun_paya_sekutu",
    "penjaga_makam_muda",
    "arwah_pendendam",
    "kepiting_sangkar",
    "inkuisitor_kecil",
    "murid_sekte_bayangan",
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_enemy_data.py::test_terdapat_file_musuh_yang_diharapkan -q`
Expected: FAIL — file musuh belum ada.

- [ ] **Step 3: Create enemy data** (6 musuh, 5 elemen covered, tag/behavior bervariasi, 2 foundation):

`data/enemies/ular_racun_paya_sekutu.json` (qi, water, beast):
```json
{
  "id": "ular_racun_paya_sekutu",
  "name": "Ular Racun Paya Sekutu",
  "tier": "qi_condensation",
  "element": "water",
  "behavior": "defensive",
  "stats": {
    "attack": 6, "defense": 3, "agility": 6,
    "intelligence": 2, "vitality": 5, "spirit": 3,
    "hp": 26, "qi": 8
  },
  "skills": ["racun_meridian"],
  "tags": ["beast"],
  "rewards": {"insight": 18, "gold": 12}
}
```
`data/enemies/penjaga_makam_muda.json` (qi, wood, undead):
```json
{
  "id": "penjaga_makam_muda",
  "name": "Penjaga Makam Muda",
  "tier": "qi_condensation",
  "element": "wood",
  "behavior": "defensive",
  "stats": {
    "attack": 7, "defense": 5, "agility": 3,
    "intelligence": 3, "vitality": 6, "spirit": 4,
    "hp": 34, "qi": 10
  },
  "skills": ["perisai_tanah", "qi_slash"],
  "tags": ["undead", "guardian"],
  "rewards": {"insight": 22, "gold": 16}
}
```
`data/enemies/arwah_pendendam.json` (qi, fire, spirit):
```json
{
  "id": "arwah_pendendam",
  "name": "Arwah Pendendam",
  "tier": "qi_condensation",
  "element": "fire",
  "behavior": "aggressive",
  "stats": {
    "attack": 6, "defense": 2, "agility": 5,
    "intelligence": 4, "vitality": 4, "spirit": 7,
    "hp": 24, "qi": 12
  },
  "skills": ["seruan_jiwa", "flame_strike"],
  "tags": ["spirit"],
  "rewards": {"insight": 20, "gold": 14}
}
```
`data/enemies/kepiting_sangkar.json` (qi, earth, beast):
```json
{
  "id": "kepiting_sangkar",
  "name": "Kepiting Sangkar",
  "tier": "qi_condensation",
  "element": "earth",
  "behavior": "defensive",
  "stats": {
    "attack": 8, "defense": 7, "agility": 1,
    "intelligence": 1, "vitality": 8, "spirit": 2,
    "hp": 40, "qi": 4
  },
  "skills": ["perisai_tanah"],
  "tags": ["beast", "armored"],
  "rewards": {"insight": 24, "gold": 20}
}
```
`data/enemies/inkuisitor_kecil.json` (foundation, metal, human):
```json
{
  "id": "inkuisitor_kecil",
  "name": "Inkuisitor Kecil",
  "tier": "foundation_establishment",
  "element": "metal",
  "behavior": "aggressive",
  "stats": {
    "attack": 12, "defense": 8, "agility": 5,
    "intelligence": 6, "vitality": 8, "spirit": 5,
    "hp": 50, "qi": 18
  },
  "skills": ["tebasan_surgawi", "qi_slash"],
  "tags": ["human", "holy_order"],
  "rewards": {"insight": 40, "gold": 35}
}
```
`data/enemies/murid_sekte_bayangan.json` (foundation, water, human):
```json
{
  "id": "murid_sekte_bayangan",
  "name": "Murid Sekte Bayangan",
  "tier": "foundation_establishment",
  "element": "water",
  "behavior": "defensive",
  "stats": {
    "attack": 10, "defense": 6, "agility": 9,
    "intelligence": 7, "vitality": 7, "spirit": 6,
    "hp": 44, "qi": 22
  },
  "skills": ["es_beku", "racun_meridian"],
  "tags": ["human", "traitor"],
  "rewards": {"insight": 45, "gold": 38}
}
```

- [ ] **Step 4: Create technique data** (6 teknik, jalur & elemen bervariasi):

`data/techniques/racun_meridian.json` (alchemy, wood):
```json
{
  "id": "racun_meridian",
  "name": "Racun Meridian",
  "path": "alchemy",
  "element": "wood",
  "type": "technique",
  "qi_cost": 7,
  "power": 6,
  "effects": [{"status": "poison", "duration": 3, "power": 3}],
  "requires": {"tier": "qi_condensation"}
}
```
`data/techniques/seruan_jiwa.json` (spirit, fire):
```json
{
  "id": "seruan_jiwa",
  "name": "Seruan Jiwa",
  "path": "spirit",
  "element": "fire",
  "type": "technique",
  "qi_cost": 9,
  "power": 0,
  "effects": [{"status": "charm", "duration": 2}],
  "requires": {"tier": "qi_condensation"}
}
```
`data/techniques/perisai_tanah_padat.json` (formation, earth):
```json
{
  "id": "perisai_tanah_padat",
  "name": "Perisai Tanah Padat",
  "path": "formation",
  "element": "earth",
  "type": "technique",
  "qi_cost": 6,
  "power": 0,
  "effects": [{"status": "barrier", "duration": 3, "power": 20}],
  "requires": {"tier": "qi_condensation"}
}
```
`data/techniques/es_beku.json` (sword, water):
```json
{
  "id": "es_beku",
  "name": "Es Beku",
  "path": "sword",
  "element": "water",
  "type": "technique",
  "qi_cost": 8,
  "power": 9,
  "effects": [{"status": "freeze", "duration": 2}],
  "requires": {"tier": "foundation_establishment"}
}
```
`data/techniques/tebasan_surgawi.json` (sword, metal):
```json
{
  "id": "tebasan_surgawi",
  "name": "Tebasan Surgawi",
  "path": "sword",
  "element": "metal",
  "type": "physical",
  "qi_cost": 12,
  "power": 15,
  "effects": [{"status": "weaken", "duration": 3}],
  "requires": {"tier": "foundation_establishment"}
}
```
`data/techniques/pil_jiwa_api.json` (spirit, fire):
```json
{
  "id": "pil_jiwa_api",
  "name": "Pil Jiwa Api",
  "path": "spirit",
  "element": "fire",
  "type": "technique",
  "qi_cost": 10,
  "power": 12,
  "effects": [{"status": "burn", "duration": 3, "power": 5}],
  "requires": {"tier": "foundation_establishment"}
}
```

- [ ] **Step 5: Update EXPECTED_TECHNIQUES** — `tests/test_technique_data.py`:

```python
EXPECTED_TECHNIQUES = {
    "qi_slash",
    "flame_strike",
    "frost_bind",
    "vine_grasp",
    "earth_charge",
    "serbuan_akar",
    "perisai_tanah",
    "iblis_pedang",
    "racun_meridian",
    "seruan_jiwa",
    "perisai_tanah_padat",
    "es_beku",
    "tebasan_surgawi",
    "pil_jiwa_api",
}
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `pytest tests/test_enemy_data.py tests/test_technique_data.py -q`
Expected: PASS (validator cek `enemy.skills` → teknik ada; teknik yang dipakai musuh sudah dibuat).

- [ ] **Step 7: Validate + commit**

Run: `python tools/validate.py` — Expected: `OK`.
```bash
git add data/enemies data/techniques tests/test_enemy_data.py tests/test_technique_data.py
git commit -m "data: 6 musuh + 6 teknik variatif lintas tier (GDD 6/7/11)"
```

---

### Task 5: Integrasi Musuh ke Peta + Peta Baru (2)

**Files:**
- Modify: `data/maps/ashfall_forest.json`, `data/maps/ruin_shrine.json`
- Create: `data/maps/makam_kuno.json`, `data/maps/paya_beracun.json`
- Modify: `tests/test_map_data.py` (EXPECTED_MAPS)

**Interfaces:**
- Consumes: enemy id Task 4, `requires_flag` gating (GDD §11).
- Produces: peta `makam_kuno`/`paya_beracun` (tier 2) dengan `enemies` — di-unlock event (Task 6), dan spawn musuh di peta.

- [ ] **Step 1: Update test (RED)** — `tests/test_map_data.py` EXPECTED_MAPS:

```python
EXPECTED_MAPS = {
    "village_emberfall",
    "ashfall_forest",
    "ruin_shrine",
    "sect_azure",
    "guild_city",
    "makam_kuno",
    "paya_beracun",
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_map_data.py::test_terdapat_file_peta_yang_diharapkan -q`
Expected: FAIL — peta baru belum ada.

- [ ] **Step 3: Create/integrate map data**

`data/maps/ashfall_forest.json` — tambah musuh baru (spawn tambahan):
```json
{
  "id": "ashfall_forest",
  "name": "Hutan Perbatasan",
  "description": "Pepohonan hangus berdiri dalam diam. Lapisan abu menutupi tanah.",
  "tier": 1,
  "enemies": [
    {"enemy": "bandit_perbatasan"},
    {"enemy": "ular_racun_paya_sekutu"},
    {"enemy": "arwah_pendendam"}
  ]
}
```
`data/maps/ruin_shrine.json` — tambah musuh setelah kuil dibersihkan:
```json
{
  "id": "ruin_shrine",
  "name": "Reruntuhan Kuil",
  "description": "Batu-batu kuno berserakan. Sisa pengorbanan lama.",
  "tier": 1,
  "enemies": [
    {"enemy": "zombie_temple", "requires_flag": "quest102_done"},
    {"enemy": "penjaga_makam", "requires_flag": "ruin_shrine_cleared"},
    {"enemy": "penjaga_makam_muda", "requires_flag": "ruin_shrine_cleared"}
  ]
}
```
`data/maps/makam_kuno.json` (tier 2, foundation):
```json
{
  "id": "makam_kuno",
  "name": "Makam Kuno",
  "description": "Koridor batu berukir nama-nama yang mati sia-sia. Udara berbau tanah lembap dan dendam.",
  "tier": 2,
  "enemies": [
    {"enemy": "inkuisitor_kecil"},
    {"enemy": "murid_sekte_bayangan"}
  ]
}
```
`data/maps/paya_beracun.json` (tier 2, foundation):
```json
{
  "id": "paya_beracun",
  "name": "Paya Beracun",
  "description": "Genangan hijau bergelembungkan racun. Sesuatu menunggu di dasar paya.",
  "tier": 2,
  "enemies": [
    {"enemy": "kepiting_sangkar"},
    {"enemy": "ular_racun_paya_sekutu"}
  ]
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_map_data.py -q`
Expected: PASS.

- [ ] **Step 5: Validate + commit**

Run: `python tools/validate.py` — Expected: `OK`.
```bash
git add data/maps tests/test_map_data.py
git commit -m "data: integrasi musuh ke peta + 2 peta fondasi Arc 2 (GDD 9/11)"
```

---

### Task 6: Quest + Event + NPC Baru + Peta Unlock

**Files:**
- Create: 5 quest di `data/quests/`
- Create: 5 event di `data/events/`
- Create: 4 NPC di `data/npc/`
- Modify: `tests/test_quest_data.py`, `tests/test_event_data.py`, `tests/test_npc_data.py` (EXPECTED sets)

**Interfaces:**
- Consumes: enemy id (Task 4), peta (Task 5), item (Task 2), NPC baru.
- Produces: alur cerita baru — quest di-`start_quest` event, `grant_item`, `unlock_map`, reward reputasi; NPC `talk` objective.

> Skema quest/npc/event diperiksa secara strict-equality oleh test; ikuti
> persis kunci yang ada. Skema quest punya `requires_flag`; NPC
> `{id,name,location,greeting,dialog}`; event `{id,trigger,actions,once}`.

- [ ] **Step 1: Update test sets (RED)** — ketiga file test:

`tests/test_quest_data.py` EXPECTED_QUESTS tambah:
```python
    "sq_paya_kotor",
    "sq_makam_bisu",
    "fquest_rebels_obat_hilang",
    "fquest_holyorder_penyusup",
    "sq_ashar_jiwa",
```
`tests/test_event_data.py` EXPECTED_EVENTS tambah:
```python
    "sq_paya_kotor_intro",
    "sq_paya_kotor_done",
    "sq_makam_bisu_intro",
    "sq_makam_bisu_done",
    "fquest_rebels_obat_hilang_intro",
    "fquest_rebels_obat_hilang_done",
    "fquest_holyorder_penyusup_intro",
    "fquest_holyorder_penyusup_done",
    "sq_ashar_jiwa_intro",
    "sq_ashar_jiwa_done",
    "unlock_makam_kuno",
    "unlock_paya_beracun",
```
`tests/test_npc_data.py` EXPECTED_NPCS tambah:
```python
    "bidan_selena",
    "penyewa_tua",
    "kurir_paya",
    "warden_arsip",
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_quest_data.py tests/test_event_data.py tests/test_npc_data.py -q`
Expected: FAIL — data baru belum ada.

- [ ] **Step 3: Create NPC data** (4):

`data/npc/bidan_selena.json`:
```json
{
  "id": "bidan_selena",
  "name": "Bidan Selena",
  "location": "village_emberfall",
  "greeting": "Kau terluka. Atau mengusir racun. Keduanya bisa kubantu.",
  "dialog": [
    "Selena menatap tangannya sendiri: 'Aku sudah menyaksikan terlalu banyak kematian yang tidak wajar.'",
    "'Ada pil di paya beracun yang bisa menyembuhkan — tapi hanya yang berani mengambil.'"
  ]
}
```
`data/npc/penyewa_tua.json`:
```json
{
  "id": "penyewa_tua",
  "name": "Penyewa Tua",
  "location": "village_emberfall",
  "greeting": "Aku tua. Tapi aku ingat nama di dinding kuil.",
  "dialog": [
    "'Setiap nama yang terukir di sana adalah orang yang bicara terlalu banyak.'",
    "'Penjaga makam muda menjaga sesuatu yang lebih tua darinya.'"
  ]
}
```
`data/npc/kurir_paya.json`:
```json
{
  "id": "kurir_paya",
  "name": "Kurir Paya",
  "location": "paya_beracun",
  "greeting": "Kabarku sampai? Pemberontak butuh obat itu.",
  "dialog": [
    "'Kiriman obat dirampas. Babi hutan mengawasinya untuk Orde Suci.'"
  ]
}
```
`data/npc/warden_arsip.json`:
```json
{
  "id": "warden_arsip",
  "name": "Warden Arsip",
  "location": "makam_kuno",
  "greeting": "Arsip tidak berbohong. Pemiliknya yang berbohong.",
  "dialog": [
    "'Inkuisitor kecil mencari sesuatu di sini. Ia tidak tahu apa yang ia cari.'"
  ]
}
```

- [ ] **Step 4: Create quest data** (5):

`data/quests/sq_paya_kotor.json`:
```json
{
  "id": "sq_paya_kotor",
  "title": "Paya Kotor",
  "type": "side",
  "description": "Bidan Selena memintamu mengambil pil pemulih besar yang tercecer di paya beracun.",
  "objectives": [
    {"kind": "enemy", "target": "kepiting_sangkar"},
    {"kind": "flag", "target": "paya_diambil"}
  ],
  "rewards": {"insight": 30, "gold": 25, "reputation": {"rebels": 10}},
  "flags_on_complete": ["sq_paya_kotor_done"],
  "next": null,
  "category": "side",
  "requires_flag": "quest103_done"
}
```
`data/quests/sq_makam_bisu.json`:
```json
{
  "id": "sq_makam_bisu",
  "title": "Makam Bisu",
  "type": "side",
  "description": "Penyewa Tua mengenal nama di dinding. Ia ingin kamu mengusir apa yang berkeliaran di makam kuno.",
  "objectives": [
    {"kind": "map", "target": "makam_kuno"},
    {"kind": "enemy", "target": "inkuisitor_kecil"}
  ],
  "rewards": {"insight": 40, "gold": 30, "reputation": {"ancient_order": 10}},
  "flags_on_complete": ["sq_makam_bisu_done"],
  "next": null,
  "category": "side",
  "requires_flag": "quest103_done"
}
```
`data/quests/fquest_rebels_obat_hilang.json`:
```json
{
  "id": "fquest_rebels_obat_hilang",
  "title": "Obat yang Hilang",
  "type": "faction",
  "description": "Kurir Paya meminta obat yang dirampas. Pemberontak butuh untuk menyelamatkan rakyat.",
  "objectives": [
    {"kind": "talk", "target": "kurir_paya"},
    {"kind": "enemy", "target": "kepiting_sangkar"}
  ],
  "rewards": {"insight": 40, "gold": 30, "reputation": {"rebels": 15}},
  "flags_on_complete": ["fquest_rebels_obat_hilang_done"],
  "next": null,
  "category": "faction",
  "requires_flag": "quest103_done"
}
```
`data/quests/fquest_holyorder_penyusup.json`:
```json
{
  "id": "fquest_holyorder_penyusup",
  "title": "Penyusup Orde",
  "type": "faction",
  "description": "Orde Suci mencurigai penyusup di makam kuno. Warden Arsip tahu lebih banyak.",
  "objectives": [
    {"kind": "talk", "target": "warden_arsip"},
    {"kind": "enemy", "target": "murid_sekte_bayangan"}
  ],
  "rewards": {"insight": 40, "gold": 30, "reputation": {"holy_order": 15}},
  "flags_on_complete": ["fquest_holyorder_penyusup_done"],
  "next": null,
  "category": "faction",
  "requires_flag": "quest103_done"
}
```
`data/quests/sq_ashar_jiwa.json`:
```json
{
  "id": "sq_ashar_jiwa",
  "title": "Asar Jiwa",
  "type": "side",
  "description": "Seorang pendekar menawarkan pil asar jiwa bila kau membuktikan kekuatanmu melawan arwah pendendam.",
  "objectives": [
    {"kind": "enemy", "target": "arwah_pendendam"}
  ],
  "rewards": {"insight": 35, "gold": 20},
  "flags_on_complete": ["sq_ashar_jiwa_done"],
  "next": null,
  "category": "side",
  "requires_flag": "quest103_done"
}
```

- [ ] **Step 5: Create event data** (12) — intro (start quest), done (reward item + unlock), unlock maps.

Pola event (skema `{id, trigger, actions, once}`, aksi `start_quest`/`grant_item`/`unlock_map`/`log`):

`data/events/sq_paya_kotor_intro.json`:
```json
{
  "id": "sq_paya_kotor_intro",
  "trigger": [{"kind": "quest_done", "quest": "quest103"}],
  "actions": [
    {"kind": "start_quest", "id": "sq_paya_kotor"},
    {"kind": "log", "text": "Bidan Selena memintamu mencari pil di paya beracun."},
    {"kind": "unlock_map", "target": "paya_beracun"}
  ],
  "once": true
}
```
`data/events/sq_paya_kotor_done.json`:
```json
{
  "id": "sq_paya_kotor_done",
  "trigger": [{"kind": "quest_done", "quest": "sq_paya_kotor"}],
  "actions": [
    {"kind": "grant_item", "id": "pil_pemulih_besar", "count": 1},
    {"kind": "log", "text": "Di antara akar paya, pil pemulih besar menanti."}
  ],
  "once": true
}
```
`data/events/sq_makam_bisu_intro.json`:
```json
{
  "id": "sq_makam_bisu_intro",
  "trigger": [{"kind": "quest_done", "quest": "quest103"}],
  "actions": [
    {"kind": "start_quest", "id": "sq_makam_bisu"},
    {"kind": "log", "text": "Penyewa Tua menyarankan kau ke makam kuno."},
    {"kind": "unlock_map", "target": "makam_kuno"}
  ],
  "once": true
}
```
`data/events/sq_makam_bisu_done.json`:
```json
{
  "id": "sq_makam_bisu_done",
  "trigger": [{"kind": "quest_done", "quest": "sq_makam_bisu"}],
  "actions": [
    {"kind": "grant_item", "id": "pil_insight_sharif", "count": 1},
    {"kind": "log", "text": "Arsip lama memberi hadiah pemahaman."}
  ],
  "once": true
}
```
`data/events/fquest_rebels_obat_hilang_intro.json`:
```json
{
  "id": "fquest_rebels_obat_hilang_intro",
  "trigger": [{"kind": "quest_done", "quest": "quest103"}],
  "actions": [
    {"kind": "start_quest", "id": "fquest_rebels_obat_hilang"},
    {"kind": "log", "text": "Kurir Paya meminta bantuan pemberontak."}
  ],
  "once": true
}
```
`data/events/fquest_rebels_obat_hilang_done.json`:
```json
{
  "id": "fquest_rebels_obat_hilang_done",
  "trigger": [{"kind": "quest_done", "quest": "fquest_rebels_obat_hilang"}],
  "actions": [
    {"kind": "grant_item", "id": "pil_qi_tenang", "count": 1},
    {"kind": "log", "text": "Obat kembali ke tangan pemberontak."}
  ],
  "once": true
}
```
`data/events/fquest_holyorder_penyusup_intro.json`:
```json
{
  "id": "fquest_holyorder_penyusup_intro",
  "trigger": [{"kind": "quest_done", "quest": "quest103"}],
  "actions": [
    {"kind": "start_quest", "id": "fquest_holyorder_penyusup"},
    {"kind": "log", "text": "Orde Suci mencurigai penyusup di makam kuno."}
  ],
  "once": true
}
```
`data/events/fquest_holyorder_penyusup_done.json`:
```json
{
  "id": "fquest_holyorder_penyusup_done",
  "trigger": [{"kind": "quest_done", "quest": "fquest_holyorder_penyusup"}],
  "actions": [
    {"kind": "grant_item", "id": "pil_besi_hitam", "count": 1},
    {"kind": "log", "text": "Penyusup diusir. Orde Suci mencatat jasamu."}
  ],
  "once": true
}
```
`data/events/sq_ashar_jiwa_intro.json`:
```json
{
  "id": "sq_ashar_jiwa_intro",
  "trigger": [{"kind": "quest_done", "quest": "quest103"}],
  "actions": [
    {"kind": "start_quest", "id": "sq_ashar_jiwa"},
    {"kind": "log", "text": "Seorang pendekar menantang kekuatanmu."}
  ],
  "once": true
}
```
`data/events/sq_ashar_jiwa_done.json`:
```json
{
  "id": "sq_ashar_jiwa_done",
  "trigger": [{"kind": "quest_done", "quest": "sq_ashar_jiwa"}],
  "actions": [
    {"kind": "grant_item", "id": "pil_asar_jiwa", "count": 1},
    {"kind": "log", "text": "Pendekar itu menyerahkan pil asar jiwa."}
  ],
  "once": true
}
```
`data/events/unlock_makam_kuno.json`:
```json
{
  "id": "unlock_makam_kuno",
  "trigger": [{"kind": "quest_done", "quest": "quest103"}],
  "actions": [
    {"kind": "unlock_map", "target": "makam_kuno"},
    {"kind": "log", "text": "Jalan menuju makam kuno terbuka."}
  ],
  "once": true
}
```
`data/events/unlock_paya_beracun.json`:
```json
{
  "id": "unlock_paya_beracun",
  "trigger": [{"kind": "quest_done", "quest": "quest103"}],
  "actions": [
    {"kind": "unlock_map", "target": "paya_beracun"},
    {"kind": "log", "text": "Paya beracun kini terjangkau."}
  ],
  "once": true
}
```

- [ ] **Step 6: Run tests + validate**

Run: `pytest tests/test_quest_data.py tests/test_event_data.py tests/test_npc_data.py tests/test_event.py -q`
Expected: PASS. Lalu `python tools/validate.py` — Expected: `OK` (semua referensi ter-resolve).

- [ ] **Step 7: Commit**

```bash
git add data/quests data/events data/npc tests/test_quest_data.py tests/test_event_data.py tests/test_npc_data.py
git commit -m "data: quest/event/NPC baru + unlock peta Arc 2 (GDD 10/12/15)"
```

---

### Task 7: Test Integrasi Engine (use + slice alur baru)

**Files:**
- Modify: `tests/test_game_loop.py` (test alur baru), `tests/test_items.py`

**Interfaces:**
- Consumes: semua data Task 3-6 + command `use` Task 2.
- Produces: bukti perilaku terintegrasi (use item, quest baru selesai, item ter-grant).

- [ ] **Step 1: Write the failing test** — tambah di `tests/test_game_loop.py`:

```python
def test_event_unlock_peta_arc2_dan_start_quest_side(tmp_path):
    """quest103_done memicu unlock makam_kuno & start quest side."""
    session = _session(tmp_path)
    session.new_game("Akar")
    session.state.flags["quest103_done"] = True
    session._run_events()
    assert session.state.flags.get("map_makam_kuno_unlocked") is True
    assert "sq_makam_bisu" in session.state.quests.started
```

> `_run_events()` adalah metode privat yang dipanggil otomatis setelah
> perintah (mis. `_cmd_cultivate`, `_cmd_rest`). Test memanggilnya langsung
> karena alur perintah penuh (go/talk/battle) sudah diuji oleh test eksisting
> `test_slice_kuil_lengkap_quest103_dan_rahasia`.

- [ ] **Step 2: Run test to verify it passes**

Run: `pytest tests/test_game_loop.py -q -k "use or arc2 or side"`
Expected: PASS.

- [ ] **Step 3: Full suite**

Run: `pytest -q` — Expected: semua PASS.
Run: `ruff check src launcher.py tools tests && ruff format --check src launcher.py tools tests`
Run: `python tools/validate.py` — Expected: `OK`.

- [ ] **Step 4: Commit**

```bash
git add tests/test_game_loop.py tests/test_items.py
git commit -m "test: integrasi use item + quest side (GDD 18/12)"
```

---

### Task 8: Verifikasi Akhir (Definition of Done, AGENTS §12)

- [ ] `pytest -q` — semua lulus
- [ ] `ruff check src launcher.py tools tests` — bersih
- [ ] `ruff format --check src launcher.py tools tests` — bersih
- [ ] `python tools/validate.py` — `OK`
- [ ] `graphify update .` (ada perubahan kode)
- [ ] Review dua tahap: kepatuhan GDD (elemen §6.2, grimdark §3.6, flag quest §24.1) lalu kualitas kode
- [ ] Ringkasan: apa yang diubah, bukti, hal yang sengaja dilewati

**Sengaja dilewati:** efek item dalam combat (schema siap, eksekusi Fase 2),
mekanisme `refine`/alkimia penuh, artefak grow & binatang roh, status effect
baru di luar daftar §16, dan `Enemy.requires_flag` di dataclass.
