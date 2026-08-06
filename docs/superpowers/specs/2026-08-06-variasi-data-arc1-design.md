# Desain: Variasi Data Arc 1 + Fondasi Arc 2 (Branch `arc1-final`)

**Status:** Disetujui pengguna — siap eksekusi (AGENTS.md §2.2 ✅)
**Berdasarkan:** GDD §22 (Target Konten), §6 (Combat), §7 (Alkimia/Item), §9 (Peta),
§12 (Quest), §15 (Event), §16 (Status Effect), §17 (Stat), §23 (Fase 1)
**Branch:** `arc1-final` (pekerja). Hasil siap di-merge & diadaptasi agent lain.
**Tanggal:** 2026-08-06

---

## 1. Tujuan

Memperkaya data game dengan **variasi tinggi** yang mengikuti GDD & arsitektur
yang sudah ada, ter-integrasi penuh ke alur Arc 1 yang berjalan (+ fondasi
Arc 2), sehingga saat branch ini di-merge agent lain bisa langsung memakai
atau mengadaptasi datanya.

**Target:** data baru valid, hijau di `pytest`/`ruff`/`validate.py`, setiap
data terpakai (bukan mati), dan tidak menghapus/mengganti data eksisting.

---

## 2. Prinsip Variasi (wajib dipenuhi)

- **5 elemen siklus** (GDD §6.2: Metal→Kayu→Tanah→Air→Api→Metal) tercakup
  untuk musuh DAN teknik — tidak ada dominasi satu elemen.
- **Musuh:** mix `tags` (`beast`/`human`/`undead`/`spirit`), `behavior`
  (`aggressive`/`defensive`/`passive`), reward bervariasi.
- **Teknik:** mix `type` (`physical`/`technique`/`buff`), efek status (§16:
  burn/poison/weaken/strengthen/dll), jalur terdistribusi (sword/alchemy/
  formation/soul). Teknik diberikan **otomatis dari tier** (derive
  `_get_player_techniques`, GDD §4.1) — cukup punya `requires.tier`.
- **Item:** pill heal/qi/insight/meridian + beberapa siap-combat.
- **Nada grimdark** (GDD §3.6) untuk semua `name`/`description`/`text`.
- **Sebaran tier:** mayoritas Arc 1 (`qi_condensation`), beberapa fondasi
  Arc 2 (`foundation_establishment`) untuk variasi lintas tier.

---

## 3. Perluasan Engine

### 3.1 Loader item diperluas — `src/engine/items.py`

`load_items()` kini mengembalikan untuk tiap item:
`id`, `name`, `type`, `description`, `effect` (schema siap-combat).

Format `effect` item (siap-combat, efek non-combat yang dipakai sekarang):

```json
{
  "id": "pil_pemulih",
  "name": "Pil Pemulih",
  "type": "consumable",
  "description": "Memulihkan HP dalam jumlah kecil.",
  "effect": {"heal_hp": 20}
}
```

Efek yang dijalankan `use` (luar combat): `heal_hp`, `restore_qi`,
`add_insight`, `add_meridian`.
Efek combat-ready (`buff_hp`, `buff_attack`, dll) **diparse tapi tidak
dieksekusi** — ditandai komentar `ponytail:` (YAGNI sampai engine combat
diperluas; file `combat.py` stabil tak disentuh).

### 3.2 Command `use <item>` — `src/core/game_loop.py`

Luar combat saja (GDD §18.2). Konsumsi item dari
`state.inventory["items"]`, terapkan efek non-combat, tampilkan pesan.

Pola reuse `_cmd_rest` (assignment langsung `player.hp`/`player.qi`).
Tidak menyentuh `player.py` (stabil).

### 3.3 Rekam jejak sentuhan engine

