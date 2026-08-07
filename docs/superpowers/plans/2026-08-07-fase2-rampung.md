# Fase 1 — Rampungkan Fase 2 (Formasi · Binatang Roh · Data Arc 2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Menuntaskan sistem engine Fase 2 yang kurang (Formasi, Binatang Roh) dan melengkapi data Arc 2 sehingga Fase 2 playable penuh dan siap menerima konten Arc 3.

**Architecture:** Modul baru `src/systems/formation.py` + `data/formations/`; perluasan `src/core/game_loop.py` (bukan `combat.py` yang stabil) untuk menerapkan buff formasi, terjemahan `formation_skill`, evolusi binatang roh, dan menetas telur; field `evolution` di model Companion; data Arc 2 (NPC kunci, dialog, teknik alchemy/soul, resep, artefak, memori, faksi quest).

**Tech Stack:** Python 3.12+, pytest, ruff, stdlib.

## Global Constraints

- **TDD wajib** (AGENTS §2.1): tulis test gagal (RED) → implementasi minimal (GREEN) → refactor → commit. Data JSON: `python3 tools/validate.py` + test `*_data.py` lulus sebelum commit.
- **JANGAN sentuh** `src/engine/combat.py`, `src/engine/cultivation.py`, `src/models/player.py` (AGENTS §6). Semua integrasi lewat `src/core/game_loop.py` (stabil-tapi-bisa-diperluas).
- Bahasa Indonesia untuk semua teks/dialog/narasi. Header docstring (Args/Returns) Bahasa Inggris.
- `snake_case` untuk ID; baris ≤ 80; double quotes; import stdlib → third-party → lokal.
- Flag quest wajib `quest<id>_done`; elemen siklus Metal→Kayu→Tanah→Air→Api→Metal.
- Nada **grimdark** (GDD §3.6) untuk semua teks baru.
- **Schema save tetap v2** — field baru (`formation_active`, `evolution`) memakai backfill pola `party_active` (GDD §19.2), tanpa bump.
- Verifikasi tiap task: `pytest -q` + `ruff check src launcher.py tools tests` + `ruff format --check` + `python3 tools/validate.py`. Setelah perubahan kode: `graphify update .`.
- Commit: `<lingkup>: <ringkasan>` (mis. `feat(system): tambah sistem formasi`).

---

### Task 1: Sistem Formasi — engine, state, command, integrasi combat

**Files:**
- Create: `src/systems/formation.py`
- Create: `data/formations/jaring_naga.json`, `data/formations/benteng_bumi.json`, `data/formations/langit_pecah.json`
- Modify: `src/core/state.py:84-154` (field `formation_active` + normalize + to_dict), `src/core/state.py:194-236` (from_dict)
- Modify: `src/core/save.py` (backfill `formation_active`)
- Modify: `src/core/game_loop.py` (`_start_battle` ~1469, `player_skills` ~1443, `battle_step` ~1547, handler baru `_cmd_formation`)
- Test: `tests/test_formation.py` (baru), `tests/test_state.py`, `tests/test_game_loop.py`

**Interfaces:**
- `load_formations(data_dir: Path | None = None) -> dict[str, dict[str, Any]]` — muat `data/formations/*.json` keyed by id. Skema: `{"id", "name", "element", "description", "buff": {"defense": 20, ...}, "skill": "earth_charge" | null}` (`buff` wajib dict, `skill` opsional).
- `formation_buff(formation_id: str, formations: dict | None = None) -> dict[str, int]` — kembalikan `formation["buff"]`; `ValueError` bila id tak dikenal.
- `formation_skill(formation_id: str, formations: dict | None = None) -> str | None` — kembalikan `formation["skill"]` atau None.
- `GameState.formation_active: str | None` (default None) — id formasi yang terpasang.
- `_cmd_formation(command) -> list[str]` — set/clear formasi, hanya di lokasi aman (sama dengan `_cmd_swap`, game_loop.py:757-762).
- `battle_step(action)` — jika `action == "formation_skill"`, terjemahkan ke `technique:<skill>` (dari formasi aktif) sebelum `battle.step()`.

- [ ] **Step 1: Tulis test gagal untuk engine formasi**

```python
# tests/test_formation.py
from src.systems.formation import load_formations, formation_buff, formation_skill

def test_load_formations_memuat_semua_file():
    formations = load_formations()
    assert "jaring_naga" in formations
    assert "benteng_bumi" in formations
    assert "langit_pecah" in formations

def test_formation_buff_mengembalikan_stat_bonus():
    buff = formation_buff("jaring_naga")
    assert isinstance(buff, dict)
    assert all(isinstance(v, int) for v in buff.values())
    assert buff  # tidak kosong

def test_formation_buff_menolak_id_tak_dikenal():
    try:
        formation_buff("tidak_ada")
    except ValueError:
        pass
    else:
        raise AssertionError("harus ValueError")

def test_formation_skill_mengembalikan_id_atau_none():
    skill = formation_skill("langit_pecah")
    assert skill is None or isinstance(skill, str)
```

- [ ] **Step 2: Jalankan test, pastikan gagal**

Run: `pytest tests/test_formation.py -v`
Expected: FAIL (modul `src.systems.formation` tidak ada → ModuleNotFoundError)

- [ ] **Step 3: Implementasi minimal `src/systems/formation.py`**

