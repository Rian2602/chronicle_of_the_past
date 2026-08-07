# Arc 2 Early Content Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Membangun *Vertical Slice* awal Arc 2 dengan menambahkan peta Sekte Awan Biru (`sect_azure`), NPC kunci (Fang Yue & Alchemist Xiu), serta kelanjutan *quest* (202–203) agar progresi narasi tersambung.

**Architecture:** Pure data-driven implementation. Kita hanya akan menambah file JSON baru untuk `maps`, `npc`, `dialogues`, dan `quests` tanpa menyentuh *core engine* Python. Verifikasi dilakukan melalui *end-to-end testing* menggunakan `GameSession` untuk mensimulasikan interaksi pemain.

**Tech Stack:** JSON (Data), Pytest (Testing).

## Global Constraints

- Wajib berpegang pada GDD §10 (Karakter), §12 (Quest), dan AGENTS.md.
- Penggunaan id harus dalam format *snake_case* (`sect_azure`, `fang_yue`, `alchemist_xiu`, `quest202`).
- Wajib menggunakan TDD: tes harus gagal karena `KeyError` (file JSON tidak ada), lalu hijau setelah file dibuat.
- Wajib berbahasa Indonesia untuk *lore*, deskripsi, dan dialog.

---

### Task 1: Peta Sekte Awan Biru

**Files:**
- Create: `tests/test_arc2_early.py`
- Create: `data/maps/sect_azure.json`

**Interfaces:**
- Consumes: `quest201_done` (meskipun *map* ini aslinya dibuka dari pilihan ending Arc 1).
- Produces: Map yang dapat diakses oleh *engine*.

- [ ] **Step 1: Write the failing test**

Dalam `tests/test_arc2_early.py`:
```python
import pytest
from src.core.game_loop import GameSession

def test_sect_azure_map():
    session = GameSession()
    # Asumsikan map sudah di-unlock oleh event sebelumnya (quest108_done)
    session.state.map_unlocks.add("sect_azure")
    
    # Pindah ke map baru
    session.process_command("go sect_azure")
    assert session.state.location == "sect_azure"
    
    # Pastikan data map valid dengan `look`
    session.process_command("look")
    log_text = "\n".join(session.state.logs)
    assert "Sekte Awan Biru" in log_text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_arc2_early.py::test_sect_azure_map -q`
Expected: FAIL karena `data/maps/sect_azure.json` tidak ditemukan.

- [ ] **Step 3: Write minimal implementation**

Buat `data/maps/sect_azure.json`:
```json
{
  "id": "sect_azure",
  "name": "Sekte Awan Biru",
  "description": "Sekte besar yang melayang di atas puncak gunung berselimut awan. Akademi utama bagi para kultivator muda di Ashenfeld.",
  "tier": 2,
  "enemies": []
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_arc2_early.py::test_sect_azure_map -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_arc2_early.py data/maps/sect_azure.json
git commit -m "data: tambah map sekte awan biru untuk arc 2"
```

---

### Task 2: NPC Fang Yue, Dialog, dan Quest 202

**Files:**
- Modify: `tests/test_arc2_early.py`
- Create: `data/npc/fang_yue.json`
- Create: `data/dialogues/dialog_fang_yue_1.json`
- Create: `data/quests/quest202.json`

**Interfaces:**
- Consumes: Map `sect_azure`
- Produces: Dialog interaktif yang menyelesaikan `quest201` dan memicu `quest202`.

- [ ] **Step 1: Write the failing test**

Tambahkan ke `tests/test_arc2_early.py`:
```python
def test_fang_yue_intro():
    session = GameSession()
    session.state.location = "sect_azure"
    
    # Inject quest201 agar aktif
    session.state.quests.started.append("quest201")
    
    session.process_command("look")
    log_text = "\n".join(session.state.logs)
    assert "Fang Yue" in log_text
    
    session.process_command("talk fang_yue")
    # Pilih opsi pertama (sapaan murid)
    session.process_command("choose 1")
    
    assert "quest201" in session.state.quests.done
    assert "quest202" in session.state.quests.started
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_arc2_early.py::test_fang_yue_intro -q`
Expected: FAIL karena NPC tidak ada.

- [ ] **Step 3: Write minimal implementation**

