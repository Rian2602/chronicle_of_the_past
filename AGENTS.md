# AGENTS.md — Chronicle of the Past (RPG Kultivasi)

Dokumen ini **wajib dibaca** oleh setiap agen AI yang ditugaskan mengerjakan proyek
game ini — baik untuk menulis **script (kode Python)** maupun **data game (JSON)**.
Tujuannya: perilaku yang konsisten, hasil yang bisa diverifikasi, dan konten yang
selaras dengan visi desain.

---

## 1. Konteks Proyek (baca dulu sebelum apa pun)

| Aspek | Nilai |
|-------|-------|
| Game | RPG teks berbasis cerita, CLI terminal |
| Judul | Chronicle of the Past |
| Tema | Fantasi gelap + sistem kultivasi (inspirasi *Against the Gods*) |
| Nada | **Gelap & serius** — pengkhianatan, konsekuensi berat, pilihan sulit |
| Bahasa konten | **Bahasa Indonesia** (semua teks, dialog, menu) |
| Stack | Python 3.12+, **Rich + Textual**, stdlib |
| Konten | **Data-driven JSON** (quest, dialog, musuh, item, teknik, peta, faksi) |
| Test | pytest · lint/format: ruff (Google Python Style Guide, line ≤ 80) |

**Sumber kebenaran desain: `GDD.md`** (di root proyek). Sebelum menulis kode
atau data apa pun untuk fitur baru, baca bagian GDD yang relevan. Jangan
menemukan ulang keputusan yang sudah dibuat di GDD. Perubahan desain yang
bertentangan dengan GDD wajib didiskusikan dengan pengguna terlebih dahulu.

---

## 2. Aturan Perilaku — Superpowers (TDD & Disiplin)

Prinsip dari plugin **Superpowers** (obra/superpowers):

### 2.1 Hukum Besi: TDD
- **TIDAK ADA KODE PRODUKSI TANPA TEST GAGAL TERLEBIH DAHULU.**
- Urutan wajib: tulis test yang **gagal (RED)** → tulis kode minimal agar
  lulus (**GREEN**) → refactor bila perlu.
- Jika kode ditulis sebelum test, hapus dan mulai ulang dari test.
- Berlaku juga untuk **data JSON**: tulis/validasi *schema check* atau test
  konten (mis. referensi NPC/musuh/peta valid, requirement quest bisa
  dipenuhi) sebelum menambah data massal.

### 2.2 Brainstorming & Desain Dulu
- Sebelum fitur baru / konten besar / perubahan arah: **tanyakan pertanyaan
  klarifikasi satu per satu**, eksplorasi 2–3 pendekatan, dan susun dokumen
  desain ringkas di `docs/superpowers/specs/` bila dampaknya luas.
- **Jangan sentuh kode/data sebelum desain disetujui pengguna.**
- Kecuali tugas kecil dan jelas (bug 1 baris, tambah 1 entri data) — gunakan
  akal sehat, bukan birokrasi.

### 2.3 Planning
- Setelah desain disetujui, pecah pekerjaan menjadi **tugas kecil
  (2–5 menit)** dengan path file yang tepat dan langkah verifikasi.
- Kerjakan berurutan; jangan lompat-lompat.

### 2.4 Bukti, Bukan Klaim
- **Verification-before-completion:** jangan menyatakan selesai sebelum
  semua test lulus, lint bersih, dan data tervalidasi.
- Klaim apa pun tentang perilaku game harus dibuktikan (test otomatis,
  smoke test, atau output nyata) — bukan "seharusnya jalan".

### 2.5 Systematic Debugging
- Dilarang "guess-and-check" atau menambal gejala.
- Ikuti 4 fase: **Investigasi Akar Masalah → Analisis Pola → Hipotesis &
  Uji → Implementasi**.
- Telusuri alur data (siapa memanggil siapa) sebelum mengubah apa pun.

### 2.6 Review Dua Tahap
- Setelah perubahan signifikan: review dulu **kepatuhan terhadap
  spesifikasi/desain**, lalu **kualitas kode**.
- Temuan **Critical/Important** menghalangi penyelesaian; temuan Minor
  dicatat.

---

