# Game Design Document — "Chronicle of the Past"

**Versi:** 1.0 (dokumen kunci pembangunan — locked)
**Status:** Disetujui sebagai sumber kebenaran desain. Perubahan desain yang bertentangan dengan dokumen ini wajib didiskusikan dengan pengguna terlebih dahulu (lihat AGENTS.md §1).
**Genre:** RPG teks berbasis cerita
**Platform:** CLI terminal (Python 3.12+, Rich + Textual)
**Bahasa:** Bahasa Indonesia
**Nada:** Gelap & serius
**Changelog:** v1.0 di §24.3.

---

## 1. Ringkasan Eksekutif

**Chronicle of the Past** adalah RPG berbasis teks (CLI) bertema **fantasi gelap dengan sistem kultivasi** — terinspirasi donghua *Against the Gods*. Pemain adalah pembudidaya (kultivator) yang menaiki tingkatan kekuatan, dari **Pengumpul Qi** hingga **Penantang Surga**, sambil mengungkap rahasia masa lalunya sendiri dan terjebak di tengah intrik **satu kerajaan luas** yang diguncang konflik antar faksi.

Keputusan kunci dari wawancara desain:

* **Tema:** Dunia fantasi gelap dengan kultivasi sebagai sistem kekuatan ("setengah-setengah" — bukan xianxia murni, bukan fantasi klasik murni).
* **Cerita:** Tidak ada penjahat tunggal. Konflik lahir dari bentrokan **5+ faksi** (kerajaan, orde suci, pemberontak, gilda, orde rahasia kuno) di belakang layar entitas kuno yang mulai bangkit.
* **Progresi:** **Tingkatan kultivasi berjenjang** (breakthrough) sebagai inti leveling.
* **Combat:** Turn-based + **5 elemen** (Metal/Kayu/Air/Api/Tanah) + **tim 4 anggota**.
* **Ending:** **Dinamis** — variasi hasil terakumulasi dari pilihan sepanjang permainan.
* **Teknologi:** Python 3.12+, UI terminal mewah dengan **Rich + Textual**, konten **data-driven JSON**.
* **Scope:** Multi-arc, target **15+ jam** playthrough lengkap (target konten per arc: §22).

---

## 2. Pilar Desain (hasil wawancara)

|#|Aspek|Keputusan|
|-|-|-|
|1|Genre|RPG teks berbasis cerita|
|2|Platform|CLI terminal|
|3|Tema|Fantasi gelap + sistem kultivasi (inspirasi *Against the Gods*)|
|4|Nada|Gelap & serius|
|5|Judul|Chronicle of the Past|
|6|Bahasa|Bahasa Indonesia|
|7|Scope|Besar: multi-arc, target 15+ jam|
|8|Dunia|Satu kerajaan luas|
|9|Protagonis|Kustomisasi latar belakang; rahasia diungkap bertahap|
|10|Antagonis|Tanpa penjahat tunggal: entitas kuno, kultus fanatik, penguasa korup, antagonis abu-abu, konflik faksi|
|11|Faksi|5+ aktif: kerajaan & bangsawan, orde suci, pemberontak, gilda-gilda, orde rahasia kuno|
|12|Progresi|Tingkatan kultivasi berjenjang (breakthrough)|
|13|Jalur|Mulai 1 jalur, bisa diperluas ke jalur lain|
|14|Combat|Turn-based + 5 elemen + tim 4 anggota|
|15|Elemen khas|Alkimia & pil, teknik rahasia, artefak/senjata roh, binatang roh, formasi/array, meridian & qi|
|16|Ending|Dinamis — variasi hasil tergantung pilihan sepanjang permainan|
|17|Teknologi|Python 3.12+ + Rich + Textual|
|18|Konten|Data-driven JSON|
|19|Prioritas MVP|Sistem kultivasi + combat dulu|

---

## 3. Premis Besar & Latar

### 3.1 Premis

Kerajaan **Ashenfeld** (keputusan final — lihat §24.1) adalah kerajaan luas yang dikuasai satu dinasti. Di bawah permukaannya, **sistem kultivasi** adalah nyata: mereka yang berbakat menyerap energi langit-bumi untuk memperkuat tubuh, jiwa, dan umur mereka. Namun kekuatan ini langka, diatur ketat, dan menjadi akar ketidakadilan — para pembudidaya kuat menindas rakyat biasa tanpa batas.

Kamu, sang protagonis, bangkit dari latar yang kamu pilih sendiri (lihat §5). Apa pun latarmu, satu hal menyatukan: **kamu menyimpan rahasia masa lalu yang bahkan kamu sendiri belum pahami** — dan dunia mulai mengingatnya.

Selama permainan kamu akan:

1. Meniti jalan kultivasi dari nol, melakukan breakthrough demi breakthrough.
2. Terjebak di tengah intrik 5+ faksi yang memperebutkan kekuasaan dan rahasia kuno.
3. Mengungkap bertahap: siapa kamu sebenarnya, dan apa yang terjadi pada masa lalumu.
4. Pada klimaks, memilih posisimu terhadap **entitas kuno** yang mulai bangkit — dan terhadap kerajaan yang membusuk.

### 3.2 Latar Dunia

* **Satu kerajaan luas** — Ashenfeld: ibukota megah, wilayah perbatasan, sekte-sekte, kota-kota gilda.
* **Desa awal:** **Desa Emberfall** (`village_emberfall`) — tempat protagonis memulai; dibedakan tegas dari nama kerajaan agar tidak membingungkan.
* **Kultivasi** adalah kekuatan nyata: tingkatan, qi, meridian, pil, artefak.
* **Langit** dalam cerita ini bukan sekadar langit — ada *sesuatu* di baliknya yang telah lama diam (entitas kuno, §3.4).
* **Periode waktu:** berlangsung sekitar **2–3 bulan** dalam waktu game, dibagi menjadi 4 arc.

### 3.3 Kebenaran yang Terungkap Berjenjang

|Arc|Fakta yang terungkap|
|-|-|
|1|Protagonis memiliki bakat aneh yang ditakuti orang; dunia menutup-nutupi sesuatu tentangnya.|
|2|Ada orde rahasia kuno yang menunggu kemunculan seseorang; faksi-faksi mulai memperebutkan protagonis.|
|3|Entitas kuno di balik langit mulai bangkit; beberapa faksi adalah pionnya.|
|4|Rahasia penuh masa lalu protagonis terungkap; keputusan akhir menentukan nasib dunia.|

