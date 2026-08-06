# Party System: Rekan Pertama + Fondasi Multi-Ally — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Menghidupkan Fase 2 (GDD §22–23): rekan tim pertama (Lin Wei) + fondasi engine multi-ally yang siap menampung binatang roh & rekan berikutnya (Fang Yue). Komponen: model `party.py`, factory `combatant_from_companion`, Battle multi-ally **dikendalikan penuh pemain** (keputusan pemilik proyek: setiap giliran sekutu menunggu perintah), perintah `party`/`swap` dengan gating lokasi aman, event `add_companion`, bond XP & peringkat rekan.

**Architecture:** `state.party` (sudah ada di save schema v2, selalu kosong) diisi daftar rekan; `state.party_active` = id rekan yang aktif (max 3 slot, GDD §20.1). `Battle` sudah menerima `allies: list[Combatant]` dan `battle_step()` sudah memberi giliran pemain untuk **setiap** sekutu (`_is_player_turn()` = current ada di `battle.allies`) — artinya alur "kontrol semua" **sudah berjalan tanpa AI rekan**. Yang perlu diubah di combat.py hanya `_first_target`: dari `opponents[0]` jadi acak di antara yang hidup agar musuh tidak fokus ke slot 1 (backward-compatible: 1 lawan ⇒ hasil sama). Rekrut via event engine action baru `add_companion` (event.py = stabil tapi bisa diperluas, §6). **`swap` di combat ditunda** (`ponytail:`): butuh roster cadangan > 3 anggota yang belum ada di Arc 2 awal — swap komposisi di lokasi aman (§20.1) diimplementasikan penuh.

**Tech Stack:** Python 3.12+, Rich/Textual (dipakai), stdlib, pytest, ruff (Google style ≤80), JSON data-driven.

## ⚠️ IZIN WAJIB (AGENTS §6, §11)

**Task 2 menyentuh `src/engine/combat.py` — file stabil Fase 0 yang dikunci.** Eksekusi plan ini **TIDAK BOLEH dimulai** tanpa persetujuan eksplisit pemilik proyek. Batas sentuhan:
- `combat.py`: **hanya** `_first_target` (randomisasi target untuk multi-sekutu). **Tidak** mengubah formula damage, status, turn order, `Battle.__init__` signature, atau menambah AI rekan/player_unit.
- `cultivation.py`, `models/player.py`: **TIDAK disentuh sama sekali**.

*(Keputusan pemilik proyek, 6 Agu 2026: pemain mengendalikan semua anggota — rekan BUKAN AI, swap di combat ditunda.)*

## Global Constraints

- TDD wajib: RED → GREEN → REFACTOR → commit (AGENTS §2.1); data JSON diuji dulu sebelum ditambah.
- `pytest -q`, `ruff check`, `ruff format --check`, `python tools/validate.py` wajib hijau sebelum DoD (§1, §12).
- `graphify update .` wajib setelah ubah engine (§4.3).
- Data eksisting **DILARANG** dihapus/diganti; hanya ditambah (§6). Rekrut Lin Wei lewat **event baru**, bukan mengubah reward quest lama.
- Bahasa Indonesia untuk semua `name/description/text`; nada **grimdark** (GDD §3.6).
- Elemen siklus Metal→Kayu→Tanah→Air→Api→Metal konsisten (GDD §6.2).
- **DILARANG**: relationship multi-atribut, camp, formasi front/mid/back, combo technique, permadeath di combat, breakthrough/meridian NPC — semua melanggar GDD §20.3/§20.4/§24.1 poin 17 (lihat Evaluasi).
- Baris ≤80; docstring Google-style (header English, isi Indonesia).
- Tidak ada dependency baru.

---

### Task 1: Model Companion + Data Lin Wei

**Files:**
- Create: `src/models/party.py`, `data/companions/lin_wei.json`
- Modify: `tests/test_validate_tool.py` (ref teknik/element), `tests/test_save.py` (roundtrip party)
- Test: `tests/test_save.py`, `tests/test_validate_tool.py`

**Interfaces:**
- Consumes: `state.party` (list of dict — schema v2 sudah ada, §19.2), teknik eksisting (`qi_slash`, `vine_grasp`).
- Produces: `Companion` dataclass (id, name, tier, element, stats, skills, bond_xp, hp/qi persisten) + `data/companions/lin_wei.json`.

-- [ ] **Step 1: Test data dulu (RED)** — `data/companions/lin_wei.json` dibuat **setelah** test berikut ditulis dan diverifikasi GAGAL karena file belum ada:

