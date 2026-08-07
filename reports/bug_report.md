# Bug Report — Chronicle of the Past

Tracker temuan perburuan bug (master plan `2026-08-08-bughunt-master-plan.md`).
Severitas: **Critical** (crash/kehilangan data/quest buntu) · **Important**
(perilaku salah tak fatal) · **Minor** (kosmetik/robustness).

Status: `OPEN` | `FIXED` | `DEFERRED`.

---

## BUG-1 · Important — KeyError crash saat inventory tanpa kunci `equipped`

- **Area:** `src/core/game_loop.py` (`_cmd_equip`, `_cmd_unequip`, `_finish_battle`)
  & `src/systems/artifact.py` (`add_artifact_xp`)
- **Reproduksi (terbukti runtime):**
  ```python
  s = GameState(player=Player(name="X"))
  s.inventory = {"items": {"cermin_bayangan": 1}}  # tanpa equipped/artifacts
  ses._cmd_equip(Command("equip", ("cermin_bayangan",), ""))
  # → CRASH: KeyError 'equipped'
  ```
- **Akar:** `GameState.__post_init__`/`from_dict` hanya memakai
  `data.get("inventory", {...})` tanpa backfill kunci `equipped`/`artifacts`;
  handler mengakses `inventory["equipped"]` langsung.
- **Dampak:** save editan tangan / legacy tanpa kunci tersebut → UI crash
  (hanya `CommandError` yang ditangkap `_run_command`).
- **Fix yang mungkin:** backfill kunci inventory di `from_dict`/`__post_init__`
  + guard `.get` di handler (TDD).
- **Fix (Batch A, 2026-08-08):** backfill inventory di `GameState.from_dict`
  (merge default `items/equipped/artifacts`); non-dict ditolak ValueError.
- **Status:** FIXED

---

## BUG-2 · Important — KeyError crash saat `pending_dialog` menunjuk node yang tak ada

- **Area:** `src/core/game_loop.py` (`_choose_dialog`), `src/engine/dialog.py` (`get_node`)
- **Reproduksi (terbukti runtime):**
  ```python
  s.flags["pending_dialog"] = {"dialog_id": "dialog_elder_mao_1", "node": "node_tidak_ada"}
  ses._cmd_choose(Command("choose", ("1",), "choose 1"))
  # → CRASH: KeyError 'node_tidak_ada'
  ```
- **Akar:** `_choose_dialog` menangani `dialog is None`, tapi `get_node`
  (KeyError) untuk node yang hilang tidak dibungkus guard.
- **Dampak:** save lama/data dialog berubah di tengah percakapan → crash UI.
- **Fix yang mungkin:** tangkap KeyError → bersihkan `pending_dialog` + pesan
  ramah (pola sama dengan dialog None).
- **Fix (Batch A, 2026-08-08):** guard `get_node` di `_choose_dialog`
  (bersihkan pending + pesan) dan `dialog_choices` (kembalikan []).
- **Status:** FIXED

---

## BUG-3 · Minor — Aksi event `start_dialog` tidak dikonsumsi (fitur mati)

- **Area:** `src/engine/event.py` (kind `start_dialog`, baris 159)
- **Bukti:** `result.dialogs` hanya di-append (`event.py:159`), tidak pernah
  dibaca modul mana pun (code search: 1 match, itu sendiri).
- **Dampak:** event dengan aksi `start_dialog` hanya menampilkan log
  "Sebuah dialog dimulai: ..." — dialog tidak pernah benar-benar terbuka.
- **Keputusan (Batch D, 2026-08-08):** DEFERRED — tidak ada data yang
  memakai aksi ini; test engine tetap ada sebagai kontrak API. Komentar
  `ponytail:` ditambahkan di `event.py` (kapan dipakai → wire ke
  `_start_dialog`).
- **Status:** DEFERRED

---