| File | Perubahan | Stabil? |
|---|---|---|
| `src/engine/items.py` | perluas `load_items()` + parse effect | tidak |
| `src/core/game_loop.py` | + `_cmd_use` | tidak |
| `src/engine/event.py` | hanya bila perlu (reuse aksi ada) | tidak |
| `combat.py`/`cultivation.py`/`player.py` | **TIDAK disentuh** | stabil |

---

## 4. Volume Data Baru (total, lintas tier)

| Kategori | Jumlah baru | Sebaran tier | Integrasi |
|---|---|---|---|
| Musuh | +6 | 4× qi, 2× foundation | spawn map `enemies` + target quest |
| Teknik | +6 | 4× qi, 2× foundation; lintas 4 jalur | otomatis dari tier |
| Item/Pil | +10 | non-combat dipakai; schema siap-combat | `use`, grant event/quest |
| Quest faksi/sampingan | +5 | 4× Arc 1 + 1 foundation | di-start event `requires_flag` |
| NPC | +4 | Arc 1 | dialog + quest `talk` |
| Peta | +2 | foundation Arc 2 | unlock event + spawn musuh |

Setiap item baru di-grant minimal 1× (event atau quest reward) supaya tidak
mati. Setiap musuh baru dipakai minimal 1× (spawn peta atau target quest).

---

## 5. Integrasi & Alur

Pola integrasi memakai mekanisme yang sudah ada (reuse):

1. **Musuh** → daftar `enemies` di `data/maps/*` (`ashfall_forest`,
   `ruin_shrine`, peta baru). Spawn bersyarat via `requires_flag`.
2. **Teknik** → otomatis tersedia sesuai `requires.tier`; juga bisa jadi
   `skills` musuh.
3. **Item** → `grant_item` di event/quest reward; pemain `use`.
4. **Quest** → `start_quest` event, `requires_flag` gate, selesai set
   `quest<id>_done` (otomatis), reward item + reputasi + insight.
5. **NPC** → file `data/npc/*` + dialog; quest objective `talk`.
6. **Peta baru** → `unlock_map` event, `map_<id>_unlocked`.

**Aturan kunci:**
- Flag quest otomatis `quest<id>_done`; DILARANG flag paralel (§11).
- Tidak menghapus/mengganti data eksisting (§6).
- Tidak mengubah GDD §24.1 (nama dunia, formula, siklus elemen, dst).

---

## 6. Verifikasi (DoD AGENTS §12)

- `pytest -q` hijau penuh; test baru RED→GREEN per task.
- `ruff check` + `ruff format --check` bersih.
- `python tools/validate.py` → `OK` (validator cek map→enemy, grant_item→item,
  quest target, NPC location).
- Test per kategori + test integrasi alur (slice kuil, choice engine, use item).
- `graphify update .` setelah ubah engine.
- Docstring Google-style (header English, isi Indonesia) untuk fungsi publik baru.
- Komentar `ponytail:` untuk shortcut dengan kondisi upgrade jelas.

---

## 7. Urutan Kerja (dekomposisi, TDD per task)

1. **Engine `use` item** + perluas loader (RED→GREEN).
2. **Musuh + teknik** data (validator per batch).
3. **Item + quest + event** integrasi.
4. **NPC + peta baru** + unlock.
5. **Test E2E alur penuh** + graphify + full suite.
6. **Commit per task logis** (scope `data`/`combat`/`quest`/`items`/`engine`).

---

## 8. Sengaja Dilewati (YAGNI)

- Efek item di dalam combat (butuh perluas `combat.py` stabil) — schema
  disiapkan, eksekusi ditunda.
- Teknik dari quest/event spesifik (grant mekanisme) — teknik otomatis dari
  tier sudah cukup.
- Sistem alkimia racik (`refine`) penuh, artefak grow, binatang roh — Fase 2+.
- Save schema change — TIDAK ada (GDD §19 aman, §11).

---

*Dokumen ini disetujui pengguna. Berikutnya: writing-plans untuk rencana
implementasi detail.*