```python
def test_data_rekan_semua_valid():
    """Rekan: skema wajib + ref teknik/element valid (GDD §20)."""
    from src.engine.combat import load_techniques

    techniques = {t.id for t in load_techniques()}
    elements = {"metal", "wood", "earth", "water", "fire", "netral"}
    data_dir = Path(__file__).resolve().parents[1] / "data" / "companions"
    assert data_dir.exists(), "data/companions/ belum ada"
    for path in data_dir.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        assert set(data) >= {"id", "name", "tier", "element", "stats", "skills"}
        assert data["id"] == path.stem
        assert data["element"] in elements
        assert all(s in techniques for s in data["skills"])
        assert {
            "attack",
            "defense",
            "agility",
            "intelligence",
            "vitality",
            "spirit",
            "hp",
            "qi",
        } <= set(data["stats"])
```
Tambahkan ke `tests/test_validate_tool.py` atau file test data baru `tests/test_companion_data.py`.

-- [ ] **Step 2: Run test, pastikan GAGAL** — `pytest tests/test_companion_data.py -q` — Expected: FAIL (dir/file belum ada).

-- [ ] **Step 3: Buat model `src/models/party.py`**:

```python
"""Rekan tim: Companion & peringkat bond (GDD §20.3)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Companion:
    """Satu rekan tim (cerita atau binatang roh, GDD §20).

    Progresi memakai bond XP terpisah; naik peringkat rekan (bukan
    breakthrough seperti protagonis, §20.3). HP/qi persisten di dunia
    seperti Player (§17.2).

    Attributes:
        id: ID unik rekan, snake_case (mis. "lin_wei").
        name: Nama tampilan dalam Bahasa Indonesia.
        tier: Tier rekan saat rekrut.
        element: Elemen rekan (siklus §6.2).
        stats: Stat dasar (attack/defense/agility/intelligence/vitality/spirit).
        skills: Teknik yang dikuasai (data/techniques/).
        bond_xp: XP ikatan terpisah dari insight protagonis (§20.3).
        rank: Peringkat rekan saat ini (1-3 per arc), dihitung dari bond_xp.
        hp: HP saat ini di dunia (dibawa ke pertarungan).
        qi: Qi saat ini di dunia.
    """

    id: str
    name: str
    tier: str
    element: str
    stats: dict[str, int]
    skills: list[str] = field(default_factory=list)
    bond_xp: int = 0
    rank: int = 1
    hp: int | None = None
    qi: int | None = None

    @property
    def hp_max(self) -> int:
        """HP maksimum dari stat (skema §14.3, sama dengan enemy)."""
        return int(self.stats.get("hp", 1))

    @property
    def qi_max(self) -> int:
        """Qi maksimum dari stat."""
        return int(self.stats.get("qi", 0))

    def to_dict(self) -> dict[str, Any]:
        """Serialize untuk save (schema §19.2, field party)."""
        return {
            "id": self.id,
            "name": self.name,
            "tier": self.tier,
            "element": self.element,
            "stats": dict(self.stats),
            "skills": list(self.skills),
            "bond_xp": self.bond_xp,
            "rank": self.rank,
            "hp": self.hp,
            "qi": self.qi,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> Companion:
        """Bangun Companion dari dict save; backfill field baru."""
        return cls(
            id=raw["id"],
            name=raw.get("name", raw["id"]),
            tier=raw.get("tier", "qi_condensation"),
            element=raw.get("element", "netral"),
            stats=dict(raw.get("stats", {})),
            skills=list(raw.get("skills", [])),
            bond_xp=int(raw.get("bond_xp", 0)),
            rank=int(raw.get("rank", 1)),
            hp=raw.get("hp"),
            qi=raw.get("qi"),
        )
```

-- [ ] **Step 4: Data `data/companions/lin_wei.json`** (nada grimdark, stat seimbang di bawah protagonis tier 1):

```json
{
  "id": "lin_wei",
  "name": "Lin Wei",
  "tier": "qi_condensation",
  "element": "wood",
  "stats": {
    "attack": 5,
    "defense": 3,
    "agility": 4,
    "intelligence": 3,
    "vitality": 5,
    "spirit": 3,
    "hp": 30,
    "qi": 8
  },
  "skills": ["qi_slash", "vine_grasp"]
}
```
_(Catatan: `rank_bond_thresholds` **tidak dipakai** — model `Companion.rank` adalah field dataclass; kenaikan rank diset oleh konten/event masa depan. Tambahan data tanpa konsumen = utang (Ponytail), jadi tidak dimasukkan.)_

