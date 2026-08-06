# Rencana Eksekusi: Variasi Data Arc 1 + Fondasi Arc 2

**Status:** Disetujui — siap eksekusi (AGENTS.md §2.2 ✅)
**Berdasarkan:** `docs/superpowers/specs/2026-08-06-variasi-data-arc1-design.md`
**Branch:** `arc1-final` (pekerja)

---

## 1. Ringkasan Eksekutif

| Sprint | Fokus | Output | Estimasi |
|--------|-------|--------|----------|
| **Sprint A** | Engine `use` + Item Loader | `load_items()` expanded, `_cmd_use` working | 2–3 jam |
| **Sprint B** | Musuh + Teknik Data | +6 enemy, +6 technique (validator green) | 3–4 jam |
| **Sprint C** | Item + Quest + Event | +10 item, +5 quest, +4 NPC, +2 map | 4–5 jam |
| **Sprint D** | E2E + Polish | Full slice test, graphify, full suite | 2–3 jam |
| **Total** | **Arc 1 Variasi + Fondasi Arc 2** | **+28 file data + 2 engine file** | **11–15 jam** |

---

## 2. Sprint A: Engine `use` + Item Loader (TDD)

### A.1 Test RED: `_cmd_use` + `load_items()` parse effect

| # | Test | File | Assert |
|---|------|------|--------|
| A.1 | `test_load_items_parsing_effect` | `tests/test_item_data.py` | `load_items()` return dict with `effect` field parsed |
| A.2 | `test_cmd_use_heal_hp` | `tests/test_game_loop.py` | `use pil_pemulih` → HP restored, item consumed |
| A.3 | `test_cmd_use_restore_qi` | `tests/test_game_loop.py` | `use pil_qi` → Qi restored |
| A.4 | `test_cmd_use_add_insight` | `tests/test_game_loop.py` | `use pil_pemahaman` → insight +X |
| A.5 | `test_cmd_use_invalid` | `tests/test_game_loop.py` | Item tidak ada / tidak punya → error jelas |
| A.6 | `test_cmd_use_tidak_bisa_combat` | `tests/test_game_loop.py` | Saat battle → "Kamu sedang bertarung!" |

### A.2 Implement GREEN

| File | Perubahan |
|------|-----------|
| `src/engine/items.py` | `load_items()` parse `effect` dict; return full item dict |
| `src/core/game_loop.py` | `_cmd_use()` handler; parse effect non-combat (`heal_hp`, `restore_qi`, `add_insight`, `add_meridian`); consume item |
| `tests/test_item_data.py` | Update `EXPECTED_ITEMS` + test schema `effect` |
| `tests/test_game_loop.py` | `_cmd_use` tests + integration |

### A.3 Verify

```bash
pytest tests/test_item_data.py tests/test_game_loop.py::test_cmd_use_* -q
ruff check src tests
python tools/validate.py
```

---

## 3. Sprint B: Musuh + Teknik Data (Batch Validator)

### B.1 Musuh Baru (+6) — Validator per Batch

| Enemy | Tier | Elemen | Type | Map | Quest/Event |
|-------|------|--------|------|-----|-------------|
| `hantu_laut` | qi | Air | Undead | ashfall_forest (night) | fquest |
| `serigala_ember` | qi | Api | Beast | ashfall_forest | fquest |
| `golem_terbakar` | foundation | Api | Construct | ruin_shrine | quest106 |
| `penunggu_hutan` | qi | Kayu | Spirit | peta_baru_1 | fquest |
| `kultisi_merah` | qi | Api | Human | ashfall_forest | holy_order |
| `abyssal_worm` | foundation | Tanah | Beast | peta_baru_2 | ancient_order |

**Validator per batch (2 musuh/batch):**
1. Buat JSON → `python tools/validate.py` → fix error
2. Update `tests/test_enemy_data.py` `EXPECTED_ENEMIES`
3. Update `tests/test_map_data.py` map enemies

### B.2 Teknik Baru (+6) — Validator per Batch

| Teknik | Path | Elemen | Type | Power | Qi | Effect | Tier |
|--------|------|--------|------|-------|----|--------|------|
| `tebasan_air` | sword | Air | physical | 12 | 8 | - | qi |
| `tebasan_angin` | sword | Kayu | physical | 10 | 6 | {weaken:2} | qi |
| `ledakan_qi` | alchemy | Api | technique | 15 | 12 | {burn:3} | qi |
| `benteng_meridian` | formation | Tanah | technique | 0 | 8 | {barrier:3,strengthen:2} | foundation |
| `senjata_roh` | spirit | Metal | technique | 18 | 14 | {weaken:3,seal:2} | foundation |
| `pemulih_jiwa` | spirit | Air | technique | 0 | 10 | {heal_hp:20,restore_qi:10} | foundation |

**Validator per batch (2 teknik/batch):**
1. Buat JSON → `python tools/validate.py`
2. Update `tests/test_technique_data.py` `EXPECTED_TECHNIQUES`
3. Test `test_skills_pemain_berasal_dari_data` update assertion

---

## 4. Sprint C: Item + Quest + NPC + Map (Integrasi)

### C.1 Item Baru (+10) — Schema Effect