```python
"""Sistem Formasi (GDD §7, §18.2) — data-driven buff tim.

Modul ringan: formasi dimuat dari data/formations/, buff-nya diterapkan
ke seluruh anggota tim saat pertarungan dimulai (lihat game_loop).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
FORMATION_DIR = DATA_DIR / "formations"


def load_formations(
    data_dir: Path | None = None,
) -> dict[str, dict[str, Any]]:
    """Muat semua formasi dari data/formations/, keyed by id.

    Args:
        data_dir: Direktori berisi JSON formasi (default data/formations/).

    Returns:
        Mapping formation_id -> dict skema GDD §7: ``id``, ``name``,
        ``element``, ``description``, ``buff`` (dict stat), ``skill``
        (opsional, id teknik).

    Raises:
        KeyError: Jika sebuah file JSON tidak punya kunci ``id``.
    """
    formations: dict[str, dict[str, Any]] = {}
    for path in sorted((data_dir or FORMATION_DIR).glob("*.json")):
        raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        formations[raw["id"]] = raw
    return formations


def formation_buff(
    formation_id: str,
    formations: dict[str, dict[str, Any]] | None = None,
) -> dict[str, int]:
    """Stat bonus dari sebuah formasi.

    Args:
        formation_id: ID formasi (snake_case).
        formations: Cache hasil load_formations (optional).

    Returns:
        Dict stat -> nilai bonus (mis. {"defense": 20}).

    Raises:
        ValueError: Jika formasi dengan id tersebut tidak ada.
    """
    catalog = formations if formations is not None else load_formations()
    formation = catalog.get(formation_id)
    if formation is None:
        raise ValueError(f"formasi tidak dikenal: {formation_id}")
    return dict(formation.get("buff", {}))


def formation_skill(
    formation_id: str,
    formations: dict[str, dict[str, Any]] | None = None,
) -> str | None:
    """Skill aktif dari formasi, bila ada (GDD §18.3 formation_skill).

    Args:
        formation_id: ID formasi (snake_case).
        formations: Cache hasil load_formations (optional).

    Returns:
        ID teknik formasi, atau None bila formasi tak punya skill.

    Raises:
        ValueError: Jika formasi dengan id tersebut tidak ada.
    """
    catalog = formations if formations is not None else load_formations()
    formation = catalog.get(formation_id)
    if formation is None:
        raise ValueError(f"formasi tidak dikenal: {formation_id}")
    return formation.get("skill")
```

- [ ] **Step 4: Buat 3 file data formasi**

```json
// data/formations/jaring_naga.json
{
  "id": "jaring_naga",
  "name": "Jaring Naga",
  "element": "earth",
  "description": "Formasi pertahanan: lafalkan jejak naga tanah, perisai mengeras bagi seluruh barisan.",
  "buff": {"defense": 20},
  "skill": null
}
```

```json
// data/formations/benteng_bumi.json
{
  "id": "benteng_bumi",
  "name": "Benteng Bumi",
  "element": "earth",
  "description": "Benteng kokoh: vitalitas barisan menguat, tapak tak goyah.",
  "buff": {"vitality": 15, "defense": 10},
  "skill": "perisai_tanah"
}
```

```json
// data/formations/langit_pecah.json
{
  "id": "langit_pecah",
  "name": "Langit Pecah",
  "element": "fire",
  "description": "Formasi agresif: semburan qi menajam, kecepatan barisan melonjak.",
  "buff": {"attack": 15, "agility": 10},
  "skill": "earth_charge"
}
```

- [ ] **Step 5: Jalankan test, pastikan lulus**

Run: `pytest tests/test_formation.py -v`
Expected: PASS

- [ ] **Step 6: Tulis test gagal untuk `formation_active` di state**

```python
# tests/test_state.py (tambahkan)
def test_formation_active_backfill_roundtrip():
    from src.core.state import GameState

    state = GameState()
    assert state.formation_active is None
    state.formation_active = "jaring_naga"
    data = state.to_dict()
    restored = GameState.from_dict(data)
    assert restored.formation_active == "jaring_naga"
```

- [ ] **Step 7: Jalankan test, pastikan gagal**

Run: `pytest tests/test_state.py::test_formation_active_backfill_roundtrip -v`
Expected: FAIL (`GameState` tidak punya atribut `formation_active`)

- [ ] **Step 8: Implementasi di `src/core/state.py`**

Tambahkan field setelah `buffs` (state.py:110):

```python
    # Formasi aktif (GDD §7, §18.2): id formasi yang terpasang, atau None.
    formation_active: str | None = None
```

Di `to_dict()` (setelah `"buffs": dict(self.buffs),` di ~state.py:173):

```python
            "formation_active": self.formation_active,
```

Di `from_dict` (setelah baris `buffs=dict(data.get("buffs", {})),` di ~state.py:234):

```python
            formation_active=data.get("formation_active"),
```

- [ ] **Step 9: Backfill di `src/core/save.py`**

Temukan tempat backfill field baru (cari `party_active` atau `buffs` di blok konstruksi GameState). Tambahkan di sampingnya:

```python
    formation_active = raw.get("formation_active")
```

lalu teruskan ke `GameState(..., formation_active=formation_active)` (atau pola yang sudah ada). Backfill default `None` aman tanpa bump schema.

- [ ] **Step 10: Jalankan test state, pastikan lulus**

Run: `pytest tests/test_state.py -v`
Expected: PASS

- [ ] **Step 11: Tulis test gagal untuk command & integrasi formasi**

