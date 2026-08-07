# Penyelesaian Akhir CotP — Master Plan (Revisi 2, 7 Agustus 2026)

> **Untuk pekerja agen:** WAJIB SUB-SKILL: gunakan `superpowers:subagent-driven-development`
> (disarankan) atau `superpowers:executing-plans` untuk mengimplementasikan rencana ini
> task-by-task. Setiap step memakai checkbox (`- [ ]`) untuk pelacakan.

**Goal:** Menuntaskan sisa proyek *Chronicle of the Past* menuju rilis v1.0 — konten asli Arc 3
(pengganti placeholder), Arc 4 penuh (quest, peta, bos, the_voice), ritual §21.3, 7 keputusan
kunci ending, dan polish Fase 5 — hingga memenuhi target GDD §22 dan Definisi Selesai AGENTS §12.

**Architecture:** Semua gating & narasi lewat event engine data-driven (GDD §15); konten JSON
mengikuti skema GDD §14 dengan pola file nyata di repo (quest208, quest101_intro,
calculate_ending_trigger). Engine baru (ritual, wire ending) ditambahkan di modul stabil-tapi-
bisa-diperluas (`game_loop.py`, `event.py`, `story.py`) — **TIDAK** menyentuh file stabil Fase 0
(`combat.py`, `cultivation.py`, `models/player.py`). Setiap penambahan data diikuti sinkronisasi
konstanta exact-set di tests dan validator.

**Tech Stack:** Python 3.12+ (perintah: `python3`), Rich/Textual, pytest, ruff,
`tools/validate.py`, `graphify`.

## Global Constraints

- **TDD wajib** (AGENTS §2.1): test gagal (RED) → implementasi minimal (GREEN) → refactor →
  commit. Untuk data JSON: RED = test konten/anti-placeholder gagal, GREEN = data valid.
- **File stabil TIDAK disentuh:** `src/engine/combat.py`, `src/engine/cultivation.py`,
  `src/models/player.py` (AGENTS §6). Integrasi lewat `game_loop.py` / modul baru.
- **Schema save tetap v2** — field baru (`ritual_ready`, `ending_points` dst.) memakai backfill
  pola `party_active` (GDD §19.2), tanpa bump schema.
- Bahasa Indonesia untuk semua teks/dialog/narasi; header docstring (Args/Returns) Bahasa
  Inggris; baris ≤ 80; double quotes; import stdlib → third-party → lokal.
- Flag quest wajib `quest<id>_done`; siklus elemen Metal→Kayu→Tanah→Air→Api→Metal.
- Nada **grimdark** (GDD §3.6): tanpa kemenangan bersih, musuh punya alasan konsisten.
- Verifikasi tiap task: `pytest -q` + `ruff check src launcher.py tools tests` +
  `ruff format --check src launcher.py tools tests` + `python3 tools/validate.py`.
  Setelah perubahan kode: `graphify update .`. Commit format `<lingkup>: <ringkasan>` (§9).

---

## Baseline Terverifikasi (7 Agustus 2026 — pengganti semua baseline lama)

Hasil audit langsung repo (lihat `audit_report.md` revisi 2): **460 test passed, 0 failed** ·
ruff & format bersih · validator OK · `main` satu-satunya branch, sinkron remote.

**Sudah selesai — JANGAN dikerjakan ulang:** lint; sistem artefak (`growth_stat`, `max_level`,
`add_artifact_xp`); command `meditate/examine/loot/recall/settings/formation`; sistem formasi
(3 formasi + `formation_skill`); `ending_points` + aksi `add_ending_points`; binatang roh
(rekrut, menetas, evolusi, recall); dialog engine (11 dialog); toko (2 shop); **endings engine
lengkap** (`story.py`: `calculate_ending` + `build_epilogue`, aksi `calculate_ending`,
4 event ending, epilog tampil sekali).

**Kondisi data aktual:** quest 24 utama (16 asli + **8 placeholder quest301–308**) + 13 fquest
(10 asli + **3 placeholder fquest_301–303**) · 49 event · 20 musuh (4 bos sesuai GDD) · 30 teknik
(**semua tier ≤ golden_core**) · 47 item (12 resep, 8 artefak) · 9 peta (7 GDD + 2 ekstra) ·
18 NPC · 6 rekan · 11 dialog · 5 memori · 6 tier kultivasi · 3 formasi · 22 modul src.

**Gap yang harus ditutup (dipetakan ke task):**

| Gap | Task |
|---|---|
| quest301–308 & fquest_301–303 masih placeholder | Task 1–2 |
| Teknik tier `soul_separation`/`void_breaker`/`heaven_challenger` (0) | Task 3 |
| Musuh non-bos Arc 3–4 (15 dari 30) | Task 4 |
| Peta `capital`/`ancient_vault`/`sky_seal` (0) | Task 5 |
| NPC `the_voice` + pendukung Arc 4 (18 dari 25) | Task 6 |
| Quest401–408 (0) + wire `arc4_boss_defeated` | Task 7–8 |
| Ritual + pertarungan dua tahap (GDD §21.3, 0%) | Task 9 |
| 7 keputusan kunci `ending_points` (belum diverifikasi) | Task 10 |
| Resep 12→14, artefak 8→12, memori 5→9 | Task 11 |
| Polish: README, smoke test, balancing ringan | Task 12 |

---

## Task 1: Konten asli quest301–308 (Arc 3 — "Antara Dua Langit")

**Files:**
- Modify: `data/quests/quest301.json` … `data/quests/quest308.json` (8 file, ganti konten)
- Create: `tests/test_quest_data.py` (tambah 1 test anti-placeholder) — modify
- Modify: `data/events/quest301_intro.json` … `data/events/quest308_intro.json` (event intro baru)

**Interfaces:**
- Consumes: skema quest dari `data/quests/quest208.json` (pola nyata: `id/title/type/
  description/objectives/rewards/flags_on_complete/next/category/requires_flag`)
- Consumes: event intro pola `data/events/quest101_intro.json` (`trigger` → `start_quest` → `log`, `once: true`)
- Produces: quest301–308 dengan judul/objektif/reward asli; event `quest30X_intro` yang
  men-start quest berikutnya; flag `quest30X_done` di `flags_on_complete`.

### Rancangan konten (konten aktual, bukan placeholder)

| ID | Judul | requires_flag | Objektif | Reward inti | next |
|---|---|---|---|---|---|
| quest301 | Panggilan Pemberontak | quest208_done | `talk` sera_ember → `map` rebel_hideout | insight 100, rep rebels +5 | quest302 |
| quest302 | Infiltrasi Katedral | quest301_done | `map` holy_cathedral → `enemy` penebus_orde_suci | insight 120, gold 300 | quest303 |
| quest303 | Dua Sisi Pedang | quest302_done | `talk` inquisitor_vega | insight 130, rep holy_order +5 | quest304 |
| quest304 | Martir atau Pejuang | quest303_done | `talk` sera_ember (pilihan faksi via dialog) | insight 150, gold 350 | quest305 |
| quest305 | Entitas Bergerak | quest304_done | `flag` memory_entitas_pertama (via event grant_memory) | insight 200 | quest306 |
| quest306 | Pengkhianat di Antara Kita | quest305_done | `kill_count` pembunuh_gilda (3) | insight 180, gold 400 | quest307 |
| quest307 | Segel yang Retak | quest306_done | `flag` segel_retak_terungkap (via event) | insight 220, artefak `salib_bisu` | quest308 |
| quest308 | Satu Jalan Tersisa | quest307_done | `enemy` bos_inquisitor_agung | insight 400, gold 800, rep faksi terpilih +10 | null |

