# Spesifikasi: Benchmark Performa (2026-08-04)

## Latar Belakang

Game CLI turn-based. Pengukuran awal (sesi 2026-08-04):

- Startup `GameContext()`: **20 ms**
- RAM: **13 MB**
- Data JSON: **216 KB / 40 file**, ascii: **28 KB / 4 file**
- Total kode ~3200 baris

Tidak ada bottleneck terukur. Rencana ini memformalkan cara membuktikan itu
secara permanen, dan **hanya mengoptimasi dimensi yang terukur lambat**.

## Tujuan

1. Membuat `tools/bench.py` (stdlib, tanpa dependency baru) sebagai alat ukur
   permanen untuk 7 dimensi performa.
2. Menetapkan ambang: dimensi dengan **median > 50 ms** wajib dioptimasi.
   Dimensi ≤ 50 ms dicatat, **tidak dioptimasi** (YAGNI).
3. Output akhir: laporan angka + (jika terpicu) perbaikan terarah yang tidak
   memutus 345 test yang ada.

## Dimensi yang Diukur

| # | Dimensi | Metode |
|---|---------|--------|
| 1 | `GameContext()` startup | konstruksi penuh (11 sumber JSON) |
| 2 | `save_game` | GameState utuh + state mid-combat → file temp |
| 3 | `load_game` + restore player | baca file + `_restore_player` |
| 4 | `run_turn` non-combat | perintah `look` |
| 5 | `run_turn` combat | satu fight penuh (`start_combat`→`player_action`→`enemy_turn`) |
| 6 | render | `combat_view.render(state)` |
| 7 | memori | `tracemalloc` peak saat `GameContext()` |

Tiap dimensi dijalankan 50×, dilaporkan **median** + **p95** (ms). Memori
dilaporkan dalam MB.

## Aturan Optimasi

- Median > 50 ms → diagnosis akar masalah, optimasi minimal (contoh kanidat:
  lazy-load dir di `GameContext`, cache baca ascii, hapus `indent=` di
  `save_game`), ulangi bench, `pytest` penuh tetap hijau.
- Median ≤ 50 ms → hanya dicatat di laporan.

## Yang Sengaja TIDAK Dilakukan

- **Tidak** menghapus/merubah animasi "Menghubungkan..." (0,5 s) — delay
  buatan yang menyembunyikan startup; fitur UX, bukan bottleneck.
- **Tidak** menambah guard waktu di pytest (flaky di CI).
- **Tidak** merombak `GameContext`, format save, atau engine tanpa bukti
  lambat.

## Output Script

- Tabel per dimensi: nama, median, p95, (memori utk #7).
- Penanda `OVER THRESHOLD` bila median > 50 ms.
- Exit code 0 (report-only; keputusan optimasi manual).

## Verifikasi

- `python tools/bench.py` menghasilkan laporan lengkap.
- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/ -q -p no:cacheprovider` → 345 hijau.
- `graphify update .`.

## Ekspektasi

Probabilitas tinggi: semua dimensi di bawah ambang → **nol perubahan produksi**,
`tools/bench.py` sendiri menjadi bukti permanennya.