## BUG-4 · Minor — Efek item `buff_qi_max` & `resist_*` tidak berefek di battle

- **Area:** `src/core/game_loop.py` (`_start_battle`, `_cmd_use`)
- **Bukti data:** `gelang_qi` (effect `buff_qi_max: 20`), `jubah_bayangan`
  (`resist_dark`), `elixir_empedu_api` (`resist_poison`).
- **Akar:** buff diterapkan ke `ally.stats["qi_max"]`, tetapi `Combatant.stats`
  hanya memakai attack/defense/agility/intelligence/vitality/spirit —
  `hp_max`/`qi_max` adalah field terpisah → `buff_qi_max` diabaikan.
  `resist_*` dicatat di stats tapi tidak dibaca engine combat (catatan
  "Fase 2" di kode — sengaja, tapi perlu diingat).
- **Dampak:** pemain membayar/memakai item yang janji efeknya tidak berjalan.
- **Fix (Batch D, 2026-08-08):** `_start_battle` menerapkan `buff_qi_max`/
  `buff_hp_max` ke field `Combatant.qi_max`/`hp_max` (bukan `stats[
  "qi_max"]` yang mati). Semantik capacity-buff: max naik, isi tetap
  (konsisten — qi regenerasi, hp butuh heal; dicatat `ponytail:` di test).
  `resist_*` tetap DEFERRED (engine combat belum membaca resist — catatan
  Fase 2 di kode).
- **Status:** FIXED (resist_* DEFERRED)

---

## BUG-5 · Minor — `_validate_references` (save.py) tidak memvalidasi item/quest/peta/teknik

- **Area:** `src/core/save.py::_validate_references`
- **Bukti (baca kode):** hanya memvalidasi `location`, `stats` player, dan
  `formation_active`. Item di inventory, quest id, lokasi, teknik di skills
  tidak dicocokkan dengan data/.
- **Dampak:** save dengan referensi rusak lolos load → error samar di
  tengah permainan (mis. item tak dikenal di `_cmd_inventory` ditampilkan
  mentah — sudah ada ponytail note).
- **Status:** OPEN
- **Fix (Batch C, 2026-08-08):** `_validate_references` kini memvalidasi
  item inventory/equipped, quest id (started/done/failed), party id, dan
  skill party terhadap data/ — save rusak ditolak SaveError saat load.
- **Status:** FIXED

---

## BUG-6 · Minor — Trigger `flag` EQUALS tanpa `value` cocok dengan flag yang hilang

- **Area:** `src/engine/event.py::_match_trigger`
- **Analisis:** `condition.get("value")` → None saat tak ada; `flags.get(flag)`
  juga None saat hilang → `EQUALS None` cocok untuk flag yang belum diset.
  Semantik "flag == None" bisa tak diinginkan untuk trigger tertentu.
- **Status:** OPEN (perlu cek data apakah ada trigger memakai pola ini)
- **Fix (Batch C, 2026-08-08):** EQUALS tanpa value kini = "flag diset"
  (`actual is True`); data tidak ada yang memakai pola lama (diverifikasi).
- **Status:** FIXED

---

## BUG-7 · Minor — `add_ending_points` dengan path tak dikenal menambah kunci liar

- **Area:** `src/engine/event.py` (kind `add_ending_points`)
- **Analisis:** `state.ending_points.get(path, 0)` lalu set — path di luar
  {defy, seal, reconcile} masuk sebagai kunci liar (tidak dipakai
  `calculate_ending`, ikut tersimpan di save).
- **Status:** OPEN (data tidak memakainya — robustness saja)
- **Fix (Batch C, 2026-08-08):** path di luar {defy, seal, reconcile}
  ditolak ValueError di `apply_action` — mencegah kunci liar.
- **Status:** FIXED

---

## BUG-8 · Minor — `grant_gold`/`change_reputation` tanpa guard nilai negatif ekstrem