> Catatan: quest305 & quest307 memakai objektif `flag` yang di-set oleh event (pola
> event intro/cerita). **Format objektif flag di quest.py: `{"kind": "flag", "target":
> "<nama_flag>"}` — tanpa `operator`/`value`** (quest.py: check_objective membaca
> `state.flags.get(objective.target) is True`). Buat event pendukung di Task 1:
> `memory_entitas_pertama` (memori, Task 11) di-trigger `quest304_done`; `segel_retak_terungkap`
> di-trigger `quest305_done`. Quest305 objektif: `{"kind": "flag", "target":
> "memory_entitas_pertama"}`; quest307: `{"kind": "flag", "target": "segel_retak_terungkap"}`.

- [ ] **Step 1: Write the failing test (anti-placeholder)**

Tambahkan di `tests/test_quest_data.py`:

```python
def test_quest_arc3_bukan_placeholder():
    """Quest Arc 3 harus punya judul naratif asli, bukan 'Quest quest30X Title'."""
    import json
    from pathlib import Path

    quests_dir = Path("data/quests")
    for quest_id in ["quest301", "quest302", "quest303", "quest304",
                     "quest305", "quest306", "quest307", "quest308"]:
        raw = json.loads((quests_dir / f"{quest_id}.json").read_text(encoding="utf-8"))
        assert raw["title"] != f"Quest {quest_id} Title", quest_id
        assert len(raw["objectives"]) >= 1, quest_id
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_quest_data.py::test_quest_arc3_bukan_placeholder -q`
Expected: FAIL (semua 8 quest masih `"Quest quest30X Title"`).

- [ ] **Step 3: Write minimal implementation (data)**

Ganti isi 8 file quest301–308 sesuai tabel di atas, memakai pola persis `quest208.json`
(lihat contoh quest301 di bawah). **Tulis judul & deskripsi naratif grimdark Bahasa Indonesia
(GDD §3.6)** — contoh lengkap quest301:

```json
{
  "id": "quest301",
  "title": "Panggilan Pemberontak",
  "type": "main",
  "category": "main",
  "description": "Sera Ember mengirim utusan ke gerbang kota. Pemberontak tahu namamu — dan itu membuatmu tidak nyaman.",
  "requires_flag": "quest208_done",
  "objectives": [
    {"kind": "talk", "target": "sera_ember"},
    {"kind": "map", "target": "rebel_hideout"}
  ],
  "rewards": {"insight": 100, "gold": 100, "reputation": {"rebels": 5}},
  "flags_on_complete": ["quest301_done"],
  "next": "quest302"
}
```

Untuk quest302–308, ulangi pola dengan isi dari tabel rancangan (judul, objektif, reward,
`flags_on_complete: ["quest30X_done"]`, `next`). Quest308: `"next": null` dan reward memakai
`reputation` faksi terpilih pemain (gunakan `{"court": 5}` default atau 0 — disetel Task 10).

- [ ] **Step 4: Buat event intro quest301–308**

Pola (salin `quest101_intro.json`): `quest301_intro` di-trigger `quest208_done`
(`quest_done` shortcut `{"kind": "quest_done", "quest": "quest208"}`) → `start_quest`
`quest301` + `log` narasi. Ulangi untuk quest302–308 dengan trigger quest sebelumnya
(`quest30X_intro` di-trigger `quest30X_done` dari quest sebelumnya). `once: true`.
Tambahkan 8 id ke `EXPECTED_EVENTS` di `tests/test_event_data.py` (pola exact-set baris 11–69).

- [ ] **Step 5: Buat 2 event pendukung**

- `memory_entitas_pertama` event: trigger `quest304_done` → `grant_memory`
  `memory_entitas_pertama` + `set_flag` `memory_entitas_pertama` true (untuk objektif
  quest305 kind=flag) + `log` → `once: true` (memori dibuat di Task 11 — buat file
  `data/story/memory_entitas_pertama.json` di sini supaya validator hijau).
- `segel_retak_terungkap` event: trigger `quest305_done` → `set_flag`
  `segel_retak_terungkap` true + `log` → `once: true`.

- [ ] **Step 6: Run tests & validators**

Run: `pytest tests/test_quest_data.py tests/test_event_data.py -q && python3 tools/validate.py`
Expected: PASS + `OK: semua data valid`.

- [ ] **Step 7: Full verification**

Run: `pytest -q && ruff check src launcher.py tools tests && ruff format --check src launcher.py tools tests`
Expected: 460+ passed, lint & format bersih.

- [ ] **Step 8: Commit**

```bash
git add data/quests/quest301.json data/quests/quest302.json data/quests/quest303.json \
        data/quests/quest304.json data/quests/quest305.json data/quests/quest306.json \
        data/quests/quest307.json data/quests/quest308.json \
        data/events/quest301_intro.json data/events/quest302_intro.json \
        data/events/quest303_intro.json data/events/quest304_intro.json \
        data/events/quest305_intro.json data/events/quest306_intro.json \
        data/events/quest307_intro.json data/events/quest308_intro.json \
        data/events/memory_entitas_pertama.json data/events/segel_retak_terungkap.json \
        data/story/memory_entitas_pertama.json tests/test_quest_data.py tests/test_event_data.py
git commit -m "data(arc3): konten asli quest301-308 + event intro & pendukung"
```

---

## Task 2: Konten asli fquest_301–303 (Arc 3 faction quests)

**Files:**
- Modify: `data/quests/fquest_301.json`, `fquest_302.json`, `fquest_303.json`
- Modify: `data/events/fquest_301_intro.json`, `fquest_302_intro.json`, `fquest_303_intro.json`
  (sesuaikan trigger/aksi bila id quest berubah)
- Modify: `tests/test_quest_data.py` (test anti-placeholder fquest)

**Interfaces:**
- Consumes: pola quest faksi nyata `data/quests/fquest_holyorder_mata.json`
- Produces: 3 quest faksi Arc 3 asli dengan `flags_on_complete: ["fquest_30X_done"]`.

### Rancangan konten

| ID | Judul | Faksi | Objektif | Reward |
|---|---|---|---|---|
| fquest_301 | Ritual yang Dilarang | holy_order (Vega) | `enemy` kultisi_merah (2) → `collect` jimat_roh_liar | insight 100, rep holy_order +8 |
| fquest_302 | Bekas Luka Gilda | guilds (Kestrel) | `kill_count` pembunuh_gilda (2) | gold 500, rep guilds +8 |
| fquest_303 | Jejak Orde Kuno | ancient_order (Warden Kai) | `map` gua_abyss → `enemy` penjaga_abyss | insight 120, rep ancient_order +8 |

