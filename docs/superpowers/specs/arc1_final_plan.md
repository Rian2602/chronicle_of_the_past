# Rencana Implementasi Final: Arc 1 Penuh + Choice Engine (Hybrid)

**Status:** Disetujui pengguna — siap eksekusi (AGENTS.md §2.2 ✅)
**Berdasarkan:** GDD §22 (Target Konten Arc 1), §15 (Event Engine), §21 (Ending), §23 (Fase 1)
**Kombinasi:** Plan transisi minimal + BIG PICKLE Arc 1 lengkap + `prompt_choice` engine
**Tanggal:** 2026-08-06

---

## 1. Ringkasan Eksekutif

| Sprint | Fokus | Output | Estimasi |
|--------|-------|--------|----------|
| **Sprint 1** | **Transisi Arc 1→2 + Choice Engine** | `prompt_choice` action, `choose` command, event `quest103_done`, memory, quest201, maps sect_azure/guild_city | 4–6 jam |
| **Sprint 2** | **Arc 1 Content Lengkap (Data Only)** | Quest 104-108 (5), 2 faksi quest, 4 NPC, 4 musuh, 3 teknik | 6–8 jam |
| **Sprint 3** | **Integrasi E2E + Polish** | Full flow test, graphify, full suite, review | 2–3 jam |
| **Total** | **Arc 1 "playable penuh" per GDD §22** | 8 quest utama, 2 quest faksi, 6 NPC, 7 musuh, 6 teknik | **12–17 jam** |

---

## 2. Sprint 1: Transisi + Choice Engine (HARI INI)

### 2.1 Engine Change: `prompt_choice` Action + `choose` Command

**File Baru/Diubah:**
- `src/engine/event.py` — tambah `prompt_choice` di `_apply_action`
- `src/core/game_loop.py` — tambah `_cmd_choose(command)`
- `tests/test_event.py` — test `prompt_choice`
- `tests/test_game_loop.py` — test `choose` command

**Desain `prompt_choice` (Disetujui):**
```json
{
  "kind": "prompt_choice",
  "options": [
    {
      "key": "a",
      "text": "Lapor sungguhan",
      "set_flag": "lapor_jujur",
      "change_reputation": {"holy_order": 10, "rebels": -10},
      "log": "Kamu melaporkan apa yang kau lihat."
    },
    {
      "key": "b",
      "text": "Menyesatkan",
      "set_flag": "lapor_bohong",
      "change_reputation": {"rebels": 10, "holy_order": -10},
      "log": "Kamu memutarbalikkan fakta."
    }
  ]
}
```

**State Management:**
- `state.flags["pending_choice"] = {event_id, options}` (pakai `flags` dict existing → **no schema change**, AGENTS.md §11 safe)
- `choose <key>` → apply option → clear `pending_choice` → run `_run_quests()` + `_run_events()`
- **Ponytail:** opsi dibatasi `set_flag`, `change_reputation`, `log`; upgrade bila butuh efek lebih kaya.

### 2.2 Transisi Arc 1→2 (Data)

| File | Deskripsi |
|------|-----------|
| `data/events/quest103_done.json` | Trigger `quest_done: quest103` → unlock `sect_azure` + `guild_city`, grant `memory_arc1_complete`, log narasi, `start_quest: quest201` |
| `data/story/memory_arc1_complete.json` | Echo memori: "Anak yang Ditunggu" + Lin Wei tahu |
| `data/quests/quest201.json` | Entry Arc 2: `requires_flag: quest103_done`, objectives: `map sect_azure`, `talk fang_yue`, `next: null` |
| `data/maps/sect_azure.json` | Sekte Awan Biru, tier 2, enemies: [] |
| `data/maps/guild_city.json` | Kota Gilda, tier 2, enemies: [] |

### 2.3 Test Sprint 1 (TDD)

| Test | File | Assert |
|------|------|--------|
| `test_action_prompt_choice` | `tests/test_event.py` | Event fire → `pending_choice` set, options tersimpan |
| `test_cmd_choose_valid` | `tests/test_game_loop.py` | `choose a` → apply flag/rep/log, clear pending, cascade quests+events |
| `test_cmd_choose_invalid_key` | `tests/test_game_loop.py` | Key salah → error, pending_choice tetap |
| `test_event_quest103_done_unlock_maps` | `tests/test_event.py` | Quest103 done → maps unlocked, memory granted, quest201 started |
| `test_arc1_to_arc2_transisi` | `tests/test_game_loop.py` | Full flow: quest101→103→event→maps→quest201→go sect_azure |

