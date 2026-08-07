# Chronicle of the Past

RPG teks berbasis cerita dengan sistem kultivasi — fantasi gelap (CLI, Python
3.12+, Rich + Textual).

- **Sumber kebenaran desain:** `GDD.md`
- **Aturan pengembangan:** `AGENTS.md`

## Cara Menjalankan

```bash
python3 launcher.py
```

Perintah inti (daftar lengkap: GDD §18): `go`, `look`, `talk <npc>`,
`cultivate`, `breakthrough`, `rest`, `meditate`, `formation <nama>`,
`ritual`, `shop`/`buy`/`sell`, `refine <item>`, `party`/`swap`, `status`,
`inventory`, `quests`, `map`, `save`/`load`.

## Status (v1.0 — Rilis)

- **Arc 1–3 playable penuh:** quest101–108, quest201–208, quest301–308
  (konten asli) + 13 quest faksi, 10 peta, 22 NPC, 26 musuh (7 bos),
  36 teknik, 14 resep, 12 artefak, 10 echo memori.
- **Arc 4 lengkap:** quest401–408, peta `capital`/`ancient_vault`/`sky_seal`,
  bos Rasul Langit & Suara, NPC `the_voice`.
- **Ending dinamis (GDD §13, §21):** 7 keputusan kunci menambah `ending_points`
  (defy/seal/reconcile) → 3 ending besar + epilog status 5 faksi. Ritual
  persiapan (GDD §21.3) membuka jalan melawan Suara.
- **Sistem inti:** kultivasi 6 tier, combat 4 anggota + 5 elemen, alkimia,
  artefak tumbuh, binatang roh (rekrut/menetas/evolusi), formasi, toko,
  save v2 dengan migrasi.

## Verifikasi

```bash
pytest -q                                   # 470+ test
ruff check src launcher.py tools tests      # lint
python3 tools/validate.py                   # validator aset data
python3 tools/smoke_playthrough.py          # smoke playthrough Arc 1-4
```