- [ ] **Step 1: Write the failing test**

Tambahkan ke `tests/test_quest_data.py`:

```python
def test_fquest_arc3_bukan_placeholder():
    """Faksi quest Arc 3 harus punya judul asli, bukan 'Quest fquest_30X Title'."""
    import json
    from pathlib import Path

    quests_dir = Path("data/quests")
    for quest_id in ["fquest_301", "fquest_302", "fquest_303"]:
        raw = json.loads((quests_dir / f"{quest_id}.json").read_text(encoding="utf-8"))
        assert raw["title"] != f"Quest {quest_id} Title", quest_id
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_quest_data.py::test_fquest_arc3_bukan_placeholder -q`
Expected: FAIL (3 quest placeholder).

- [ ] **Step 3: Write minimal implementation (data)**

Ganti isi fquest_301–303 sesuai tabel; periksa `data/quests/fquest_holyorder_mata.json`
untuk pola `type: "faction"`/`category` yang dipakai repo. Contoh fquest_301:

```json
{
  "id": "fquest_301",
  "title": "Ritual yang Dilarang",
  "type": "faction",
  "category": "faction",
  "description": "Vega mendengar rencana kultus menggelar ritual di lorong bawah Katedral. Dia tidak peduli soal moral — dia peduli pada keheningan.",
  "requires_flag": "quest303_done",
  "objectives": [
    {"kind": "enemy", "target": "kultisi_merah", "count": 2}
  ],
  "rewards": {"insight": 100, "gold": 200, "reputation": {"holy_order": 8}},
  "flags_on_complete": ["fquest_301_done"],
  "next": null
}
```

Ulangi pola untuk fquest_302, fquest_303 (objektif/`rewards` sesuai tabel).

- [ ] **Step 4: Periksa & sesuaikan event intro**

Baca `data/events/fquest_301_intro.json` — pastikan `start_quest` mengarah ke id yang
masih valid dan `log`-nya naratif (sesuaikan teks bila perlu). Validator akan menolak
referensi rusak.

- [ ] **Step 5: Run tests & validators**

Run: `pytest tests/test_quest_data.py -q && python3 tools/validate.py`
Expected: PASS + `OK`.

- [ ] **Step 6: Commit**

```bash
git add data/quests/fquest_301.json data/quests/fquest_302.json data/quests/fquest_303.json \
        data/events/fquest_301_intro.json data/events/fquest_302_intro.json \
        data/events/fquest_303_intro.json tests/test_quest_data.py
git commit -m "data(arc3): konten asli fquest_301-303 (faksi quest Arc 3)"
```

---

## Task 3: Teknik tier tinggi Arc 3–4 (soul_separation, void_breaker, heaven_challenger)

**Files:**
- Create: 6 teknik baru di `data/techniques/` (tier sesuai tabel)
- Modify: `tests/test_technique_data.py` (tambah id ke exact-set / test konten)

**Interfaces:**
- Consumes: skema teknik dari `data/techniques/ikatan_roh.json` (`id/name/path/element/type/
  qi_cost/power/effects/requires.tier`)
- Produces: teknik tier `soul_separation` (3), `void_breaker` (2), `heaven_challenger` (1).

### Rancangan konten

| id | nama | path | element | tier | power |
|---|---|---|---|---|---|
| langkah_seribu | Langkah Seribu Bayangan | sword | metal | soul_separation | 42 |
| pil_pembakar_surgawi | Pil Pembakar Surgawi | alchemy | fire | soul_separation | 38 |
| segel_jiwa_pecah | Segel Jiwa Pecah | formation | earth | soul_separation | 40 |
| seruan_jiwa_tinggi | Seruan Jiwa Tinggi | spirit | water | void_breaker | 55 |
| penebasan_kehampaan | Penebasan Kehampaan | sword | metal | void_breaker | 60 |
| tangan_langit | Tangan Langit | formation | wood | heaven_challenger | 75 |

- [ ] **Step 1: Write the failing test**

Tambahkan ke `tests/test_technique_data.py` (ikuti pola exact-set file itu):

```python
def test_teknik_tier_tinggi_ada():
    """Teknik Arc 3-4 (tier soul_separation ke atas) harus tersedia."""
    import json
    from pathlib import Path

    techniques_dir = Path("data/techniques")
    ids = {"langkah_seribu", "pil_pembakar_surgawi", "segel_jiwa_pecah",
           "seruan_jiwa_tinggi", "penebasan_kehampaan", "tangan_langit"}
    files = {p.stem for p in techniques_dir.glob("*.json")}
    assert ids <= files, f"Kurang: {ids - files}"
    for tid in ids:
        raw = json.loads((techniques_dir / f"{tid}.json").read_text(encoding="utf-8"))
        assert raw["requires"]["tier"] in {"soul_separation", "void_breaker", "heaven_challenger"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_technique_data.py::test_teknik_tier_tinggi_ada -q`
Expected: FAIL (file belum ada).

- [ ] **Step 3: Write minimal implementation (data)**

Contoh `data/techniques/langkah_seribu.json` (pola dari `ikatan_roh.json`):

```json
{
  "id": "langkah_seribu",
  "name": "Langkah Seribu Bayangan",
  "path": "sword",
  "element": "metal",
  "type": "physical",
  "qi_cost": 28,
  "power": 42,
  "effects": [{"status": "bleed", "chance": 0.3, "duration": 2}],
  "requires": {"tier": "soul_separation"}
}
```

Ulangi untuk 5 teknik lain (isi `name`/`element`/`power`/`effects` sesuai tabel; `effects`
boleh kosong `[]` bila tidak ada status). `element` mengikuti siklus GDD §6.2.

- [ ] **Step 4: Run tests & validators**

Run: `pytest tests/test_technique_data.py -q && python3 tools/validate.py`
Expected: PASS + `OK`.

- [ ] **Step 5: Commit**

```bash
git add data/techniques/langkah_seribu.json data/techniques/pil_pembakar_surgawi.json \
        data/techniques/segel_jiwa_pecah.json data/techniques/seruan_jiwa_tinggi.json \
        data/techniques/penebasan_kehampaan.json data/techniques/tangan_langit.json \
        tests/test_technique_data.py
git commit -m "data(technique): teknik tier soul_separation/void_breaker/heaven_challenger"
```

---

## Task 4: Musuh non-bos Arc 3–4

**Files:**
- Create: 6 musuh di `data/enemies/`
- Modify: `tests/test_enemy_data.py` (tambah id ke exact-set)
- Modify: `data/maps/holy_cathedral.json`, `data/maps/rebel_hideout.json`,
  `data/maps/capital.json` (Task 5), `data/maps/ancient_vault.json` (Task 5) — daftarkan
  musuh baru pada `enemies`