### 2.4 Update Test Expected Sets

```python
# tests/test_event_data.py
EXPECTED_EVENTS += {"quest103_done"}

# tests/test_quest_data.py  
EXPECTED_QUESTS += {"quest201"}

# tests/test_map_data.py
EXPECTED_MAPS += {"sect_azure", "guild_city"}
```

---

## 3. Sprint 2: Arc 1 Content Lengkap (Data Only)

### 3.1 Quest Utama 104-108 (Chain Lewat Event)

| Quest | ID | Judul | Objectives | Rewards | Flags on Complete | Next | Requires |
|-------|-----|-------|------------|---------|-------------------|------|----------|
| 104 | `quest104` | Kabar yang Tak Boleh Keluar | `talk elder_mao`, `talk lin_wei` | insight 40, gold 20, rep rebels +5 | `quest104_done` | `quest105` | `quest103_done` |
| 105 | `quest105` | Peziarah dari Selatan | `talk diakon_soren`, `flag peziarah_terjawab` | insight 50, gold 25, rep holy_order +5 | `quest105_done` | `quest106` | `quest104_done` |
| 106 | `quest106` | Arsip yang Terbakar | `talk guntur`, `enemy penjaga_arsip` | insight 60, gold 30, rep ancient_order +5 | `quest106_done` | `quest107` | `quest105_done` |
| 107 | `quest107` | Nama di Dinding | `talk lin_wei`, `flag nama_terbaca` | insight 70, gold 35, rep rebels +5 | `quest107_done` | `quest108` | `quest106_done` |
| 108 | `quest108` | Jalan ke Kebenaran | `talk elder_mao`, `flag truth_decided` | insight 100, gold 50, rep ancient_order +10 | `quest108_done`, `ending_path_set` | `null` | `quest107_done` |

**Event Chain (Pola Existing):**
- `quest104_intro` (trigger `quest_done: quest103` atau `day_passed`) → `start_quest: quest104`
- `quest104_done` → unlock/grant/log → `start_quest: quest105`
- ...dst sampai `quest108_done`

**Quest 105 & 108: Menggunakan `prompt_choice`**
- Quest105: Diakon Soren tanya → choice: lapor jujur (holy_order+10, rebels-10) / menyesatkan (rebels+10, holy_order-10)
- Quest108: Elder Mao tanya jalan → choice: set flag `ending_path_defy` / `ending_path_seal` / `ending_path_reconcile` (defer points, pakai flag)

### 3.2 Quest Faksi (2 Quest)

| Quest | ID | Faksi | Judul | Objectives | Rewards | Choice |
|-------|-----|-------|-------|------------|---------|--------|
| 1 | `fquest_rebels_kiriman` | rebels | Kiriman yang Hilang | `talk jati`, `enemy babi_hutan_qi`, `enemy pembelot_pemberontak` | insight 40, gold 30, rebels +15 | Tidak |
| 2 | `fquest_holyorder_mata` | holy_order | Mata Sang Orde | `talk diakon_soren`, `flag laporan_sampai` | insight 30, gold 20 | **Ya** (prompt_choice: lapor jujur vs menyesatkan) |

### 3.3 NPC Baru (4 → Total 6)

| NPC | ID | Lokasi | Peran | Dialog Kunci |
|-----|-----|--------|-------|--------------|
| Diakon Soren | `diakon_soren` | village_emberfall | Orde Suci (abu-abu), quest105 & fquest_holyorder | "Orde suci mencari kemurnian. Kau... kotor." |
| Guntur | `guntur` | village_emberfall | Saksi tua pembantaian, quest106 | "Aku lihat api malam itu. Nama-nama terukir." |
| Jati | `jati` | ashfall_forest | Kurir pemberontak, koneksi Lin Wei, fquest_rebels | "Lin Wei kirim aku. Pemberontak butuh bantuan." |
| Mira | `mira` | village_emberfall | Ibu anak hilang (benang babi hutan), flavor | "Anakku pergi ke hutan... tidak pulang." |

### 3.4 Musuh Baru (4 → Total 7 Non-Bos)

