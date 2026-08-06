# AGENTS.md — Chronicle of the Past (RPG Kultivasi)

**Status: dokumen kontrol perilaku wajib.** Setiap agent AI yang menyentuh
repo ini — Claude (chat/CLI/MCP), OpenCode dengan plugin **Superpowers**,
**Ponytail**, dan **Graphify**, atau tool lain yang membaca `AGENTS.md` —
**wajib mematuhi dokumen ini sebelum menulis satu baris kode atau data pun.**
ini bukan saran, ini kontrak perilaku. Pelanggaran terhadap aturan bertanda
**WAJIB**/**DILARANG**/**STOP** berarti pekerjaan belum boleh dianggap selesai.

Format dokumen ini sengaja disusun setara dua standar sekaligus:

* **CLAUDE.md** (konvensi resmi Claude Code, Anthropic): ringkas, berbasis
aksi, *command-first*, tidak menduplikasi konten yang sudah ada di tempat
lain, tidak menempel blok kode besar, dan setiap aturan ditulis sebagai
tindakan konkret — bukan imbauan samar seperti "tulis kode yang bersih".
* **AGENTS.md** (standar terbuka lintas-tool, kini dinaungi Agentic AI
Foundation di bawah Linux Foundation): markdown polos tanpa skema wajib,
dibaca otomatis oleh berbagai agent — termasuk **OpenCode, yang membaca
file ini secara native**.

---

## §1. Konteks Proyek & Sumber Kebenaran

|Aspek|Nilai|
|-|-|
|Game|RPG teks berbasis cerita, CLI terminal|
|Judul|Chronicle of the Past|
|Tema|Fantasi gelap + sistem kultivasi (inspirasi *Against the Gods*)|
|Nada|**Grimdark** — pengkhianatan nyata, konsekuensi tak bisa dibatalkan|
|Bahasa konten|**Bahasa Indonesia** (semua teks, dialog, menu, docstring)|
|Stack|Python 3.12+, **Rich + Textual**, stdlib|
|Konten|**Data-driven JSON** (quest, dialog, musuh, item, teknik, peta, faksi)|
|Kualitas|pytest · ruff (Google Python Style Guide, line ≤ 80)|
|Status|Fase 0 (MVP) selesai · **Fase 1 aktif** — lihat GDD §23|

**Sumber kebenaran DESAIN: `GDD.md`.** Sumber kebenaran PERILAKU AGENT:
dokumen ini. **Jangan menduplikasi isi GDD di sini** — rujuk nomor bagian
(`GDD §12.3`, dst.). Sebelum menulis kode/data untuk fitur apa pun, baca
bagian GDD yang relevan (lihat peta rujukan §5). Perubahan yang bertentangan
dengan GDD **wajib didiskusikan dengan pemilik proyek dulu** — jangan
menemukan ulang keputusan yang sudah dibuat.

### Urutan Otoritas Bila Terjadi Konflik

1. Instruksi eksplisit pengguna pada sesi berjalan.
2. `AGENTS.md` bersarang yang lebih dekat ke file yang sedang diedit (bila
ada — sesuai resolusi standar terbuka AGENTS.md).
3. Dokumen ini (`AGENTS.md`, root proyek).
4. `GDD.md` untuk keputusan desain/lore.
5. Google Python Style Guide untuk hal teknis yang tak diatur di atas.

Jika dua sumber bertentangan dan bukan kasus sederhana (mis. GDD belum
mencakup sebuah fitur yang sedang dikerjakan) — **STOP, laporkan konflik,
jangan menebak** (lihat §11).

### Perintah Wajib (jalankan, jangan asumsikan hasilnya)

```bash
pytest -q                                          # semua test harus lulus
ruff check src launcher.py tools tests             # lint
ruff format --check src launcher.py tools tests    # format check
python tools/validate.py                           # validator aset data (GDD §25.3)
graphify update .                                   # perbarui knowledge graph setelah ubah kode
graphify query "<pertanyaan>"                       # tanya graph sebelum grep manual
```

---

## §2. Hukum Superpowers — TDD & Disiplin Proses

Prinsip diverifikasi langsung dari **obra/superpowers** (Jesse Vincent,
MIT) — "agentic skills framework & software development methodology".

### 2.1 Hukum Besi: RED → GREEN → REFACTOR → COMMIT