-- [ ] **Step 5: Test save roundtrip (RED)** — tambah di `tests/test_save.py`. **Gunakan helper yang ADA di file itu** (`_state()`, `save_game`, `load_game`) — **bukan** `_session`/`_load_slot` (tidak ada di test_save.py):

```python
def test_save_roundtrip_party(tmp_path):
    """Field party (schema v2) tersimpan & termuat utuh (GDD §19.2)."""
    from src.models.party import Companion

    state = _state()
    companion = Companion(
        id="lin_wei",
        name="Lin Wei",
        tier="qi_condensation",
        element="wood",
        stats={"hp": 30, "qi": 8},
        skills=["qi_slash"],
        bond_xp=25,
    )
    state.party = [companion.to_dict()]
    save_game(state, "save1", tmp_path)
    loaded = load_game("save1", tmp_path)
    assert loaded.party[0]["id"] == "lin_wei"
    assert loaded.party[0]["bond_xp"] == 25
```

-- [ ] **Step 6: Run test, pastikan GAGAL dulu lalu HIJAU** — verifikasi RED (party belum diproses / model belum ada), implementasi minimal, lalu `pytest tests/test_save.py tests/test_companion_data.py -q`.

-- [ ] **Step 7: Validator ref teknik → skema companion** — tambah di `tools/validate.py`: cek tiap `data/companions/*.json` (skema wajib, teknik ter-resolve, element valid). Test RED di `tests/test_validate_tool.py`:

```python
def test_validator_menangkap_ref_skill_rekan(tmp_path):
    """Rekan dengan skill tak dikenal wajib dilaporkan (GDD §20.3)."""
    data = _pohon_data(tmp_path)
    (data / "companions").mkdir()
    (data / "companions" / "rekan_test.json").write_text(
        json.dumps(
            {
                "id": "rekan_test",
                "name": "Rekan Uji",
                "tier": "qi_condensation",
                "element": "fire",
                "stats": {"hp": 20, "qi": 5},
                "skills": ["hantu_kuno"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    assert any("hantu_kuno" in e for e in collect_errors(data))
```

-- [ ] **Step 8: Verifikasi + commit**
```bash
pytest -q && ruff check src launcher.py tools tests && ruff format --check src launcher.py tools tests && python tools/validate.py
git add src/models/party.py data/companions tests
git commit -m "data: rekan pertama Lin Wei + model Companion party (GDD 20)"
```

---

### Task 2: Combat Multi-Ally — Target Acak + Factory Rekan (⚠️ izin combat.py)

**Files:**
- Modify: `src/engine/combat.py` (hanya `_first_target`: randomisasi)
- Modify: `src/models/combatant.py` (factory `combatant_from_companion`)
- Test: `tests/test_combat.py` (2 test baru)

**Interfaces:**
- Consumes: `Companion` (Task 1), `Battle` eksisting.
- Produces: battle dengan 2+ sekutu, semuanya dikendalikan pemain (alur `battle_step` eksisting sudah memberi giliran per sekutu); target musuh acak di antara sekutu hidup (backward-compatible 1v1).

-- [ ] **Step 1: Test RED** — tambah di `tests/test_combat.py`. **Gunakan helper yang ADA**: `_player()`, `_wolf()` (dari data serigala_qi, hp 30), `_FixedRng`; `combatant_from_companion` (factory Task 2) untuk rekan. **JANGAN** pakai `_player_combatant`/`_enemy_combatant`/`_techniques()` — tidak ada di file itu. Tambah helper baru `_companion_uji()` (memakai `Companion` dari `src.models.party` — Task 1):

```python
from src.models.party import Companion


def _companion_uji() -> Companion:
    """Companion uji standar (stat Lin Wei data Task 1)."""
    return Companion(
        id="lin_wei",
        name="Lin Wei",
        tier="qi_condensation",
        element="wood",
        stats={
            "attack": 5,
            "defense": 3,
            "agility": 4,
            "intelligence": 3,
            "vitality": 5,
            "spirit": 3,
            "hp": 30,
            "qi": 8,
        },
        skills=["qi_slash"],
    )


def test_battle_dua_sekutu_keduanya_dapat_giliran_pemain():
    """Dengan 2 sekutu, tiap sekutu mendapat giliran perintah (GDD §6.1)."""
    player = _player()  # combatant_from_player, agility 5
    ally = combatant_from_companion(_companion_uji())
    enemy = _wolf()
    battle = Battle(
        allies=[player, ally],
        enemies=[enemy],
        techniques=load_techniques(),
        rng=_FixedRng(0.5),
    )
    acted: set[str] = set()
    while not battle.over and len(acted) < 6:
        if battle.current in battle.allies:
            acted.add(battle.current.name)
            battle.step("attack")  # pemain mengendalikan tiap sekutu
        else:
            battle.step_enemy()
    assert acted >= {"Akar", "Lin Wei"}
```

