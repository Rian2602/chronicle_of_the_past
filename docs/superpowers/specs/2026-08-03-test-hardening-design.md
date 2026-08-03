# Chronicle of the Past — Test Hardening Design Spec

> **For agentic workers:** This is the validated design for additional tests.
> Tujuan: meningkatkan keyakinan "bebas dari bug" dengan regression +
> integration test di jalur berisiko yang belum teruji. Disetujui pengguna
> 2026-08-03 (pendekatan: hardening terarah, tanpa dependency baru).

## Prinsip

- Fokus pada gap berisiko yang sudah dipetakan, bukan mengejar coverage 100%.
- Tanpa dependency baru (tanpa pytest-cov/hypothesis).
- Tanpa perubahan kode produksi — **kecuali** test menemukan bug nyata; maka
  fix akar masalah (ini tujuan suite-nya).
- Mengikuti pola per-module yang sudah ada; satu file test baru
  (`test_launcher.py`).

## Grup Test

### G1 — Combat save/restore roundtrip (`tests/test_game_flow.py`)
- Save di tengah combat → `continue_game` → combat ter-restore:
  `enemy_id`, `enemy_hp`, `round_no`, `turn_order`, statuses jadi objek
  `StatusEffect`, `result` enum.
- Status (burn) roundtrip utuh: kind/duration/power.
- **Regression guard `_restore_combat`:** `combat_data.result` korup → tidak
  crash, `result=None`.
- `enemy_id` tak dikenal → combat tidak di-restore.

### G2 — xp_bonus / award_xp
- `tests/test_level_system.py`: unit `award_xp` (1.2→36, 1.0→30, 0→0).
- `tests/test_combat.py`: regression fix xp_bonus — Scholar menang combat
  reward 30 → +36, log "mendapat 36 XP".
- `tests/test_quests.py`: Scholar selesaikan quest reward 50 → +60.

### G3 — Game glue paths (`tests/test_game_flow.py`)
- Defeat → "Kamu gugur dalam pertarungan...", `_combat is None`.
- Escape sukses → "melarikan diri", `_combat is None`.
- Observe = free turn: tidak memicu enemy turn (log tak ada serangan musuh).
- Item di combat juga free turn.

### G4 — Input edge cases via `run_turn` (`tests/test_game_flow.py`)
- Perintah tak dikenal, input kosong, `use <unknown>`, `equip <unknown>`,
  `talk <unknown>`, `save` tanpa path, `select` tanpa dialog.

### G5 — launcher (`tests/test_launcher.py`, file baru)
- `main()` gagal load data (`ContentError`) → return 1.
- `_menu_selection`: navigasi `s` lalu Enter → pilihan benar.
- `_game_loop`: tangkap `SaveError` dari `run_turn` tanpa crash.
  (monkeypatch `builtins.input`/`builtins.print`; loop diakhiri "quit").

### G6 — unit kecil (`tests/test_world.py`)
- `weighted_choice`: semua bobot ≤ 0 → `None`; entri tunggal → selalu terpilih.

## Verifikasi

- pytest hijau setelah tiap grup:
  `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/ -q -p no:cacheprovider`
- `compileall` + `graphify update .` di akhir.
- Commit per grup ke master (tanpa branch baru), push via URL eksplisit.

## Out of scope

- pytest-cov / target coverage (ditolak pengguna).
- Refactor launcher/game untuk testability (monkeypatch cukup).
- Fuzzing / property-based testing.
