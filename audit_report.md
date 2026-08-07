# Laporan Audit Proyek "Chronicle of the Past" — Status Implementasi & Gap GDD

**Sumber spesifikasi:** `GDD.md` (v1.6 locked) & `AGENTS.md`
**Tanggal audit:** 7 Agustus 2026 (revisi 2 — menggantikan revisi sebelumnya yang ditulis saat suite masih merah)
**Metode:** pemeriksaan langsung `src/`, `data/`, `tests/` + eksekusi ulang semua alat verifikasi resmi proyek.

---

## 1. Ringkasan Eksekutif

Proyek **Chronicle of the Past** adalah RPG teks kultivasi (Python 3.12, Rich/Textual, konten data-driven JSON). Kondisi aktual terverifikasi:

| Ranah | Status | Bukti |
|---|---|---|
| **Validator data** | ✅ Lulus | `python3 tools/validate.py` → `OK: semua data valid, referensi ter-resolve.` |
| **Unit test** | ✅ **460 passed, 0 failed** | `pytest -q` (stabil, dijalankan berulang) |
| **Lint (ruff check)** | ✅ Bersih | `All checks passed!` |
| **Format (ruff format)** | ✅ 60 file rapi | `ruff format --check` |
| **Git** | ✅ `main` satu-satunya branch, sinkron remote | `## main...origin/main` |
| **Engine inti** | ✅ Lengkap (22 file `.py`) | semua modul GDD §14.2 terpasang |
| **Ending engine** | ✅ Terpasang (GDD §13/§21) | `story.py` + 4 event ending (lihat §4.4) |
| **Konten per Arc** | Fase 0–2 ✅ · Arc 3 ⚠️ (quest utama placeholder) · Arc 4 ❌ (0%) | lihat §4 |

**Kesimpulan singkat:** fondasi engine **lengkap dan teruji** (460 test hijau, lint/format/validator bersih), konten Arc 1–2 **asli dan lengkap**, **ending engine sudah terpasang**, tapi Arc 3 masih menyisakan **quest utama placeholder** (quest301–308, fquest_301–303), dan **Arc 4 belum ada sama sekali** (quest 401–408, 3 peta, 2 bos, ritual, NPC final). Semua gap dirinci di §4–5.

---

## 2. Status Verifikasi Teknis (Bukti Eksekusi Ulang)

```bash
pytest -q                       → 460 passed in 12.49s
ruff check src launcher.py tools tests → All checks passed!
ruff format --check ...         → 60 files already formatted
python3 tools/validate.py       → OK: semua data valid, referensi ter-resolve.
git status -sb                  → ## main...origin/main (sinkron, bersih)
```

---

## 3. Inventori Aset (Kondisi Aktual)

### 3.1 Data (folder `data/`)

| Folder | Jumlah | Detail |
|---|---|---|
| `data/quests/` | **37** | 24 quest utama (quest101–108, 201–208, 301–308) + 13 quest faksi (fquest_*) |
| `data/events/` | **49** | termasuk ending engine, intro/done quest, rekrut rekan, unlock peta |
| `data/enemies/` | **20** | 5 ber-tag `boss`; 15 non-bos |
| `data/techniques/` | **30** | semua ber-tier ≤ `golden_core` (qi_cond 7, foundation 4, golden_core 19) |
| `data/items/` | **47** | material 5, consumable 21, recipe 12, artifact 8, tool 1 |
| `data/shops/` | **2** | `pedagang_kelana`, `toko_tie` |
| `data/maps/` | **9** | lihat §4.2 |
| `data/npc/` | **18** | lihat §4.3 |
| `data/companions/` | **6** | lin_wei, kestrel, macan_baja, phoenix_abu, serigala_bayangan (+evolved) |
| `data/dialogues/` | **11** | dialog node-graph untuk 10 NPC |
| `data/story/` (memori) | **5** | memory_arc1_complete, arc2_climax, ashfall_first_echo, sekte_intrik, shrine_trial |
| `data/cultivation/` | **6** | **lengkap**: qi_condensation → heaven_challenger |
| `data/formations/` | **3** | benteng_bumi, jaring_naga, langit_pecah |
| `data/memories/` | — | (tidak ada folder; memori hidup di `data/story/`) |