```python
def test_target_musuh_acak_dengan_banyak_sekutu():
    """Musuh membidik sekutu hidup secara acak (bukan selalu slot 1)."""
    player = _player()
    ally = combatant_from_companion(_companion_uji())
    enemy = _wolf()
    battle = Battle(
        allies=[player, ally],
        enemies=[enemy],
        techniques=load_techniques(),
        rng=_FixedRng(0.5),
    )
    hit_targets: set[str] = set()
    while not battle.over:
        if battle.current in battle.allies:
            battle.step("attack")
        else:
            result = battle.step_enemy()
            if result is not None and result.target:
                hit_targets.add(result.target)
    assert "Lin Wei" in hit_targets
```
_(Dua pelajaran dari simulasi engine aktual:
1. **JANGAN parsing log** (`"menyerang" in line`): wolf behavior `aggressive` memakai teknik sehingga log-nya `"memakai Tebasan Qi (...)"` — filter `"menyerang"` menghasilkan set kosong meski implementasi benar. Ambil `ActionResult.target` langsung dari return `step_enemy()` — andal, bebas format log.
2. **JANGAN pakai defend** di loop pemain: `take_damage` membagi 2 saat defend dan `physical_damage` minimal 1 → damage jadi 0, target tak pernah kena.
**Simulasi terverifikasi**: dengan `_FixedRng(0.5)` + implementasi indexing (Step 3), wolf menyerang index = int(0.5 × 2) = 1 → Lin Wei deterministik. RED (sebelum fix): `{"Akar"}` — GREEN (sesudah): `{"Lin Wei"}`.)_

-- [ ] **Step 2: Run test, pastikan GAGAL** — Expected: test 1 mungkin lulus (alur giliran per-sekutu sudah ada) — **test 2 wajib GAGAL**: `_first_target` selalu slot 0 → `hit_targets == {"Akar"}`, `"Lin Wei" not in hit_targets`.

-- [ ] **Step 3: Implementasi minimal `combat.py`** — hanya satu fungsi. **PENTING: pakai indexing `self._rng.random()` — BUKAN `self._rng.choice()`** — karena helper `_FixedRng` (yang dipakai semua test combat 1v1 lama) hanya punya method `.random()`, bukan `.choice()`; memakai `.choice()` akan memecah suite (AttributeError):
```python
def _first_target(self, unit: Combatant) -> Combatant:
    """Lawan pertama yang hidup; dengan banyak lawan dipilih acak.

    Backward-compatible: 1 lawan ⇒ hasil identik dengan perilaku lama.
    Implementasi memakai indexing rng.random() agar kompatibel dengan
    RNG uji bertipe _FixedRng yang hanya menyediakan random().
    """
    opponents = self._alive(self._opponents(unit))
    if not opponents:
        raise RuntimeError("tidak ada lawan yang hidup")
    if len(opponents) == 1:
        return opponents[0]
    index = int(self._rng.random() * len(opponents))
    return opponents[index]
```
_(Catatan: `_begin_turn` charm tetap `allies[0]` — luar scope; tandai `# ponytail: charm tetap target pertama, acak saat multi-charm dibutuhkan`. **Verifikasi teknis**: dengan `_FixedRng(0.5)` dan 2 sekutu, index = int(0.5 × 2) = 1 → wolf selalu menyerang Lin Wei — deterministik untuk test.)_

-- [ ] **Step 4: Factory `combatant_from_companion`** di `src/models/combatant.py`:

```python
def combatant_from_companion(companion: Companion) -> Combatant:
    """Buat Combatant dari Companion; luka di dunia ikut terbawa (§20.4).

    HP/qi saat ini diwarisi dari Companion (None berarti penuh).
    """
    combatant = Combatant(
        name=companion.name,
        element=companion.element,
        stats={
            key: value
            for key, value in companion.stats.items()
            if key not in ("hp", "qi")
        },
        hp_max=companion.hp_max,
        qi_max=companion.qi_max,
        qi_regen=COMPANION_QI_REGEN,  # konstanta baru, default 2
        skills=list(companion.skills),
    )
    combatant.hp = (
        companion.hp if companion.hp is not None else combatant.hp_max
    )
    combatant.qi = (
        companion.qi if companion.qi is not None else combatant.qi_max
    )
    return combatant
```

-- [ ] **Step 5: Run test, HIJAU** — `pytest tests/test_combat.py -q`.

