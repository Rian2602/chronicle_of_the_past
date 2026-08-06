# Rencana Penyelesaian Arc 1 (Fase 1) — Chronicle of the Past

**Status:** Draf desain — menunggu persetujuan pengguna (AGENTS.md §2.2)
**Berdasarkan:** GDD §22 (Target Konten per Arc), §15 (Event Engine), §23 (Roadmap Fase 1)
**Tanggal:** 2026-08-06

---

## 1. Latar Belakang & Masalah

**Fakta terverifikasi:**
- Arc 1 hanya punya **3/8 quest utama** (quest101, 102, 103)
- Quest terakhir `quest103` memiliki `next: null` dan **tidak ada event `quest103_done`**
- Setelah kalahkan bos Penjaga Makam → **tidak ada narasi penutup, tidak unlock peta Arc 2, tidak start quest Arc 2**
- Peta `sect_azure` & `guild_city` (Arc 2) **tidak ter-unlock oleh event manapun**
- NPC `fang_yue` (mentor Sekte Awan Biru) **belum ada**
- Target GDD §22 Arc 1: **8 quest utama, 2 quest faksi, 6 NPC, 7 musuh, 6 teknik, 3 pil, 2 artefak, 1 binatang roh**

**Kesimpulan:** Arc 1 **BELUM** "playable penuh" per kriteria Fase 1 (§23). Transisi ke Arc 2 putus.

---

## 2. Tujuan Desain

Menyelesaikan Arc 1 agar memenuhi **minimum Fase 1 criteria**: "Arc 1 playable penuh + test", dengan fokus pada:
1. **Transisi Arc 1 → Arc 2 berfungsi** (event `quest103_done` unlock peta + start quest201)
2. **Narasi penutup Arc 1** (echo memori rahasia pertama)
3. **Quest201 sebagai entry point Arc 2** (bawa pemain ke sekte/gilda)
4. **Validasi data & test hijau** (pytest + validate.py)

**Scope TIDAK termasuk** (ditunggu Fase 2+):
- Quest faksi Arc 1 (2 quest) — bisa ditambah paralel
- NPC pendukung tambahan (4 NPC) — bisa ditambah paralel
- Musuh/teknik/item tambahan — sesuai kebutuhan quest201+
- Lin Wei join party — butuh quest Arc 2 di sekte dulu
- Alkimia/formasi/status effect penuh — Fase 2/5

---

## 3. Desain Solusi (Minimal, Data-Driven)

### 3.1 Event `quest103_done` (Kunci Utama)

**File:** `data/events/quest103_done.json` (BARU)

```json
{
  "id": "quest103_done",
  "trigger": [
    {"kind": "quest_done", "quest": "quest103"}
  ],
  "actions": [
    {
      "kind": "unlock_map",
      "target": "sect_azure"
    },
    {
      "kind": "unlock_map",
      "target": "guild_city"
    },
    {
      "kind": "grant_memory",
      "memory_id": "memory_arc1_complete"
    },
    {
      "kind": "log",
      "text": "Penjaga Makam runtuh, dan debu abad berkeliaran. Di tengah reruntuhan, kau menemukan gulungan kuno yang bercerita tentang 'Anak yang Ditunggu' — dan nama itu tertulis di dinding kuil bersama nama-nama yang gagal. Saat kau membaca baris terakhir, suara lin Wei bergema dari hutan: 'Sekte Awan Biru... mereka tahu.'"
    },
    {
      "kind": "start_quest",
      "id": "quest201"
    }
  ],
  "once": true
}
```

**Alasan desain:**
- Mengikuti pola event existing (`quest101_done`, `unlock_ruin_shrine`)
- `unlock_map` → set flag `map_<id>_unlocked` + tambah ke `state.map_unlocks` (GDD §15.3)
- `grant_memory` → echo memori rahasia pertama (GDD §3.3 Arc 1: "dunia menutup-nutupi sesuatu")
- `start_quest` → langsung mulai quest201 (cascade dalam pass sama, §15.4)
- `once: true` → hanya jalan sekali, set `event_quest103_done_done`

### 3.2 Echo Memori `memory_arc1_complete`