| Musuh | ID | Elemen | Tipe | Lokasi | Teknik | Note |
|-------|-----|--------|------|--------|--------|------|
| Penebus Orde Suci | `penebus_orde_suci` | Api | Human | ashfall_forest | flame_strike | Orde Suci aggression |
| Pembelot Pemberontak | `pembelot_pemberontak` | Air | Human | ashfall_forest | frost_bind | Turncoat rebel |
| Penjaga Arsip | `penjaga_arsip` | Kayu | Undead | ruin_shrine | vine_grasp (baru) | Guard quest106 |
| Babi Hutan Qi | `babi_hutan_qi` | Tanah | Beast | ashfall_forest | earth_charge (baru) | Fquest_rebels target |

**Siklus Elemen Musuh Lengkap 5:** ✅
- Existing: serigala_qi (??), bandit_perbatasan (??), zombie_temple (??), penjaga_makam (earth)
- Baru: api, air, kayu, tanah → **5 elemen covered**

### 3.5 Teknik Baru (3 → Total 6)

| Teknik | ID | Path | Elemen | Type | Power | Qi Cost | Requires |
|--------|-----|------|--------|------|-------|---------|----------|
| Serbuan Akar | `serbuan_akar` | Alkimia/Formasi | Kayu | Physical | 10 | 8 | tier: qi_condensation |
| Perisai Tanah | `perisai_tanah` | Formasi | Tanah | Buff | - | 6 | tier: qi_condensation |
| Iblis Pedang | `iblis_pedang` | Pedang | Metal | Physical | 14 | 14 | tier: foundation_establishment |

**Cakupan Elemen Pemain Lengkap 5:** ✅
- Existing: qi_slash (metal), flame_strike (api), frost_bind (air)
- Baru: kayu, tanah → **5 elemen covered**

---

## 4. Sprint 3: Integrasi E2E + Polish

### 4.1 Full Flow Test
- `test_arc1_full_playthrough` — quest101→108 + 2 faksi + semua NPC + semua musuh + semua teknik
- `test_choice_system_integration` — quest105 choice → reputasi berubah → quest108 choice → flag ending_path
- `test_element_coverage` — 5 elemen musuh & pemain ter-exercise

### 4.2 Graphify & Full Suite
```bash
graphify update .
pytest -q && ruff check src launcher.py tools tests && ruff format --check src launcher.py tools tests && python tools/validate.py
```

### 4.3 Review Dua Tahap (AGENTS.md §2.7)
1. **Kepatuhan GDD §22** — target konten Arc 1 terpenuhi semua?
2. **Kualitas Kode** — docstring, ponytail comments, no dead code

---

## 5. File Manifest (Semua File Baru/Diubah)

### Engine (Sprint 1)
```
src/engine/event.py                    # +prompt_choice action
src/core/game_loop.py                  # +_cmd_choose
tests/test_event.py                    # +test_action_prompt_choice*
tests/test_game_loop.py                # +test_cmd_choose* + test_arc1_to_arc2_transisi
```

### Data Transisi (Sprint 1)
```
data/events/quest103_done.json         # BARU
data/story/memory_arc1_complete.json   # BARU
data/quests/quest201.json              # BARU
data/maps/sect_azure.json              # BARU
data/maps/guild_city.json              # BARU
```

### Data Arc 1 Content (Sprint 2)
```
data/quests/quest104.json              # BARU
data/quests/quest105.json              # BARU (prompt_choice)
data/quests/quest106.json              # BARU
data/quests/quest107.json              # BARU
data/quests/quest108.json              # BARU (prompt_choice, ending flag)
data/quests/fquest_rebels_kiriman.json # BARU
data/quests/fquest_holyorder_mata.json # BARU (prompt_choice)

data/events/quest104_intro.json        # BARU
data/events/quest104_done.json         # BARU
data/events/quest105_done.json         # BARU
data/events/quest106_done.json         # BARU
data/events/quest107_done.json         # BARU
data/events/quest108_done.json         # BARU
data/events/fquest_rebels_kiriman_done.json # BARU
data/events/fquest_holyorder_mata_done.json # BARU

data/npc/diakon_soren.json             # BARU
data/npc/guntur.json                   # BARU
data/npc/jati.json                     # BARU
data/npc/mira.json                     # BARU

data/enemies/penebus_orde_suci.json    # BARU
data/enemies/pembelot_pemberontak.json # BARU
data/enemies/penjaga_arsip.json        # BARU
data/enemies/babi_hutan_qi.json        # BARU

data/techniques/serbuan_akar.json      # BARU
data/techniques/perisai_tanah.json     # BARU
data/techniques/iblis_pedang.json      # BARU
```