**Interfaces:**
- Consumes: skema musuh dari `data/enemies/penebus_orde_suci.json` (`id/name/tier/element/
  behavior/stats/skills/tags/requires_flag`)
- Produces: musuh Arc 3–4 yang valid & ter-referensi peta.

### Rancangan konten

| id | nama | tier | element | tags | peta |
|---|---|---|---|---|---|
| tentara_salib | Tentara Salib Orde Suci | qi_condensation | metal | human, holy_order | holy_cathedral |
| uskup_muda | Uskup Muda | foundation_establishment | fire | human, holy_order | holy_cathedral |
| pemberontak_fanatik | Pemberontak Fanatik | qi_condensation | wood | human, rebels | rebel_hideout |
| pengikut_bisikan | Pengikut Bisikan | golden_core | earth | cultist | ancient_vault |
| agen_kuno | Agen Orde Kuno | golden_core | metal | ancient_order | ancient_vault |
| manifestasi_langit | Manifestasi Langit | soul_separation | air | celestial | sky_seal |

- [ ] **Step 1: Write the failing test** (pola sama dengan Task 3 — exact-set di
  `tests/test_enemy_data.py`; tambahkan 6 id di atas).

- [ ] **Step 2: Run test to verify it fails** — `pytest tests/test_enemy_data.py -q`
  Expected: FAIL.

- [ ] **Step 3: Write minimal implementation (data)**

Contoh `data/enemies/tentara_salib.json` (pola dari `penebus_orde_suci.json`):

```json
{
  "id": "tentara_salib",
  "name": "Tentara Salib Orde Suci",
  "tier": "qi_condensation",
  "element": "metal",
  "behavior": "aggressive",
  "stats": {"attack": 18, "defense": 14, "hp": 90, "qi": 20},
  "skills": ["tebasan_bayangan"],
  "tags": ["human", "holy_order"],
  "requires_flag": "quest302_done"
}
```

Ulangi untuk 5 musuh lain; pastikan `skills` merujuk teknik yang ada di `data/techniques/`
(validator mengecek referensi).

- [ ] **Step 4: Daftarkan musuh di peta**

Tambah entri ke array `enemies` di peta terkait (pola `data/maps/holy_cathedral.json`:
`{"enemy": "<id>", "requires_flag": "<quest30X_done>"}`). Peta `capital`/`ancient_vault`/
`sky_seal` dibuat di Task 5 — bila Task 5 belum selesai, kerjakan Task 5 lebih dulu lalu
kembali ke Step 4.

- [ ] **Step 5: Run tests & validators** — `pytest tests/test_enemy_data.py -q && python3 tools/validate.py`
  Expected: PASS + `OK`.

- [ ] **Step 6: Commit**

```bash
git add data/enemies/tentara_salib.json data/enemies/uskup_muda.json \
        data/enemies/pemberontak_fanatik.json data/enemies/pengikut_bisikan.json \
        data/enemies/agen_kuno.json data/enemies/manifestasi_langit.json \
        data/maps/*.json tests/test_enemy_data.py
git commit -m "data(enemy): musuh non-bos Arc 3-4 + daftar di peta"
```

---

## Task 5: Peta Arc 4 (capital, ancient_vault, sky_seal) + unlock event

**Files:**
- Create: `data/maps/capital.json`, `data/maps/ancient_vault.json`, `data/maps/sky_seal.json`
- Create: `data/events/unlock_capital.json`, `data/events/unlock_ancient_vault.json`,
  `data/events/unlock_sky_seal.json`
- Modify: `tests/test_map_data.py`, `tests/test_event_data.py` (exact-set)

**Interfaces:**
- Consumes: pola peta `data/maps/guild_city.json` + event unlock `data/events/unlock_ruin_shrine.json`
  (`unlock_map` action → `map_<id>_unlocked`)
- Produces: 3 peta Arc 4 + gating via `map_<id>_unlocked`.

### Rancangan konten

| id | nama | tier | isi |
|---|---|---|---|
| capital | Ibukota Ashenfeld | 3 | 0 enemy (politik); unlock quest305_done |
| ancient_vault | Ruang Rahasia Kuno | 4 | enemy: penjaga_abyss, agen_kuno, pengikut_bisikan; unlock quest401_done |
| sky_seal | Segel Langit | 6 | enemy: manifestasi_langit, rasul_langit, suara (Task 7–8); unlock quest407_done |

- [ ] **Step 1: Write the failing test** (pola exact-set `tests/test_map_data.py` — tambah 3 id
  dan 3 event unlock di `tests/test_event_data.py`).

- [ ] **Step 2: Run test to verify it fails** — `pytest tests/test_map_data.py tests/test_event_data.py -q`
  Expected: FAIL (file belum ada).

- [ ] **Step 3: Write minimal implementation (data)**

Contoh `data/maps/capital.json`:

```json
{
  "id": "capital",
  "name": "Ibukota Ashenfeld",
  "description": "Marmer hitam dan kaca patri. Para bangsawan menukar nyawa rakyat untuk duduk di singgasana.",
  "tier": 3,
  "enemies": []
}
```

Contoh event unlock `data/events/unlock_capital.json` (pola `unlock_ruin_shrine.json`):

```json
{
  "id": "unlock_capital",
  "trigger": [{"kind": "quest_done", "quest": "quest305"}],
  "actions": [
    {"kind": "unlock_map", "target": "capital"},
    {"kind": "set_flag", "flag": "map_capital_unlocked", "value": true},
    {"kind": "log", "text": "Gerbang ibukota terbuka di hadapanmu — dan di baliknya, politik yang lebih mematikan daripada pedang."}
  ],
  "once": true
}
```

Ulangi untuk `ancient_vault` (unlock `quest401_done`), `sky_seal` (unlock `quest407_done`).
> **Peta TIDAK punya field `connections`** (skema peta: hanya `id/name/description/tier/enemies`
> — verifikasi `data/maps/guild_city.json`). Gating antar peta murni lewat event
> `unlock_map` + flag `map_<id>_unlocked`; jangan menambah field koneksi.

- [ ] **Step 4: Run tests & validators** — `pytest tests/test_map_data.py tests/test_event_data.py -q && python3 tools/validate.py`
  Expected: PASS + `OK`.

- [ ] **Step 5: Commit**

```bash
git add data/maps/capital.json data/maps/ancient_vault.json data/maps/sky_seal.json \
        data/events/unlock_capital.json data/events/unlock_ancient_vault.json \
        data/events/unlock_sky_seal.json tests/test_map_data.py tests/test_event_data.py
git commit -m "data(arc4): peta capital/ancient_vault/sky_seal + event unlock"
```

---

## Task 6: NPC Arc 4 (the_voice + pendukung)

**Files:**
- Create: `data/npc/the_voice.json` + 2 pendukung (mis. `sekretaris_istana.json`,
  `utusan_kuno.json`)
- Create: `data/dialogues/dialog_the_voice_1.json` (node-graph pilihan keputusan final)
- Modify: `tests/test_npc_data.py`, `tests/test_dialog.py` (exact-set)
- Modify: `data/maps/sky_seal.json` (taruh `the_voice` di NPC peta, bila peta punya field NPC)