### 3.2 Kode (`src/`, 22 file `.py`) — semua GDD §14.2 terpenuhi

- `src/core/`: `game_loop`, `input`, `save`, `state`
- `src/engine/`: `combat`, `cultivation`, `dialog`, `event`, `items`, `maps`, `quest`, `shop`, `story`
- `src/models/`: `combatant`, `enemy`, `party`, `player`, `technique`
- `src/systems/`: `formation`
- `src/ui/`: `app` (Textual) + `launcher.py`
- `tests/`: **32 file test**, 460 kasus lulus

---

## 4. Status Konten per Arc vs GDD §22

### 4.1 Quest

| Arc | GDD target | Aktual | Status |
|---|---|---|---|
| Arc 1 (quest101–108) | 8 utama | 8 **asli** (judul/objektif naratif) | ✅ Lengkap |
| Arc 2 (quest201–208) | 8 utama | 8 **asli** | ✅ Lengkap |
| Arc 3 (quest301–308) | 8 utama | 8 file, **semua placeholder** (`"Quest quest30X Title"`, objektif `enemy:kultis_bayangan`, rantai next 301→308) | ⚠️ Placeholder |
| Arc 4 (quest401–408) | 8 utama | **0** | ❌ Belum ada |
| Quest faksi | 10 | 13 file — 10 **asli** + 3 placeholder (`fquest_301–303` berjudul `"Quest fquest_30X Title"`) | ⚠️ Sebagian |

### 4.2 Peta (target 10)

| Peta GDD | Ada? | Catatan |
|---|---|---|
| `village_emberfall`, `ashfall_forest`, `ruin_shrine` (Arc 1) | ✅ | |
| `sect_azure`, `guild_city` (Arc 2) | ✅ | |
| `holy_cathedral`, `rebel_hideout` (Arc 3) | ✅ | |
| `capital` (Arc 3–4) | ❌ | **belum ada** |
| `ancient_vault`, `sky_seal` (Arc 4) | ❌ | **belum ada** |
| Ekstra non-GDD | — | `gua_abyss`, `hutan_kelabu` (tambahan) |

### 4.3 NPC & Musuh

| Kategori | GDD target | Aktual | Gap |
|---|---|---|---|
| NPC | 25 | 18 | −7; **`the_voice` (Arc 4) belum ada**; `inquisitor_vega`, `sera_ember`, `warden_kai` sudah ada |
| Musuh non-bos | 30 | 15 | −15 (khususnya konten Arc 3–4: manifestasi entitas, pion langit, pemberontak fanatik) |
| Bos | 5 | 4 sesuai GDD | ✅ `penjaga_makam` (A1), `bos_sekte_bayangan` (A2), `bos_inquisitor_agung` (A3); **`rasul_langit` & `suara` (A4) belum ada** (`golem_terbakar`, `abyssal_worm` ekstra) |

### 4.4 Ending Engine (GDD §13, §21) — ✅ SUDAH TERPASANG (fase sebelumnya)

- `src/engine/story.py`: `calculate_ending()` (pemenang dari `ending_points` + tie-break), `build_epilogue()` (status 5 faksi, label Indonesia GDD §8)
- `src/engine/event.py`: aksi `calculate_ending` → set flag `ending_<jalur>_win`
- `src/core/game_loop.py`: epilog ditampilkan sekali pasca `_run_events`
- 4 event: `calculate_ending_trigger`, `ending_defy`, `ending_seal`, `ending_reconcile`
- ⚠️ **Pemicu in-game belum aktif** — flag `arc4_boss_defeated` hanya ada di event trigger; **belum ada bos Arc 4 yang men-set-nya** (lihat §5)

### 4.5 Konten Pendukung vs GDD §22