### 3.4 Antagonis (tanpa penjahat tunggal)

|Ancaman|Peran|
|-|-|
|**Entitas kuno**|Kekuatan purba di balik langit; bangkit bertahap sejak Arc 2, aktif penuh di Arc 3–4.|
|**Kultus fanatik**|Orde suci yang "memurnikan" ketidakmurnian; dalang pembantaian di masa lalu protagonis.|
|**Penguasa korup**|Kaisar/bangsawan yang memakai kultivasi untuk menindas; musuh struktural.|
|**Antagonis abu-abu**|Tokoh-tokoh dengan alasan moral sendiri — bisa sekutu atau lawan tergantung pilihan.|
|**Konflik antar faksi**|Tidak ada "bos final" tunggal; setiap arc punya bos yang mewakili kepentingan faksi tertentu.|

---

## 4. Sistem Kultivasi (inti gameplay)

### 4.1 Tingkatan Kultivasi

Kemajuan pemain diukur dalam **tingkatan kultivasi** — bukan level angka biasa. Setiap tingkatan adalah lompatan besar (power spike) dan membuka teknik baru.

|#|Tingkatan|Insight kumulatif|Perkiraan Jam|Catatan|
|-|-|-|-|-|
|1|**Pengumpul Qi**|0 → 100|Arc 1|Awal; tubuh diresapi qi pertama kali|
|2|**Pendirian Fondasi**|300|Arc 1–2|Fondasi meridian stabil; jalur kultivasi aktif|
|3|**Kristal Emas**|800|Arc 2–3|Inti energi terbentuk; kekuatan mulai diperhitungkan faksi|
|4|**Jiwa Terpisah**|2000|Arc 3|Jiwa bisa "berpisah"; binatang roh & teknik jiwa terbuka|
|5|**Pemutus Kehampaan**|5000|Arc 4|Menembus batas; mulai "terlihat" oleh entitas kuno|
|6|**Penantang Surga**|12000|Arc 4 (akhir)|Puncak; posisi final melawan langit|

**Kurva insight:** tiap tingkatan kira-kira **2,5×** dari sebelumnya (100 → 300 → 800 → 2000 → 5000 → 12000). Angka final hidup di `data/cultivation/` — tabel di atas adalah referensi desain.

**Breakthrough** = momen besar, bukan sekadar naik XP:

* **Syarat:** akumulasi pemahaman (insight) mencapai ambang tingkatan berikutnya, bahan/ramuan pendukung, dan sering kali **momen cerita** (gate quest/flag).
* **Risiko (keputusan final):** bisa **gagal** → cedera **sementara** (−25% stat selama 2 hari game) dan 30% peluang memicu pertarungan **inner demon**. **Tidak ada penalti permanen** (lihat §24.1). Sukses dasar 55%, +5% per poin stat pendukung jalur, +10–20% dari pil breakthrough, cap 90%.
* **Hadiah:** stat besar, teknik baru, penampilan/hud berubah, dan event cerita.

### 4.2 Meridian & Qi

* **Qi** adalah sumber daya utama pertarungan (pengganti "MP" sederhana).
* **Meridian** menentukan kapasitas qi dan laju regenerasi; bisa dibuka/diperkuat lewat kultivasi dan pil.
* Serangan kuat (teknik tingkat tinggi) menguras qi besar; **meditasi** di lokasi aman memulihkan qi.
* Formula kapasitas & regenerasi di §17.

### 4.3 Pemahaman (XP)

* Nama internal: `insight` (pemahaman) — diperoleh dari pertarungan, quest, membaca gulungan, meditasi.
* Kurva: meningkat per tingkatan; breakthrough membutuhkan insight + syarat khusus.

---

## 5. Protagonis & Jalur Kultivasi

### 5.1 Kustomisasi Latar Belakang

Saat memulai, pemain memilih latar belakang yang memengaruhi stat awal, dialog, dan quest awal:

|Latar|Efek|
|-|-|
|**Anak rakyat biasa**|+Pemahaman awal, reputasi rakyat tinggi, mulai tanpa koneksi|
|**Bekas murid sekte**|Mulai dengan 1 teknik, reputasi sekte tinggi, tapi "dicap"|
|**Orang buangan bangsawan**|+Emas awal, reputasi istana rendah, quest khusus balas dendam|
|**Pencari harta**|+Item/alat alkimia awal, gilda menyukaimu|
|**Yatim misterius**|Stat seimbang; kunci rahasia masa lalu (§5.3) lebih cepat terbuka|

### 5.2 Jalur Kultivasi (kelas)

Pemain memilih **satu jalur utama** saat Pendirian Fondasi, dan **bisa mempelajari jalur lain** seiring cerita (dengan biaya lebih mahal — "expandable"):

|Jalur|Gaya|Stat inti (lihat §17)|Contoh teknik|
|-|-|-|-|
|**Jalan Pedang**|Fisik, senjata, tempo|Attack, Agility|Tebasan Qi, Iblis Pedang, Formasi Pedang|
|**Jalan Alkimia**|Dukungan, racik pil, kontrol|Intelligence, Vitality|Pil Pembakar, Racun Meridian, Tangan Emas|
|**Jalan Formasi**|Strategi, area, buff|Intelligence, Defense|Jaring Formasi, Segel Penjara, Array Langit|
|**Jalan Jiwa**|Sihir jiwa, binatang roh, kontrol|Intelligence, Spirit|Seruan Jiwa, Ikatan Roh, Pandangan Jiwa|

**Aturan jalur:**

* Jalur utama gratis penuh; jalur kedua/ketiga terbuka lewat quest atau biaya besar.
* Setiap jalur punya 1–2 teknik awal + 2–4 teknik lanjutan per tingkatan.

### 5.3 Rahasia Masa Lalu (diungkap bertahap)

* Protagonis punya **bakat aneh** yang membuat dunia takut/menutupinya.
* Rahasia terungkap lewat *echo memori* — pecahan ingatan yang terbuka di momen-momen tertentu (diberikan lewat event engine, §15).
* Tidak ada "kekuatan instan gratis": rahasia memberi akses teknik/quest unik, bukan cheat.

---

## 6. Sistem Combat

### 6.1 Dasar