| Item | Type | Effect | Grant Source |
|------|------|--------|--------------|
| `pil_pemulih` | consumable | `heal_hp:25` | quest104, event |
| `pil_qi` | consumable | `restore_qi:15` | quest105, shop |
| `pil_pemahaman` | consumable | `add_insight:30` | quest106, drop |
| `ramuan_meridian` | consumable | `add_meridian:1` | event, rare drop |
| `pil_antidot` | consumable | `cure_poison` | holy_order shop |
| `batu_qi` | material | - | craft, drop |
| `esensi_api` | material | - | craft, drop |
| `esensi_air` | material | - | craft, drop |
| `esensi_kayu` | material | - | craft, drop |
| `esensi_tanah` | material | - | craft, drop |

**Validator:** `test_item_data.py` `EXPECTED_ITEMS` + `effect` schema

### C.2 Quest Faksi/Sampingan (+5)

| Quest | Faksi | Type | Objectives | Reward | Requires |
|-------|-------|------|------------|--------|----------|
| `fquest_hutan_ember` | Rebels | faction | talk jati, enemy hantu_laut, enemy serigala_ember | insight 50, gold 40, rebels +20 | quest103 |
| `fquest_abyssal` | Ancient | faction | talk penunggu_hutan, enemy abyssal_worm | insight 60, gold 50, ancient_order +15 | quest106 |
| `fquest_kultisi` | Holy | faction | talk kultisi_merah, enemy kultisi_merah | insight 40, gold 30, holy_order +15 | quest105 |
| `fquest_pelipur` | Rebels | side | talk mira, collect batu_qi x3 | pil_pemulih x2, rebels +10 | quest104 |
| `fquest_fondasi` | Ancient | foundation | enemy golem_terbakar, enemy penunggu_hutan | pil_peneguh_fondasi, ancient_order +10 | foundation_establishment |

### C.3 NPC Baru (+4)

| NPC | Lokasi | Quest | Dialog Key |
|-----|--------|-------|------------|
| `penunggu_hutan` | peta_baru_1 | fquest_abyssal | lore ancient_order |
| `kultisi_merah` | ashfall_forest | fquest_kultisi | holy_order grimdark |
| `penjaga_abyss` | peta_baru_2 | fquest_abyssal | lore abyssal_worm |
| `pedagang_kelana` | peta_baru_1 | shop items | trade esensi |

### C.4 Peta Baru (+2, Foundation Arc 2)

| Map | Tier | Enemies | Unlock |
|-----|------|---------|--------|
| `hutan_kelabu` | 2 | penunggu_hutan, abyssal_worm | event quest106_done |
| `gua_abyss` | 2 | abyssal_worm, golem_terbakar | event quest107_done |

---

## 5. Sprint D: E2E + Polish

### D.1 Test Integrasi

| Test | File | Scenario |
|------|------|----------|
| `test_use_item_flow` | `test_game_loop.py` | grant item via event → use → effect applied |
| `test_quest_faksi_flow` | `test_game_loop.py` | start fquest → complete → reward + event |
| `test_new_enemy_spawn` | `test_game_loop.py` | go new map → look → enemy spawn |
| `test_new_technique_available` | `test_game_loop.py` | breakthrough foundation → technique unlocked |

### D.2 Full Suite

```bash
pytest -q
ruff check src launcher.py tools tests
ruff format --check src launcher.py tools tests
python tools/validate.py
graphify update .
```

---

## 6. Quality Gates per Task (AGENTS §12)

| Gate | Check |
|------|-------|
| TDD | Test RED→GREEN→REFACTOR per file |
| Lint | `ruff check` + `ruff format --check` |
| Test | `pytest -q` (target 280+ passed) |
| Validate | `python tools/validate.py` OK |
| Graph | `graphify update .` |
| Docstring | Google-style (header English, isi Indonesia) |
| Ponytail | Komentar `ponytail:` shortcut + upgrade condition |

---

## 7. Risk & Mitigasi

| Risiko | Prob | Mitigasi |
|--------|------|----------|
| Validator tolak cross-ref | Tinggi | `validate.py` setelah SETIAP file JSON |
| Quest engine bug (faction) | Sedang | Workaround di test (skip known issue) |
| Item effect combat not ready | Rendah | Schema ready, exec deferred (ponytail) |
| Data mati (tidak terpakai) | Sedang | Grant minimal 1× via event/quest reward |

---

## 8. Commit Strategy (AGENTS §9)

| Scope | Contoh Pesan |
|-------|--------------|
| `engine` | `engine: expand load_items parse effect + add _cmd_use` |
| `data` | `data: add 6 enemy + 6 technique (batch 1)` |
| `quest` | `quest: add 5 faction quest + events` |
| `test` | `test: add use item + faction quest integration` |
| `data` | `data: add 10 item + 5 quest + 4 NPC + 2 map` |

---

## 9. Sengaja Dilewati (YAGNI) — Per Design Doc

| Fitur | Alasan |
|-------|--------|
| Efek item combat | Butuh perluas `combat.py` (stabil) |
| Alkimia `refine` | Fase 2+ |
| Artefak grow / binatang roh | Fase 2+ |
| Save schema change | Tidak ada (GDD §19 aman) |

---

## 10. Next Action

**Mulai Sprint A.1:** Test RED `test_load_items_parsing_effect` di `tests/test_item_data.py`

```bash
# 1. Test RED
# 2. Implement load_items() parse effect
# 3. Test GREEN + validate
```