```python
# tests/test_game_loop.py (tambahkan; pakai helper _session yang sudah ada)
def test_cmd_formation_set_dan_clear():
    from src.core.input import Command

    session = _session(tmp_path)  # ikuti helper yang ada
    session.new_game("Akar")
    res = session._cmd_formation(Command("formation", ["jaring_naga"]))
    assert "jaring_naga" in " ".join(res)
    assert session.state.formation_active == "jaring_naga"
    res = session._cmd_formation(Command("formation", []))
    assert session.state.formation_active is None


def test_cmd_formation_menolak_id_tak_dikenal():
    from src.core.input import Command

    session = _session(tmp_path)
    session.new_game("Akar")
    res = session._cmd_formation(Command("formation", ["tidak_ada"]))
    assert session.state.formation_active is None


def test_start_battle_menerapkan_buff_formasi_ke_semua_ally():
    # state.buffs adalah pola protagonis; formasi menambah buff ke semua
    # ally (protagonis + rekan aktif).
    session = _session(tmp_path)
    session.new_game("Akar")
    session.state.formation_active = "jaring_naga"
    # Enemy tier 1 yang pasti ada di data, mis. babi_hutan_qi.
    session._start_battle("babi_hutan_qi")
    ally = session.battle.allies[0]
    base_defense = ally.stats["defense"] - 20
    assert ally.stats["defense"] == base_defense + 20


def test_battle_step_formation_skill_menggunakan_teknik_formasi():
    # Simulasikan: formasi benteng_bumi punya skill perisai_tanah.
    session = _session(tmp_path)
    session.new_game("Akar")
    session.state.formation_active = "benteng_bumi"
    session._start_battle("babi_hutan_qi")
    # Perilaku: aksi formation_skill diterjemahkan tanpa ValueError
    # "aksi tidak dikenal" dari Battle.
    frame = session.battle_step("formation_skill")
    assert frame.error is None or "qi" in frame.error.lower()
```

> Catatan implementasi: periksa helper `_session` dan pemain "Akar" di
> `tests/test_game_loop.py` (jalur kultivasi) serta daftar musuh tier 1.
> Sesuaikan id musuh/teknik dengan data aktual bila nama berbeda — tapi
> JANGAN melemahkan assertion (mis. menghapus cek defense).

- [ ] **Step 12: Jalankan test, pastikan gagal**

Run: `pytest tests/test_game_loop.py -k formation -v`
Expected: FAIL (belum ada `_cmd_formation`, buff belum diterapkan)

- [ ] **Step 13: Implementasi di `src/core/game_loop.py`**

Handler baru (taruh dekat `_cmd_swap`, di bawah `_cmd_settings` area ~game_loop.py:799; pastikan urutan tidak memecah struct):

```python
    def _cmd_formation(self, command: Command) -> list[str]:
        """Pasang/bongkar formasi, hanya di lokasi aman (GDD §18.2)."""
        if self.in_battle:
            return ["Tidak bisa mengatur formasi saat bertarung."]
        location_data = load_maps().get(self.state.location, {})
        if location_data.get("enemies"):
            return [
                "Area ini tidak aman untuk memasang formasi. "
                "Kembali ke desa atau kota dulu."
            ]
        if not command.args:
            if self.state.formation_active is None:
                return [
                    "Formasi apa? Contoh: formation jaring_naga. "
                    "Formasi aktif: tidak ada."
                ]
            name = load_formations()[self.state.formation_active]["name"]
            self.state.formation_active = None
            return [f"Formasi {name} dibongkar."]
        formation_id = command.args[0]
        formations = load_formations()
        if formation_id not in formations:
            return [f"Formasi '{formation_id}' tidak dikenal."]
        self.state.formation_active = formation_id
        return [
            f"Formasi {formations[formation_id]['name']} terpasang. "
            "Bonus berlaku untuk seluruh tim saat bertarung."
        ]
```

Impor modul di bagian atas `game_loop.py` (ikuti pola import lokal atau top-level yang sudah ada):

```python
from src.systems.formation import (
    formation_buff,
    formation_skill as get_formation_skill,
    load_formations,
)
```

Perluas `player_skills` (game_loop.py:1451-1454) — skill formasi aktif ikut tersedia:

```python
        skills = [
            technique.id
            for technique in load_techniques()
            if technique.requires.get("tier") == self.state.player.tier_id
        ]
        if self.state.formation_active:
            skill = get_formation_skill(self.state.formation_active)
            if skill:
                skills.append(skill)
        return skills
```

Di `_start_battle` (perluas loop buff di game_loop.py:1469) — buff formasi berlaku ke SEMUA ally:

```python
        # Formasi aktif (GDD §7): buff area diterapkan ke seluruh tim.
        formation_bonus = {}
        if self.state.formation_active:
            formation_bonus = formation_buff(self.state.formation_active)
        for key, value in self.state.buffs.items():
            ally.stats[key] = ally.stats.get(key, 0) + value
        for ally_unit in [ally] + [c for c in allies[1:]]:
            for stat, value in formation_bonus.items():
                ally_unit.stats[stat] = ally_unit.stats.get(stat, 0) + value
```

> Catatan: pindahkan pemanggilan `combatant_from_companion` ke list sementara
> agar rekan ikut dapat buff, ATAU terapkan buff formasi di akhir setelah
> semua ally terbentuk (`allies` lengkap). Ikuti struktur `_start_battle`
> saat ini tanpa mengubah `combat.py`.

Di `battle_step` (sebelum `battle.step(action)` di game_loop.py:1562):

```python
            if action == "formation_skill" and self.state.formation_active:
                skill = get_formation_skill(self.state.formation_active)
                if skill:
                    action = f"technique:{skill}"
```

- [ ] **Step 14: Jalankan test, pastikan lulus**

Run: `pytest tests/test_game_loop.py -k formation -v`
Expected: PASS

- [ ] **Step 15: Verifikasi penuh & commit**

```bash
pytest -q
ruff check src launcher.py tools tests
ruff format --check src launcher.py tools tests
python3 tools/validate.py
git add src/systems/formation.py data/formations tests/test_formation.py src/core/state.py src/core/save.py src/core/game_loop.py tests/test_state.py tests/test_game_loop.py
git commit -m "feat(system): tambah sistem formasi (buff tim + formation_skill)"
```

---

### Task 2: Sistem Binatang Roh — evolusi, menetas, recall riil, wire macan_baja