* **TIDAK ADA KODE PRODUKSI TANPA TEST GAGAL LEBIH DULU.** Tidak ada
pengecualian untuk "tugas kecil" pada hukum ini — pengecualian hanya
berlaku untuk langkah brainstorming (§2.2), bukan untuk TDD.
* Urutan wajib: tulis test yang **gagal (RED)** → tulis kode minimal agar
lulus (**GREEN**) → **refactor** bila perlu (struktur, bukan perilaku) →
**commit**. Jika kode ditulis sebelum test, hapus dan mulai ulang dari test.
* Berlaku juga untuk **data JSON**: tulis/jalankan validator skema atau
test konten (referensi NPC/musuh/peta valid, requirement quest bisa
dipenuhi) sebelum menambah data massal.

### 2.2 Brainstorming & Desain Dulu

* Sebelum fitur baru / konten besar / perubahan arah: **ajukan pertanyaan
klarifikasi satu per satu**, eksplorasi 2–3 pendekatan, lalu susun
dokumen desain ringkas (di `docs/superpowers/specs/` bila dampaknya
luas) sebelum menulis kode.
* **Jangan sentuh kode/data sebelum desain disetujui pengguna.**
* Pengecualian: tugas kecil dan jelas (bug 1 baris, tambah 1 entri data) —
pakai akal sehat, bukan birokrasi.

### 2.3 Isolasi Workspace untuk Perubahan Besar

* Untuk perubahan besar, eksperimental, atau berisiko (menyentuh file
"stabil" §6, mengubah schema save, refactor lintas modul): buat branch
atau git worktree terisolasi dulu sebelum mulai implementasi, supaya
branch utama tetap bersih dan mudah dibatalkan bila gagal.
* Tidak wajib untuk perbaikan kecil/lokal.

### 2.4 Planning

* Setelah desain disetujui, pecah pekerjaan jadi **tugas kecil (2–5 menit
kerja)** dengan path file yang tepat dan langkah verifikasi eksplisit.
* Kerjakan berurutan; jangan lompat-lompat antar tugas yang belum selesai.

### 2.5 Bukti, Bukan Klaim

* **Verification-before-completion:** jangan menyatakan selesai sebelum
semua test lulus, lint bersih, dan data tervalidasi.
* Klaim apa pun tentang perilaku game harus dibuktikan (test otomatis,
smoke test, atau output nyata) — **"seharusnya jalan" bukan bukti.**

### 2.6 Systematic Debugging

* Dilarang *guess-and-check* atau menambal gejala tanpa memahami akar
masalah.
* Ikuti 4 fase: **Investigasi Akar Masalah → Analisis Pola → Hipotesis &
Uji → Implementasi.** Telusuri alur data (siapa memanggil siapa) —
gunakan Graphify (§4) untuk ini — sebelum mengubah apa pun.

### 2.7 Review Dua Tahap

* Setelah perubahan signifikan: review dulu **kepatuhan terhadap
spesifikasi/desain (GDD)**, baru kemudian **kualitas kode**.
* Temuan **Critical/Important** menghalangi penyelesaian tugas; temuan
Minor dicatat (mis. sebagai komentar `ponytail:`, lihat §3.3) tapi tidak
memblokir.

---

## §3. Hukum Ponytail — Tangga Minimalisme

Prinsip diverifikasi langsung dari **DietrichGebert/ponytail** (MIT) —
"makes your AI agent think like the laziest senior dev in the room."

### 3.1 Tangga Keputusan

Sebelum menulis kode/data, naiki tangga ini — **berhenti di anak tangga
pertama yang terpenuhi**. Tangga ini dijalankan **setelah** memahami
masalah dan menelusuri kode/data terkait (via Graphify, §4) — bukan
pengganti pemahaman, hanya pengganti solusi berlebihan:

1. Apakah ini benar-benar perlu ada? Kalau tidak → lewati (YAGNI).
2. Sudah ada di codebase ini? → **Pakai ulang, jangan tulis ulang.**
3. Bisa pakai stdlib Python? → Pakai itu.
4. Ada fitur native platform yang sudah menyediakan ini? → Pakai itu.
5. Ada dependency yang sudah terpasang (Rich/Textual) yang bisa menangani
ini? → Pakai itu.
6. Bisa selesai dalam satu baris? → Tulis satu baris.
7. Baru kalau semua di atas tidak berlaku: tulis **kode minimal yang
berfungsi**.

### 3.2 Lazy, Bukan Lalai

Yang **TIDAK BOLEH** dikorbankan demi ringkas:

