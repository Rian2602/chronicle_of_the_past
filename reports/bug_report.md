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
---

## Putaran 2 — TUI Hunt & Regresi (8 Agustus 2026)

Metode: fuzz deterministik ulang (5 seed, 0 crash), TUI hunt via tmux
(terminal 120×30/120×45, alur interaksi penuh), playthrough Arc 4 +
fitur eksternal `_battle_use_item`, audit balance & cross-check flag.

## BUG-14 · Important — HUD menampilkan HP 0/80 setelah kalah battle

- **Area:** `src/core/game_loop.py` (`status_lines`, `_finish_battle`)
- **Reproduksi (terbukti tmux):** kalah battle (KO) → pesan "sadar
  kembali dengan luka menganga" → HUD & perintah `status` menampilkan
  `HP 0/80` padahal `state.player.hp` sudah dipulihkan ke 80.
- **Akar:** `_finish_battle` meng-set `player.hp = player.hp_max` pada
  jalur kalah, tapi `self._ally` (combatant lama dengan hp 0) tidak
  di-reset ke None. `status_lines` memilih `self._ally.hp` selama
  `_ally is not None` → menampilkan nilai stale 0.
- **Dampak:** pemain berpikir HP-nya 0 (harus rest) padahal sebenarnya
  pulih; `status` menipu. Reproduksi headless membuktikan
  `player.hp == 80` — bug murni di lapisan tampilan.
- **Fix yang mungkin:** reset `self._ally = None` (dan `_ally_map = {}`)
  di akhir `_finish_battle`; atau `status_lines` hanya memakai
  `_ally.hp` saat `self.in_battle`.
- **Fix (Putaran 2, 2026-08-08):** `_finish_battle` kini reset
  `self._ally = None` + `self._ally_map = {}` di akhir (berlaku untuk
  semua jalur: menang/kalah/kabur — `_write_back_allies` sudah dipanggil
  sebelumnya, `battle_frame` tidak membaca `_ally`, `_cmd_party` di-guard
  `in_battle`). Test RED→GREEN:
  `test_status_lines_pasca_kalah_tidak_stale`.
- **Status:** FIXED

## BUG-15 · Minor — OptionList aksi tidak auto-highlight opsi pertama

- **Area:** `src/ui/app.py` (`_populate_actions`)
- **Reproduksi (terbukti tmux):** setelah setiap aksi, menu aksi
  di-rebuild via `set_options` → `highlighted` reset ke None → tekan
  Enter pada opsi pertama tidak merespons; pemain harus menekan panah
  bawah dulu setiap kali (tidak ada indikator seleksi visual).
- **Akar:** Textual 8.2.8 tidak auto-highlight opsi pertama setelah
  `set_options` saat widget difokus; test suite menyetel `highlighted`
  secara programatik sehingga lolos test.
- **Dampak:** UX tersendat — satu ketukan ekstra (Down) per aksi;
  pemain bisa salah pilih (Enter tanpa Down = tidak ada aksi).
- **Fix yang mungkin:** di `_populate_actions`, set `highlighted = 0`
  setelah mengisi opsi (bila daftar non-kosong).
- **Fix (Putaran 2, 2026-08-08):** `_populate_actions` set
  `actions.highlighted = 0` setelah `set_options` bila daftar
  non-kosong. Terbukti tmux: Enter langsung mengeksekusi opsi pertama
  (Lihat → deskripsi lokasi muncul) tanpa panah dulu. Test RED→GREEN:
  `test_aksi_auto_highlight_opsi_pertama`.
- **Status:** FIXED

## BUG-16 · Minor — Log game tak terbaca di terminal pendek

- **Area:** `src/ui/app.py` (`compose`, `#content-tabs` / `#game-log`)
- **Reproduksi (terbukti tmux):** di terminal 120×30, panel log
  terdesak jadi 1 baris (teks tidak terlihat, hanya artefak scrollbar);
  di 120×45 log tampil penuh.
- **Akar:** tata letak tanpa height minimum untuk area konten.
- **Dampak:** pemain di terminal kecil tidak bisa membaca narasi/battle
  log sama sekali.
- **Fix yang mungkin:** beri `min_height` pada area konten / `#game-log`
  atau `overflow-y` yang memaksa scroll yang benar.
- **Fix (Putaran 2, 2026-08-08):** `min-height: 5` pada `#content-tabs`,
  `#game-log`, `#memory-log`, `#map-panel`. Terbukti tmux (matriks
  ukuran): log terbaca di 120×30, 24, 18, 16, 15 baris; di bawah 15
  baris menu aksi yang terpotong (trade-off dicatat `ponytail:` di
  CSS), bukan log. Test RED→GREEN:
  `test_log_terbaca_di_terminal_pendek` (size=(120,30)).