### Test Expected Updates (Sprint 1+2)
```
tests/test_event_data.py     # EXPECTED_EVENTS + 1 transisi + 11 Arc 1 = +12
tests/test_quest_data.py     # EXPECTED_QUESTS + 1 transisi + 7 Arc 1 = +8
tests/test_npc_data.py       # EXPECTED_NPCS + 4 = +4
tests/test_enemy_data.py     # EXPECTED_ENEMIES + 4 = +4
tests/test_technique_data.py # EXPECTED_TECHNIQUES + 3 = +3
tests/test_map_data.py       # EXPECTED_MAPS + 2 = +2
```

---

## 6. Urutan Eksekusi Detail (TDD Per Tugas)

### SPRINT 1 — HARI INI

#### Fase 1A: Choice Engine (RED→GREEN)
```
[ ] 1.1 Test RED: test_action_prompt_choice (tests/test_event.py)
[ ] 1.2 Implement: _apply_action kind="prompt_choice" (src/engine/event.py)
[ ] 1.3 Test GREEN: pytest tests/test_event.py::test_action_prompt_choice -q
[ ] 1.4 Test RED: test_cmd_choose_valid/invalid (tests/test_game_loop.py)
[ ] 1.5 Implement: _cmd_choose (src/core/game_loop.py)
[ ] 1.6 Test GREEN: pytest tests/test_game_loop.py::test_cmd_choose* -q
[ ] 1.7 Validate: python tools/validate.py
```

#### Fase 1B: Transisi Data (RED→GREEN)
```
[ ] 1.8 Test RED: test_event_quest103_done_unlock_maps (tests/test_event.py)
[ ] 1.9 Data: quest103_done.json, memory_arc1_complete.json, quest201.json, sect_azure.json, guild_city.json
[ ] 1.10 Test GREEN: pytest tests/test_event.py::test_event_quest103_done_unlock_maps -q
[ ] 1.11 Validate: python tools/validate.py
[ ] 1.12 Update EXPECTED_EVENTS, EXPECTED_QUESTS, EXPECTED_MAPS
[ ] 1.13 Test RED: test_arc1_to_arc2_transisi (tests/test_game_loop.py)
[ ] 1.14 Test GREEN: pytest tests/test_game_loop.py::test_arc1_to_arc2_transisi -q
[ ] 1.15 Full Sprint 1 verify: pytest -q && ruff check && python tools/validate.py
```

### SPRINT 2 — ARC 1 CONTENT

#### Fase 2A: Quest Chain 104-108 + Events
```
[ ] 2.1 Quest104 + event intro/done (data + test)
[ ] 2.2 Quest105 + event done + prompt_choice (data + test)
[ ] 2.3 Quest106 + event done (data + test)
[ ] 2.4 Quest107 + event done (data + test)
[ ] 2.5 Quest108 + event done + prompt_choice + ending flag (data + test)
[ ] 2.6 Validate each step: python tools/validate.py
```

#### Fase 2B: Faction Quest
```
[ ] 2.7 fquest_rebels_kiriman + event (data + test)
[ ] 2.8 fquest_holyorder_mata + event + prompt_choice (data + test)
```

#### Fase 2C: NPC + Musuh + Teknik
```
[ ] 2.9 4 NPC (data + test_npc_data.py)
[ ] 2.10 4 Musuh (data + test_enemy_data.py)
[ ] 2.11 3 Teknik (data + test_technique_data.py)
[ ] 2.12 Update all EXPECTED_* sets
[ ] 2.13 Validate full: python tools/validate.py
```

### SPRINT 3 — E2E
```
[ ] 3.1 Test full playthrough
[ ] 3.2 graphify update .
[ ] 3.3 Full suite + lint + format + validate
[ ] 3.4 Review §2.7
```

---

## 7. Kriteria Selesai (Definition of Done - AGENTS.md §12)