* Validasi input di titik yang menerima data dari luar (save file, JSON).
* Penanganan error yang mencegah kehilangan data (save rusak, data invalid).
* Keamanan & integritas state.
* **Kompatibilitas terminal** — deteksi kapabilitas (mis. dukungan Unicode)
sebelum memakai karakter/formatting yang bisa gagal di lingkungan lain;
jangan hardcode asumsi tentang terminal pengguna.
* Apa pun yang secara eksplisit diminta pengguna.

### 3.3 Jejak Utang Teknis — Komentar `ponytail:`

Setiap kali mengambil jalan pintas yang disengaja (rung tangga di atas
rung 7, atau simplifikasi yang punya batas jelas), tandai di kode:

```python
# ponytail: pakai pencarian linear, upgrade ke dict kalau item > 50
```

Format: `# ponytail: <apa yang dilewati> → upgrade saat <kondisi>`. Ini
membuat utang teknis eksplisit dan bisa dilacak — bukan hilang jadi
"nanti" yang tidak pernah terjadi. Kumpulkan semua tanda ini sebelum
merilis sebuah Fase (lihat GDD §23) untuk ditinjau ulang.

### 3.4 Skala Proses sesuai Ukuran Tugas

|Ukuran tugas|Contoh|Proses|
|-|-|-|
|Kecil|bug 1 baris, 1 entri data, typo teks|TDD tetap wajib; brainstorming (§2.2) & worktree (§2.3) boleh dilewati|
|Sedang|1 quest/dialog/NPC baru, 1 sistem kecil|Alur penuh §10, tanpa perlu dokumen desain terpisah|
|Besar|sistem baru (mis. combat baru), ubah schema save, refactor lintas modul|Alur penuh §10 + dokumen desain (§2.2) + worktree (§2.3) + review dua tahap (§2.7)|

### 3.5 Gaya Respons

Utamakan kode/data dulu, penjelasan maksimal 3 baris untuk hal yang
sengaja disederhanakan (gunakan format `ponytail:` di §3.3, bukan esai).

---

## §4. Hukum Graphify — Navigasi Berbasis Graph

Prinsip diverifikasi langsung dari **Graphify-Labs/graphify** (Apache
2.0). Proyek ini **sudah punya knowledge graph aktif** di `graphify-out/`
(`graph.json`, `GRAPH_REPORT.md`, `graph.html`, snapshot harian) — bukan
hipotetis, sudah dipakai.

### 4.1 Kapan & Bagaimana

* Untuk pertanyaan seputar codebase: **`graphify query "<pertanyaan>"`
dulu**, sebelum grep mentah atau baca file satu-satu. Gunakan
`graphify path "<A>" "<B>"` untuk relasi antar modul, dan
`graphify explain "<konsep>"` untuk konsep fokus. Hasilnya subgraf
terarah — jauh lebih kecil dari hasil grep.
* Baca `graphify-out/GRAPH_REPORT.md` hanya untuk tinjauan arsitektur besar
(bukan untuk tugas kecil sehari-hari).
* Graph yang kotor setelah kode diubah adalah hal wajar — bukan alasan
melewati Graphify. Lewati hanya jika tugasnya memang tentang grafik yang
basi, atau pengguna menyuruh tidak memakainya.

### 4.2 EXTRACTED vs INFERRED

Setiap edge di graph ditandai **EXTRACTED** (eksplisit dari source, mis.
`import` langsung) atau **INFERRED** (disimpulkan Graphify). Perlakukan
klaim EXTRACTED sebagai fakta; perlakukan klaim INFERRED sebagai hipotesis
yang **masih perlu diverifikasi** dengan membaca kode sungguhan sebelum
dipakai sebagai dasar keputusan besar.

### 4.3 Update Graph

* **Setelah mengubah kode, jalankan `graphify update .`** — parsing
berjalan lokal (tree-sitter, deterministic, tanpa LLM, tidak ada data
yang keluar dari mesin) sehingga murah dan aman dijalankan sering.
* Untuk perubahan murni data JSON, update graph **tidak wajib**.

---

## §5. Peta Rujukan GDD — Jangan Duplikasi, Cukup Rujuk