**Files:**
- Modify: `src/models/party.py` (field `evolution` di `Companion`, `to_dict`, `from_dict`)
- Modify: `src/core/game_loop.py` (`_cmd_recall`, `_cmd_use` untuk `hatch_companion`, `_cmd_breakthrough` untuk cek evolusi, helper `_evolve_companions`)
- Create: `data/companions/serigala_bayangan_evolved.json`
- Create: `data/items/telur_phoenix_abu.json` (telur binatang roh baru)
- Create: `data/companions/phoenix_abu.json` (binatang roh dari telur)
- Create: `data/events/macan_baja_recruit.json` (event rekrut `macan_baja`)
- Modify: `data/companions/serigala_bayangan.json` (tambah field `evolution`)
- Test: `tests/test_evolution.py` (baru), `tests/test_companion_data.py`, `tests/test_game_loop.py`

**Interfaces:**
- `Companion.evolution: dict[str, Any] | None` — `{"trigger_tier": "golden_core", "evolved_id": "serigala_bayangan_evolved"}`. `from_dict` backfill default None; `to_dict` serialize bila ada.
- `GameLoop._evolve_companions(tier_id: str) -> list[str]` — untuk tiap rekan di `state.party` yang `evolution.trigger_tier == tier_id`, ganti dengan data `evolved_id` (pertahankan `bond_xp`/`rank`/`hp`/`qi`), kembalikan pesan evolusi. Rekan yang sudah berevolusi tidak punya field `evolution` (sekali per §20.3).
- Efek item baru `hatch_companion` di `_cmd_use`: `{"hatch_companion": "phoenix_abu"}` → tambah rekan ke `state.party`, aktifkan bila slot tersedia, hapus telur.
- `_cmd_recall(command)` → delegasikan ke `_cmd_swap` (semantik panggil/lepas, GDD §18.2).

- [ ] **Step 1: Tulis test gagal untuk field evolution**

```python
# tests/test_evolution.py
from src.models.party import Companion, load_companions


def _raw_companion() -> dict:
    return {
        "id": "serigala_bayangan",
        "name": "Serigala Bayangan",
        "tier": "foundation_establishment",
        "element": "water",
        "stats": {"attack": 15, "defense": 10, "agility": 30},
        "skills": ["qi_slash"],
        "evolution": {
            "trigger_tier": "golden_core",
            "evolved_id": "serigala_bayangan_evolved",
        },
    }


def test_from_dict_memuat_evolution():
    companion = Companion.from_dict(_raw_companion())
    assert companion.evolution == {
        "trigger_tier": "golden_core",
        "evolved_id": "serigala_bayangan_evolved",
    }


def test_to_dict_menyimpan_evolution():
    companion = Companion.from_dict(_raw_companion())
    assert companion.to_dict()["evolution"] == companion.evolution


def test_from_dict_backfill_tanpa_evolution():
    raw = _raw_companion()
    del raw["evolution"]
    assert Companion.from_dict(raw).evolution is None


def test_data_companion_mempunyai_evolution_valid():
    companions = load_companions()
    by_id = {c.id: c for c in companions}
    assert by_id["serigala_bayangan"].evolution is not None
    evolved_id = by_id["serigala_bayangan"].evolution["evolved_id"]
    assert evolved_id in by_id
```

- [ ] **Step 2: Jalankan test, pastikan gagal**

Run: `pytest tests/test_evolution.py -v`
Expected: FAIL (Companion tidak punya atribut `evolution`)

- [ ] **Step 3: Implementasi `evolution` di `src/models/party.py`**

```python
    # Evolusi sekali (GDD §20.3): trigger_tier -> ganti id, tanpa flag
    # tambahan (rekan berevolusi tidak lagi punya field ini).
    evolution: dict[str, Any] | None = None
```

Di `to_dict` (tambah sebelum `return`):

```python
        if self.evolution:
            result["evolution"] = dict(self.evolution)
```

dan ubah blok `return` menjadi `result` terlebih dahulu, atau tambahkan baris langsung:

```python
        return {
            "id": self.id,
            # ... field existing ...
            "hp": self.hp,
            "qi": self.qi,
            "evolution": dict(self.evolution) if self.evolution else None,
        }
```

Di `from_dict`:

```python
            hp=raw.get("hp"),
            qi=raw.get("qi"),
            evolution=raw.get("evolution"),
        )
```

- [ ] **Step 4: Tambah data evolusi**

Ubah `data/companions/serigala_bayangan.json` — tambah field:

```json
  "evolution": {
    "trigger_tier": "golden_core",
    "evolved_id": "serigala_bayangan_evolved"
  }
```

Buat `data/companions/serigala_bayangan_evolved.json`:

```json
{
  "id": "serigala_bayangan_evolved",
  "name": "Serigala Malam Belati",
  "tier": "golden_core",
  "element": "water",
  "stats": {
    "attack": 28,
    "defense": 18,
    "agility": 45,
    "intelligence": 10,
    "vitality": 22,
    "spirit": 15,
    "hp": 180,
    "qi": 80
  },
  "skills": ["tebasan_bayangan", "frost_bind"]
}
```

> Verifikasi `tebasan_bayangan` & `frost_bind` punya `requires.tier`
> ≤ golden_core di data/techniques; sesuaikan jika tidak.

- [ ] **Step 5: Jalankan test, pastikan lulus**

Run: `pytest tests/test_evolution.py -v`
Expected: PASS

- [ ] **Step 6: Tulis test gagal untuk evolusi saat breakthrough**

```python
# tests/test_evolution.py (lanjutan)
from src.core.state import GameState


class DummyPlayer:
    tier_id = "qi_condensation"
    hp = qi = hp_max = qi_max = insight = gold = meridian_buka = 0
    is_injured = False
    injury_days_remaining = 0


def _game_session_with_companion():
    from src.core.game_loop import GameSession
    from tests.test_game_loop import _session  # ikuti helper yang ada

    session = _session(__import__("pathlib").Path("/tmp/x"))
    session.new_game("Akar")
    session.state.party = [_raw_companion()]
    session.state.party_active = ["serigala_bayangan"]
    return session


def test_evolve_mengganti_rekan_saat_tier_tercapai():
    from src.core.input import Command

    session = _game_session_with_companion()
    session.state.player.tier_id = "golden_core"
    messages = session._evolve_companions("golden_core")
    ids = [raw["id"] for raw in session.state.party]
    assert "serigala_bayangan_evolved" in ids
    assert "serigala_bayangan" not in ids
    assert any("Serigala Malam Belati" in m for m in messages)
    # party_active ikut diperbarui
    assert "serigala_bayangan_evolved" in session.state.party_active
```