* **Turn-based klasik** — giliran bergantian antar anggota tim dan musuh dalam **urutan tetap**.
* **Urutan giliran (order):** dihitung **sekali saat pertarungan dimulai** dari `agility` (tertinggi duluan), lalu tetap untuk seluruh pertarungan — bukan inisiatif dinamis per giliran (keputusan final, §24.1).
* **Tim 4 anggota:** protagonis + maksimal 3 rekan/binatang roh aktif (aturan rekrut: §20).
* **Defend / Escape / Observe / Item** — aksi standar (daftar perintah lengkap: §18).
* Status effect (racun, stun, dll.): §16.

### 6.2 Lima Elemen (siklus)

```
Metal → Kayu → Tanah → Air → Api → Metal
```

|Elemen|Menaklukkan|Dikalahkan oleh|
|-|-|-|
|Metal|Kayu|Api|
|Kayu|Tanah|Metal|
|Tanah|Air|Kayu|
|Air|Api|Tanah|
|Api|Metal|Air|

* Setiap teknik/musuh punya elemen.
* **Keunggulan elemen:** damage ×1.5. **Kalah elemen:** damage ×0.7.
* **Resonansi tim:** komposisi elemen tim memberi bonus sinergi (mis. 3 elemen berbeda → +10% qi regen).

### 6.3 Qi & Resource

* Setiap anggota punya **qi** sendiri (formula §17).
* Teknik menguras qi; regenerasi per giliran (dari meridian).
* **Formasi aktif** (bila dipasang) mengubah aturan resource/buff tim.

### 6.4 Formula Dasar (angka final — lihat §17 untuk definisi stat)

* **Damage fisik:** `max(1, attack − defense/2) × element_mult × rand(0.9–1.1)`.
* **Damage teknik:** `max(1, power + stat_inti × 0.5 − resist_lawan) × element_mult × rand(0.9–1.1)`.
* **Multiplier elemen:** 1.5 jika unggul, 0.7 jika kalah.
* **Crit:** `5% + agility × 0.1%` (cap 25%), damage crit ×1.8.
* **Miss:** `max(5%, 20% − agility × 0.1%)` — minimun 5%.
* **Dodge:** `5% + agility × 0.1%` (cap 30%).

---

## 7. Elemen Khas Cultivation

|Sistem|Deskripsi|
|-|-|
|**Alkimia & Pil**|Racik bahan → pil: pil kultivasi (tambah insight), pil penyembuh, pil buff, pil breakthrough. Resep ditemukan/dibeli/dipelajari. Kualitas pil (rendah→surgawi) memengaruhi efek.|
|**Teknik Rahasia**|Skill langka terikat lore; beberapa hanya bisa didapat dari quest faksi, ruang rahasia, atau peti kuno. Bisa di-*equip* (jumlah slot terbatas).|
|**Artefak & Senjata Roh**|Item bertingkat (Mortil → Roh → Surgawi) yang **tumbuh bersama pemilik** — naik level artefak, bukan diganti. Senjata roh bisa punya "kesadaran" (dialog kecil).|
|**Binatang Roh**|Rekan spiritual; **rekrut (kalahkan → ikat) ATAU menetas dari telur** — dua-duanya aktif (keputusan final, §24.1). Ikut bertarung, punya elemen & teknik sendiri, bisa berevolusi sekali. Detail: §20.|
|**Formasi / Array**|Ritual persiapan: pasang formasi sebelum pertempuran penting → buff area/efek besar. Beberapa formasi dipakai di luar combat (pertahanan, penyembuhan).|
|**Meridian & Qi**|Sistem resource utama (§4.2, formula §17).|

---

## 8. Faksi & Reputasi

|Faksi|ID internal|Tokoh kunci|Tujuan|Sikap ke protagonis|
|-|-|-|-|-|
|**Istana Kerajaan**|`court`|Kaisar (boneka?), Kanselir, Jenderal|Mengendalikan kultivasi untuk kekuasaan|Rebut/diadili|
|**Orde Suci (kultus)**|`holy_order`|Inkuisitor Agung, Para Uskup|"Memurnikan" dunia dari qi kotor|Musnahkan / rekrut|
|**Pemberontak**|`rebels`|Pemimpin gerakan, mantan bangsawan|Menumbangkan tirani kultivasi|Sekutu potensial|
|**Gilda-gilda**|`guilds`|Gilda Dagang, Gilda Pembunuh, Gilda Petualang|Untung dari konflik|Klien / target|
|**Orde Rahasia Kuno**|`ancient_order`|Penjaga rahasia, sisa orde lama|Mencegah entitas kuno bangkit|Kunci utama|

**Reputasi:** hadiah quest & pilihan dialog menaikkan/turunkan reputasi per faksi (`change_reputation` di event, §15). Ambang tertentu membuka quest eksklusif, sekutu, diskon, dan **jalur ending** (§21). Kisaran: −100 s/d +100; ambang utama di ±30 dan ±70.

---

## 9. Peta & Dunia (satu kerajaan luas)

|ID|Wilayah|Arc|Keterangan|
|-|-|-|-|
|`village_emberfall`|Desa Emberfall|1|Desa awal; tempat protagonis memulai|
|`ashfall_forest`|Hutan Perbatasan|1|Area latihan & musuh liar|
|`ruin_shrine`|Kuil Reruntuhan|1|Rahasia pertama; bos Arc 1|
|`sect_azure`|Sekte Awan Biru|2|Sekte utama; akademi kultivasi|
|`guild_city`|Kota Gilda|2|Kota dagang; gilda-gilda|
|`holy_cathedral`|Katedral Suci|3|Markas Orde Suci (berbahaya)|
|`rebel_hideout`|Markas Pemberontak|3|Kamp rahasia|
|`capital`|Ibukota Ashenfeld|3–4|Istana, politik, arena|
|`ancient_vault`|Ruang Rahasia Kuno|4|Orde rahasia; lore entitas kuno|
|`sky_seal`|Segel Langit|4|Lokasi final; climactic battle|

**Gating peta:** flag `map_<id>_unlocked` diset lewat event engine (`unlock_map`, §15) — mencegah lompat konten. Peta awal (`village_emberfall`) terbuka sejak awal.

---

## 10. NPC & Karakter (final default)