## 3. Aturan Minimalisme — Ponytail (Tangga)

Sebelum menulis kode/data, periksa tangga ini dari atas — **berhenti di anak
tangga pertama yang terpenuhi**:

1. Apakah ini benar-benar perlu ada? Kalau tidak, lewati (YAGNI).
2. Sudah ada di codebase ini? **Pakai ulang, jangan tulis ulang.**
3. Bisa pakai stdlib Python? Pakai itu.
4. Ada fitur native yang sudah menyediakan ini? Pakai itu.
5. Ada dependency yang sudah terpasang (Rich/Textual) yang bisa menangani
   ini? Pakai itu.
6. Bisa selesai dalam satu baris? Tulis satu baris.
7. Baru kalau semua di atas tidak berlaku: tulis **kode minimal yang
   berfungsi**.

**Tangga ini dijalankan SETELAH memahami masalah dan menelusuri kode/data
yang relevan** — bukan pengganti pemahaman, hanya pengganti solusi berlebihan.

**Lazy, bukan lalai.** Yang TIDAK BOLEH dikorbankan demi ringkas:
- Validasi input di titik yang menerima data dari luar (save file, JSON).
- Penanganan error yang mencegah kehilangan data (save rusak, data invalid).
- Keamanan & integritas state.
- Apa pun yang secara eksplisit diminta pengguna.

**Gaya respons:** utamakan kode/data dulu, penjelasan maksimal 3 baris
(`[kode] → dilewati: X, tambah saat Y`) untuk hal yang sengaja disederhanakan.

---

## 4. Aturan Navigasi Codebase — Graphify

Prinsip dari plugin **Graphify** (Graphify-Labs/graphify). Proyek ini punya
knowledge graph di `graphify-out/` (bila sudah dibuat).

- Untuk pertanyaan seputar codebase: **coba `graphify query "<pertanyaan>"`
  dulu** bila `graphify-out/graph.json` ada. Gunakan `graphify path "<A>"
  "<B>"` untuk relasi antar modul dan `graphify explain "<konsep>"` untuk
  konsep fokus. Hasilnya subgraf terarah — jauh lebih kecil dari grep mentah.
- Jika `graphify-out/wiki/index.md` ada, gunakan untuk navigasi luas.
- Baca `graphify-out/GRAPH_REPORT.md` hanya untuk tinjauan arsitektur besar.
- File `graphify-out/` yang kotor setelah update adalah hal wajar — bukan
  alasan untuk melewati graphify. Lewati hanya jika tugasnya memang tentang
  grafik yang basi, atau pengguna menyuruh tidak memakainya.
- **Setelah mengubah kode, jalankan `graphify update .`** agar grafik tetap
  mutakhir (AST-only, tanpa biaya API). Untuk perubahan murni data JSON,
  update graph tidak wajib.

---

## 5. Konvensi Data Game (khusus proyek)

Semua konten game hidup di `data/` sebagai JSON. Ikuti skema yang sudah ada
di GDD §14 dan contoh file yang sudah ada — **jangan membuat skema paralel**.

### 5.1 Aturan Umum Data
- Bahasa Indonesia untuk `name`, `description`, `lore`, `text` dialog, dan
  pesan apa pun yang tampil ke pemain.
- ID dalam `snake_case`: `quest101`, `elder_mao`, `qi_slash`, `pill_insight`,
  `map_guild_city`, `killed_grave_warden_3`.
- Setiap file JSON: valid (cek dengan parser), satu entitas per file kecuali
  koleksi (events, memories, scenes).
- Referensi antar data (NPC di peta, item di loot, skill di musuh, quest di
  event) **wajib valid** — selalu jalankan validator data sebelum commit.

### 5.2 Skema Inti (ringkas — detail di GDD §14)
- **Quest:** `id`, `title`, `type`, `description`, `objectives`,
  `requirements` (kind: `talk`/`enemy`/`map`/`flag`/`collect`/`kill_count`/
  `escort`/`breakthrough`), `rewards`, `flags_on_complete`, `next`.
- **Teknik:** `id`, `name`, `path` (sword/alchemy/formation/spirit),
  `element` (metal/wood/water/fire/earth), `type`, `qi_cost`, `power`,
  `effects`, `requires.tier`.
