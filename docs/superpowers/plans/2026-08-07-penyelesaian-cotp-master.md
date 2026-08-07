# Penyelesaian Chronicle of the Past — Master Plan (Fase 1 → Rilis)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Menyelesaikan game dari kondisi saat ini (Fase 2 berjalan) sampai rilis v1.0 — Arc 2 playable penuh → Arc 3 → Arc 4 + ending dinamis → polish.

**Architecture:** Fase 1 menuntaskan sistem engine Fase 2 yang kurang (Formasi, Binatang Roh) lalu melengkapi data Arc 2. Fase 2–3 mengisi konten Arc 3 dan Arc 4 + engine ending dinamis (`calculate_ending` di `story.py`). Fase 4 balancing, migrasi save final, smoke test, dan dokumentasi. Semua gating cerita lewat event engine (GDD §15, §24.1 poin 16).

**Tech Stack:** Python 3.12+, Rich + Textual, pytest, ruff, stdlib.

## Global Constraints

- **TDD wajib**: test gagal dulu (RED) → implementasi minimal (GREEN). Data JSON: validator `python3 tools/validate.py` + test `*_data.py` harus lulus sebelum commit (AGENTS §2.1).
- **File stabil TIDAK disentuh**: `src/engine/combat.py`, `src/engine/cultivation.py`, `src/models/player.py` (AGENTS §6). Semua fitur baru memakai `src/core/game_loop.py` (stabil-tapi-bisa-diperluas) atau modul baru.
- Bahasa Indonesia untuk semua teks/dialog/narasi/docstring-prosa. Header docstring (Args/Returns/…) Bahasa Inggris.
- ID & nama berkas `snake_case`; baris ≤ 80; double quotes; import stdlib → third-party → lokal.
- Flag quest wajib `quest<id>_done`; siklus elemen Metal→Kayu→Tanah→Air→Api→Metal.
- Nada naratif **grimdark** (GDD §3.6): tanpa kemenangan bersih, musuh punya alasan konsisten.
- **Schema save tetap v2** sampai Fase 4 — setiap field baru (`formation_active`, evolusi, telur) memakai backfill (pola `party_active`, GDD §19.2).
- Verifikasi tiap task: `pytest -q` + `ruff check src launcher.py tools tests` + `ruff format --check` + `python3 tools/validate.py`. Setelah perubahan kode: `graphify update .`.
- Commit: `<lingkup>: <ringkasan>` (§9), satu perubahan logis per commit.

## Baseline Terverifikasi (7 Agustus 2026)

- Test 402 lulus, lint & format bersih, validator OK.
- **Selesai (jangan dikerjakan ulang)**: lint fix; artefak (`growth_stat`/`max_level`, `add_artifact_xp` dipanggil di `game_loop.py:1637`); command `meditate/examine/loot/recall(sebagian)/settings`; ending points (`state.py:112`, aksi `add_ending_points`); rekrut `serigala_bayangan` (event `quest208_done`).
- Data ada: 6 tier · 14 teknik (sword 5, formation 5, alchemy 2, soul 2) · 18 musuh (4 bos-tag) · 7 peta · 16 quest utama (101–108, 201–208) + 7 fquest · 38 item · 13 NPC · 3 rekan · 5 dialog · 37 event · 4 memori · 1 toko.

## Gap yang Harus Ditutup

| Area | Gap |
|-|-|
| Sistem Formasi | Tidak ada. `formation`/`formation_skill` dead command (di `input.py`, tanpa handler). |
| Sistem Binatang Roh | Evolusi belum ada; menetas dari telur belum ada; `_cmd_recall` stub; `macan_baja` data yatim (tanpa event rekrut). |
| Data Arc 2 | NPC kunci `blacksmith_tie`/`kestrel`; teknik alchemy(2)/soul(2) kurang; resep & artefak Arc 2; 1 echo memori; 3 faksi quest Arc 2. |
| Arc 3 | 0% — 3 peta, 7 NPC, quest301–308, 10 musuh (1 bos), 3 faksi quest, 2 memori. |
| Arc 4 + Ending | 0% — 2 peta, 5 NPC, quest401–408, ending engine, 2 bos, sisa pool data. |
| Polish | Balancing, migrasi save final, smoke test 4 arc + 3 ending, README (basi: "Fase 0"). |

## Fase & Dependensi

1. **`2026-08-07-fase2-rampung.md`** (Fase 1, prioritas tertinggi) — formasi → binatang roh → data Arc 2 → housekeeping.
2. **`2026-08-07-arc3.md`** (Fase 2) — konten Arc 3 (butuh Fase 1 rampung).
3. **`2026-08-07-arc4-ending.md`** (Fase 3) — Arc 4 + ending dinamis (butuh Fase 2).
4. **`2026-08-07-polish-rilis.md`** (Fase 4) — balancing, migrasi, smoke test, README, rilis.

## Definisi Selesai per Fase (gate)

- [ ] `pytest -q` lulus penuh
- [ ] `ruff check` dan `ruff format --check` bersih
- [ ] `python3 tools/validate.py` OK (semua referensi ter-resolve)
- [ ] Data mengikuti GDD §22 (target per arc)
- [ ] Arc playable (smoke test manual) dan/atau unit test alur utama
- [ ] `graphify update .` dijalankan setelah perubahan kode
- [ ] Tidak melanggar AGENTS §11

## Catatan Teknis

1. **Pola buff formasi** (tanpa menyentuh `combat.py`): buff diterapkan ke SEMUA ally di `game_loop._start_battle` (perluas loop buff item di `game_loop.py:1469`); `formation_skill` diterjemahkan ke `technique:<skill>` di `game_loop.battle_step:1562`; skill formasi masuk `player_skills` saat formasi aktif (`game_loop.py:1443`).
2. **Pola evolusi** (tanpa menyentuh `cultivation.py`): cek kondisi evolusi di `_cmd_breakthrough` setelah sukses breakthrough (`game_loop.py:1217`).
3. **Pool teknik** saat ini: sword 5, formation 5, alchemy 2, soul 2 → penambahan difokuskan ke alchemy & soul (target total 30, GDD §22).
4. **`src/systems/`** kosong → formasi masuk `src/systems/formation.py` (GDD §14.2).
5. Rekan/binatang roh diwakili `data/companions/`; `state.party_active` (max 3 slot, GDD §20.1).