|Kalau mengerjakan...|Baca GDD §|
|-|-|
|Sistem kultivasi / breakthrough / meridian|§4|
|Latar belakang / jalur kultivasi protagonis|§5|
|Combat / formula damage / elemen|§6, §17|
|Alkimia, pil, artefak, binatang roh, formasi|§7|
|Faksi & reputasi|§8|
|Peta & gating lokasi|§9|
|NPC baru / eksisting|§10|
|Musuh & bos|§11|
|Quest (engine & data)|§12.2–§12.4|
|Dialog NPC (engine & data)|§12.5, §10|
|Ending & epilog|§13, §21|
|Struktur folder / arsitektur|§14|
|Event engine (trigger/action)|§15|
|Status effect (buff/debuff/dot)|§16|
|Stat baru — **STOP dulu, baca §24.1 poin 13**|§17, §24.1|
|Perintah game baru|§18|
|Save schema / migrasi|§19|
|Rekrut/progresi anggota tim|§20|
|Target konten per arc|§22|
|Status Fase & file mana yang stabil|§23|
|Keputusan yang tidak boleh diubah diam-diam|§24.1|
|DataCache / profiler / asset validator|§25|

**Catatan gap yang ditemukan saat penyusunan dokumen ini:** GDD.md belum
punya bagian bernomor untuk **sistem toko/shop** meski pekerjaan itu
sedang berjalan. Sesuai §2.2, fitur besar yang belum terdokumentasi di GDD
wajib melalui brainstorming + ringkasan desain dulu — pertimbangkan
menambahkan bagian toko ke GDD.md (mis. sebagai §7a atau bagian baru)
begitu desainnya stabil, supaya dokumen ini tetap bisa merujuk ke sana
alih-alih menduplikasi aturannya di sini.

---

## §6. Keputusan Terkunci & File Stabil Fase 0

* **GDD §24.1** berisi 23 keputusan desain terkunci (nama dunia, formula,
siklus elemen, aturan flag, dll.). **DILARANG** mengubahnya secara diam-
diam — kontradiksi dengan §24.1 wajib dihentikan dan didiskusikan (§11).
* **File "tidak perlu diubah" (GDD §23):** `src/engine/combat.py`,
`src/engine/cultivation.py`, `src/models/player.py` — Fase 0 selesai
dan stabil. Sentuh hanya bila diminta eksplisit atau ada bug terbukti
(dengan test yang membuktikannya, §2.1).
* **File "stabil tapi bisa diperluas":** `src/engine/event.py` (tambah
`start_quest` action support), `src/core/game_loop.py` (tambah handler
`_cmd_talk()`), `src/core/save.py` (tambah migrasi bila schema berubah)
— perluas tanpa merestrukturisasi tanpa alasan kuat.
* **Data eksisting** (6 tier, 3 teknik, 4 musuh, 8 event, 3 peta, 3 quest,
  2 memori) — **DILARANG**
dihapus atau diganti; hanya ditambah.

---

## §7. Konvensi Kode Python & Docstring Google (WAJIB)

* Python 3.12+; stdlib dulu, baru Rich/Textual bila perlu (tangga §3.1).
* **Google Python Style Guide**: baris ≤ 80 karakter, import terurut
(stdlib → third-party → lokal), 2 baris kosong antar fungsi top-level,
double quotes.
* Struktur folder: lihat GDD §14.2 — jangan duplikasikan di sini.
* Validasi wajib sebelum commit: `ruff check`, `ruff format --check`,
`pytest -q` (lihat §1).
* **DILARANG** menambah dependency baru tanpa kebutuhan nyata (tangga §3.1
rung 5 berarti dependency yang *sudah* terpasang boleh dipakai bebas —
dependency *baru* tetap butuh justifikasi).

### Template Docstring Wajib

**Header section** (`Args`, `Returns`, `Raises`, `Yields`, `Attributes`,
`Example(s)`, `Note`) **WAJIB dalam Bahasa Inggris persis seperti ini** —
supaya dikenali tooling (ruff/pydocstyle convention Google) dan generator
dokumentasi standar. **Isi/prosa** (ringkasan, deskripsi tiap parameter)
**WAJIB Bahasa Indonesia**, konsisten dengan konten game.

```python
def hitung_damage_fisik(attack: int, defense: int, mult_elemen: float) -> int:
    """Hitung damage fisik akhir setelah defense dan multiplier elemen.

    Rumus mengikuti GDD §6.4.

    Args:
        attack: Nilai attack penyerang.
        defense: Nilai defense target.
        mult_elemen: Multiplier elemen (0.7 kalah, 1.0 netral, 1.5 unggul).

    Returns:
        Damage akhir, dibulatkan ke bawah, minimum 1.

    Raises:
        ValueError: Jika attack atau defense bernilai negatif.
    """


@dataclass(frozen=True)
class Quest:
    """Satu quest (main atau faksi). Skema lengkap di GDD §12.3.

    Attributes:
        id: ID unik quest, snake_case (mis. "quest101").
        title: Judul quest dalam Bahasa Indonesia.
        objectives: Daftar syarat yang harus dipenuhi untuk selesai.
    """
```