- [ ] **Step 7: Jalankan test, pastikan gagal**

Run: `pytest tests/test_evolution.py::test_evolve_mengganti_rekan_saat_tier_tercapai -v`
Expected: FAIL (`_evolve_companions` belum ada)

- [ ] **Step 8: Implementasi `_evolve_companions` di `game_loop.py`**

```python
    def _evolve_companions(self, tier_id: str) -> list[str]:
        """Evolusi binatang roh saat tier terpicu (GDD §20.3, sekali).

        Rekan dengan evolution.trigger_tier == tier_id diganti datanya
        dari companion evolved_id, mempertahankan bond_xp/rank. Rekan
        hasil evolusi tak punya field evolution -> tidak berevolusi lagi.

        Args:
            tier_id: Tier pemain setelah breakthrough.

        Returns:
            Daftar pesan evolusi untuk ditampilkan.
        """
        messages: list[str] = []
        for raw in self.state.party:
            evolution = raw.get("evolution")
            if not evolution or evolution.get("trigger_tier") != tier_id:
                continue
            evolved_id = evolution["evolved_id"]
            evolved = Companion.from_dict(
                load_companion(evolved_id).to_dict()
            )
            evolved.bond_xp = int(raw.get("bond_xp", 0))
            evolved.rank = int(raw.get("rank", 1))
            raw.update(evolved.to_dict())
            messages.append(
                f"{evolved.name} berevolusi! Bentuk barunya "
                "berdenyut dengan kekuatan baru."
            )
        active = list(self.state.party_active)
        evolved_ids = {raw["id"] for raw in self.state.party}
        self.state.party_active = [
            cid for cid in active if cid in evolved_ids
        ] + [raw["id"] for raw in self.state.party
             if raw["id"] in active and raw["id"] not in evolved_ids]
        return messages
```

> Sederhanakan bagian `party_active` agar tetap berisi id yang ada di
> party. Implementer boleh menulis versi lebih bersih — yang penting
> id lama yang berevolusi diganti id baru di `party_active`.

Panggil di `_cmd_breakthrough` SETELAH sukses (temukan titik sukses di
game_loop.py:1217+; jangan ubah `cultivation.py`):

```python
        messages.extend(self._evolve_companions(self.state.player.tier_id))
```

- [ ] **Step 9: Jalankan test, pastikan lulus**

Run: `pytest tests/test_evolution.py -v`
Expected: PASS

- [ ] **Step 10: Tulis test gagal untuk recall & hatch**

```python
# tests/test_game_loop.py (tambahkan)
def test_cmd_recall_mendelegasikan_ke_swap():
    from src.core.input import Command

    session = _session(tmp_path)
    session.new_game("Akar")
    session.state.party = [{"id": "lin_wei", "name": "Lin Wei"}]
    session.state.party_active = []
    res = session._cmd_recall(Command("recall", ["lin_wei"]))
    assert "Lin Wei" in " ".join(res)
    assert "lin_wei" in session.state.party_active
    res = session._cmd_recall(Command("recall", ["lin_wei"]))
    assert "lin_wei" not in session.state.party_active


def test_cmd_use_menetaskan_telur_menambah_rekan():
    from src.core.input import Command

    session = _session(tmp_path)
    session.new_game("Akar")
    session.state.inventory["items"]["telur_phoenix_abu"] = 1
    res = session._cmd_use(Command("use", ["telur_phoenix_abu"]))
    ids = [raw["id"] for raw in session.state.party]
    assert "phoenix_abu" in ids
    assert session.state.inventory["items"].get("telur_phoenix_abu", 0) == 0
```

- [ ] **Step 11: Jalankan test, pastikan gagal**

Run: `pytest tests/test_game_loop.py -k "recall or telur" -v`
Expected: FAIL (recall masih stub, hatch belum ada)

- [ ] **Step 12: Implementasi recall & hatch**

`_cmd_recall` (game_loop.py:796) — delegasikan ke `_cmd_swap`:

```python
    def _cmd_recall(self, command: Command) -> list[str]:
        """Panggil/lepas binatang roh (GDD §18.2) — sama dengan swap."""
        return self._cmd_swap(command)
```

`_cmd_use` (tambah di blok effect, setelah `add_meridian`, game_loop.py:~391):

```python
            if effect.get("hatch_companion"):
                companion_id = effect["hatch_companion"]
                ids = [raw["id"] for raw in self.state.party]
                if companion_id not in ids:
                    companion = Companion.from_dict(
                        load_companion(companion_id).to_dict()
                    )
                    self.state.party.append(companion.to_dict())
                    if len(self.state.party_active) < 3:
                        self.state.party_active.append(companion_id)
                lines.append(f"Telur menetas: {companion.name} bergabung!")
```

Pastikan `Companion`, `load_companion` sudah diimpor di game_loop.py
(cari di bagian atas atau blok import lokal; tambahkan bila belum).

- [ ] **Step 13: Data telur & binatang roh baru**

```json
// data/items/telur_phoenix_abu.json
{
  "id": "telur_phoenix_abu",
  "name": "Telur Phoenix Abu",
  "type": "consumable",
  "description": "Telur tua yang berdenyut hangat. Sesuatu di dalamnya menunggu untuk lahir.",
  "effect": {"hatch_companion": "phoenix_abu"},
  "price": 0
}
```