- **Area:** `src/engine/event.py`
- **Analisis:** `grant_gold` menambah `amount` apa adanya; `gold` tidak pernah
  di-clamp ≥ 0 (pembelian sudah di-guard, jalur event tidak).
- **Status:** OPEN (data bersih saat ini — robustness)
- **Fix (Batch C, 2026-08-08):** `grant_gold` di-clamp `max(0, ...)`
  (emas tak pernah negatif); change_reputation negatif tetap sah (test
  mengunci perilaku itu).
- **Status:** FIXED

---

## BUG-9 · Note — RichLog tanpa batas pertumbuhan (performa sesi panjang)

- **Area:** `src/ui/app.py` (`#game-log`)
- **Analisis:** log ditulis tanpa cap; sesi panjang / battle massal bisa
  menurunkan performa render Textual.
- **Keputusan (Batch D, 2026-08-08):** DEFERRED — bukan bug fungsional;
  komentar `ponytail:` ditambahkan di `src/ui/app.py` (kapan perlu cap →
  ukur performa sesi panjang dulu).
- **Status:** DEFERRED (Minor; bukan bug fungsional)

---

## BUG-10 · Note — Istirahat memulihkan HP penuh walau masih cedera

- **Area:** `src/core/game_loop.py::_cmd_rest`
- **Analisis:** `player.hp = hp_max` di-set sebelum `advance_day`; cedera
  (injury_days_remaining) belum tentu habis → HP penuh + stat −25% selama
  sehari. Konsisten dengan desain (cedera = penalti stat terpisah) — dicatat
  sebagai catatan desain, bukan bug.
- **Keputusan (Batch D, 2026-08-08):** ditutup sebagai desain (GDD §4.1:
  cedera = penalti stat sementara; pemulihan HP penuh saat istirahat
  adalah perilaku yang dimaksudkan).
- **Status:** CLOSED (desain)

---

## BUG-11 · Important — 35 item tidak pernah bisa diperoleh (konten mati)

- **Area:** `data/items/*.json` (35 dari 53 item)
- **Bukti (BFS reachability, `scratch_item_reach.py`):** hanya **18 item**
  yang bisa diperoleh pemain via semua sumber resmi — event `grant_item`
  (termasuk di dalam `prompt_choice`), reward quest, stock toko, rantai
  resep (`learn_recipe` → bahan-bahan). Sisanya **35 tak terjangkau**:
  - **8 artefak:** `cermin_bayangan`, `cincin_roh_kenabian`, `gelang_qi`,
    `jimat_roh_liar`, `jubah_bayangan`, `liontin_api`, `mahkota_ashfall`,
    `talisman_penyegel`
  - **13 konsumabel:** `elixir_empedu_api`, `pil_antidot`, `pil_asar_jiwa`,
    `pil_baja_tubuh`, `pil_besi_hitam`, `pil_buka_meridian`, `pil_kristal`,
    `pil_langkah_angin`, `pil_pemahaman_sharif`, `pil_pemulih_kecil`,
    `pil_qi_tenang`, `pil_racun_meridian`, `telur_phoenix_abu`
  - **14 resep:** `resep_pil_angin/asar_jiwa/baja/baja_hitam/baja_tubuh/`
    `besi_hitam/kristal/peneguh_fondasi/qi_tenang/racun`, `resep_ramuan_meridian`
    (+ lainnya)
- **Pengecualian wajar:** `pil_uji_buff`, `pil_uji_heal` (item test).
- **Dampak:** janji konten (artefak kuat, pil breakthrough, resep ala
  GDD §7) tidak tercapai pemain normal; beberapa artefak (mis.
  `talisman_penyegel`, `mahkota_ashfall`) tampak bernilai cerita/ending.
- **Fix yang mungkin:** wire ke reward quest/event/boss drop sesuai desain;
  jangan dihapus tanpa diskusi (GDD §6: data eksisting hanya ditambah).