|ID|Nama|Lokasi|Peran|
|-|-|-|-|
|`elder_mao`|Sesepuh Mao|village_emberfall|Guru pertama; membimbing kultivasi awal|
|`lin_wei`|Lin Wei|village_emberfall|Rekan masa kecil; kunci latar protagonis|
|`fang_yue`|Fang Yue|sect_azure|Senior sekte; mentor Jalan Pedang|
|`alchemist_xiu`|Xiu Sang Alkemi|sect_azure / guild_city|Guru alkimia; toko resep|
|`blacksmith_tie`|Tie Pandai Senjata|guild_city|Artefak & senjata roh|
|`kestrel`|Kestrel|guild_city|Pemimpin Gilda Pembunuh (abu-abu)|
|`inquisitor_vega`|Vega|holy_cathedral|Inkuisitor; antagonis abu-abu yang bisa jadi sekutu|
|`sera_ember`|Sera Ember|rebel_hideout|Pemimpin pemberontak|
|`warden_kai`|Penjaga Kai|ancient_vault|Sisa Orde Rahasia; jembatan ke lore inti|
|`the_voice`|Suara|sky_seal|Entitas kuno (antagonis puncak)|

> Nama di atas adalah **default final** (keputusan §24.1) — dapat diganti hanya bila ada alasan desain yang kuat dan disetujui pengguna.

---

## 11. Musuh & Bos (final default per arc)

Tingkatan kolom "akhir arc" mengikuti §4.1 — **kurva bos diselaraskan dengan tingkatan pemain** (perbaikan I2): bos utama setiap arc berada satu tingkatan di bawah puncak pemain, kecuali bos final.

|Arc|Tingkatan pemain (akhir arc)|Musuh khas|Bos (tingkatan)|
|-|-|-|-|
|1|Pengumpul Qi|Serigala Qi, Bandit perbatasan, Zombi Kuil|**Penjaga Makam** (Pengumpul Qi puncak)|
|2|Kristal Emas|Murid sekte saingan, Binatang roh liar, Agen Orde Suci|**Kepala Sekte Bayangan** (Kristal Emas awal)|
|3|Jiwa Terpisah|Tentara salib Orde Suci, Pembunuh gilda, Iblis formasi|**Inkuisitor Agung** (Kristal Emas puncak)|
|4|Penantang Surga|Manifestasi entitas, Pion langit, Pemberontak fanatik|**Rasul Langit** (Pemutus Kehampaan puncak) → **Suara** (Penantang Surga — di luar ukuran mortal)|

**Aturan bos:** tag `boss`, tak bisa kabur, hadiah istimewa, dan sering memicu event cerita (bukan sekadar naik XP). Setiap bos punya `requires_flag` yang membuka kemunculannya (gate quest/arc — §15). **Bos final (Suara)** berada sedikit di atas tingkatan mortal: pemain harus menutup kesenjangan dengan ritual, formasi, artefak, dan sekutu (lihat §21 Penentu Ending).

---

## 12. Struktur Arc & Quest

### 12.1 Ringkasan Arc

|Arc|Judul|Inti|Bos|
|-|-|-|-|
|1|**Gerbang Qi**|Bangun di desa; mulai kultivasi; kuil reruntuhan; rahasia pertama|Penjaga Makam|
|2|**Sekte & Intrik**|Masuk sekte; gilda; orde rahasia mulai mencari "yang ditunggu"|Kepala Sekte Bayangan|
|3|**Antara Dua Langit**|Orde Suci & pemberontak; entitas kuno bangkit; pilih posisi faksi|Inkuisitor Agung|
|4|**Menentang Langit**|Ruang rahasia kuno; rahasia penuh terungkap; keputusan final|Rasul Langit / Suara|

### 12.2 Quest

* **32 quest utama** (8 per arc — target final, §22) mengalir berkelanjutan per arc, ditambah **10 quest faksi eksklusif**.
* **Kind requirement** (engine quest): `talk`, `enemy`, `map`, `flag`, `collect`, `kill_count`, `escort`, `breakthrough` (baru — butuh pemain mencapai tingkatan tertentu).
* **Quest percabangan:** beberapa quest punya 2–3 penyelesaian yang memengaruhi reputasi dan flag ending (§21).
* **Flag kelulusan:** quest yang selesai **otomatis** men-set flag `quest<id>_done` oleh engine (keputusan final §24.1) — event memakai flag ini sebagai trigger (§15).

### 12.3 Format Quest (data-driven)

```json
{
  "id": "quest101",
  "title": "Qi Pertama",
  "type": "main",
  "description": "Sesepuh Mao mengajarkanmu menghirup qi langit-bumi.",
  "objectives": [
    {"kind": "talk", "target": "elder_mao"},
    {"kind": "breakthrough", "target": "qi_condensation"}
  ],
  "rewards": {"insight": 50, "gold": 20, "reputation": {"rebels": 5}},
  "flags_on_complete": ["quest101_done", "path_unlocked_sword"],
  "next": "quest102",
  "category": "main",
  "requires_flag": null
}
```

> **Catatan:** `objectives` adalah array **objek** (mekanik) — label naratif untuk
> pemain dihasilkan engine dari `objective_label`, bukan disimpan sebagai
> string. `requires_flag` opsional: quest menunggu flag terbuka bila diisi.

### 12.4 Quest Engine (interface)

* `QuestObjective`: `kind` + `target` + `count` (default 1).
* Kind requirement (8): `talk`, `enemy`, `map`, `flag`, `collect`,
  `kill_count`, `escort`, `breakthrough`.
* Fungsi engine: `load_quests` (muat dari `data/quests/`), `active_quests`
  (started & belum done & `requires_flag` terpenuhi), `check_objective`
  (satu objektif terpenuhi?), `advance_quest` (maju ke objektif berikutnya),
  `complete_quest` (selesai + set flag `quest<id>_done` + reward),
  `objective_label` (teks pemain dari objek mekanik).

> **Catatan naming flag:** wajib `quest<id>_done` (mis. `quest101_done`) — **bukan** `q101_done`. Berlaku konsisten di quest, event, dan musuh (`requires_flag`).

---

## 13. Ending Dinamis

* **Tidak ada ending tunggal.** Jejak keputusan (flag + reputasi + posisi faksi) terakumulasi sepanjang 4 arc.
* **3 ending besar** + **banyak variasi kecil**:

  * **Menentang Langit** — melawan entitas kuno dan menulis ulang aturan dunia.
  * **Menyegel Diri** — menarik diri dari konflik; dunia memilih jalannya sendiri (banyak variasi: siapa menang, siapa kalah).
  * **Rekonsiliasi** — jalan abu-abu: berdiri di antara faksi dan entitas, mencegah kehancuran total.