- **Status:** FIXED

## BUG-17 · Minor — Riwayat log hilang saat resume (Lanjutkan)

- **Area:** `src/ui/app.py` (tombol Lanjutkan → `GameScreen(initial_log=[])`)
- **Reproduksi (terbukti tmux):** escape ke menu → Lanjutkan (c) →
  sesi state dipertahankan (nama, lokasi, HP, insight) tapi log/story
  history kosong.
- **Dampak:** pemain kehilangan konteks narasi sesi berjalan.
- **Fix yang mungkin:** simpan log terakhir di `GameSession`/app dan
  teruskan ke `GameScreen` saat resume.
- **Fix (Putaran 2, 2026-08-08):** `ChronicleApp.log_history` (cap 200
  baris) diisi `_remember_log` di `_run_command`/`_battle_raw`
  (termasuk cabang observe); resume (`action_resume_game`) meneruskan
  `initial_log=list(log_history)`; mulai baru & muat save me-reset
  riwayat (muat = pesan hasil load). Terbukti tmux: setelah escape →
  Lanjutkan (c), log masih berisi baris sesi sebelumnya. Test
  RED→GREEN: `test_resume_mempertahankan_riwayat_log`.
- **Status:** FIXED

## Ringkasan Putaran 2

| Severitas | Jumlah | ID |
|---|---|---|
| Critical | 0 | — |
| Important | 1 | BUG-14 ✅ |
| Minor | 3 | BUG-15 ✅, BUG-16 ✅, BUG-17 ✅ |

*Semua 4 temuan putaran 2 FIXED dengan TDD RED→GREEN + verifikasi tmux
(BUG-15/16/17 di terminal asli; BUG-14 via test headless + unit).
Rencana perbaikan: `docs/superpowers/plans/2026-08-08-bughunt-round2-fix-plan.md`.*

---

## Putaran 3 — Sistem Baru & Playthrough Deep (8 Agustus 2026)

Metode: fuzz sistem baru (ritual/formation/swap/recall/unequip/buy/sell/
refine — 3 seed × 300 langkah dunia + 150 battle, 0 crash), playthrough
dalam (ritual sukses/gagal, battle swap 4 anggota, 3 dialog bercabang
aktual + elder_mao, evolusi & hatch, formation_skill battle). Rencana:
`docs/superpowers/plans/2026-08-08-bughunt-round3.md` (Fase A–B).

## BUG-18 · Important — Battle swap mengganti rekan yang salah (fallback active[0])

- **Area:** `src/core/game_loop.py` (`_battle_swap`, fitur eksternal yang
  ikut ter-commit putaran 2)
- **Reproduksi (terbukti runtime):** party 4 (aktif lin_wei/jati/kestrel,
  cadangan guntur); battle; majukan sampai giliran **Jati**; `swap:guntur`
  → **lin_wei yang keluar**, bukan Jati (rekan yang sedang bertarung).
- **Akar:** `_battle_swap` mencocokkan `current.name` (mis. `"Jati"`)
  dengan `raw["id"]` (mis. `"jati"`) — dua domain berbeda, **tidak pernah
  cocok** → `current_id` selalu None → fallback `active[0]` (lin_wei)
  selalu keluar walau giliran milik rekan lain. Saat giliran protagonis
  (bukan rekan), fallback memang benar — bug hanya terlihat saat giliran
  rekan non-pertama.
- **Dampak:** pemain yang swap rekan terpukul bisa menukar rekan yang
  salah (yang masih segar keluar, yang terluka tetap di medan).
- **Fix (Putaran 3, 2026-08-08):** cocokkan via `_ally_map` (referensi
  objek `combatant is battle.current`, filter `cid in active`) — sama
  dengan cara `_write_back_allies` menemukan combatan. Test RED→GREEN:
  `test_battle_swap_mengganti_rekan_yang_sedang_giliran`.
- **Perluasan BUG-18 (review independen, 3 isu dikonfirmasi + fixed):**
  1. *Swap kedua gagal identity match* — setelah swap 1, map lama
     di-rebuild membuat objek baru ≠ battle.allies → swap 2 tidak cocok.
  2. *Damage rekan hilang* — HP/qi live tidak disinkron ke party sebelum
     swap → luka terbakar saat combatant dibangun ulang dari raw lama.
  3. *Rekan pengganti tidak pernah benar-benar bertarung* — akar masalah:
     `_rebuild_ally_map` membangun map terpisah yang tidak pernah
     menggantikan objek di `battle.allies`/`turn_order` (engine combat
     membandingkan via identitas objek, GDD §6) → musuh tetap menyerang
     rekan yang sudah keluar, rekan baru tidak diserang & tidak menyerang.