```json
// data/companions/phoenix_abu.json
{
  "id": "phoenix_abu",
  "name": "Phoenix Abu",
  "tier": "golden_core",
  "element": "fire",
  "stats": {
    "attack": 20,
    "defense": 12,
    "agility": 25,
    "intelligence": 12,
    "vitality": 18,
    "spirit": 20,
    "hp": 120,
    "qi": 90
  },
  "skills": ["flame_strike"]
}
```

> Verifikasi `flame_strike` requires.tier ≤ golden_core. Tambahkan
> narasi grimdark pada description.

- [ ] **Step 14: Event rekrut `macan_baja`**

```json
// data/events/macan_baja_recruit.json
{
  "id": "macan_baja_recruit",
  "trigger": [
    {"kind": "quest_done", "quest": "quest207"}
  ],
  "actions": [
    {"kind": "add_companion", "id": "macan_baja"},
    {"kind": "log", "text": "Macan Baja, penjaga arena sekte yang kau kalahkan, kini mengikutimu — bukan karena takluk, melainkan karena tak ada lagi yang tersisa baginya untuk dijaga."}
  ],
  "once": true
}
```

> Pastikan id quest sesuai data quest Arc 2 (quest207 atau quest yang
> paling masuk akal; sesuaikan bila chain berbeda). Jika quest207 sudah
> punya event `quest207_done`, gunakan trigger tersebut atau quest lain
> yang belum dipakai.

- [ ] **Step 15: Verifikasi penuh & commit**

```bash
pytest -q
ruff check src launcher.py tools tests
ruff format --check src launcher.py tools tests
python3 tools/validate.py
graphify update .
git add src/models/party.py src/core/game_loop.py data/companions data/items/telur_phoenix_abu.json data/events/macan_baja_recruit.json tests/test_evolution.py tests/test_companion_data.py tests/test_game_loop.py
git commit -m "feat(companion): sistem evolusi + menetas + recall binatang roh"
```

---

### Task 3: Data Arc 2 — NPC kunci, dialog, teknik, resep, artefak, memori, faksi quest

**Files:**
- Create: `data/npc/blacksmith_tie.json`, `data/npc/kestrel.json`, `data/npc/penjaga_sekte.json`, `data/npc/murid_sekte.json`, `data/npc/pedagang_kota.json`, `data/npc/informan_gilda.json` (4 pendukung opsional)
- Create: `data/dialogues/dialog_alchemist_xiu_1.json`, `data/dialogues/dialog_kestrel_1.json`, `data/dialogues/dialog_blacksmith_tie_1.json`
- Create: 6 teknik baru: `data/techniques/racun_meridian_lanjut.json`, `data/techniques/tangan_emas.json`, `data/techniques/pil_pembakar.json` (alchemy); `data/techniques/seruan_jiwa.json`, `data/techniques/ikatan_roh.json`, `data/techniques/pandangan_jiwa.json` (soul)
- Create: `data/items/resep_pil_besi_hitam.json`, `data/items/resep_pil_qi_tenang.json`, `data/items/resep_pil_peneguh_fondasi.json`, `data/items/resep_ramuan_meridian.json`
- Create: 3 artefak: `data/items/pedang_taring_naga.json`, `data/items/jimat_roh_liar.json`, `data/items/salib_bisu.json`
- Create: `data/story/memory_sekte_intrik.json` (echo memori Arc 2)
- Test: `tests/test_npc_data.py`, `tests/test_dialog.py`, `tests/test_technique_data.py`, `tests/test_items.py`, `tests/test_shop_data.py`, `tests/test_quest_data.py`, `tests/test_story.py` (update), `tests/test_validate_tool.py`

**Interfaces:**
- Skema NPC: `{"id", "name", "location", "role", "greeting", "dialog": [...], "shop": "<id>" | null}` (lihat `data/npc/elder_mao.json`). `blacksmith_tie` di `guild_city` dengan `shop` (buat `data/shops/toko_tie.json` bila perlu, pola `data/shops/pedagang_kelana.json`).
- Skema dialog: graf node (GDD §12.5) — lihat `data/dialogues/dialog_fang_yue_1.json`. Aksi memakai format §15.3.
- Skema teknik: GDD §14.3 (`requires.tier` wajib; path `alchemy`/`soul`).
- Skema resep: `type=recipe`, `effect.learn_recipe` → id pil; `recipe` daftar bahan (bahan harus ada di data/items).
- Skema artefak: `type=artifact`, `growth_stat`, `max_level`.
- Skema memori: `{"id", "title", "text"}` (GDD §15.3 grant_memory) — lihat `data/story/memory_shrine_trial.json`.
- Semua referensi (NPC di peta, bahan di resep, skill di companion, flag quest di event) wajib valid — validator.

- [ ] **Step 1: Tulis test data awal (RED)**