* Setiap ending punya epilog singkat yang menyebut faksi yang selamat/berkuasa berdasarkan reputasi pemain.
* **Penentu mekanik ending (skor, ambang, tie-break):** §21.

---

## 14. Teknologi & Arsitektur

### 14.1 Stack

* **Python 3.12+**
* **Rich** — warna, tabel, panel, progress bar untuk tampilan utama.
* **Textual** — TUI interaktif untuk menu/dialog pilihan (dua-duanya dipakai).
* **pytest** — testing (dev dependency).
* **ruff** — lint & format (Google Python Style Guide).

### 14.2 Struktur Proyek (final)

```
chronicle_of_the_past/
├── GDD.md                  # dokumen ini (sumber kebenaran desain)
├── AGENTS.md               # aturan perilaku agen AI
├── launcher.py             # entry point
├── pyproject.toml
├── src/
│   ├── core/               # game loop, state, save (§19), input
│   ├── engine/             # combat, cultivation, quest, event (§15), dialog
│   ├── systems/            # alkimia, artefak, binatang roh, formasi, faksi
│   ├── models/             # player, enemy, item, technique, party
│   └── ui/                 # rich/textual views, hud, renderer
├── data/
│   ├── cultivation/        # tingkatan, jalur
│   ├── techniques/         # teknik rahasia
│   ├── items/              # pil, artefak, bahan
│   ├── enemies/            # musuh & bos
│   ├── quests/             # quest per arc
│   ├── events/             # event engine (§15)
│   ├── dialogues/
│   ├── maps/
│   ├── npc/
│   ├── factions/
│   └── story/              # memories, scenes, epilog
└── tests/
```

### 14.3 Contoh Data

**Tingkatan kultivasi:**

```json
{
  "id": "qi_condensation",
  "name": "Pengumpul Qi",
  "order": 1,
  "insight_required": 100,
  "stat_bonus": {"attack": 4, "hp": 40, "qi": 10},
  "unlocks": ["path_selection", "technique_basic"]
}
```

**Teknik:**

```json
{
  "id": "qi_slash",
  "name": "Tebasan Qi",
  "path": "sword",
  "element": "metal",
  "type": "physical",
  "qi_cost": 5,
  "power": 8,
  "effects": [],
  "requires": {"tier": "qi_condensation"}
}
```

**Pil:**

```json
{
  "id": "pill_insight",
  "name": "Pil Pemahaman",
  "effect": {"insight": 30},
  "recipe": [{"item": "herb_qi", "qty": 2}, {"item": "dew_morning", "qty": 1}]
}
```

**Musuh:**

```json
{
  "id": "grave_warden",
  "name": "Penjaga Makam",
  "tier": "qi_condensation",
  "element": "earth",
  "behavior": "defensive",
  "stats": {"attack": 10, "defense": 8, "hp": 45, "qi": 12},
  "skills": ["bone_crush", "earth_wall"],
  "tags": ["boss", "undead"],
  "requires_flag": "quest104_done"
}
```

> **Sistem save/load** (format, migrasi, anti-corrupt): §19. **Event engine** (format event, trigger/action): §15.

---

## 15. Event Engine (baru — fondasi gating & narasi)

Event adalah **mesin naratif data-driven**: pemicu kondisi (flag/quest/tier) → aksi (set flag, unlock peta, mulai quest, beri echo memori, ubah reputasi). Semua gating cerita, unlock peta, dan echo memori lewat event — **bukan hardcode di kode**.

### 15.1 Format Event

```json
{
  "id": "event_guild_city_unlock",
  "trigger": [
    {"kind": "flag", "flag": "quest102_done", "operator": "EQUALS", "value": true}
  ],
  "actions": [
    {"kind": "unlock_map", "target": "guild_city"},
    {"kind": "set_flag", "flag": "map_guild_city_unlocked", "value": true},
    {"kind": "log", "text": "Rumor tentang kota gilda mencapai telingamu..."}
  ],
  "once": true
}
```

### 15.2 Kind Trigger

|Kind|Makna|Contoh|
|-|-|-|
|`flag`|Cek flag dengan operator|`EQUALS` / `NOT_EQUALS` / `MISSING` (flag belum diset)|
|`quest_done`|Quest selesai (shortcut `quest<id>_done`)|`{"kind": "quest_done", "quest": "quest105"}`|
|`tier_reached`|Tingkatan kultivasi tercapai|`{"kind": "tier_reached", "tier": "golden_core"}`|
|`location_entered`|Pemain masuk peta|`{"kind": "location_entered", "map": "ancient_vault"}`|
|`day_passed`|Waktu game mencapai hari ke-N|`{"kind": "day_passed", "day": 7}`|

### 15.3 Kind Action

|Kind|Efek|
|-|-|
|`set_flag` / `clear_flag`|Set/hapus flag (`{flag, value}`)|
|`unlock_map`|Buka peta + set `map_<id>_unlocked`|
|`start_quest`|Mulai quest (`{id}`)|
|`grant_memory`|Beri echo memori (`{memory_id}`)|
|`grant_item` / `grant_gold`|Beri item / emas|
|`change_reputation`|Ubah reputasi faksi (`{faction, delta}`)|
|`start_dialog`|Paksa dialog (`{dialog_id}`)|
|`log`|Teks narasi singkat|

### 15.4 Aturan Proses

* **Kapan diproses:** setelah setiap aksi pemain di luar combat (setelah quest selesai, breakthrough, pindah peta, selesai dialog) — sekali per momen.
* **`once: true`** → event otomatis men-set `event_<id>_done` setelah dijalankan; `once: false` → repeatable (dibatasi trigger-nya sendiri).
* **Urutan:** event dievaluasi dalam urutan file; event yang memicu quest harus mendahului event yang bergantung pada flag quest itu.
* **Flag `quest<id>_done` otomatis** dari engine quest (§12.2) menjamin trigger event tidak pernah "hilang" karena lupa set flag.

---

## 16. Status Effects (baru)

Daftar status yang dipakai engine combat. Semua efek dihitung pada awal giliran pemilik status (tick) sebelum aksi.