**Interfaces:**
- Consumes: pola NPC `data/npc/warden_kai.json` + dialog `data/dialogues/dialog_warden_kai_1.json`
- Produces: `the_voice` (antagonis puncak, GDD §10) + dialog dengan pilihan yang men-set
  `ending_points` (di-wire Task 10).

- [ ] **Step 1: Write the failing test** (pola exact-set `tests/test_npc_data.py` — tambah 3 id
  NPC dan 1 id dialog di `tests/test_dialog.py`).

- [ ] **Step 2: Run test to verify it fails** — `pytest tests/test_npc_data.py tests/test_dialog.py -q`
  Expected: FAIL.

- [ ] **Step 3: Write minimal implementation (data)**

Contoh `data/npc/the_voice.json` (pola `warden_kai.json`):

```json
{
  "id": "the_voice",
  "name": "Suara",
  "location": "sky_seal",
  "role": "Entitas kuno di balik langit — antagonis puncak",
  "greeting": "…Kamu akhirnya datang. Aku sudah mengenalmu sejak sebelum namamu ada.",
  "dialog": ["dialog_the_voice_1"]
}
```

Dialog `dialog_the_voice_1.json` memakai pola node-graph GDD §12.5 — 3 pilihan keputusan
kunci yang masing-masing membawa `actions` `add_ending_points` (mis. `{"kind":
"add_ending_points", "path": "defy", "amount": 10}`). Detail penuh ada di Task 10 —
di sini cukup buat struktur node dengan 3 choice dan `actions` kosong dulu, atau langsung
wire ke Task 10 bila Task 10 dikerjakan berurutan.

- [ ] **Step 4: Run tests & validators** — `pytest tests/test_npc_data.py tests/test_dialog.py -q && python3 tools/validate.py`
  Expected: PASS + `OK`.

- [ ] **Step 5: Commit**

```bash
git add data/npc/the_voice.json data/npc/sekretaris_istana.json data/npc/utusan_kuno.json \
        data/dialogues/dialog_the_voice_1.json tests/test_npc_data.py tests/test_dialog.py
git commit -m "data(arc4): NPC the_voice + pendukung + dialog keputusan final"
```

---

## Task 7: Quest401–408 (Arc 4 — "Menentang Langit") + event intro

**Files:**
- Create: `data/quests/quest401.json` … `data/quests/quest408.json`
- Create: `data/events/quest401_intro.json` … `data/events/quest408_intro.json`
- Modify: `tests/test_quest_data.py`, `tests/test_event_data.py` (exact-set)

**Interfaces:**
- Consumes: pola quest208 (reward `grant_item`), pola event intro Task 1
- Produces: chain quest401→408; quest408 selesai → `quest408_done` (dipakai Task 8 untuk
  wire `arc4_boss_defeated`).

### Rancangan konten