```python
# tests/test_arc2_data.py (file baru)
from src.engine.items import load_items
from src.engine.maps import load_maps
from src.engine.quest import load_quests  # sesuaikan nama fungsi aktual
from src.engine.dialog import load_dialogs
from src.models.party import load_companions


def test_npc_kunci_arc2_ada_di_guild_city():
    import json
    from pathlib import Path

    npc_dir = Path("data/npc")
    data = {
        path.stem: json.loads(path.read_text(encoding="utf-8"))
        for path in npc_dir.glob("*.json")
    }
    assert "blacksmith_tie" in data
    assert data["blacksmith_tie"]["location"] == "guild_city"
    assert "kestrel" in data
    assert data["kestrel"]["location"] == "guild_city"


def test_dialog_arc2_merujuk_npc_yang_ada():
    import json
    from pathlib import Path

    npc_dir = Path("data/npc")
    npc_ids = {path.stem for path in npc_dir.glob("*.json")}
    for path in Path("data/dialogues").glob("dialog_*_1.json"):
        raw = json.loads(path.read_text(encoding="utf-8"))
        assert raw["npc"] in npc_ids


def test_teknik_alchemy_dan_soul_arc2_bertambah():
    from src.engine import items  # tidak dipakai; gunakan load dari data
    import json
    from pathlib import Path

    tech = {
        path.stem: json.loads(path.read_text(encoding="utf-8"))
        for path in Path("data/techniques").glob("*.json")
    }
    alchemy = [t for t in tech.values() if t.get("path") == "alchemy"]
    soul = [t for t in tech.values() if t.get("path") == "soul"]
    assert len(alchemy) >= 5
    assert len(soul) >= 5


def test_resep_arc2_melengkapi_pil_yang_ada():
    import json
    from pathlib import Path

    resep = {
        path.stem: json.loads(path.read_text(encoding="utf-8"))
        for path in Path("data/items").glob("resep_*.json")
    }
    targets = {r["effect"]["learn_recipe"] for r in resep.values()}
    for pil in ["pil_besi_hitam", "pil_qi_tenang", "pil_peneguh_fondasi"]:
        assert pil in targets


def test_artefak_arc2_punya_growth_stat_dan_max_level():
    items = load_items()
    artifacts = [
        item for item in items.values() if item.get("type") == "artifact"
    ]
    assert len(artifacts) >= 6
    for item in artifacts:
        assert item.get("growth_stat")
        assert item.get("max_level")
```

> Sesuaikan nama fungsi load (`load_maps`/`load_quests`/`load_dialogs`)
> dengan modul aktual saat implementasi. Jangan menghapus assertion.

- [ ] **Step 2: Jalankan test, pastikan gagal**

Run: `pytest tests/test_arc2_data.py -v`
Expected: FAIL (blacksmith_tie/kestrel belum ada, teknik/resep/artefak kurang)

- [ ] **Step 3: Tambah data NPC & shop**

`data/npc/blacksmith_tie.json` (pola `data/npc/alchemist_xiu.json`):

```json
{
  "id": "blacksmith_tie",
  "name": "Tie Pandai Senjata",
  "location": "guild_city",
  "role": "Pandai besi; artefak & senjata roh (GDD §10).",
  "greeting": "Baja yang bagus menunggu tangan yang tepat. Lihat daganganku.",
  "dialog": [
    "Senjata roh tumbuh bersama pemiliknya. Pilih yang mau menemanimu mati."
  ],
  "shop": "toko_tie"
}
```

`data/shops/toko_tie.json` (pola `data/shops/pedagang_kelana.json`):

```json
{
  "id": "toko_tie",
  "name": "Tempa Tie",
  "items": [
    {"item": "pedang_awan_hitam", "count": 1},
    {"item": "pedang_taring_naga", "count": 1},
    {"item": "pil_pemulih_besar", "count": 3}
  ]
}
```

> Validasi: semua `item` di shop harus ada & ber-`price`.

`data/npc/kestrel.json`:

```json
{
  "id": "kestrel",
  "name": "Kestrel",
  "location": "guild_city",
  "role": "Pemimpin Gilda Pembunuh; karakter abu-abu (GDD §10).",
  "greeting": "Kau terlihat seperti orang yang harganya layak dibayar. Baik untuk mati, atau untuk membunuh.",
  "dialog": [
    "Gilda membunuh demi bayaran, bukan demi keyakinan. Keyakinan adalah kemewahan orang mati."
  ]
}
```

- [ ] **Step 4: Tambah 3 dialog Arc 2**

`data/dialogues/dialog_blacksmith_tie_1.json`:

```json
{
  "id": "dialog_blacksmith_tie_1",
  "npc": "blacksmith_tie",
  "nodes": {
    "start": {
      "text": "Senjata roh tidak dibuat dengan api saja. Ia ditempa oleh tekad, dan dihancurkan oleh keraguan.",
      "choices": [
        {
          "text": "Apa yang kau tahu tentang senjata yang tumbuh?",
          "next": "info",
          "requires_flag": null,
          "actions": []
        },
        {
          "text": "[Meninggalkan tempa]",
          "next": null,
          "actions": []
        }
      ]
    },
    "info": {
      "text": "Pilih satu dan ia akan belajar dari pertumpahan darahmu. Jangan pilih yang kau tak sanggup menanggung harganya.",
      "choices": [
        {
          "text": "[Meninggalkan tempa]",
          "next": null,
          "actions": []
        }
      ]
    }
  }
}
```

`data/dialogues/dialog_kestrel_1.json`:

```json
{
  "id": "dialog_kestrel_1",
  "npc": "kestrel",
  "nodes": {
    "start": {
      "text": "Kota ini penuh mata yang meminta bayaran. Telingaku mendengar nama yang seharusnya sudah mati — dan namamu ada di antaranya.",
      "choices": [
        {
          "text": "Siapa yang memburuku?",
          "next": "jawaban",
          "requires_flag": null,
          "actions": []
        },
        {
          "text": "[Pergi]",
          "next": null,
          "actions": []
        }
      ]
    },
    "jawaban": {
      "text": "Orde Suci memberi imbalan besar untuk informasi tentang bakat semacam dirimu. Pilih sisimu baik-baik — harga itu tak akan menunggumu lama.",
      "choices": [
        {
          "text": "[Pergi]",
          "next": null,
          "actions": []
        }
      ]
    }
  }
}
```

`data/dialogues/dialog_alchemist_xiu_1.json` — ikuti pola yang sama,
bertema resep dan racun meridian, nada grimdark.

- [ ] **Step 5: Tambah 6 teknik (alchemy 3, soul 3)**

Pola (lihat `data/techniques/jarum_racun.json` untuk skema persis):

```json
// data/techniques/seruan_jiwa.json (path soul)
{
  "id": "seruan_jiwa",
  "name": "Seruan Jiwa",
  "path": "soul",
  "element": "water",
  "type": "technique",
  "qi_cost": 8,
  "power": 12,
  "effects": [{"status": "charm", "duration": 2}],
  "requires": {"tier": "golden_core"}
}
```