|ID|Nama|Tipe|Efek|Durasi (giliran)|Contoh sumber|
|-|-|-|-|-|-|
|`poison`|Racun|dot|Damage per giliran (4% max HP)|3|Racun Meridian (Alkimia), ular roh|
|`burn`|Terbakar|dot|Damage per giliran (api, power tetap)|3|Teknik elemen api|
|`bleed`|Berdarah|dot|Damage per giliran (fisik)|2|Teknik pedang|
|`stun`|Terpukul|control|Skip 1 giliran|1|Jaring Formasi|
|`freeze`|Membeku|control|Skip giliran + defense +50%|2|Teknik elemen air/es|
|`charm`|Pesona|control|Menyerang sekutu sendiri|2|Seruan Jiwa (Jalan Jiwa)|
|`slow`|Lambat|debuff|Agility −30%|3|Teknik formasi|
|`seal`|Terkunci|debuff|Qi regen 0 + teknik diblokir|2|Segel Penjara|
|`weaken`|Lemah|debuff|Attack −25%|3|Racun meridian lanjutan|
|`barrier`|Perisai|buff|Defense +30%|3|Teknik tanah/formasi|
|`strengthen`|Menguat|buff|Attack +25%|3|Pil buff / teknik|
|`haste`|Cepat|buff|Agility +25%|3|Teknik angin/jiwa|
|`qi_flow`|Aliran Qi|buff|Qi regen +50%|3|Formasi|

**Aturan umum:**

* **Dot tidak stack** — kena kembali = refresh durasi, bukan tumpuk damage.
* **Buff/debuff sejenis tidak stack** — yang baru menggantikan yang lama.
* Status berakhir saat pertarungan usai, kecuali status dari **event cerita** (mis. kutukan) yang berjalan di waktu game dan dicek saat rest/travel.
* Pembersihan status: pil penawar, teknik pembersih, atau rest.
* Boss kebal terhadap control (`stun`/`freeze`/`charm`) kecuali dinyatakan lain di data musuh.

---

## 17. Daftar Stat Final (baru — perbaikan I5)

Definisi tunggal stat yang dipakai seluruh sistem. Tidak ada stat di luar daftar ini.

### 17.1 Stat Primer

|Stat|Peran|Formula yang memakai|
|-|-|-|
|`attack`|Kekuatan serangan fisik|Damage fisik (§6.4)|
|`defense`|Ketahanan fisik|Pengurang damage fisik|
|`agility`|Kecepatan & presisi|Urutan giliran (§6.1), crit, miss, dodge|
|`intelligence`|Kekuatan teknik|Damage teknik (jalur Alkimia/Formasi/Jiwa)|
|`vitality`|Daya tahan tubuh|HP max, resistensi racun/bleed|
|`spirit`|Kekuatan jiwa|Teknik Jalan Jiwa, resistensi charm/seal|

### 17.2 Stat Resource & Turunan

|Stat|Rumus|
|-|-|
|`hp_max`|`40 + vitality × 8 + bonus_tingkatan`|
|`qi_max`|`10 + order_tingkatan × 5 + meridian_buka × 3`|
|`qi_regen` (per giliran)|`2 + meridian_buka`|
|`crit_chance`|`min(25%, 5% + agility × 0.1%)`|
|`dodge_chance`|`min(30%, 5% + agility × 0.1%)`|
|`miss_rate` (dikenakan ke lawan)|`max(5%, 20% − agility × 0.1%)`|
|`resist_<elemen>`|Dari peralatan/teknik; default 0; pengurang linear damage teknik|

### 17.3 Stat Ekonomi

* `gold` — mata uang.
* `insight` — pemahaman (XP kultivasi, §4.3).
* `meridian_buka` — jumlah meridian yang dibuka (0–8); menaikkan qi & regen.
* Reputasi faksi (5 faksi, §8) — bukan stat combat, tapi penentu ending (§21).

---

## 18. Daftar Perintah Game (baru)

### 18.1 Perintah Global (selalu tersedia)

|Perintah|Deskripsi|
|-|-|
|`help`|Bantuan & daftar perintah konteks|
|`status`|Stat, tingkatan, qi, kondisi|
|`inventory` (alias `tas`)|Lihat item, equip/unequip|
|`quests` (alias `misi`)|Daftar quest aktif/selesai|
|`map`|Peta & lokasi yang terbuka|
|`party` (alias `tim`)|Kelola anggota tim (§20)|
|`save` / `load`|Simpan/muat (§19)|
|`settings` (alias `pengaturan`)|Tampilan, kecepatan teks, konfirmasi|
|`quit` (alias `keluar`)|Keluar (dengan prompt simpan)|

### 18.2 Perintah Eksplorasi

|Perintah|Deskripsi|
|-|-|
|`go <lokasi>`|Pindah ke lokasi terhubung|
|`look` (alias `amat`)|Amati lingkungan, NPC, objek interaktif|
|`talk <npc>` (alias `bicara`)|Bicara dengan NPC|
|`examine <objek>` (alias `periksa`)|Periksa objek/petunjuk|
|`loot` (alias `rampas`)|Ambil jarahan di lokasi|
|`cultivate` (alias `kultivasi`)|Kumpulkan insight (biaya waktu game)|
|`breakthrough` (alias `terobosan`)|Coba terobosan ke tingkatan berikutnya|
|`meditate` (alias `meditasi`)|Pulihkan qi (lokasi aman)|
|`rest` (alias `istirahat`)|Lewati hari; pulihkan HP/status|
|`refine <resep>` (alias `racik`)|Racik pil (butuh resep + bahan + alat)|
|`formation <nama>` (alias `formasi`)|Pasang/bongkar formasi|
|`equip` / `unequip`|Pasang/lepas senjata, artefak, teknik|
|`use <item>`|Pakai item (pil, dll.)|
|`recall <binatang_roh>`|Panggil/lepas binatang roh|

### 18.3 Perintah Combat (giliran pemain)

|Perintah|Deskripsi|
|-|-|
|`attack` (alias `serang`)|Serangan dasar (mengisi sedikit qi)|
|`technique <nama>` (alias `teknik`)|Pakai teknik (menguras qi)|
|`defend` (alias `bertahan`)|Pertahanan: damage masuk −50%|
|`item` (alias `pakai`)|Pakai item dalam pertarungan|
|`observe` (alias `amati`)|Analisis musuh: lihat HP/qi/elemen/status (gratis, §keputusan combat)|
|`swap <anggota>` (alias `ganti`)|Tukar anggota (1×/giliran, memakai giliran)|
|`formation_skill`|Skill formasi aktif (bila formasi terpasang)|
|`escape` (alias `kabur`)|Kabur (gagal vs boss)|

---

## 19. Sistem Save (baru)

### 19.1 Slot & Momen Simpan