- **Fix final (Putaran 3):** `_battle_swap` kini mengganti objek
  Combatant **in-place** di `battle.allies` & `battle.turn_order`
  (identity), menyinkron HP/qi live ke `state.party` sebelum komposisi
  berubah, dan membangun combatant rekan masuk dari raw tersimpan.
  `_rebuild_ally_map` dihapus (mati — tak ada pemanggil tersisa).
  Formasi aktif diterapkan ke rekan yang baru masuk (GDD §7).
  Test RED→GREEN: `test_battle_swap_kedua_masih_mengganti_yang_giliran`
  (swap 1→2→3), `test_battle_swap_damage_rekan_tidak_hilang`,
  `test_battle_swap_rekan_baru_benar_bertarung` (rekan baru ada di
  battle.allies, giliran berlanjut normal).
- **Status:** FIXED

## Verifikasi BERSIH putaran 3 (bukan bug)

- **Ritual**: jalur sukses (artefak pedang_taring_naga + formasi + tim)
  set `ritual_ready` + pesan "sudah selesai" saat diulang; jalur gagal
  menampilkan daftar alasan tanpa set flag. Benar.
- **Battle swap HP/qi**: cadangan yang masuk memakai HP tersimpan di
  party (12/40 terbawa ke combatant live). Benar (setelah BUG-18).
- **Dialog bercabang** (xiu/fang_yue/blacksmith_tie/elder_mao): semua
  node `next` valid, percakapan selesai (flag talked), change_reputation
  diterapkan. Benar.
- **Evolusi & hatch**: breakthrough multi-tier tidak crash; telur phoenix
  menetas; hatch duplikat ditolak (guard). Benar.
- **formation_skill**: tersedia di sub-menu Teknik saat formasi aktif;
  dieksekusi tanpa crash; tanpa formasi = error frame ramah. Benar.
- **Fuzz sistem baru**: 0 crash; invariant hp/qi/gold ≥ 0, party_active
  ≤ 3 dan valid. Benar.

## Catatan Balance (bukan bug) — item reward vs gold quest

- Banyak item grant jauh lebih bernilai dari gold reward quest
  (mis. talisman_penyegel harga 2500 vs quest401 gold 300;
  mahkota_ashfall 2000 vs quest304 gold 150; cincin_roh_kenabian 1200
  vs quest303 gold 200). Item reward = bonus naratif, bukan masalah
  fatal — dicatat untuk peninjauan kurva ekonomi.
- Keseimbangan battle awal: Serang 2–3 damage/giliran vs Bandit
  Perbatasan 10–11 damage → spam Serang selalu kalah (dikalahkan saat
  musuh 10/28). Catatan desain untuk iterasi balance Arc 1.

## False positive (sudah diverifikasi bukan bug)

- `quest405` objective `ritual_ready`: di-set oleh perintah `ritual`
  (`_cmd_ritual` → `check_ritual_ready` + `state.flags`), bukan event —
  jalur pemicu ada, bukan deadlock.
- Perintah kosong `''`/spasi: ditangani "Belum tersedia" (tidak crash).
- Fitur eksternal `_battle_use_item` (use:<id> di battle): heal
  bekerja, material ditolak — berfungsi benar.
- Fuzz regresi: 5 seed (42/1337/7/99/555) × 400 langkah = 0 crash,
  save round-trip identik, battle selalu berakhir.

---

## Putaran 3 Fix — Balance Gold Quest + Fase C–E Lanjutan (8 Agustus 2026)

Metode (rencana `2026-08-08-bughunt-round3-fix-plan.md`): verifikasi
final BUG-18 (fuzz ulang swap 3 seed × 27 swap, 0 crash), balance gold
reward quest (TDD RED→GREEN), audit data Arc 2–4 (BFS penuh), save
migrasi & korupsi parsial, TUI hunt battle di tmux 80×24.

## BALANCE-1 · Note→Fix — Gold quest tak sebanding nilai item yang di-grant

- **Area:** `data/quests/*.json` (rewards.gold) — 11 quest
- **Bukti (skrip):** quest yang men-grant item mahal memberi gold jauh
  lebih kecil (quest401 grant talisman_penyegel 2500 → gold 300;
  quest304 grant mahkota_ashfall 2000 → gold 150; quest303 grant
  cincin_roh_kenabian 1200 → gold 200).