**File:** `data/story/memory_arc1_complete.json` (BARU)

```json
{
  "id": "memory_arc1_complete",
  "title": "Anak yang Ditunggu",
  "text": "Dinding kuil penuh nama. Ratusan nama, semua digores — gagal. Di bagian paling bawah, nama baru terukir saat Penjaga Makam jatuh. Bukan namamu. Nama itu: 'Anak yang Ditunggu'. Dan di sampingnya, tanda tangan yang kau kenal: Lin Wei. Dia tahu. Dia selalu tahu."
}
```

**Konsistensi:** Format sama dengan `memory_ashfall_first_echo.json`, `memory_shrine_trial.json`.

### 3.3 Quest `quest201` (Entry Point Arc 2)

**File:** `data/quests/quest201.json` (BARU)

```json
{
  "id": "quest201",
  "title": "Menuju Sekte Awan Biru",
  "type": "main",
  "description": "Gulungan kuil mengarah ke Sekte Awan Biru. Lin Wei menunggu di sana — dan jawaban tentang masa lalumu.",
  "objectives": [
    {"kind": "map", "target": "sect_azure"},
    {"kind": "talk", "target": "fang_yue"}
  ],
  "rewards": {"insight": 50, "gold": 30, "reputation": {"ancient_order": 10}},
  "flags_on_complete": ["quest201_done"],
  "next": "quest202",
  "category": "main",
  "requires_flag": "quest103_done"
}
```

**Catatan:**
- `requires_flag: "quest103_done"` → quest hanya muncul setelah Arc 1 selesai (engine quest cek flag ini)
- Objective 1: `map` → `sect_azure` (pemain harus go ke sekte)
- Objective 2: `talk` → `fang_yue` (NPC mentor sekte, butuh dibuat)
- Reward reputasi `ancient_order` +10 (sektenya bagian orde rahasia kuno, GDD §8)

### 3.4 NPC `fang_yue` (Mentor Sekte Awan Biru)

**File:** `data/npc/fang_yue.json` (BARU)

```json
{
  "id": "fang_yue",
  "name": "Fang Yue",
  "location": "sect_azure",
  "greeting": "Kau datang. Baik. Gulungan kuil tidak bohong.",
  "dialog": [
    "Fang Yue menatapmu tajam: 'Sekte Awan Biru bukan tempat berlatih biasa. Kami melatih mereka yang dipilih — dan menyingkirkan yang tidak.'",
    "'Kamu memiliki bakat aneh. Itu bisa dilihat dari meridianmu. Pilih jalurmu: Pedang, Alkimia, Formasi, atau Jiwa.'",
    "'Pilihlah dengan hati-hati. Jalur utamamu gratis; jalur lain... mahal.'"
  ]
}
```

**Konsistensi:** Format sama dengan `elder_mao.json`, `lin_wei.json`. Lokasi `sect_azure` (harus unlock dulu via event).

### 3.5 Peta `sect_azure` & `guild_city` (Minimal)

**File:** `data/maps/sect_azure.json` (BARU)

```json
{
  "id": "sect_azure",
  "name": "Sekte Awan Biru",
  "description": "Puncak gunung tertutup awan, bangunan jade putih berjejer di tepi jurang. Angin berdengar seperti nyanyian pedang.",
  "tier": 2,
  "enemies": []
}
```

**File:** `data/maps/guild_city.json` (BARU)

```json
{
  "id": "guild_city",
  "name": "Kota Gilda",
  "description": "Kota batu di persimpangan jalan, penuh pedagang, pemburu, dan rahasia. Gilda Dagang, Pembunuh, dan Petualang berbagi atap.",
  "tier": 2,
  "enemies": []
}
```

**Catatan:** Musuh kosong dulu (bisa ditambah nanti saat quest202+). Tier 2 = Arc 2 (GDD §9).

---

## 4. Rencana Kerja (Tugas Kecil 2–5 Menit, TDD per Tugas)

### Tahap 1: Event & Memori (Fundasi Transisi)