* **3 slot manual** (`save`) + **1 slot autosave** yang menimpa otomatis saat: quest selesai, breakthrough, rest, dan pindah arc.
* Setiap save menyimpan **waktu game** (hari/jam) dan posisi pemain.

### 19.2 Struktur Save (JSON)

```json
{
  "schema_version": 1,
  "player": {"name": "…", "background": "…", "path": "sword", "tier": "qi_condensation", "stats": {}, "insight": 0, "gold": 0, "meridian_buka": 0},
  "party": [{"id": "lin_wei", "tier": "…", "bond_xp": 0}],
  "inventory": {"items": {}, "equipped": {}, "artifacts": {}},
  "quests": {"started": [], "done": [], "failed": []},
  "flags": {},
  "reputation": {"court": 0, "holy_order": 0, "rebels": 0, "guilds": 0, "ancient_order": 0},
  "memories": [],
  "map_unlocks": [],
  "location": "village_emberfall",
  "time": {"day": 1, "hour": 8},
  "settings": {}
}
```

### 19.3 Migrasi & Anti-Corrupt

* **Migrasi:** `schema_version` dinaikkan saat struktur berubah; engine punya `migrations: dict[versi_lama → fungsi]`. **Backfill wajib:** saat load, untuk setiap quest di `quests.done` yang belum punya flag `quest<id>_done`, set flag itu (pelajaran dari proyek sebelumnya — mencegah event gate mati di save lama).
* **Validasi:** sebelum dimuat, cek JSON valid + referensi (item, quest, peta) ter-resolve. Gagal → coba backup `.bak`; tetap gagal → pesan jelas + kembali ke menu (tanpa crash).
* **Atomic write:** tulis `save.json.tmp` lalu `os.replace` → tidak ada save setengah rusak.
* **Anti-cheat ringan:** tidak ada enkripsi; data bisa diedit manual oleh pemain (konsekuensi ditanggung pemain).

---

## 20. Aturan Rekrut Tim (baru)

### 20.1 Komposisi Tim

* Tim aktif **maksimal 4**: protagonis + 3 slot rekan/binatang roh.
* Anggota punya elemen & teknik sendiri → komposisi memengaruhi **resonansi tim** (§6.2).
* **Swap komposisi hanya di lokasi aman** (desa/kota/rest). Dalam combat: `swap` 1×/giliran dengan memakai giliran anggota aktif.

### 20.2 Sumber Anggota

|Sumber|Cara|Contoh|
|-|-|-|
|**Rekan cerita**|Quest utama/faksi|Lin Wei (Arc 1–2), Fang Yue (Arc 2), Kestrel (Arc 3, abu-abu)|
|**Binatang roh — rekrut**|Kalahkan di pertarungan → ikat (butuh Jalan Jiwa atau item khusus)|Serigala Bayangan|
|**Binatang roh — menetas**|Telur dari quest/loot/bos → menetas setelah N hari atau tier tertentu|Telur Phoenix Abu|

> **Keputusan final:** binatang roh memakai **dua-duanya** (rekrut + menetas) — bukan salah satu (§24.1).

### 20.3 Progresi Anggota

* Rekan/binatang roh memakai **bond XP** terpisah (bukan insight protagonis).
* Tidak melakukan breakthrough seperti protagonis; naik **peringkat rekan** (1–3 peringkat per arc) yang membuka teknik mereka.
* Binatang roh bisa **berevolusi sekali** (saat tier tertentu) — perubahan bentuk, elemen, stat.

### 20.4 Kematian & KO

* **KO** dalam combat: pulih otomatis setelah pertarungan/rest.
* **Kematian permanen** hanya dari momen cerita yang ditulis (scripted) — selalu ada peringatan/kesempatan mencegah. Nada gelap ≠ hukuman tak adil.

---

## 21. Penentu Ending (baru)

### 21.1 Mekanik Skor

* Sepanjang permainan ada **7 keputusan kunci** (1 di Arc 1, 2 di Arc 2–4) yang men-set flag **dan** menambah `ending_points` ke salah satu dari 3 jalur: `defy` (menentang langit), `seal` (menyegel diri), `reconcile` (rekonsiliasi).
* Keputusan kunci ditandai eksplisit di quest/dialog (biasanya pilihan sulit dengan konsekuensi reputasi).
* **Ending utama:** jalur dengan poin tertinggi. **Tie-break:** keputusan kunci terakhir yang diambil menentukan.
* Persyaratan minimum: tingkatan **Pemutus Kehampaan** dan sekutu/ritual cukup — jika tidak, ending berujung pada variasi "kegagalan heroik".

### 21.2 Ending & Epilog

|Ending|Syarat utama|Variasi (contoh)|
|-|-|-|
|**Menentang Langit**|`defy` tertinggi + ritual lengkap|Epilog: kerajaan dibangun ulang / langit dirombak / harga yang dibayar (siapa gugur)|
|**Menyegel Diri**|`seal` tertinggi|Siapa menang di antara faksi? Entitas tertidur kembali?|
|**Rekonsiliasi**|`reconcile` tertinggi|Orde suci dan pemberontak hidup berdampingan? Pengorbanan siapa?|

* **Epilog** disusun dari **reputasi 5 faksi** (§8): status per faksi (hancur / lemah / kuat / berkuasa) disebut di epilog.

### 21.3 Cara Melawan Entitas Kuno (Ending 1 — keputusan final)

* **Ritual + pertarungan dua tahap:**

  1. **Persiapan ritual:** kumpulkan artefak + pasang formasi + pilih sekutu (komposisi tim) → memengaruhi buff/stat di tahap kedua.
  2. **Pertarungan Suara:** bos final (tier 6+, §11). Jika persiapan kurang, bos mendapat bonus (stat +25% per komponen ritual yang hilang).
* Ini menegaskan prinsip "kekuatan tidak gratis": bahkan ending puncak butuh investasi naratif & sistem.

---

## 22. Target Konten per Arc (baru)

Angka final untuk perencanaan produksi. Total = target minimum yang harus tercapai saat rilis.