-- [ ] **Step 6: Full suite + commit**
```bash
pytest -q && ruff check src launcher.py tools tests && ruff format --check src launcher.py tools tests
git add src/engine/combat.py src/models/combatant.py tests/test_combat.py
git commit -m "combat: target musuh acak multi-sekutu + factory rekan (GDD 6.1)"
```

---

### Task 3: game_loop — Multi-Ally Start/Finish + Bond XP

**Files:**
- Modify: `src/core/game_loop.py` (`_start_battle`, `_finish_battle`)
- Test: `tests/test_game_loop.py` (2 test)

**Interfaces:**
- Consumes: `state.party`, `state.party_active`, Task 2.
- Produces: battle dibangun dari protagonis + rekan aktif (semua dikendalikan pemain via `battle_step` eksisting); pasca-battle hp/qi semua sekutu ditulis balik, KO dipulihkan (§20.4), bond XP naik untuk yang hidup.

-- [ ] **Step 1: Test RED** — tambah di `tests/test_game_loop.py`. Helper yang ADA: `_session(tmp_path, seed)` & `_dispatch(session, raw)` — pakai itu. **PENTING**: `_start_battle` membaca rekan dari `state.party` (dict) yang difilter `party_active` — jadi **test wajib mengisi `state.party` dan `state.party_active`** (bukan hanya active). Juga ikuti pola playthrough yang ada (`talk elder_mao` + `breakthrough` sebelum `go ashfall_forest`, karena peta bergating §9):

```python
def _rekrut_lin_wei(session) -> None:
    """Suntik rekan Lin Wei langsung ke state (bukan via event)."""
    from src.models.party import Companion

    session.state.party = [
        Companion(
            id="lin_wei",
            name="Lin Wei",
            tier="qi_condensation",
            element="wood",
            stats={
                "attack": 5,
                "defense": 3,
                "agility": 4,
                "intelligence": 3,
                "vitality": 5,
                "spirit": 3,
                "hp": 30,
                "qi": 8,
            },
            skills=["qi_slash"],
        ).to_dict()
    ]
    session.state.party_active = ["lin_wei"]


def test_battle_dengan_rekan_aktif_dan_bond_xp(tmp_path):
    """Rekan aktif ikut bertarung; bond XP naik setelah menang (GDD §20.3)."""
    session = _session(tmp_path)
    session.new_game("Akar")
    _rekrut_lin_wei(session)
    _dispatch(session, "talk elder_mao")
    session.state.player.add_insight(100)
    _dispatch(session, "breakthrough")
    _dispatch(session, "go ashfall_forest")
    _dispatch(session, "look")
    assert len(session.battle.allies) == 2
    frame = session.battle_frame()
    while not frame.over:
        frame = session.battle_step("attack")
    assert frame.victory is True
    member = next(m for m in session.state.party if m["id"] == "lin_wei")
    assert member["bond_xp"] > 0


def test_rekan_ko_pulih_setelah_pertarungan(tmp_path):
    """KO rekan dipulihkan otomatis pasca battle (GDD §20.4)."""
    session = _session(tmp_path)
    session.new_game("Akar")
    _rekrut_lin_wei(session)
    _dispatch(session, "talk elder_mao")
    session.state.player.add_insight(100)
    _dispatch(session, "breakthrough")
    _dispatch(session, "go ashfall_forest")
    _dispatch(session, "look")
    ally = session.battle.allies[1]
    ally.hp = 0  # simulasi KO
    while not session.battle_frame().over:
        session.battle_step("attack")
    member = next(m for m in session.state.party if m["id"] == "lin_wei")
    assert member["hp"] == member["stats"]["hp"]  # pulih penuh
```

*(Sesuaikan nama musuh `go`/`look` bila gating peta berubah; verifikasi via smoke test Task 7.)*

-- [ ] **Step 2: Run test, pastikan GAGAL** — `_start_battle` masih 1 ally, `_finish_battle` belum tulis balik rekan.

-- [ ] **Step 3: Implementasi `game_loop.py`**:
- `_start_battle`: setelah `ally = combatant_from_player(...)`, muat `state.party_active` → `combatant_from_companion` tiap rekan → `allies=[ally, *rekan]`. Simpan mapping `self._ally_map: dict[str, Combatant]` (id → combatan) untuk tulis balik.
- `_is_player_turn`/`battle_step`: **tanpa perubahan** — alur eksisting sudah memberi giliran pemain untuk tiap sekutu (keputusan "kontrol semua").
- `_finish_battle`: loop semua `battle.allies` — cocokkan ke player (`self._ally`) atau ke `_ally_map`; tulis balik `hp/qi` (min dengan max); yang KO (hp == 0) → pulih penuh (§20.4). Pada kemenangan: `bond_xp += BOND_XP_VICTORY` (konstanta 10) untuk rekan yang hidup; log `"Ikatan dengan Lin Wei menguat (+10 bond XP)."`. Pada kekalahan: protagonis pulih penuh (perilaku lama dipertahankan).
- `status_lines`: biarkan (sudah pakai `_ally.hp` = HP live protagonis; rekan tampil di panel party).