- **Item/Pil:** `id`, `name`, `effect`, `recipe` (untuk pil).
- **Musuh:** `id`, `name`, `tier`, `element`, `behavior`, `stats`,
  `skills`, `tags` (termasuk `boss`), `requires_flag` (gate kemunculan).
- **Tingkatan kultivasi:** `id`, `name`, `order`, `insight_required`,
  `stat_bonus`, `unlocks` (urutan tetap: Pengumpul Qi → Pendirian Fondasi →
  Kristal Emas → Jiwa Terpisah → Pemutus Kehampaan → Penantang Surga).

### 5.3 Konsistensi Naratif
- Nada **gelap & serius**: dialog deskriptif, gaya novel ringan, 2–5 baris
  per beat; quest kunci boleh lebih panjang.
- Siklus elemen **Metal→Kayu→Tanah→Air→Api→Metal** harus konsisten di semua
  teknik, musuh, dan efek.
- Tim combat **maksimal 4 anggota** (protagonis + 3 rekan/binatang roh).
- Reputasi **5 faksi**: istana, orde suci, pemberontak, gilda, orde rahasia.
- Quest yang selesai wajib men-set flag `quest<id>_done` (otomatis engine);
  jangan menambah flag paralel tanpa alasan.

---

## 6. Konvensi Kode (Python)

- Python 3.12+; gunakan stdlib dulu, lalu Rich/Textual bila perlu (lihat
  tangga Ponytail §3).
- **Google Python Style Guide**: line ≤ 80 karakter, docstring format Google,
  import terurut (stdlib → third-party → lokal).
- Struktur: `src/core/` (game loop, state, save), `src/engine/` (combat,
  cultivation, quest, event, dialog), `src/systems/` (alkimia, artefak,
  binatang roh, formasi, faksi), `src/models/`, `src/ui/`.
- Jalur validasi: `ruff check src launcher.py tools tests` dan
  `ruff format --check ...`; test: `pytest -q`.
- Jangan perkenalkan dependency baru tanpa kebutuhan nyata (tangga Ponytail).

---

## 7. Alur Kerja Standar untuk Tugas Baru

1. **Pahami** — baca `GDD.md` bagian relevan; pakai `graphify` untuk
   menavigasi codebase; telusuri kode/data yang terkait.
2. **Desain** (bila dampak luas) — pertanyaan klarifikasi → dokumen desain →
   persetujuan pengguna.
3. **Rencana** — pecah jadi tugas kecil dengan path file & langkah verifikasi.
4. **TDD** — test gagal dulu (RED) → implementasi minimal (GREEN).
5. **Data** — tambah/edit JSON sesuai skema; validasi referensi.
6. **Verifikasi** — `pytest -q` + `ruff check` + validator data/smoke test.
7. **Graphify** — `graphify update .` setelah perubahan kode.
8. **Review** — dua tahap: kepatuhan desain, lalu kualitas kode.
9. **Lapor ringkas** — apa yang diubah, bukti verifikasi, hal yang dilewati
   dan kapan perlu ditambahkan.

---

## 8. Definisi Selesai (Definition of Done)

Sebuah tugas dinyatakan selesai hanya jika **semua** terpenuhi:

- [ ] Perilaku sesuai GDD dan spesifikasi yang disetujui.
- [ ] Test baru ditulis dengan pola RED→GREEN; `pytest -q` lulus penuh.
- [ ] `ruff check` dan `ruff format --check` bersih.
- [ ] Data JSON valid; semua referensi antar data ter-resolve.
- [ ] Alur utama terverifikasi (unit test dan/atau smoke test permainan).
- [ ] Tidak ada kode mati, duplikasi, atau abstraksi tak terpakai.
- [ ] `graphify update .` dijalankan (bila ada perubahan kode).
- [ ] Ringkasan singkat diberikan: perubahan, bukti, dan yang dilewati.

---

*Dokumen ini disusun dari prinsip plugin **Superpowers** (TDD & disiplin
desain), **Ponytail** (minimalisme tangga), dan **Graphify** (navigasi
knowledge graph). Perbarui dokumen ini bila aturan proyek berubah.*