- [ ] **GDD §22 Target Arc 1 Terpenuhi Semua:**
  - [ ] 8 quest utama (101-108)
  - [ ] 2 quest faksi (rebels + holy_order)
  - [ ] 6 NPC (elder_mao, lin_wei, diakon_soren, guntur, jati, mira)
  - [ ] 7 musuh non-bos (3 existing + 4 baru, 5 elemen covered)
  - [ ] 1 bos (penjaga_makam)
  - [ ] 6 teknik (3 existing + 3 baru, 5 elemen covered)
  - [ ] 3 resep pil (existing 1 + 2 ponytail)
  - [ ] 2 artefak roh (ponytail)
  - [ ] 1 binatang roh (ponytail)
  - [ ] 2 echo memori (existing 2 + 1 arc1_complete = 3, target 2 ✅)
  - [ ] Durasi 2-3 jam (smoke test)

- [ ] **Engine Choice Berfungsi:**
  - [ ] `prompt_choice` action di event
  - [ ] `choose <key>` command di game
  - [ ] Dipakai 3×: quest105, quest108, fquest_holyorder_mata
  - [ ] Reputasi & flag berubah per choice

- [ ] **Transisi Arc 1→2 Lancar:**
  - [ ] quest103_done → unlock sect_azure & guild_city
  - [ ] grant memory_arc1_complete
  - [ ] start quest201
  - [ ] go sect_azure → talk fang_yue → quest201 advance

- [ ] **Quality Gates:**
  - [ ] `pytest -q` lulus (243 + ~30 baru = ~273)
  - [ ] `ruff check` & `ruff format --check` bersih
  - [ ] `python tools/validate.py` → OK
  - [ ] Docstring Google-style semua fungsi baru
  - [ ] `ponytail:` comments untuk shortcuts
  - [ ] `graphify update .` fresh

---

## 8. Ponytail Comments (Utang Teknis Terencana)

| Lokasi | Komentar | Upgrade Saat |
|--------|----------|--------------|
| `data/maps/sect_azure.json` | `# ponytail: enemies kosong, isi saat quest202+ musuh Arc 2 ditambah` | Fase 2 quest202+ |
| `data/maps/guild_city.json` | `# ponytail: enemies kosong, isi saat quest faksi kota ditambah` | Fase 2 faksi kota |
| `data/quests/quest201.json` | `# ponytail: next=null, tambah quest202 saat Fase 2 desain` | Fase 2 |
| `src/engine/event.py` | `# ponytail: prompt_choice opsi limited to set_flag/change_reputation/log; upgrade saat butuh grant_item/start_quest` | Butuh efek lebih kaya |
| `data/quests/quest108.json` | `# ponytail: ending_path flag only, points system §21 nanti` | Fase 4 ending system |
| `data/quests/fquest_rebels_kiriman.json` | `# ponytail: reward pil/artefak nanti saat sistem alkimia/equip siap` | Fase 2 sistem |

---

## 9. Risiko & Mitigasi

| Risiko | Prob | Dampak | Mitigasi |
|--------|------|--------|----------|
| `prompt_choice` engine bug | Sedang | Blokir 3 quest | Test unit komprehensif Sprint 1A; manual smoke test |
| Validator tolak cross-ref baru | Tinggi | Blokir data | `validate.py` setelah SETIAP file JSON baru; urut: maps → NPC → quest → event |
| Event cascade urutan salah | Sedang | Quest tidak start | Test integration `test_arc1_to_arc2_transisi` + `test_arc1_full_playthrough` |
| Quest105/108 choice tidak update rep | Rendah | Narasi rusak | Test `test_choice_system_integration` assert reputasi delta |
| Scope creep Sprint 2 | Sedang | Delay | **Hanya data**, tidak tambah engine; ponytail untuk fitur nanti |

---

## 10. Persetujuan Final (Sudah Diberikan)

✅ **1. Hybrid (Sprint 1: transisi + choice engine)**
✅ **2. prompt_choice design OK**
✅ **3. Arc 1 content penuh Sprint 2**

---

**SIAP MULAI SPRINT 1.1 — Test RED `test_action_prompt_choice`**

```bash
# Langkah pertama:
# 1. Buka tests/test_event.py
# 2. Tulis test_action_prompt_choice (RED)
# 3. Implement _apply_action kind="prompt_choice" di src/engine/event.py (GREEN)
```

**Mulai?**