Buat `data/quests/quest202.json`:
```json
{
  "id": "quest202",
  "title": "Tugas Murid Baru",
  "type": "main",
  "description": "Temui Xiu Sang Alkemi di pelataran sekte.",
  "objectives": [
    {"kind": "talk", "target": "alchemist_xiu"}
  ],
  "rewards": {"insight": 100},
  "flags_on_complete": ["quest202_done"],
  "next": "quest203",
  "category": "main",
  "requires_flag": "quest201_done"
}
```

Buat `data/npc/fang_yue.json`:
```json
{
  "id": "fang_yue",
  "name": "Fang Yue",
  "description": "Seorang kultivator senior dengan pedang panjang di punggungnya. Auranya tajam bagai silet.",
  "location": "sect_azure",
  "greeting": "Anak baru? Jangan menghalangi jalanku.",
  "dialog": [],
  "dialogue_id": "dialog_fang_yue_1"
}
```

Buat `data/dialogues/dialog_fang_yue_1.json`:
```json
{
  "id": "dialog_fang_yue_1",
  "npc": "fang_yue",
  "nodes": {
    "start": {
      "text": "Jadi kau yang selamat dari Hutan Perbatasan? Aku Fang Yue. Apa tujuanmu di sini?",
      "choices": [
        {
          "text": "Aku datang untuk berlatih.",
          "next": "accept",
          "requires_flag": null
        }
      ]
    },
    "accept": {
      "text": "Bagus. Jika kau ingin bertahan di sini, temui Xiu Sang Alkemi. Dia ada tugas untuk murid baru.",
      "choices": [
        {
          "text": "[Mengangguk]",
          "next": null,
          "actions": [
            {"kind": "set_flag", "flag": "quest201_done", "value": true},
            {"kind": "start_quest", "id": "quest202"}
          ]
        }
      ]
    }
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_arc2_early.py::test_fang_yue_intro -q`
Expected: PASS 

- [ ] **Step 5: Commit**

```bash
git add tests/test_arc2_early.py data/npc/fang_yue.json data/dialogues/dialog_fang_yue_1.json data/quests/quest202.json
git commit -m "data: tambah fang yue dan quest202 untuk progresi sekte"
```

---

### Task 3: NPC Alchemist Xiu dan Ekspansi Quest

**Files:**
- Modify: `tests/test_arc2_early.py`
- Create: `data/npc/alchemist_xiu.json`
- Create: `data/quests/quest203.json`

**Interfaces:**
- Consumes: `quest202` aktif.
- Produces: Progresi menuju `quest203`.

- [ ] **Step 1: Write the failing test**

Tambahkan ke `tests/test_arc2_early.py`:
```python
def test_alchemist_xiu_quest():
    session = GameSession()
    session.state.location = "sect_azure"
    session.state.quests.started.append("quest202")
    
    session.process_command("talk alchemist_xiu")
    
    # Engine akan otomatis memajukan quest jika kind="talk" terpenuhi
    assert "quest202" in session.state.quests.done
    # quest202 punya next="quest203", jadi otomatis start quest203
    assert "quest203" in session.state.quests.started
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_arc2_early.py::test_alchemist_xiu_quest -q`
Expected: FAIL karena npc `alchemist_xiu` tidak ada.

- [ ] **Step 3: Write minimal implementation**

Buat `data/quests/quest203.json`:
```json
{
  "id": "quest203",
  "title": "Ujian Alkimia",
  "type": "main",
  "description": "Racik Pil Pemahaman menggunakan Kuali Roh untuk membuktikan kemampuanmu kepada Xiu.",
  "objectives": [
    {"kind": "collect", "target": "pill_insight", "count": 1}
  ],
  "rewards": {"insight": 150, "gold": 50},
  "flags_on_complete": ["quest203_done"],
  "next": "quest204",
  "category": "main",
  "requires_flag": "quest202_done"
}
```

Buat `data/npc/alchemist_xiu.json`:
```json
{
  "id": "alchemist_xiu",
  "name": "Xiu Sang Alkemi",
  "description": "Tangan dan wajahnya dipenuhi noda abu. Bau herbal tajam menguar dari jubahnya.",
  "location": "sect_azure",
  "greeting": "Bahan, bahan! Aku butuh lebih banyak bahan! Ah, murid baru ya? Kebetulan sekali.",
  "dialog": [
    "Jika kau ingin berlatih alkimia, kau harus tahan panas."
  ]
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_arc2_early.py::test_alchemist_xiu_quest -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_arc2_early.py data/npc/alchemist_xiu.json data/quests/quest203.json
git commit -m "data: tambah alchemist xiu dan quest203"
```