| # | Tugas | File | Test (RED→GREEN) | Verifikasi |
|---|-------|------|------------------|------------|
| 1.1 | Test event `quest103_done` trigger `quest_done` | `tests/test_event.py` | `test_event_quest103_done_unlock_maps` | pytest |
| 1.2 | Buat `data/events/quest103_done.json` | `data/events/quest103_done.json` | - | `python tools/validate.py` |
| 1.3 | Test echo memori `memory_arc1_complete` | `tests/test_event.py` | `test_grant_memory_arc1_complete` | pytest |
| 1.4 | Buat `data/story/memory_arc1_complete.json` | `data/story/memory_arc1_complete.json` | - | `python tools/validate.py` |
| 1.5 | Test integrasi: quest103 done → event fire → maps unlock + quest201 start | `tests/test_game_loop.py` | `test_quest103_complete_transisi_arc2` | pytest |

### Tahap 2: Quest201 & NPC Fang Yue

| # | Tugas | File | Test (RED→GREEN) | Verifikasi |
|---|-------|------|------------------|------------|
| 2.1 | Test quest201 load & requires_flag | `tests/test_quest.py` / `test_quest_data.py` | `test_quest201_requires_quest103_done` | pytest |
| 2.2 | Buat `data/quests/quest201.json` | `data/quests/quest201.json` | - | `python tools/validate.py` |
| 2.3 | Test NPC fang_yue load & location | `tests/test_npc_data.py` | `test_npc_fang_yue_location_sect_azure` | pytest |
| 2.4 | Buat `data/npc/fang_yue.json` | `data/npc/fang_yue.json` | - | `python tools/validate.py` |
| 2.5 | Test talk fang_yue setelah go sect_azure | `tests/test_game_loop.py` | `test_talk_fang_yue_quest201_advance` | pytest |

### Tahap 3: Peta Arc 2

| # | Tugas | File | Test (RED→GREEN) | Verifikasi |
|---|-------|------|------------------|------------|
| 3.1 | Test map sect_azure & guild_city load | `tests/test_map_data.py` | `test_map_sect_azure_guild_city_valid` | pytest |
| 3.2 | Buat `data/maps/sect_azure.json` | `data/maps/sect_azure.json` | - | `python tools/validate.py` |
| 3.3 | Buat `data/maps/guild_city.json` | `data/maps/guild_city.json` | - | `python tools/validate.py` |
| 3.4 | Test go sect_azure setelah quest103_done | `tests/test_game_loop.py` | `test_go_sect_azure_unlocked_after_quest103` | pytest |

### Tahap 4: Integrasi End-to-End & Polish

| # | Tugas | File | Test | Verifikasi |
|---|-------|------|------|------------|
| 4.1 | Smoke test: main game Arc 1→2 flow | Manual / `tests/test_game_loop.py` | `test_arc1_to_arc2_full_flow` | pytest + manual |
| 4.2 | Update knowledge graph | - | `graphify update .` | graphify-out fresh |
| 4.3 | Full test suite + lint + validate | - | `pytest -q && ruff check && ruff format --check && python tools/validate.py` | All green |

---

## 5. Dependensi & Urutan Eksekusi

```
Tahap 1 (Event & Memori) → WAJIB SELESAI DULU
    ↓
Tahap 2 (Quest201 & NPC) → BISA PARALEL DENGAN Tahap 3
    ↓
Tahap 3 (Peta Arc 2) → BISA PARALEL DENGAN Tahap 2
    ↓
Tahap 4 (E2E Test + Graphify + Full Suite)
```

**Catatan:** Tahap 1 mesti selesai dulu karena Quest201 butuh `sect_azure` unlocked, dan NPC `fang_yue` butuh `sect_azure` sebagai location valid (validator cek NPC.location ∈ map_ids).

---

## 6. Kriteria Selesai (Definition of Done per AGENTS.md §12)