-- [ ] **Step 4: Run test, HIJAU** — `pytest tests/test_game_loop.py -q`.

-- [ ] **Step 5: Full suite + commit**
```bash
pytest -q && ruff check src launcher.py tools tests && ruff format --check src launcher.py tools tests
git add src/core/game_loop.py tests/test_game_loop.py
git commit -m "engine: battle multi-ally start/finish + bond XP + pemulihan KO (GDD 20)"
```

---

### Task 4: Perintah party & swap (gating lokasi aman)

**Files:**
- Modify: `src/core/game_loop.py` (`_cmd_party`, `_cmd_swap` baru), `src/core/input.py` (sudah ada alias `swap`/`ganti`/`party`/`tim` — verifikasi)
- Modify: `src/core/state.py` (field `party_active`)
- Test: `tests/test_game_loop.py` (2 test), `tests/test_save.py` (roundtrip `party_active`)

**Interfaces:**
- Consumes: `Companion` (Task 1), `state`.
- Produces: `party` menampilkan tim + bond/rank; `swap <id>` menukar komposisi **hanya di lokasi aman** (peta tanpa musuh, GDD §20.1). `swap` di combat **tidak diimplementasikan** (`ponytail:` butuh roster cadangan > 3 anggota).

-- [ ] **Step 1: Test RED** — tambah di `tests/test_game_loop.py`:

```python
def test_swap_hanya_di_lokasi_aman(tmp_path):
    """Swap komposisi dilarang di area berbahaya (GDD §20.1)."""
    session = _session(tmp_path)
    session.new_game("Akar")
    _dispatch(session, "go ashfall_forest")  # peta dengan musuh
    lines = _dispatch(session, "swap lin_wei")
    assert any("aman" in line.lower() for line in lines)


def test_party_menampilkan_rekan_dan_bond(tmp_path):
    """Perintah party menampilkan anggota aktif + bond XP (GDD §20.3)."""
    session = _session(tmp_path)
    session.new_game("Akar")
    session.state.party_active = ["lin_wei"]
    lines = _dispatch(session, "party")
    assert any("Lin Wei" in line for line in lines)
    assert any("bond" in line.lower() for line in lines)
```

-- [ ] **Step 2: Run test, pastikan GAGAL** — `_cmd_party` masih stub "Fase 1"; `swap` mengembalikan `UNAVAILABLE` = "Belum tersedia (Fase 1)." (karena `"swap"` belum ada di set `AVAILABLE`, game_loop.py:64).

-- [ ] **Step 3: Implementasi**:
- `state.py`: `party_active: list[str] = field(default_factory=list)`; sertakan di `to_dict`/`from_dict` (backfill `data.get("party_active", [])` — tidak naikkan schema v2, field baru dengan default aman).
- **`game_loop.py` `AVAILABLE` (baris 64-90)**: tambah `"swap"` ke set — tanpa ini dispatch menolak sebelum handler dipanggil (baris 169-170).
- `_cmd_party`: muat `Companion.from_dict` dari `state.party` yang aktif → tampilkan nama, tier, elemen, HP, bond XP, rank. Jika kosong: "Timmu hanya <nama> (rekrut rekan untuk mengisi 3 slot)." (grimdark, sesuai lore).
- `_cmd_swap(command)`: parse arg id rekan. **Hanya berlaku di luar battle.** Cek lokasi aman = `not load_maps().get(location, {}).get("enemies")` → tolak dengan pesan "Hanya di lokasi aman" (GDD §20.1); lalu update `party_active` (max 3). Di dalam battle → tolak dengan pesan jelas (swap combat ditunda, `ponytail:`).
- `party_lines()` (panel UI): panggil `_cmd_party` (tetap, sudah wired).

-- [ ] **Step 4: Test save roundtrip `party_active`** — tambah di `tests/test_save.py` (pola Task 1 Step 5 — pakai `_state()`/`save_game`/`load_game`):