- **Keputusan pemilik proyek (2026-08-08):** sesuaikan gold reward.
  Aturan: `gold_baru = max(gold, floor(30% × nilai_item / 50) × 50)`.
- **Fix (TDD RED→GREEN):** test baru
  `test_gold_reward_sebanding_grant_item` (tests/test_quest_data.py)
  gagal untuk 11 quest → update gold: fquest_gilda_kontrak 40→100,
  quest203 50→150, quest204 20→150, quest205 40→100, quest206 50→150,
  quest207 100→200, quest303 200→350, quest304 150→600, quest401
  300→850, quest403 400→500, quest404 200→350. Item tanpa `price`
  (artefak naratif) bernilai 0, tidak mengunci.
- **Status:** FIXED

## BUG-19 · Minor — Menu aksi battle tidak terlihat di terminal 80×24

- **Area:** `src/ui/app.py` (battle actions OptionList)
- **Reproduksi (terbukti tmux 80×24):** saat battle dimulai, menu aksi
  (Serang/Teknik/Bertahan/Amati/Item/Kabur) **tidak tampil sama sekali**
  — baris terpotong di bawah footer; navigasi buta (Down×5 + Enter
  untuk Kabur terbukti berfungsi, tapi pemain tak bisa melihat opsi).
- **Dampak:** di terminal pendek, pemain tidak tahu aksi apa yang
  tersedia saat battle; hanya bisa menebak urutan.
- **Status:** DEFERRED (Minor UX, note `ponytail:` di `app.py`) —
  perbaikan tata letak battle frame di terminal pendek butuh redesign
  layout; kelas yang sama dengan BUG-16 (log tak terbaca) yang sudah
  FIXED, jadi kandidat iterasi UI berikutnya.

## BUG-20 · Minor — Header clock (jam) menimpa border panel kanan

- **Area:** `src/ui/app.py` (Header clock)
- **Reproduksi (terbukti tmux 80×24):** jam kanan atas menabrak garis
  border panel kanan (`▔▔` terlihat di capture); HUD "Lokasi: … | Hari
  1, jam …" terpotong wrap di kolom tengah; party HP bar menampilkan
  `━╺━━ --` tanpa angka.
- **Dampak:** kosmetik — teks terpotong/tumpang tindih di ukuran
  kecil, tidak ada kehilangan fungsi.
- **Status:** DEFERRED (Minor UX, note `ponytail:` di `app.py`) —
  dicatat untuk iterasi tata letak.

## Verifikasi BERSIH Fase C–E (bukan bug)

- **C1 Referensi & flag lintas arc (BFS 45 quest × 74 event × dialog):**
  0 deadlock — semua objective flag/quest_done/collect punya sumber
  set (event `once` men-set event_<id>_done otomatis di engine;
  ritual_ready di-set perintah `ritual` — false positive lama).
- **C2 Event once/trigger:** 0 event once mati, 0 trigger unreachable.
- **C3 Tier gating:** 2 catatan desain (mahkota_ashfall 2000 di
  quest304, cincin_roh_kenabian 1200 di quest303) — reward naratif,
  gold quest-nya sudah dinaikkan (BALANCE-1), bukan bug.
- **D1 Migrasi schema v1:** save v1 (ritual_ready field lama) dimuat
  tanpa error, flag ter-backfill. **D2 Korupsi parsial (7 kasus: skills
  party, bond_xp, buffs, shop_sold negatif, kills bukan int, inventory
  rusak, party_active tak dikenal):** 0 exception liar — SaveError rapi
  atau defensif + main 20 langkah tanpa crash.
- **E1 TUI battle 80×24:** battle penuh (menang/kalah/kabur), swap
  absen benar untuk tim tanpa rekan, resume mempertahankan state & log,
  HP KO pulih — 0 crash, 0 traceback, 0 markup Rich bocor.

## Catatan Jujur (proses, 2026-08-08)

- Lint repo saat ini **tidak hijau penuh** karena perubahan eksternal
  paralel yang belum selesai di `src/engine/combat.py` (2× E501),
  `src/systems/formation.py`, `src/core/game_loop.py` (termasuk
  `session.log_history` yang di-tambah ulang — dead code, tidak ada
  yang membaca; sudah pernah dihapus saat fix BUG-18). File stabil
  `combat.py` tidak disentuh (AGENTS §6). Commit fix putaran 3 hanya
  memuat file task sendiri (quest JSON + laporan); perubahan eksternal
  dibiarkan di working tree untuk proses paralel.
