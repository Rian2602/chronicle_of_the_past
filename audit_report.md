# Laporan Audit Proyek "Chronicle of the Past" — Status Implementasi & Gap GDD

**Sumber spesifikasi:** `GDD.md` (v1.6 locked) & `AGENTS.md`
**Tanggal audit:** 7 Agustus 2026 (revisi — menggantikan draf audit sebelumnya yang sudah tidak akurat)
**Metode:** pemeriksaan langsung `src/`, `data/`, `tests/` + eksekusi ulang semua alat verifikasi resmi proyek.

---

## 1. Ringkasan Eksekutif

Proyek **Chronicle of the Past** adalah RPG teks kultivasi (Python 3.12, Rich/Textual, konten data-driven JSON). Kondisi aktual:

| Ranah | Status | Bukti |
|---|---|---|
| **Validator data** | ✅ Lulus | `python3 tools/validate.py` → `OK: semua data valid, referensi ter-resolve.` |
| **Unit test** | ⚠️ **1 gagal konsisten** + 1 flaky | `pytest -q` → **455 passed, 1 failed** (`test_story.py::test_apply_action_calculate_ending`); `test_app.py::test_pilih_option_serang_melakukan_battle_step` pernah gagal 1× (flaky) |
| **Lint (ruff check)** | ⚠️ 2 error | `tests/test_story.py`: F401 (`pytest` tak terpakai) + E501 (baris 82 > 80) |
| **Format (ruff format)** | ⚠️ 1 file | `src/engine/story.py` perlu diformat ulang |
| **Konten per Arc** | Fase 0–2 ✅ · Arc 3 ⚠️ (placeholder) · Arc 4 ❌ (0%) | lihat §4 |
| **Sistem engine inti** | ~95% terpasang | semua modul `src/` ada; gap kecil (inner demon fight, swap in combat) |

**Kesimpulan singkat:** fondasi engine dan konten Arc 1–2 **utuh dan teruji**; Arc 3 baru berupa **kerangka placeholder** (quest301–308 & fquest_301–303 berisi judul/deskripsi dummy); Arc 4 + sistem ending dinamis **belum ada**; dan ada **satu pekerjaan setengah jadi** (action `calculate_ending`) yang membuat suite test **merah** saat ini.

> ⚠️ **Koreksi terhadap laporan audit sebelumnya:** draf lama mengklaim *"449 passed / 0 lint error / Arc 3 100% selesai"*. Setelah diverifikasi ulang: suite saat ini **1 gagal konsisten**, lint **2 error**, dan quest301–308 **berisi placeholder** (bukan konten naratif). Angka pada laporan ini adalah kondisi aktual terverifikasi.

---

## 2. Status Verifikasi Teknis (Bukti Eksekusi Ulang)

```bash
# 1. Validator aset data
python3 tools/validate.py
# OK: semua data valid, referensi ter-resolve.

# 2. Test suite (dijalankan 3×, konsisten)
pytest -q
# FAILED tests/test_story.py::test_apply_action_calculate_ending - ValueError: kind aksi tidak dikenal: calculate_ending
# 1 failed, 455 passed in ~13s
# (1× dari 4 run: test_app.py::test_pilih_option_serang_melakukan_battle_step ikut gagal — flaky/urutan)

# 3. Lint
ruff check src launcher.py tools tests
# Found 2 errors: F401 unused import `pytest` (test_story.py:3), E501 line too long 82>80 (test_story.py:31)

# 4. Format
ruff format --check src launcher.py tools tests
# 1 file would be reformatted: src/engine/story.py (baris 63)
```

### Akar masalah test merah (kritis)
`tests/test_story.py` menuntut aksi event `{"kind": "calculate_ending"}` yang men-set flag `ending_<path>_win`, tetapi `ACTION_KINDS` di `src/engine/event.py` **belum memuat** `calculate_ending`, dan `apply_action` belum punya cabangnya. Artinya: `src/engine/story.py::calculate_ending()` (fungsi) sudah ditulis + state `ending_points` sudah ada + aksi `add_ending_points` sudah aktif, tetapi **penutup terakhir (aksi pemicu ending) belum di-wire** — pekerjaan Fase 4 (GDD §21) setengah jadi dan tidak ter-commit (`M src/engine/story.py`, `?? tests/test_story.py` di git status).

---

## 3. Inventaris Data Aktual (239 file JSON, 13 direktori)