> Salin skema aktual dari teknik soul/alchemy yang ada (`jaring_jiwa`,
> `jarum_racun`) — gunakan field persis yang dipakai data eksisting agar
> validator & engine konsisten. Siklus elemen wajib konsisten (§6.2).

Isi 6 teknik:
- alchemy: `racun_meridian_lanjut` (dot poison kuat), `tangan_emas` (buff strengthen), `pil_pembakar` (burn)
- soul: `seruan_jiwa` (charm), `ikatan_roh` (seal), `pandangan_jiwa` (observe/agility debuff slow)

- [ ] **Step 6: Tambah 4 resep Arc 2**

Pola `resep_pil_baja` di atas (effect.learn_recipe → id pil):

```json
// data/items/resep_pil_besi_hitam.json
{
  "id": "resep_pil_besi_hitam",
  "name": "Resep Pil Besi Hitam",
  "type": "recipe",
  "description": "Mengajarkan cara meracik Pil Besi Hitam.",
  "price": 350,
  "effect": {"learn_recipe": "pil_besi_hitam"},
  "recipe": [
    {"item": "batu_qi", "qty": 2},
    {"item": "esensi_tanah", "qty": 2}
  ]
}
```

> Gunakan bahan yang SUDAH ada di data/items (periksa `esensi_*`, dll.).
> Buat `resep_pil_qi_tenang`, `resep_pil_peneguh_fondasi`,
> `resep_ramuan_meridian` dengan pola sama.

- [ ] **Step 7: Tambah 3 artefak Arc 2**

Pola `data/items/pedang_awan_hitam.json`:

```json
// data/items/pedang_taring_naga.json
{
  "id": "pedang_taring_naga",
  "name": "Pedang Taring Naga",
  "type": "artifact",
  "description": "Bilah dari taring iblis yang membeku. Ia lapar — dan yang memberinya makan akan tumbuh.",
  "price": 800,
  "growth_stat": "attack",
  "max_level": 5
}
```

Buat juga `jimat_roh_liar.json` (growth_stat spirit) dan
`salib_bisu.json` (growth_stat vitality), dengan narasi grimdark.

- [ ] **Step 8: Tambah echo memori Arc 2**

```json
// data/story/memory_sekte_intrik.json
{
  "id": "memory_sekte_intrik",
  "title": "Bisikan di Lorong Sekte",
  "text": "Gema ingatan asing: dua bayangan berbicara tentang 'yang ditunggu'. 'Ia sudah masuk sekte,' kata satu. 'Biarkan ia tumbuh — kami sudah menunggu dua ratus tahun, beberapa bulan lagi bukan apa-apa.' Namamu tak disebut. Namun kau tahu mereka membicarakanmu."
}
```

Buat event `data/events/memory_sekte_intrik.json` dengan trigger
`{"kind": "quest_done", "quest": "quest203"}` (sesuaikan quest) dan aksi
`grant_memory` → `memory_sekte_intrik`.

- [ ] **Step 9: Verifikasi faksi quest Arc 2**

Periksa `data/quests/fquest_*.json`: pastikan minimal 3 faksi quest
ber-`requires_flag` dari quest2xx (Arc 2). Bila belum, pindahkan
`requires_flag` beberapa fquest Arc 1 ke quest2xx ATAU tambah fquest baru.
Wajib `python3 tools/validate.py` lulus.

- [ ] **Step 10: Jalankan test, pastikan lulus**

Run: `pytest tests/test_arc2_data.py -v && python3 tools/validate.py`
Expected: PASS, validator OK

- [ ] **Step 11: Verifikasi penuh & commit**

```bash
pytest -q
ruff check src launcher.py tools tests
ruff format --check src launcher.py tools tests
python3 tools/validate.py
graphify update .
git add data/npc data/dialogues data/techniques data/items data/story data/events data/shops tests/test_arc2_data.py
git commit -m "data(arc2): lengkapi NPC, dialog, teknik, resep, artefak, memori"
```

---

### Task 4: Housekeeping — README & file asing

**Files:**
- Modify: `README.md` (bagian Status — saat ini basi "Fase 0 MVP dalam pengembangan")
- Modify/del: `check_content_v2.py` (untracked di root — tentukan nasibnya)

- [ ] **Step 1: Cek isi `check_content_v2.py` dan README**

Run: `sed -n '1,40p' check_content_v2.py && sed -n '1,20p' README.md`
Baca dulu: apakah `check_content_v2.py` memakai validasi yang sudah
ditangani `tools/validate.py`? Kalau ya (duplikasi) → hapus (DILARANG
menghapus milik pihak lain; konfirmasi ke controller). Kalau punya
fungsi unik → pindahkan ke `tools/`.

- [ ] **Step 2: Update README status**

Ubah bagian Status menjadi: Fase 0–1 selesai, Fase 2 playable (atau
sesuai kondisi setelah Task 1–3). Tulis dalam Bahasa Indonesia, singkat.

- [ ] **Step 3: Verifikasi & commit**

```bash
pytest -q
git add README.md
git commit -m "docs: perbarui status proyek di README"
```

---

## Definisi Selesai Fase 1

- [ ] `pytest -q` lulus penuh
- [ ] `ruff check` & `ruff format --check` bersih
- [ ] `python3 tools/validate.py` OK
- [ ] Formasi playable: `formation <id>` set/clear, buff tim di battle, `formation_skill` jalan
- [ ] Binatang roh: evolusi terpicu breakthrough, telur menetas, `recall` berfungsi, `macan_baja` dapat direkrut
- [ ] Data Arc 2 lengkap: blacksmith_tie & kestrel + dialog + 6 teknik + 4 resep + 3 artefak + 1 memori + 3 faksi quest
- [ ] README tidak basi
- [ ] `graphify update .` dijalankan