- **Fix (Batch B, 2026-08-08):** 34 item di-wire ke `rewards.grant_items`
  quest (quest203–207, 301–307, 401–406, fquest_gilda_kontrak) + event
  `fquest_hutan_ember_done` (telur_phoenix_abu) sesuai lore per arc;
  engine quest diperluas mendukung `grant_items` (list, backward-compat
  `grant_item`). Test `test_semua_item_dapat_diperoleh` (BFS reachability)
  mengunci 0 item unreachable selamanya.
- **Status:** FIXED

---

## BUG-12 · Important — Kompanion `kestrel` & `phoenix_abu` tak bisa diperoleh

- **Area:** `data/companions/kestrel.json`, `data/companions/phoenix_abu.json`
- **Bukti (code search + BFS):**
  - `add_companion` hanya untuk `lin_wei`, `macan_baja` (+ `quest208_done`);
    tidak ada event/dialog yang merekrut **kestrel** — padahal
    `fquest_gilda_kontrak` punya objektif `talk` ke kestrel dan
    `dialog_kestrel_1` ada.
  - **phoenix_abu** hanya menetas dari `telur_phoenix_abu` (effect
    `hatch_companion`) — dan telur itu sendiri unreachable (BUG-11).
  - `serigala_bayangan` & `lin_wei` & `macan_baja` **aman** (via
    `quest208_done`, `lin_wei_recruit`, `macan_baja_recruit`).
- **Dampak:** 2 dari 5 kompanion (40%) tidak pernah bisa direkrut.
- **Fix yang mungkin:** tambahkan aksi `add_companion`/`hatch` di event
  quest faksi atau drop bos sesuai lore.
- **Fix (Batch B, 2026-08-08):** event baru `kestrel_recruit` (trigger
  `fquest_gilda_kontrak_done` → `add_companion kestrel`, pola
  `macan_baja_recruit`); `telur_phoenix_abu` di-grant event
  `fquest_hutan_ember_done` → `use` telur menetas `phoenix_abu` (GDD
  §20.2). Test `test_semua_kompanion_dapat_direkrut` mengunci jalur
  rekrut untuk semua kompanion.
- **Status:** FIXED

---

## Fase 2 — yang sudah diverifikasi BERSIH (bukan bug)

- **Referensi putus:** tidak ada — semua quest/event/NPC/map/enemy/teknik/
  formasi/kompanion ter-resolve (termasuk aksi di dalam `prompt_choice`
  event *dan* pilihan dialog).
- **Quest buntu (deadlock):** tidak ada — semua `next`/`requires_flag`
  menunjuk id yang ada; tidak ada objektif `collect` yang menarget item
  mati (BUG-11 tidak mengganjal quest).
- **Memori:** 10/10 di-grant (temuan awal "memory_arc1_complete mati"
  adalah **false positive** dari script yang tidak menembus `prompt_choice`;
  `quest108_done` dan `dialog_the_voice_1` memang men-grant-nya).
- **Duplikasi ID:** tidak ada — semua id unik per domain.
- **Balance sanity:** kurva musuh per tier masuk akal (Arc 1 lemah →
  `rasul_langit` 1800 hp / `suara` 3000 hp di puncak); tidak ada anomali
  yang harus di-flag.

---

## BUG-13 · Important — KeyError `agility` crash saat battle dengan party member tanpa stats

- **Area:** `src/engine/combat.py::_resolve_physical` (baris ~385),
  `src/models/combatant.py::combatant_from_companion`
- **Reproduksi (terbukti runtime, seed 42 fuzz deep):**
  ```python
  state.party = [{"id": "kestrel"}]          # save korup: tanpa stats
  state.party_active = ["kestrel"]
  # battle di ashfall_forest, musuh menyerang ally pertama
  # → KeyError: 'agility' (target_stats["agility"])
  ```