| Direktori | File | Rincian |
|---|---|---|
| `data/quests/` | 37 | 24 main (101–108, 201–208 real; **301–308 placeholder**) + 13 faksi (10 real; **fquest_301–303 placeholder**) |
| `data/events/` | 45 | intro/done quest, unlock peta, echo memori, prompt pilihan |
| `data/items/` | 47 | 21 consumable (pil), 12 resep, 8 artefak, 5 material, 1 alat (`kuali_roh`) |
| `data/techniques/` | 30 | 30 teknik, seimbang 5 elemen |
| `data/enemies/` | 20 | 15 non-bos + 5 bertag `boss` (3 bos arc + 2 mini-bos faksi) |
| `data/npc/` | 18 | Emberfall, Sekte Azure, Guild City, Rebel Hideout, Cathedral |
| `data/dialogues/` | 11 | graf node multi-pilihan (elder_mao, lin_wei, xiu, kestrel, vega, sera, warden_kai, dll.) |
| `data/maps/` | 9 | 7 peta GDD + 2 ekstra (gua_abyss, hutan_kelabu) |
| `data/companions/` | 6 | 3 binatang roh (+1 varian evolusi) + 2 rekan cerita |
| `data/cultivation/` | 6 | 6 tingkatan lengkap (Pengumpul Qi → Penantang Surga) |
| `data/story/` | 5 | 5 echo memori |
| `data/formations/` | 3 | benteng_bumi, jaring_naga, langit_pecah |
| `data/shops/` | 2 | pedagang_kelana, toko_tie |

---

## 4. Matriks Target Konten GDD §22 vs Aktual

| Kategori | Target GDD | Aktual | % | Catatan |
|---|---|---|---|---|
| Quest utama | 32 | 24 file | 75% | **Konten nyata hanya 16** (Arc 1–2); 8 file Arc 3 = placeholder |
| Quest faksi | 10 | 13 file | 130% | Konten nyata 10; 3 file placeholder (fquest_301–303) |
| Peta baru | 10 | 9 file | 90% | 7 sesuai GDD + 2 ekstra; **hilang: `capital`, `ancient_vault`, `sky_seal`** |
| NPC | 25 | 18 | 72% | 10 inti GDD §10 ada; **hilang: `the_voice`** |
| Musuh non-bos | 30 | 15 | 50% | Kurang 15 (terutama Arc 3 lanjutan & Arc 4) |
| Bos | 5 | 3 arc-bos | 60% | penjaga_makam ✓, bos_sekte_bayangan ✓, bos_inquisitor_agung ✓; **hilang: Rasul Langit & Suara** (+2 mini-bos faksi sudah ada) |
| Teknik | 30 | 30 | 100% | ✅ lengkap |
| Resep pil | 14 | 12 | 86% | Kurang 2 |
| Artefak roh | 12 | 8 | 67% | Kurang 4 |
| Binatang roh | 4 | 3 (+1 evolusi) | 75% | serigala_bayangan, phoenix_abu, macan_baja; Arc 4 belum |
| Echo memori | 9 | 5 | 56% | Kurang 4 (terutama Arc 3 lanjutan & Arc 4) |

---

## 5. Matriks Implementasi Sistem GDD (yang SUDAH ada)

| GDD § | Sistem | Status & catatan |
|---|---|---|
| §4/§17 | Kultivasi: 6 tingkatan, insight, breakthrough (sukses/gagal, cedera −25% 2 hari, 30% inner demon **flag**), meridian 0–8, formula qi/hp/crit/miss/dodge | ✅ inti; ⚠️ pertarungan inner demon fisik ditunda (hanya flag + catatan) |
| §5 | Latar belakang & jalur (path) protagonis, rahasia via echo memori | ✅ (`background`, `path` di save; 4 jalur: sword/alchemy/formation/soul) |
| §6 | Combat turn-based, order agility tetap, tim max 4, 5 elemen ×1.5/×0.7, resonansi tim, defend/observe/escape/item | ✅; ⚠️ `swap` dalam combat ditunda (`ponytail:`) |
| §7 | Alkimia (12 resep, `learn_recipe`, refine + kuali_roh), artefak bertumbuh (`growth_stat`/`max_level`), binatang roh (rekrut + menetas + evolusi), formasi (3), toko (buy/sell, 40%, `shop_sold`, restock) | ✅ lengkap |
| §8 | 5 faksi, reputasi −100..+100, trigger event `reputation_reached` | ✅ |
| §9 | Gating peta via event `unlock_map` (`map_<id>_unlocked`), mekanisme `requires_flag` di enemies peta | ✅ |
| §10 | 18 NPC + 11 dialog graf | ✅ 18/25 (lihat §4) |
| §11 | Musuh & bos per arc | ⚠️ 20/35 (lihat §4) |
| §12 | Quest engine: 8 kind objective, `quest<id>_done` otomatis, dialog engine + `talked_<id>` + fallback | ✅ |
| §15 | Event engine: 6 trigger, 12 aksi, `once`, cascade, `prompt_choice` | ✅ |
| §16 | 13 status effect (3 dot, 3 kontrol, 3 debuff, 4 buff), bos kebal kontrol | ✅ |
| §18 | 30+ perintah dengan alias Indonesia, koreksi typo difflib, autocomplete TAB | ✅ lengkap (incl. combat) |
| §19 | Save v2: 3 slot + autosave, migrasi v1→v2, backfill `quest<id>_done`, atomic write, anti-corrupt `.bak` | ✅ |
| §20 | Party 4 slot, bond XP, peringkat rekan, rekrut+menetas, evolusi sekali, KO pulih otomatis | ✅ |
| §21 | `ending_points` (defy/seal/reconcile) + aksi `add_ending_points` + fungsi `calculate_ending()` | ⚠️ **setengah jadi** — aksi `calculate_ending` belum di-wire (test merah) |