```python
def test_save_roundtrip_party_active(tmp_path):
    """party_active (field baru, backfill aman) ikut tersimpan (GDD §19.2)."""
    state = _state()
    state.party_active = ["lin_wei"]
    save_game(state, "save1", tmp_path)
    loaded = load_game("save1", tmp_path)
    assert loaded.party_active == ["lin_wei"]
```

-- [ ] **Step 5: Run test, HIJAU + full suite + commit**
```bash
pytest -q && ruff check src launcher.py tools tests && ruff format --check src launcher.py tools tests
git add src/core/game_loop.py src/core/state.py tests/test_game_loop.py tests/test_save.py
git commit -m "engine: perintah party + swap gating lokasi aman (GDD 18/20.1)"
```

---

### Task 5: Event add_companion + Validator + Rekrut Lin Wei

**Files:**
- Modify: `src/engine/event.py` (action `add_companion`), `tools/validate.py` (ref companion + whitelist)
- Create: `data/events/lin_wei_recruit.json`
- Test: `tests/test_event.py` (1), `tests/test_validate_tool.py` (1)

**Interfaces:**
- Consumes: `state.party`, `Companion`.
- Produces: action event baru `add_companion` (id + optional rank) yang menambah rekan ke `state.party`; event rekrut Lin Wei dipicu flag `quest103_done` (data eksisting tidak diubah — event baru saja).

-- [ ] **Step 1: Test RED** — tambah di `tests/test_event.py`. **Gunakan helper yang ADA**: `_state()`, `_event(...)`, `_fire(event, state)` → `process_events(state, [event])`. **JANGAN** pakai `_state_dengan_flag`/`run_events` — tidak ada. Set flag via `state.flags[...]` langsung:

```python
def test_action_add_companion_menambah_party():
    """Event add_companion memasukkan rekan ke state.party (GDD §20.2)."""
    state = _state()
    state.flags["quest103_done"] = True
    event = _event(
        trigger=[
            {
                "kind": "flag",
                "flag": "quest103_done",
                "operator": "EQUALS",
                "value": True,
            }
        ],
        actions=[{"kind": "add_companion", "id": "lin_wei"}],
    )
    _fire(event, state)
    assert any(m["id"] == "lin_wei" for m in state.party)
    assert "lin_wei" in state.party_active
```

-- [ ] **Step 2: Run test, pastikan GAGAL** — `run_events` tidak mengenal `add_companion`.

-- [ ] **Step 3: Implementasi `event.py`** — **DUA titik, bukan satu**:
1. **`ACTION_KINDS` (event.py:27-39)**: tambah `"add_companion"` ke set — TANPA ini `_apply_action` langsung `ValueError` (baris 118: `if kind not in ACTION_KINDS`).
2. **`_apply_action`**: tambah cabang (catatan: result memakai `result.logs`, bukan `log_entries`):
```python
elif kind == "add_companion":
    companion_id = action["id"]
    if not any(m.get("id") == companion_id for m in state.party):
        raw = load_companion(companion_id)  # loader di models/party.py
        state.party.append(Companion.from_dict(raw).to_dict())
        state.party_active.append(companion_id)
        result.logs.append(f"{raw['name']} kini bersamamu.")
```
Tambahkan `load_companions(data_dir)` di `models/party.py` (pola `load_enemies`/`load_items`), dengan `load_companion(companion_id)` convenience.

-- [ ] **Step 4: Data `data/events/lin_wei_recruit.json`** (grimdark, konsisten lore Arc 1 — Lin Wei menatapmu setelah kemenangan di kuil):

```json
{
  "id": "lin_wei_recruit",
  "trigger": [{"kind": "flag", "flag": "quest103_done"}],
  "actions": [
    {"kind": "add_companion", "id": "lin_wei"},
    {"kind": "log", "text": "Di gerbang desa, Lin Wei menunggumu — bukan sebagai orang yang dikirim, tapi sebagai orang yang memilih. 'Kuil itu tidak membunuhmu. Itu artinya aku salah tentang takdirmu.' Ia mencabut pedangnya dan bersumpah di bawah abu."}
  ],
  "once": true
}
```

-- [ ] **Step 5: Validator** — whitelist `add_companion` + cek ref id ke `data/companions/`; test RED di `tests/test_validate_tool.py` (event `add_companion` ke id tak dikenal dilaporkan).

-- [ ] **Step 6: Run test, HIJAU + full suite + commit**
```bash
pytest -q && ruff check src launcher.py tools tests && ruff format --check src launcher.py tools tests && python tools/validate.py
git add src/engine/event.py src/models/party.py tools/validate.py data/events tests
git commit -m "event: add_companion + rekrut Lin Wei pasca kuil (GDD 20.2/25.3)"
```