- **Akar:** `Companion.from_dict` toleran `stats` kosong (backfill `{}`),
  `combatant_from_companion` menyalinnya ke `Combatant.stats`, dan battle
  mengakses `stats["agility"]` langsung (dodge_chance) saat musuh
  menyerang → KeyError. Jalur rekrut normal AMAN (`load_companion().
  to_dict()` skema penuh), jadi ini kelas save korup/legacy — sama
  dengan BUG-1/2.
- **Dampak:** save editan tangan / party rusak → UI crash saat battle.
  `_validate_references` (BUG-5) tidak memvalidasi `state.party`.
- **Fix yang mungkin:** validasi/backfill stats party di `from_dict`
  (default dari data/companions) atau guard `stats.get` di combat.
- **Fix (Batch A, 2026-08-08):** backfill stats party di
  `GameState.from_dict` via `load_companion()` — merge per-kunci untuk
  stats kosong ATAU parsial (nilai eksisting dipertahankan); id tak
  dikenal dibiarkan, divalidasi keras di lapisan save/BUG-5.
- **Status:** FIXED

---

## Fase 3 — hasil fuzz dinamis (yang sudah diverifikasi AMAN)

Dijalankan `scratch_fuzz.py` (deterministik seeded) 6 seed (42, 1337, 7,
99, 2026, 555):

- **Fuzz perintah dunia** (600-800 langkah/seed): 0 crash di play normal,
  0 pelanggaran invariant (hp/qi/gold/stock/day/hour) — semua argumen
  valid, salah, garbage, dan kosong ditangani sebagai pesan, bukan crash.
- **Auto-battle massal** (semua 37 musuh × aksi acak): 0 crash; battle
  selalu berakhir (menang/kalah/kabur) tanpa loop tak terbatas;
  `formation_skill` tanpa formasi aman (error frame).
- **Save round-trip** (to_dict→from_dict & save_game→load_game): identik
  (gold/nama dipertahankan).
- **Mutasi save acak** (60 trial: kunci dihapus/None/tipe salah):
  `load_game` selalu melempar `SaveError` yang rapi — tidak ada
  exception liar.
- **Fuzz deep** (semua peta terbuka, tier puncak, 4 anggota tim,
  ritual/bos flags): 0 crash dengan party skema penuh → alur late-game
  (ritual, bos, ending) stabil.

**Temuan:** BUG-13 (satu-satunya crash) — hanya muncul dari save korup,
  bukan play normal.

---

## Ringkasan

| Severitas | Jumlah | ID |
|---|---|---|
| Critical | 0 | — |
| Important | 5 | BUG-1 ✅, BUG-2 ✅, BUG-11 ✅, BUG-12 ✅, BUG-13 ✅ |
| Minor | 6 | BUG-3 ⏸, BUG-4 ✅ (resist_* ⏸), BUG-5 ✅, BUG-6 ✅, BUG-7 ✅, BUG-8 ✅ |
| Note | 2 | BUG-9 ⏸, BUG-10 ✅ (desain) |

⏸ = DEFERRED (dicatat `ponytail:` di kode) · ✅ = FIXED/CLOSED.

**Terbukti runtime:** BUG-1, BUG-2, BUG-13 · **Terbukti code-search/read:**
BUG-3, BUG-4, BUG-5, BUG-9, BUG-10 · **Terbukti BFS/scan data:** BUG-11,
BUG-12 · **Analisis statik:** BUG-6, BUG-7, BUG-8.

*Diisi: 8 Agustus 2026 — Fase 1 (review statik), Fase 2 (integritas data),
Fase 3 (fuzz dinamis). Batch A (BUG-1/2/13), Batch C (BUG-5/6/7/8),
Batch D (BUG-3/4/9/10) dan Batch B (BUG-11/12) selesai dengan TDD
2026-08-08. Semua 13 temuan tertutup (FIXED/CLOSED/DEFERRED dengan
`ponytail:` note).*