---

## 6. Gap — yang BELUM ada (sesuai GDD)

### 6.1 Arc 4 (0% — GDD §12.1, §22)
- **Quest utama `quest401`–`quest408`** (8 quest).
- **Peta `capital`, `ancient_vault`, `sky_seal`** (GDD §9) — termasuk peta final pertarungan klimaks.
- **Bos `Rasul Langit` & `Suara`/`the_voice`** (GDD §11) + ~6 musuh non-bos Arc 4.
- **NPC `the_voice`** (GDD §10).
- 4 echo memori Arc 3–4 & 4 artefak tambahan untuk mencapai target §22.

### 6.2 Ending Dinamis (GDD §13, §21) — setengah jadi
- Aksi event `calculate_ending` **tidak ada** di `ACTION_KINDS`/`apply_action` (penyebab suite merah). Test menuntut: set `ending_<path>_win` berdasarkan jalur poin tertinggi.
- **Epilog berbasis reputasi 5 faksi** (GDD §21.2) — belum ada konten/generator.
- **Ritual + pertarungan dua tahap melawan Suara** (GDD §21.3) — belum ada (skema ritual, buff/penalti komponen, boss final 2-stage).
- 7 keputusan kunci penentu `ending_points` (GDD §21.1) — hanya landasan state/aksi yang ada, belum ada keputusan berjangkarnya di quest/dialog Arc 3–4.

### 6.3 Fitur ditunda (dicatat `ponytail:` / di-changelog)
- Pertarungan **inner demon** 30% (GDD §4.1) — flag & catatan saja.
- **Swap anggota dalam combat** (GDD §18.3) — swap hanya di lokasi aman.
- Penyempurnaan kecil Arc 3: dialog/variasi faksi, echo memori sampingan.

### 6.4 Kualitas (harus dibenahi sebelum klaim "selesai")
- 1 test gagal konsisten + 1 test flaky (lihat §2).
- 2 error `ruff check` + 1 file belum `ruff format`.
- Konten placeholder quest301–308 & fquest_301–303 harus diganti narasi grimdark asli (judul/deskripsi/objective/reward nyata).

---

## 7. Rekomendasi Langkah Selanjutnya

1. **Perbaiki suite merah dulu** (kecil): tambah `calculate_ending` ke `ACTION_KINDS` + cabang `apply_action` di `event.py`, bersihkan lint/format `test_story.py` & `story.py`. Ini menyelesaikan satu-satunya test gagal + 2 error lint.
2. **Isi konten Arc 3 yang asli** — ganti placeholder quest301–308 & fquest_301–303 dengan narasi grimdark (sesuai GDD §12, tone §3.6).
3. **Bangun Arc 4** — quest401–408, peta capital/ancient_vault/sky_seal, bos Rasul Langit & Suara, NPC the_voice, 4 memori, 4 artefak.
4. **Selesaikan sistem ending** — aksi `calculate_ending`, epilog berbasis reputasi, ritual 2-tahap, keputusan kunci di quest/dialog Arc 3–4.
5. **Fase 5 polish** — smoke test alur penuh (mulai → 4 arc → ending), selidiki test flaky `test_app`, tuning keseimbangan (GDD §24.2).
6. Commit pekerjaan yang belum di-commit (`story.py`, `test_story.py`, dokumen plan) setelah hijau.

---

*Laporan disusun ulang 7 Agustus 2026 berdasarkan verifikasi langsung: `validate.py`, `pytest -q` (3×), `ruff check`, `ruff format --check`, inspeksi `data/*.json`, dan `src/*.py`.*
