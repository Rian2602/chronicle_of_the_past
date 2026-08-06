# Perbaikan Multi-Ally Combat (UX & Test Hang)

**Konteks**:
Implementasi Party System (GDD §20) oleh Freebuff berhasil menambah Companion ke pertempuran (via event `lin_wei_recruit.json`). Namun, ini memicu dua masalah fatal akibat transisi dari sistem *Single-Ally* ke *Multi-Ally*:

1. **Test Infinite Loop**: Skrip pengujian otomatis E2E (`tests/test_game_loop.py::test_arc1_full_playthrough`) dirancang dengan asumsi pemain bertarung sendirian. Ketika giliran Lin Wei tiba, skrip memaksa perintah `technique:flame_strike` (berdasarkan pengecekan *Qi Protagonis*). Perintah ditolak karena tidak valid bagi Lin Wei, giliran tidak berganti, dan `while loop` berjalan selamanya hingga *timeout*.
2. **UX Ambigu**: Tidak ada penanda UI tentang "Giliran Siapa" yang aktif, sehingga baik AI *Tester* (Pi) maupun *Pemain Nyata* akan kebingungan memberi instruksi, berujung pada pengulangan kegagalan perintah.

---

## 🛠 Langkah Perbaikan

### Task 1: Hapus Infinite Loop pada `test_game_loop.py`
**File Target**: `tests/test_game_loop.py`
**Deskripsi Pekerjaan**:
- Ubah semua `while not frame.over:` (terutama di `test_arc1_full_playthrough` dan blok perulangan 3 musuh di bawahnya) agar mendeteksi giliran.
- Gunakan identifikasi *active ally* (`session.battle.current.id`).
- Jika `session.battle.current.id == "player"`: jalankan logika lama (`technique:flame_strike` jika qi cukup).
- Jika giliran companion (misal: `lin_wei`): jalankan perintah fallback yang aman, yaitu `attack` biasa atau teknik spesifiknya (`technique:qi_slash` jika QI cukup).

### Task 2: Tambahkan Properti `active_ally_name` pada `BattleFrame`
**File Target**: `src/core/game_loop.py`
**Deskripsi Pekerjaan**:
- Ubah *dataclass* `BattleFrame` dengan menambah *field* `active_ally_name: str | None = None`.
- Di dalam metode `battle_frame()`, set nilai properti tersebut:
  ```python
  active_ally_name = battle.current.name if not battle.over and self._is_player_turn() else None
  ```

### Task 3: Injeksi Penanda Giliran pada UI / Battle Log
**File Target**: `src/core/game_loop.py` (dan `src/ui/app.py` jika perlu)
**Deskripsi Pekerjaan**:
- Pastikan pemain manusia/AI tahu sedang mengendalikan siapa! 
- Modifikasi fungsi `battle_step()` dan/atau `battle_frame()`. Jika `active_ally_name` tidak None, tambahkan baris eksplisit di akhir `frame.log` (atau pastikan prompt UI menampilkannya):
  `"[Giliran {active_ally_name}] Gunakan attack / defend / technique / observe / escape."`
- (Opsional) Pada *start battle* (`_start_battle`), pastikan baris pertama prompt giliran juga merujuk ke karakter dengan *Inisiatif (Agility)* tertinggi yang mendapat giliran pertama.

---

*Disetujui oleh Senior Evaluator Antigravity untuk dieksekusi oleh Freebuff.*