* Setiap fungsi/method publik (tidak diawali `_`) **wajib** punya
docstring. Fungsi privat kecil (<5 baris, logika trivial dari namanya)
boleh tanpa docstring.
* Docstring **bukan** tempat menaruh histori perubahan atau catatan
TODO — pakai komentar `ponytail:` (§3.3) atau pesan commit (§9).

---

## §8. Konvensi Data Game (JSON)

Semua konten hidup di `data/` sebagai JSON. Ikuti skema di GDD §14 dan
contoh file eksisting — **DILARANG membuat skema paralel.**

* Bahasa Indonesia untuk `name`, `description`, `lore`, `text` dialog, dan
semua pesan yang tampil ke pemain.
* ID dalam `snake_case` (`quest101`, `elder_mao`, `qi_slash`).
* Setiap file JSON valid (cek dengan parser); satu entitas per file
kecuali koleksi (events, memories, scenes).
* Referensi antar data (NPC di peta, item di loot, skill di musuh, quest
di event) **wajib valid** — jalankan `python tools/validate.py` sebelum
commit (§1, lihat GDD §25.3).
* Nada narasi **grimdark** (GDD §3.6): tidak ada kemenangan bersih, musuh
punya alasan yang konsisten secara internal, kematian scripted tidak
bisa di-undo. Baca GDD §3.6 sebelum menulis dialog/quest/event apa pun.
* Quest yang selesai **wajib** men-set flag `quest<id>_done` (otomatis via
engine) — **DILARANG** menambah flag paralel tanpa alasan kuat.
* Siklus elemen **Metal→Kayu→Tanah→Air→Api→Metal** harus konsisten di
semua teknik, musuh, dan efek (GDD §6.2).

---

## §9. Konvensi Git & Commit

* Satu commit = satu perubahan logis. Jangan campur perubahan data JSON
besar-besaran dengan refactor engine dalam commit yang sama.
* Pesan commit ringkas berformat `<lingkup>: <ringkasan>`, mis.
`quest: tambah validasi requirement kind=escort`. Lingkup umum:
`kultivasi`, `combat`, `quest`, `dialog`, `data`, `test`, `docs`.
* Tandai jelas di pesan commit bila menyentuh file "stabil Fase 0" (§6).
* Jangan commit `saves/`, `__pycache__/`, `.venv/`, `logs/`, atau isi
cache `graphify-out/cache/` — cek `.gitignore` proyek sebelum commit.

---

## §10. Alur Kerja Standar untuk Tugas Baru

1. **Pahami** — baca `GDD.md` bagian relevan (§5); `graphify query` untuk
navigasi codebase (§4); telusuri kode/data terkait.
2. **Desain** (bila dampak sedang/besar, §3.4) — pertanyaan klarifikasi →
2–3 pendekatan → dokumen desain ringkas → persetujuan pengguna.
3. **Isolasi** (bila tugas besar/berisiko, §2.3) — branch/worktree baru.
4. **Rencana** — pecah jadi tugas kecil dengan path file & langkah
verifikasi (§2.4).
5. **Tangga Ponytail** (§3.1) — cek apakah solusi sudah tersedia sebelum
menulis kode baru.
6. **TDD** — test gagal dulu (RED) → implementasi minimal (GREEN) →
refactor → commit (§2.1).
7. **Data** — tambah/edit JSON sesuai skema GDD §14; validasi referensi.
8. **Verifikasi** — `pytest -q` + `ruff check` + `ruff format --check` +
validator data/smoke test (§1).
9. **Graphify** — `graphify update .` setelah perubahan kode (§4.3).
10. **Review** — dua tahap: kepatuhan desain dulu, lalu kualitas kode
(§2.7).
11. **Lapor ringkas** — apa yang diubah, bukti verifikasi, hal yang
dilewati dan kapan perlu ditambahkan (rujuk komentar `ponytail:`).

---

## §11. Kondisi STOP & Larangan Eksplisit

### STOP — berhenti dan tanyakan ke pengguna, jangan menebak