- [ ] Semua test baru RED→GREEN→REFACTOR, `pytest -q` lulus penuh (243+ test)
- [ ] `ruff check src launcher.py tools tests` bersih
- [ ] `ruff format --check src launcher.py tools tests` bersih
- [ ] Docstring Google-style untuk fungsi/test baru (Bahasa Inggris header, Bahasa Indonesia isi)
- [ ] Data JSON valid; `python tools/validate.py` → "OK: semua data valid, referensi ter-resolve"
- [ ] Alur utama terverifikasi: quest101→102→103→event quest103_done→unlock sect_azure+guild_city→grant memory→start quest201→go sect_azure→talk fang_yue
- [ ] Tidak ada kode mati, duplikasi, abstraksi tak terpakai
- [ ] Komentar `ponytail:` dengan kondisi upgrade jelas (bila ada)
- [ ] `graphify update .` dijalankan
- [ ] Tidak melanggar §11 (file stabil Fase 0 tidak disentuh, schema save tidak berubah)
- [ ] Ringkasan singkat diberikan

---

## 7. Estimasi Waktu

| Tahap | Estimasi | Catatan |
|-------|----------|---------|
| 1. Event & Memori | 1–2 jam | 5 tugas kecil, validasi data kritis |
| 2. Quest201 & NPC | 1–2 jam | 5 tugas, butuh NPC location valid |
| 3. Peta Arc 2 | 30–60 menit | 4 tugas, sederhana |
| 4. E2E + Full Suite | 30–60 menit | Smoke test manual + graphify |
| **Total** | **3–5 jam** | Bisa diselesaikan 1 hari kerja |

---

## 8. Risiko & Mitigasi

| Risiko | Probabilitas | Dampak | Mitigasi |
|--------|-------------|--------|----------|
| Validator tolak referensi baru (map/NPC/quest) | Tinggi | Blokir | Jalankan `validate.py` setelah setiap file JSON baru, perbaiki urut |
| Event tidak fire (trigger salah / urutan file) | Sedang | Transisi gagal | Test integrasi Tahap 1.5 wajib; event file naming urut abjad (`quest103_done.json` > `quest101_done.json`) |
| Quest201 tidak muncul (requires_flag) | Sedang | Progresi stuck | Test `test_quest201_requires_quest103_done` memvalidasi engine quest |
| Quest engine cascade event tidak jalan | Rendah | Narasi/quest201 tidak start | Sudah diverifikasi existing (`quest101_done` → `unlock_ruin_shrine` berjalan) |

---

## 9. Catatan Ponytail (Utang Teknis Terencana)

| Komentar | Lokasi | Kondisi Upgrade |
|----------|--------|-----------------|
| `# ponytail: peta sect_azure/guild_city enemies kosong, isi saat quest202+ musuh Arc 2 ditambah` | `data/maps/sect_azure.json`, `guild_city.json` | Saat tambah musuh Arc 2 (target §22: 8 musuh non-bos Arc 2) |
| `# ponytail: quest201 hanya 2 objektif (map + talk), perluas saat quest202+ butuh collect/kill_count` | `data/quests/quest201.json` | Saat desain quest Arc 2 lengkap |
| `# ponytail: NPC fang_yue dialog statis, nanti butuh branching berdasarkan jalur pemain (Pedang/Alkimia/Formasi/Jiwa)` | `data/npc/fang_yue.json` | Saat implement jalur kultivasi (§5.2) |

---

## 10. Persetujuan Diperlukan

Sebelum mulai implementasi, butuh konfirmasi pengguna pada:

1. **Narasi echo memori `memory_arc1_complete`** — apakah teks di atas sesuai visi "rahasia pertama terungkap" (GDD §3.3)?
2. **Quest201 objective** — `map sect_azure` → `talk fang_yue` apakah benar? Atau butuh `talk lin_wei` dulu di village?
3. **Reward quest201** — `ancient_order +10` reputasi apakah benar? (Sekte Awan Biru = orde rahasia kuno per GDD §8)
4. **Urutan unlock** — `sect_azure` DAN `guild_city` sekaligus, atau bertahap?
5. **Apakah quest faksi Arc 1 (2 quest) ditambah sekarang atau nanti?** (Rekomendasi: nanti, fokus transisi dulu)

---

*Dokumen ini mengikuti AGENTS.md §2.2 (Brainstorming & Desain Dulu) dan §10 (Alur Kerja Standar). Implementasi HANYA dimulai setelah desain disetujui.*