| ID | Judul | requires_flag | Objektif | Reward inti | next |
|---|---|---|---|---|---|
| quest401 | Ruang yang Terkunci | quest308_done | `map` ancient_vault → `talk` warden_kai | insight 300 | quest402 |
| quest402 | Penjaga Terakhir | quest401_done | `enemy` penjaga_abyss | insight 320, gold 500 | quest403 |
| quest403 | Echo Terakhir | quest402_done | `flag` rahasia_terungkap (via event grant_memory) | insight 400 | quest404 |
| quest404 | Keputusan di Ambang | quest403_done | `talk` the_voice (keputusan kunci #7, Task 10) | insight 200 | quest405 |
| quest405 | Ritual Persiapan | quest404_done | `flag` ritual_ready (via Task 9) | insight 300, artefak ritual | quest406 |
| quest406 | Rasul Langit | quest405_done | `enemy` rasul_langit | insight 800, gold 1000 | quest407 |
| quest407 | Pintu Langit Terbuka | quest406_done | `map` sky_seal | insight 400 | quest408 |
| quest408 | Suara | quest407_done | `enemy` suara | insight 1500, gold 2000 | null |

- [ ] **Step 1: Write the failing test** (pola exact-set: tambah quest401–408 ke
  `EXPECTED_QUESTS` di `tests/test_quest_data.py` + 8 event intro ke `EXPECTED_EVENTS`).
  Expected setelah run: FAIL (file belum ada).

- [ ] **Step 2: Run test to verify it fails** — `pytest tests/test_quest_data.py tests/test_event_data.py -q`
  Expected: FAIL.

- [ ] **Step 3: Write minimal implementation (data)**

Ulangi pola quest dari Task 1. Contoh quest405 (ritual, memakai flag dari Task 9):

```json
{
  "id": "quest405",
  "title": "Ritual Persiapan",
  "type": "main",
  "category": "main",
  "description": "Warden Kai membaca gulungan tua: tanpa ritual, melawan Suara sama saja bunuh diri.",
  "requires_flag": "quest404_done",
  "objectives": [
    {"kind": "flag", "target": "ritual_ready"}
  ],
  "rewards": {"insight": 300, "gold": 300, "reputation": {"ancient_order": 10}},
  "flags_on_complete": ["quest405_done"],
  "next": "quest406"
}
```

Quest403: objektif `{"kind": "flag", "target": "rahasia_terungkap"}` — buat event
pendukung `rahasia_terungkap` (trigger `quest402_done` → `grant_memory`
`memory_arc4_truth` + `set_flag` `rahasia_terungkap` true; memori dibuat Task 11).
Quest401–408 reward memakai `grant_item` bila perlu (pola quest208).

- [ ] **Step 4: Buat 8 event intro quest401–408** (pola Task 1; `quest401_intro` trigger
  `quest308_done`, sisanya rantai quest sebelumnya).

- [ ] **Step 5: Run tests & validators** — `pytest tests/test_quest_data.py tests/test_event_data.py -q && python3 tools/validate.py`
  Expected: PASS + `OK`.

- [ ] **Step 6: Commit**

```bash
git add data/quests/quest401.json data/quests/quest402.json data/quests/quest403.json \
        data/quests/quest404.json data/quests/quest405.json data/quests/quest406.json \
        data/quests/quest407.json data/quests/quest408.json \
        data/events/quest401_intro.json data/events/quest402_intro.json \
        data/events/quest403_intro.json data/events/quest404_intro.json \
        data/events/quest405_intro.json data/events/quest406_intro.json \
        data/events/quest407_intro.json data/events/quest408_intro.json \
        data/events/rahasia_terungkap.json data/story/memory_arc4_truth.json \
        tests/test_quest_data.py tests/test_event_data.py
git commit -m "data(arc4): quest401-408 + event intro & memori rahasia"
```

---

## Task 8: Wire `arc4_boss_defeated` → ending terpicu in-game

**Files:**
- Create: `data/enemies/rasul_langit.json`, `data/enemies/suara.json` (2 bos Arc 4)
- Create: `data/events/suara_defeated.json` (trigger `quest408_done` → set
  `arc4_boss_defeated` true)
- Modify: `tests/test_enemy_data.py`, `tests/test_event_data.py` (exact-set)
- Modify: `tests/test_game_loop.py` (test integrasi: bos kalah → ending muncul)

**Interfaces:**
- Consumes: `_finish_battle` di `game_loop.py` (baris ±1801) yang memanggil `_run_quests()` +
  `_run_events()` setelah kemenangan; event `calculate_ending_trigger` (sudah ada, trigger
  `arc4_boss_defeated`); `calculate_ending`/`build_epilogue` di `story.py`
- Produces: flag `arc4_boss_defeated` diset setelah `quest408_done` → `calculate_ending` →
  `ending_<jalur>_win` → event ending + epilog tampil satu pass.

- [ ] **Step 1: Write the failing test**

Tambahkan ke `tests/test_game_loop.py` (pola test integrasi yang sudah ada untuk ending):

```python
def test_bos_final_kalah_memantik_ending_in_game():
    """quest408 selesai (bos suara kalah) → arc4_boss_defeated → ending muncul."""
    from src.core.state import GameState
    from src.engine.event import load_events, process_events

    state = GameState()
    state.ending_points = {"defy": 50, "seal": 10, "reconcile": 10}
    state.flags["quest408_done"] = True

    logs = list(process_events(state, load_events()).logs)
    assert "arc4_boss_defeated" in state.flags and state.flags["arc4_boss_defeated"] is True
    assert state.flags.get("ending_defy_win") is True
    assert any("EPILOG" in line for line in logs)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_game_loop.py::test_bos_final_kalah_memantik_ending_in_game -q`
Expected: FAIL (`arc4_boss_defeated` tidak pernah diset).

- [ ] **Step 3: Write minimal implementation (data)**

`data/events/suara_defeated.json`:

```json
{
  "id": "suara_defeated",
  "trigger": [{"kind": "quest_done", "quest": "quest408"}],
  "actions": [
    {"kind": "set_flag", "flag": "arc4_boss_defeated", "value": true},
    {"kind": "log", "text": "Langit di atas Ashenfeld terbelah sejenak — lalu diam."}
  ],
  "once": true
}
```

Bos `rasul_langit.json` & `suara.json`: pola `data/enemies/bos_inquisitor_agung.json`
(`tags: ["boss"]`, `requires_flag` quest terkait, tier `void_breaker` & `heaven_challenger`,
stats agresif, `behavior: "boss"` bila repo memakai field itu — periksa file bos existing).
Daftarkan di `data/maps/sky_seal.json` (Task 5) dengan `requires_flag` quest405/quest407.

- [ ] **Step 4: Run tests & validators**

Run: `pytest tests/test_game_loop.py tests/test_enemy_data.py tests/test_event_data.py -q && python3 tools/validate.py`
Expected: PASS + `OK` (alur: `quest408_done` → `suara_defeated` → `arc4_boss_defeated` →
`calculate_ending_trigger` (urutan abjad file: `c` < `e`) → `ending_defy` + epilog).

- [ ] **Step 5: Full verification** — `pytest -q && ruff check src launcher.py tools tests && ruff format --check src launcher.py tools tests`
  Expected: semua hijau.

- [ ] **Step 6: Commit**

```bash
git add data/enemies/rasul_langit.json data/enemies/suara.json \
        data/events/suara_defeated.json data/maps/sky_seal.json \
        tests/test_game_loop.py tests/test_enemy_data.py tests/test_event_data.py
git commit -m "feat(story): wire arc4_boss_defeated setelah bos final + bos rasul_langit & suara"
```

---

## Task 9: Ritual & pertarungan dua tahap (GDD §21.3)

**Files:**
- Create: `src/systems/ritual.py` (engine ritual: cek syarat, set `ritual_ready`)
- Create: `data/events/ritual_prepare.json` (log narasi ritual)
- Modify: `src/core/game_loop.py` (command `ritual` + handler `_cmd_ritual`)
- Modify: `src/core/state.py` (field `ritual_ready: bool = False` + normalize/to_dict/from_dict
  backfill)
- Modify: `src/core/save.py` (backfill `ritual_ready` di load)
- Test: `tests/test_ritual.py` (baru)

**Interfaces:**
- Consumes: `GameState` (`inventory`, `formation_active`, `party_active`, `flags`), pola
  command `_cmd_formation` di `game_loop.py`
- Produces: `check_ritual_ready(state) -> tuple[bool, list[str]]` (syarat: artefak ritual
  `pedang_taring_naga` di inventory + formasi terpasang + tim ≥ 2 anggota) dan
  `_cmd_ritual(command) -> list[str]` yang men-set `state.ritual_ready` bila syarat
  terpenuhi, lalu quest405 (kind=flag `ritual_ready`) bisa selesai.

- [ ] **Step 1: Write the failing test**

`tests/test_ritual.py`:

```python
import pytest
from src.core.state import GameState
from src.systems.ritual import check_ritual_ready


def test_ritual_belum_siap_tanpa_syarat():
    state = GameState()
    ok, reasons = check_ritual_ready(state)
    assert ok is False
    assert len(reasons) >= 1


def test_ritual_siap_dengan_semua_syarat():
    state = GameState()
    state.inventory["items"] = {"pedang_taring_naga": 1}
    state.formation_active = "jaring_naga"
    state.party_active = ["lin_wei"]
    ok, reasons = check_ritual_ready(state)
    assert ok is True, reasons
    assert reasons == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_ritual.py -q`
Expected: FAIL (`ImportError: cannot import name 'check_ritual_ready'`).

- [ ] **Step 3: Write minimal implementation**

`src/systems/ritual.py`:

```python
"""Sistem ritual persiapan melawan entitas kuno (GDD §21.3).

Ritual butuh artefak kunci, formasi terpasang, dan tim yang cukup.
Syarat penuh hidup di data event; fungsi ini hanya pengecek state.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.state import GameState

RITUAL_ARTIFACT = "pedang_taring_naga"
RITUAL_MIN_PARTY = 2


def check_ritual_ready(state: GameState) -> tuple[bool, list[str]]:
    """Periksa apakah ritual persiapan sudah lengkap.

    Args:
        state: GameState permainan saat ini.

    Returns:
        Tuple (siap, daftar alasan yang belum terpenuhi). ``siap`` True
        bila semua syarat terpenuhi.
    """
    reasons: list[str] = []
    items = state.inventory.get("items", {}) if hasattr(state.inventory, "get") else {}
    if items.get(RITUAL_ARTIFACT, 0) < 1:
        reasons.append("Artefak ritual (Pedang Taring Naga) belum ada.")
    if not state.formation_active:
        reasons.append("Formasi belum terpasang.")
    if len(state.party_active) + 1 < RITUAL_MIN_PARTY:
        reasons.append("Tim terlalu kecil.")
    return (not reasons, reasons)
```

> Catatan implementer: sesuaikan akses inventory dengan struktur nyata `GameState`
> (periksa `src/core/state.py` — key `inventory["items"]` dari GDD §19.2). Bila struktur
> berbeda, samakan test + implementasi pada struktur nyata (jangan ubah schema save).

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_ritual.py -q`
Expected: PASS.

- [ ] **Step 5: Tambah command `ritual` di game_loop**

Handler `_cmd_ritual(command)` (pola `_cmd_formation`): panggil `check_ritual_ready`,
kalau siap → `state.ritual_ready = True` + log narasi + `state.flags["ritual_ready"] =
True` (quest405 kind=flag membaca flags) — **set keduanya** supaya quest engine dan event
engine konsisten. Daftarkan di dispatcher command `game_loop.py` (pola handler lain).
Field `ritual_ready` ditambahkan ke `state.py` + `save.py` backfill (pola `formation_active`).

- [ ] **Step 6: Tambah event narasi `ritual_prepare.json`**

Trigger `{"kind": "flag", "flag": "ritual_ready", "operator": "EQUALS", "value": true}`
→ `log` narasi ritual selesai + `set_flag` `ritual_prepared_narrated` (guard), `once: true`.
Tambahkan ke `EXPECTED_EVENTS` di `tests/test_event_data.py`.

- [ ] **Step 7: Run tests & full verification**

Run: `pytest -q && ruff check src launcher.py tools tests && ruff format --check src launcher.py tools tests && python3 tools/validate.py`
Expected: semua hijau. Lalu `graphify update .`.

- [ ] **Step 8: Commit**

```bash
git add src/systems/ritual.py src/core/game_loop.py src/core/state.py src/core/save.py \
        data/events/ritual_prepare.json tests/test_ritual.py tests/test_event_data.py
git commit -m "feat(ritual): sistem ritual persiapan GDD §21.3 + command ritual"
```

---

## Task 10: 7 keputusan kunci → `ending_points` (GDD §21.1)

**Files:**
- Modify: 7 titik keputusan (dialog/quest/event existing + baru) untuk menambah aksi
  `add_ending_points`
- Modify: `data/dialogues/dialog_the_voice_1.json` (3 pilihan → 3 jalur)
- Modify: `tests/test_dialog.py`, `tests/test_event.py` (test aksi `add_ending_points`)

**Interfaces:**
- Consumes: aksi `add_ending_points` di `event.py` (sudah ada: `{"kind":
  "add_ending_points", "path": "defy|seal|reconcile", "amount": int}`)
- Produces: 7 keputusan kunci yang menambah `state.ending_points` → `calculate_ending`
  punya data nyata dari playthrough (bukan hanya save yang diedit).

### Rancangan 7 titik (sesuai GDD §21.1: 1 Arc 1, 2 tiap Arc 2–4)

| # | Arc | Titik | Pilihan | Poin |
|---|---|---|---|---|
| 1 | 1 | `dialog_elder_mao_1.json` (node "ready") | pilihan baru "Jalan sendiri" / "Patuh desa" | defy +10 / seal +10 |
| 2 | 2 | `dialog_fang_yue_1.json` | dukung sekte / bantu gilda | seal +10 / reconcile +10 |
| 3 | 2 | `dialog_kestrel_1.json` | terima kontrak / tolak | defy +10 / reconcile +10 |
| 4 | 3 | `dialog_sera_ember_1.json` | bergabung pemberontak / tahan diri | defy +10 / seal +10 |
| 5 | 3 | `dialog_inquisitor_vega_1.json` | serang orde / cari jalan damai | defy +10 / reconcile +10 |
| 6 | 4 | `dialog_warden_kai_1.json` | ikuti ritual penuh / hemat sumber | reconcile +10 / seal +10 |
| 7 | 4 | `dialog_the_voice_1.json` | 3 pilihan: hancurkan / segel / rekonsiliasi | defy/seal/reconcile +15 |

- [ ] **Step 1: Write the failing test**

Tambahkan ke `tests/test_dialog.py`:

```python
def test_dialog_keputusan_kunci_menambah_ending_points():
    """Pilihan keputusan kunci memuat aksi add_ending_points yang valid."""
    import json
    from pathlib import Path

    dialogues_dir = Path("data/dialogues")
    for dialog_id in ["dialog_elder_mao_1", "dialog_fang_yue_1", "dialog_kestrel_1",
                      "dialog_sera_ember_1", "dialog_inquisitor_vega_1",
                      "dialog_warden_kai_1", "dialog_the_voice_1"]:
        raw = json.loads((dialogues_dir / f"{dialog_id}.json").read_text(encoding="utf-8"))
        found = False
        for node in raw["nodes"].values():
            for choice in node.get("choices", []):
                for action in choice.get("actions", []):
                    if action.get("kind") == "add_ending_points":
                        assert action["path"] in {"defy", "seal", "reconcile"}
                        found = True
        assert found, f"{dialog_id}: tidak ada keputusan kunci"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_dialog.py::test_dialog_keputusan_kunci_menambah_ending_points -q`
Expected: FAIL (dialog existing belum punya aksi `add_ending_points`; `dialog_the_voice_1`
belum dibuat di Task 6 — kerjakan Task 6 dulu bila perlu).

- [ ] **Step 3: Write minimal implementation (data)**

Tambahkan `actions: [{"kind": "add_ending_points", "path": "<jalur>", "amount": 10}]`
pada pilihan yang dimaksud di 6 dialog existing (hati-hati: **jangan mengubah struktur
node/pilihan yang sudah ada** — tambah pilihan baru atau tambah `actions` ke pilihan
yang paling sesuai narasi). Untuk `dialog_the_voice_1` (Task 6), buat 3 pilihan final:

```json
{
  "text": "Hancurkan langit ini.",
  "next": null,
  "actions": [{"kind": "add_ending_points", "path": "defy", "amount": 15}]
}
```

Ulangi untuk `seal` dan `reconcile` (+15).

- [ ] **Step 4: Run tests & validators**

Run: `pytest tests/test_dialog.py tests/test_event.py -q && python3 tools/validate.py`
Expected: PASS + `OK` (pastikan validator mengenali `add_ending_points` sebagai kind
aksi valid — sudah terdaftar di `ACTION_KINDS` event.py).

- [ ] **Step 5: Commit**

```bash
git add data/dialogues/dialog_elder_mao_1.json data/dialogues/dialog_fang_yue_1.json \
        data/dialogues/dialog_kestrel_1.json data/dialogues/dialog_sera_ember_1.json \
        data/dialogues/dialog_inquisitor_vega_1.json data/dialogues/dialog_warden_kai_1.json \
        data/dialogues/dialog_the_voice_1.json tests/test_dialog.py
git commit -m "data(story): 7 keputusan kunci add_ending_points (GDD §21.1)"
```

---

## Task 11: Pelengkap data (memori 5→9, resep 12→14, artefak 8→12)

**Files:**
- Create: 4 memori di `data/story/` (`memory_entitas_pertama` sudah dibuat Task 1;
  tambah `memory_arc3_choice`, `memory_arc4_truth` (sudah Task 7), `memory_arc4_choice`,
  `memory_arc1_kuil` — sesuaikan agar total 9)
- Create: 2 resep & 4 artefak di `data/items/`
- Modify: `tests/test_items.py`, `tests/test_event_data.py` (bila ada exact-set memori),
  `tools/validate.py` (bila skema memori perlu validasi — cek dulu)

**Interfaces:**
- Consumes: pola memori `data/story/memory_arc2_climax.json` (`id/title/text`); pola item
  `data/items/pedang_awan_hitam.json` (artefak: `growth_stat`/`max_level`); pola resep
  `data/items/resep_pemulih.json`
- Produces: total 9 memori, 14 resep, 12 artefak sesuai GDD §22.

### Rancangan

| Memori | Arc | trigger event |
|---|---|---|
| memory_arc1_kuil | 1 | `shrine_reveal` (ada) — event grant_memory baru bila perlu |
| memory_arc3_choice | 3 | `memory_entitas_pertama` event (Task 1) |
| memory_arc4_truth | 4 | `rahasia_terungkap` (Task 7) |
| memory_arc4_choice | 4 | `dialog_the_voice_1` / event quest404 |

Resep baru: `resep_pil_apocalypse` (Arc 4, butuh 3 bahan), `resep_pil_kehampaan` (Arc 4).
Artefak baru: `mahkota_ashfall` (Arc 4, growth_stat), `mantra_bisikan` (Arc 4),
`cincin_roh_kenabian` (Arc 3), `talisman_penyegel` (Arc 4 — artefak ritual).

- [ ] **Step 1: Write the failing test** (pola exact-set test item/memori — periksa
  `tests/test_items.py`; tambah id resep/artefak yang belum terdaftar).

- [ ] **Step 2: Run test to verify it fails** — `pytest tests/test_items.py -q`
  Expected: FAIL (file belum ada).

- [ ] **Step 3: Write minimal implementation (data)** — contoh artefak Arc 4:

```json
{
  "id": "talisman_penyegel",
  "name": "Talisman Penyegel",
  "type": "artifact",
  "tier": "surgawi",
  "growth_stat": "spirit",
  "max_level": 5,
  "description": "Ukiran rune kuno yang menahan sesuatu di balik langit. Sekarang, menahanmu juga."
}
```

- [ ] **Step 4: Run tests & validators** — `pytest tests/test_items.py tests/test_event_data.py -q && python3 tools/validate.py`
  Expected: PASS + `OK`.

- [ ] **Step 5: Commit**

```bash
git add data/story/*.json data/items/resep_pil_apocalypse.json \
        data/items/resep_pil_kehampaan.json data/items/mahkota_ashfall.json \
        data/items/mantra_bisikan.json data/items/cincin_roh_kenabian.json \
        data/items/talisman_penyegel.json data/events/*.json tests/test_items.py
git commit -m "data: lengkapi memori 9, resep 14, artefak 12 (GDD §22)"
```

---

## Task 12: Polish Fase 5 — README, smoke test, balancing ringan

**Files:**
- Modify: `README.md` (instruksi install + cara main + status proyek)
- Create: `tools/smoke_playthrough.py` (jalan otomatis Arc 1→4 tanpa UI, sampai ending)
- Modify: `tests/test_docs.py` (bila memvalidasi README/daftar fitur)
- Modify: data keseimbangan ringan (harga jual, insight reward) bila smoke test
  menunjukkan ketidakseimbangan — **setelah data smoke, bukan sebelum**

**Interfaces:**
- Consumes: `GameSession`/`dispatch` dari `game_loop.py` (pola smoke test yang sudah ada di
  sesi sebelumnya: `s.new_game('Akar')` + `s.dispatch(Command(...))`)
- Produces: smoke script yang membuktikan game bisa dimulai → breakthrough → bertarung →
  menyelesaikan quest → mencapai ending, tanpa crash.

- [ ] **Step 1: Write the failing test (smoke)**

`tools/smoke_playthrough.py` — alur: `new_game` → `cultivate` → `rest` → `go ashfall_forest`
→ `look` → battle `attack` (looping sampai menang) → `go village_emberfall` →
`talk elder_mao` → `use pil_qi` → simpan `assert` di tiap langkah. Jalankan:
`python3 tools/smoke_playthrough.py` — Expected awal: berjalan (bukan test merah —
ini smoke, bukan unit test; validasinya exit code 0).

- [ ] **Step 2: Verifikasi** — `python3 tools/smoke_playthrough.py && pytest -q && ruff check src launcher.py tools tests && ruff format --check src launcher.py tools tests && python3 tools/validate.py`

- [ ] **Step 3: Update README** — ganti status basi ("Fase 0") dengan status rilis v1.0;
  tambah cara main, daftar perintah GDD §18, dan deskripsi jalur ending.

- [ ] **Step 4: Commit**

```bash
git add README.md tools/smoke_playthrough.py tests/test_docs.py
git commit -m "docs: README rilis v1.0 + smoke playthrough tool"
```

---

## Self-Review (dilakukan sebelum handoff)

1. **Spec coverage** — file rekomendasi `rencana_penyelesaian_cotp.md` P1–P5 dipetakan:
   P1 (sudah selesai di baseline), P2 (sudah selesai), P3 → Task 1–2 & 4, P4 → Task 5–9,
   P5 → Task 12. Gap audit (`audit_report.md` revisi 2) semuanya punya task: quest
   placeholder (1–2), teknik tier (3), musuh (4), peta (5), NPC (6), quest401–408 & wire
   (7–8), ritual (9), keputusan kunci (10), data pelengkap (11), polish (12). ✅
2. **Placeholder scan** — tidak ada "TBD"/"similar to Task N" di step inti; tiap task punya
   test nyata + contoh implementasi nyata. Rancangan konten quest/musuh/teknik memakai
   tabel konten aktual, bukan deskripsi samar. ✅
3. **Type consistency** — `check_ritual_ready(state) -> tuple[bool, list[str]]` dipakai
   konsisten di Task 9 test & implementasi; `add_ending_points` dipakai Task 10 dengan
   format `{"kind", "path", "amount"}` yang sama; flag `quest<id>_done`, `arc4_boss_defeated`,
   `ending_<jalur>_win`, `ritual_ready` konsisten antar task. ✅

**Catatan ketergantungan eksekusi:** Task 1→2→4→5→6→7→8 berurutan (quest chain); Task 3
independen; Task 9 butuh Task 5 (peta) & 7 (quest405); Task 10 butuh Task 6 (dialog
the_voice); Task 11 tersebar (memori dikonsumsi Task 1 & 7); Task 12 terakhir.

---

*Rencana ini menggantikan baseline rencana lama (fase4-master-plan, master-plan-penyelesaian)
yang menargetkan ending engine — sudah selesai dan di-merge ke main (commit 4c6e92e). Segala
keputusan desain tetap mengacu GDD.md; perubahan yang bertentangan dengan GDD §24.1 wajib
diskusi dulu (AGENTS §11).*