|Konten|Arc 1|Arc 2|Arc 3|Arc 4|Total|
|-|-|-|-|-|-|
|Quest utama|8|8|8|8|**32**|
|Quest faksi|2|3|3|2|**10**|
|Peta baru|3|2|3|2|**10** (§9)|
|NPC (inti + pendukung)|6|7|7|5|**25**|
|Musuh (non-bos)|7|8|9|6|**30**|
|Bos|1|1|1|2|**5** (§11)|
|Teknik|6|8|8|8|**30**|
|Resep pil|3|4|4|3|**14**|
|Artefak roh|2|3|3|4|**12**|
|Binatang roh|1|1|1|1|**4**|
|Echo memori (rahasia)|2|2|2|3|**9**|
|Durasi main|2–3 jam|3–4 jam|3–4 jam|4–5 jam|**12–16 jam** (15+ dengan side content)|

---

## 23. Roadmap Pengembangan

|Fase|Isi|Kriteria selesai|
|-|-|-|
|**Fase 0 — MVP**|Engine combat (turn-based + elemen + qi + tim 4 + status dasar §16), sistem kultivasi (tingkatan + breakthrough + meridian), alkimia dasar (2–3 pil), launcher Rich/Textual, save/load dasar (§19)|Bisa main: mulai → kultivasi → 1 pertarungan tim → breakthrough → simpan/muat|
|**Fase 1 — Arc 1**|Data quest101+, event engine (§15), peta awal, NPC awal, bos Arc 1, rahasia pertama, echo memori|Arc 1 playable penuh + test|
|**Fase 2 — Arc 2**|Sekte, gilda, orde rahasia, teknik/artefak/binatang roh (§20), reputasi faksi, rekan tim pertama|Arc 2 playable|
|**Fase 3 — Arc 3**|Orde Suci, pemberontak, entitas kuno aktif, formasi, keputusan kunci pertama|Arc 3 playable|
|**Fase 4 — Arc 4 & Ending**|Ruang rahasia, rahasia penuh, sistem skor ending (§21), 3 ending + variasi, epilog|Game lengkap 15+ jam|
|**Fase 5 — Polish**|Keseimbangan, save migration (§19.3), smoke tests, README, playtest|Rilis v1.0|

---

## 24. Keputusan Desain Terkunci

### 24.1 Keputusan Final (termasuk konversi "Belum Diputuskan" → default)

1. Tema "setengah-setengah": kultivasi sebagai sistem kekuatan di dunia fantasi gelap (bukan xianxia murni).
2. Breakthrough = momen cerita, bisa gagal; **gagal = cedera sementara** (−25% stat, 2 hari), 30% memicu inner demon fight — **tanpa penalti permanen**.
3. Tim combat maksimal 4 anggota (§20).
4. 5 elemen dengan siklus Metal→Kayu→Tanah→Air→Api→Metal.
5. Jalur kultivasi bisa diperluas, bukan mutasi kelas.
6. Ending dinamis (3 besar + variasi), bukan 6 ending kaku; penentu mekanik di §21.
7. Konten 100% data-driven JSON.
8. UI Rich (tampilan) + Textual (interaksi).
9. **Nama dunia final:** kerajaan **Ashenfeld**, desa awal **Emberfall** (`village_emberfall`), sekte **Awan Biru** (`sect_azure`); nama karakter di §10 adalah default final.
10. **Jumlah konten target:** 32 quest utama + 10 quest faksi (detail §22).
11. **Formula keseimbangan:** angka konkret di §6.4 & §17 (bukan draf).
12. **Binatang roh:** rekrut + menetas — **keduanya** aktif (§20.2).
13. **Ending "Menentang Langit":** ritual + pertarungan dua tahap (§21.3).
14. **Inisiatif combat:** turn-based klasik — order dihitung sekali dari agility saat combat dimulai, tetap untuk seluruh pertarungan (§6.1).
15. **Flag quest:** engine otomatis men-set `quest<id>_done` saat quest selesai; event/musuh memakai flag ini sebagai trigger (§12.2, §15). Naming wajib `quest<id>_done`, bukan `q<id>_done`.
16. **Gating peta & cerita:** lewat event engine (`unlock_map`, trigger flag) — bukan hardcode (§15).
17. **Kematian rekan:** permanen hanya dari momen cerita scripted, dengan peringatan (§20.4).
18. **Save:** 3 slot manual + autosave; migrasi + backfill `quest<id>_done` pada load save lama (§19).

### 24.2 Belum Diputuskan (terbuka untuk produksi)

* Detail flavor nama sekte sekunder, kota gilda, dan karakter pendukung (bukan inti) — bebas dikembangkan penulis konten selama konsisten nada gelap.
* Angka halus keseimbangan (damage per skill, harga toko) — disetel saat playtest Fase 5, mengikuti kerangka formula §6.4/§17.

### 24.3 Changelog

**v1.0 (2026-08-05)** — Naik status dari draf 0.1 menjadi **dokumen kunci pembangunan**:

* **Perbaikan inkonsistensi (I1–I5):**

  * I1 — Flag naming diseragamkan ke `quest<id>_done` di §12.3 & §14.3 (sebelumnya `q101_done`/`q104_done`), selaras AGENTS.md §5.3.
  * I2 — Kurva bos diselaraskan dengan tingkatan pemain (§11): Rasul Langit → Pemutus Kehampaan, Suara → Penantang Surga+; tabel kini memuat kolom tingkatan pemain akhir arc.
  * I3 — Cross-ref §3.1 diperbaiki (kini → §24.1); nama kerajaan **Ashenfeld** & desa **Emberfall** diputuskan final agar tidak membingungkan.
  * I4 — Inisiatif combat dikunci ke turn-based klasik (order tetap, dihitung sekali dari agility) di §6.1.
  * I5 — Daftar stat final eksplisit di §17; formula §6.4 kini merujuk definisi tunggal.
* **Bagian baru:** §15 Event Engine, §16 Status Effects, §17 Daftar Stat Final, §18 Daftar Perintah Game, §19 Sistem Save, §20 Aturan Rekrut Tim, §21 Penentu Ending, §22 Target Konten per Arc.
* **Konversi "Belum Diputuskan" → keputusan default terkunci** (§24.1): nama dunia, jumlah quest, formula keseimbangan, binatang roh (rekrut+menetas), cara melawan entitas kuno (ritual+pertarungan), penalti breakthrough (sementara), inisiatif klasik, flag otomatis.
* Roadmap dipindah ke §23; struktur proyek §14.2 ditambah `data/events/`.

---

*Dokumen ini adalah sumber kebenaran desain. Perubahan bertentangan dengan dokumen ini wajib didiskusikan dengan pengguna (AGENTS.md §1). Status: v1.0 — dokumen kunci pembangunan.*