| Konten | Target | Aktual | Gap |
|---|---|---|---|
| Teknik | 30 | 30 ✅ | tapi **semua tier ≤ golden_core** — teknik tier `soul_separation`/`void_breaker`/`heaven_challenger` (Arc 3–4) belum ada |
| Resep pil | 14 | 12 | −2 |
| Artefak roh | 12 | 8 | −4 |
| Binatang roh | 4 | 4 (+1 evolusi) | ✅ |
| Echo memori | 9 | 5 | −4 (Arc 3–4 belum) |
| Kultivasi tier | 6 | 6 | ✅ lengkap |

---

## 5. Gap vs GDD (Apa yang Belum Ada)

### Prioritas tinggi (blokir tamat / Fase 4)
1. **Quest Arc 4 (quest401–408)** — GDD §12.2, §22: 8 quest utama final (Ruang Rahasia Kuno → rahasia penuh → keputusan final).
2. **Peta Arc 4**: `capital`, `ancient_vault`, `sky_seal` (GDD §9).
3. **Bos Arc 4**: `rasul_langit` (Pemutus Kehampaan puncak) & `suara` (Penantang Surga) — GDD §11. Tanpa bos ini, `arc4_boss_defeated` tak pernah diset, ending engine tak pernah terpicu in-game.
4. **NPC `the_voice`** (entitas kuno, sky_seal) — GDD §10.

### Prioritas sedang (konten Arc 3 asli)
5. **Ganti placeholder quest301–308** (judul/objektif/next naratif sesuai GDD §12.3) dan **fquest_301–303**.
6. **Teknik tier tinggi** (Arc 3–4): tier `soul_separation`, `void_breaker`, `heaven_challenger` — GDD §22 menarget 30 total, sekarang semua terkonsentrasi di golden_core.
7. **Musuh non-bos Arc 3–4** (tentara salib, manifestasi entitas, pion langit, pemberontak fanatik) — GDD §11.
8. **Echo memori Arc 3–4** (target 9, baru 5) — GDD §22.

### Prioritas rendah (pelengkap Fase 5)
9. **Ritual + pertarungan dua tahap** (GDD §21.3) untuk ending "Menentang Langit" — belum ada sistemnya sama sekali.
10. **Resep pil −2** dan **artefak roh −4** (GDD §22).
11. **Keputusan kunci (7)** yang menambah `ending_points` — GDD §21.1 menyebut 1 di Arc 1, 2 di Arc 2–4; perlu diverifikasi berapa yang sudah ter-wire di quest/dialog existing.

### Catatan teknis lain
- `swap` dalam combat & inner demon fight (30% gagal breakthrough) sempat tercatat sebagai gap kecil di audit sebelumnya — perlu verifikasi ulang di sesi berikutnya.

---

## 6. Skor Kelengkapan Keseluruhan

| Komponen | Skor |
|---|---|
| Engine inti (semua modul) | **100%** |
| Ending engine (mekanisme) | **100%** (menunggu pemicu konten) |
| Data valid & teruji | **100%** (460 test, lint, validator) |
| Arc 1 | **100%** |
| Arc 2 | **100%** |
| Arc 3 | **~50%** (peta/NPC/bos/faksi asli ada; quest utama masih placeholder; teknik/musuh/memori Arc 3 kurang) |
| Arc 4 | **0%** |
| Fase 5 (polish, playtest, keseimbangan) | **0%** |

**Kesimpulan:** Game bisa dimainkan penuh hingga akhir Arc 2; Arc 3 bisa dimasuki tapi quest utamanya masih kosong; game **belum bisa ditamatkan** karena Arc 4 dan pemicu ending belum ada. Prioritas berikutnya: **konten asli Arc 3** (ganti placeholder) → **Arc 4 lengkap** (quest, peta, bos, the_voice) → polish Fase 5.

---

*Dokumen ini diperbarui otomatis dari pemeriksaan langsung repo pada 7 Agustus 2026. Angka aktual (37 quest, 49 event, 20 musuh, 30 teknik, 47 item, 9 peta, 18 NPC, 6 rekan, 11 dialog, 5 memori, 6 tier, 3 formasi, 22 modul src, 32 file test, 460 test lulus) diverifikasi langsung dari sistem file dan alat verifikasi proyek.*