* Perubahan bertentangan dengan **GDD §24.1** (keputusan terkunci).
* Perlu mengubah file "tidak perlu diubah" di §6 tanpa instruksi eksplisit.
* Schema save (`GDD §19.2`) perlu berubah — `schema_version` naik +
migrasi wajib ditulis, minta konfirmasi dulu.
* Requirement ambigu yang berdampak pada >1 sistem/file.
* Ditemukan kredensial, secret, atau permintaan mengakses hal di luar
scope proyek ini.
* Konflik terdeteksi antara `AGENTS.md` dan `GDD.md` (lihat contoh gap di
§5) — laporkan gapnya, jangan mengarang keputusan desain sendiri.
* Operasi destruktif di luar scope tugas (hapus massal, force-push, dst).

### DILARANG — tidak perlu bertanya, memang tidak boleh

* Menulis kode produksi sebelum test gagal (§2.1) — tanpa pengecualian.
* Mengklaim tugas selesai tanpa bukti otomatis (§2.5).
* *Guess-and-check* debugging (§2.6).
* Menghapus atau melemahkan test yang ada supaya suite terlihat hijau.
* Menambah stat atau mekanik baru di luar GDD §17/§24 tanpa diskusi.
* Hardcode gating cerita/peta di luar event engine (GDD §24.1 poin 18).
* Membuat flag penyelesaian quest paralel selain `quest<id>_done`.
* Mengubah nama/ID dunia yang sudah terkunci (GDD §24.1 poin 10–11).
* Menghapus atau mengganti data eksisting di `data/` (§6).

---

## §12. Definisi Selesai (Definition of Done)

Tugas **TIDAK BOLEH** dilaporkan selesai kecuali **semua** berikut
terpenuhi — ini adalah gerbang (gate), bukan saran:

* [ ] Perilaku sesuai GDD dan spesifikasi yang disetujui.
* [ ] Test baru ditulis dengan pola RED→GREEN→REFACTOR; `pytest -q` lulus
penuh.
* [ ] `ruff check` dan `ruff format --check` bersih.
* [ ] Docstring Google-style lengkap untuk semua fungsi/method publik baru
(§7).
* [ ] Data JSON valid; semua referensi antar data ter-resolve.
* [ ] Alur utama terverifikasi (unit test dan/atau smoke test permainan).
* [ ] Tidak ada kode mati, duplikasi, atau abstraksi tak terpakai.
* [ ] Semua komentar `ponytail:` yang ditambahkan punya kondisi upgrade
yang jelas (§3.3).
* [ ] `graphify update .` dijalankan bila ada perubahan kode (§4.3).
* [ ] Tidak melanggar satu pun butir §11.
* [ ] Ringkasan singkat diberikan: perubahan, bukti verifikasi, dan hal
yang sengaja dilewati.

---

## §13. Interoperabilitas Lintas Tool & Pemeliharaan Dokumen

* **OpenCode** membaca `AGENTS.md` ini secara native (termasuk oleh plugin
Superpowers, Ponytail, Graphify).
* **Claude Code** secara native hanya membaca `CLAUDE.md`, bukan
`AGENTS.md`. Root proyek ini punya `CLAUDE.md` berisi satu baris impor
(`@AGENTS.md`) — sesuai pola resmi yang direkomendasikan tim Claude
Code — supaya Claude Code ikut memuat dokumen ini secara utuh. **Jangan
hapus `CLAUDE.md`**; bila perlu aturan khusus Claude Code saja,
tambahkan di bawah baris impor tersebut, jangan duplikasi isi file ini.
* Bila suatu saat ada `AGENTS.md` di subfolder (mis. `src/systems/`), file
yang **paling dekat** ke lokasi yang diedit menang untuk hal spesifik
subfolder itu — dokumen ini tetap berlaku untuk hal lintas-proyek.
* **Rawat dokumen ini seperti kode**: setiap baris yang tidak lagi benar
lebih berbahaya daripada baris yang hilang, karena agent akan
mengikutinya dengan percaya diri. Jangan menduplikasi isi GDD.md di
sini — perbarui rujukan §-nya saja bila GDD berubah.

---

*Diperbarui: 6 Agustus 2026. Disusun dari riset langsung terhadap
obra/superpowers, DietrichGebert/ponytail, dan Graphify-Labs/graphify
(GitHub), konvensi resmi CLAUDE.md Claude Code (code.claude.com/docs/en/
memory), dan standar terbuka AGENTS.md (agents.md, Agentic AI Foundation).
Perbarui bagian ini bila prinsip proyek berubah — jangan biarkan dokumen
basi.*