---

### Task 6: UI — Panel Party Bond/HP + HUD Multi-Ally

**Files:**
- Modify: `src/ui/app.py` (sidebar party), `src/core/game_loop.py` (`party_lines`)
- Test: `tests/test_app.py` (1), `tests/test_game_loop.py` (perluasan `test_party_menampilkan...`)

**Interfaces:**
- Consumes: `_cmd_party` (Task 4).
- Produces: panel kanan menampilkan anggota aktif (nama, HP, elemen, bond) dengan markup Rich — konsisten tema grimdark (GDD §14.1).

-- [ ] **Step 1: Test RED** — perluas `party_lines` agar mengembalikan baris ber-markup; test UI memverifikasi panel memuat nama rekan:

```python
def test_sidebar_party_menampilkan_rekan():
    """Panel party UI menampilkan rekan aktif + bond (GDD §14.1)."""
    # (pola pilot query_one('#panel-party') atau unit test party_lines)
    lines = session.party_lines()
    assert any("Lin Wei" in line for line in lines)
    assert any("bond" in line.lower() for line in lines)
```

-- [ ] **Step 2: Implementasi** — `party_lines()`: baris `[bold gold3]PARTY (n/4)[/]`, tiap anggota `[cyan]{nama}[/] · Tier · HP ██ bar · bond {xp}` (reuse `make_bar`), slot kosong `(kosong)`.

-- [ ] **Step 3: Test HIJAU + full suite + commit**
```bash
pytest -q && ruff check src launcher.py tools tests && ruff format --check src launcher.py tools tests
git add src/ui/app.py src/core/game_loop.py tests
git commit -m "ui: panel party bond/HP + slot rekan (GDD 14.1)"
```

---

### Task 7: Verifikasi Akhir + Sinkronisasi Dokumen

**Files:**
- Modify: `GDD.md` (§14.2 tambah `data/companions/`; §20 changelog v1.4; §19.2 catatan `party_active`), `AGENTS.md` (§6 inventori)

-- [ ] **Step 1: GDD** — §14.2 tambah `data/companions/` ke tree; changelog v1.4 (party system); §19.2 catatan `party_active` (field baru dengan backfill, schema tetap v2).
-- [ ] **Step 2: AGENTS §6** — perbarui inventori: tambah rekan/companion.
-- [ ] **Step 3: Gerbang penuh** — `pytest -q` · `ruff check` · `ruff format --check` · `python tools/validate.py` · `graphify update .`.
-- [ ] **Step 4: Smoke test alur nyata** — mainkan: quest103 selesai → event rekrut → `party` menampilkan Lin Wei → battle 2 ally (pemain mengendalikan Akar & Lin Wei bergiliran) → bond XP naik → save/load roundtrip party utuh.
-- [ ] **Step 5: Review dua tahap** — kepatuhan GDD (§20, §24.1 poin 17, grimdark) lalu kualitas kode; commit docs:
```bash
git add GDD.md AGENTS.md
git commit -m "docs: party system GDD v1.4 + inventori AGENTS (GDD 20)"
```

---

## Task 8: DoD (AGENTS §12)

- [ ] Perilaku sesuai GDD §20/§6.1/§24.1 (tanpa formasi/relationship/permadeath).
- [ ] `pytest -q` penuh lulus (RED→GREEN per task).
- [ ] `ruff check` & `ruff format --check` bersih.
- [ ] Docstring Google-style lengkap (Companion, factory, aksi swap, event add_companion).
- [ ] Data JSON valid; ref rekan→teknik/event ter-resolve (`tools/validate.py`).
- [ ] Alur utama terverifikasi (unit + smoke test).
- [ ] Tidak ada kode mati/duplikasi; `ponytail:` pada charm targeting & konstanta.
- [ ] `graphify update .` dijalankan.
- [ ] Tidak melanggar §11 (izin combat.py = Task 2 gate).
- [ ] Ringkasan: perubahan, bukti, hal yang sengaja dilewati.

**Sengaja dilewati (terkunci di Evaluasi):** formasi Front/Middle/Back, role (guardian/healer/dll), relationship multi-atribut (trust/loyalty/affinity/fear/respect), combo technique, camp (talk/cook/train/spar/gift), permadeath di combat, breakthrough/meridian NPC, **`swap` di combat** (butuh roster cadangan > 3 anggota — `ponytail:` di Task 4), binatang roh (rekrut/menetas — Fase 2 lanjutan begitu engine multi-ally stabil), teknik kombinasi resonansi tim (§6.2 bonus — catat `ponytail:` di kode).
