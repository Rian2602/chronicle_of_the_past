# Protokol Kolaborasi — Freebuff (Eksekutor) ↔ Antigravity (Reviewer)

Dokumen ini mendefinisikan **kontrak kerja dua-agen** untuk proyek Chronicle of
the Past. Tujuan: memangkas pemborosan token (tidak ada lagi salin-tempel
transkrip panjang) dan mempercepat siklus TDD dengan pembagian peran yang tegas.

> Status: dokumen perilaku tambahan. Tidak menggantikan `AGENTS.md` — dokumen
> itu tetap satu-satunya sumber kebenaran perilaku. Bila bertentangan,
> `AGENTS.md` menang (urutan otoritas AGENTS §1).

## 1. Peran

| Agen | Peran | Tanggung jawab |
|-|-|-|
| **Freebuff** | **Eksekutor** | Membaca rencana, menulis kode/data (TDD RED→GREEN), menjalankan gerbang (pytest/ruff/validate), commit, dan menulis handoff. |
| **Antigravity** | **Reviewer & Evaluator** | Membaca handoff + diff/commit, memverifikasi kepatuhan GDD/AGENTS, menulis verdict terstruktur. **Tidak menulis kode produksi.** |

Pembagian ini mencegah dua agen menulis file yang sama secara bersamaan.

## 2. Alur Kerja (loop)

```
1. Freebuff  : kerjakan task dari rencana (TDD) → commit → tulis handoff
2. User/CLI  : jalankan `tools/agent_review.sh <task-id>`
3. Antigravity: baca handoff + cek kode → tulis verdict ke .agent-sync/reviews/
4. Freebuff  : baca verdict
     ├─ APPROVED → lanjut task berikutnya (atau push bila user minta)
     └─ NEEDS_FIX → perbaiki Critical/Important → ulangi dari langkah 1
```

**Satu task = satu handoff = satu review.** Task kecil (bug 1 baris) boleh
langsung APPROVED tanpa loop; task besar wajib review.

## 3. Format Handoff (Freebuff → outbox)

File: `.agent-sync/outbox/<task-id>.md` (gitignored, transien).

```markdown
# Handoff: <task-id>
- Rencana: <path plan docs/superpowers/plans/...>
- Commit: <hash> (<pesan>)

## Ringkasan
<2-4 baris: apa yang diubah dan mengapa>

## File diubah
- <path> (+N/−M) — <alasan singkat>

## Bukti verifikasi
- pytest: N passed
- ruff check / format: bersih
- tools/validate.py: OK

## Titik fokus reviewer
<1-3 pertanyaan/risiko spesifik yang ingin diverifikasi>
```

**Aturan hemat token:** handoff maksimal ~30 baris. Jangan salin output test
penuh — cukup angka. Jangan salin kode — cukup path + baris yang relevan.

## 4. Format Verdict (Antigravity → reviews)

File: `.agent-sync/reviews/<task-id>.md`.

```markdown
# Verdict: APPROVED | NEEDS_FIX
## Critical (blokir penyelesaian)
- ...
## Important (wajib dibenahi sebelum push)
- ...
## Minor (opsional, boleh dicatat ponytail:)
- ...
## Verifikasi reviewer
- [ ] Kepatuhan GDD/AGENTS (sebutkan §)
- [ ] Test/lint/validator benar-benar dijalankan (bukan klaim)
- [ ] Tidak ada regresi pada sistem lain
```

## 5. Aturan Main

1. **Hanya Freebuff yang menyentuh kode produksi.** Antigravity menulis hanya
   file verdict (dan boleh membaca apa pun).
2. **Handoff harus jujur**: sertakan bukti gerbang nyata. Klaim tanpa bukti
   = ditolak reviewer (AGENTS §2.5).
3. **Reviewer memverifikasi, bukan menebak**: jalankan/minta jalankan gerbang
   bila ragu; jangan APPROVED hanya dari deskripsi.
4. **Verdict `NEEDS_FIX` mengharuskan ulang loop**; `APPROVED` berarti task
   selesai dan boleh dilanjutkan ke task berikutnya.
5. **Push ke `origin/main` hanya atas instruksi user**, setelah task yang
   bersangkutan APPROVED.
6. File `.agent-sync/` **tidak pernah di-commit** (lihat `.gitignore`).
   Dokumen ini dan skripnya **wajib di-commit** (aturan main terversi).

## 6. Cara Menjalankan Review

```bash
# Review task dengan handoff yang sudah ada
tools/agent_review.sh <task-id>

# Review dengan instruksi tambahan (mis. fokus pada sistem tertentu)
tools/agent_review.sh <task-id> --prompt "Fokus verifikasi kepatuhan GDD §20"
```

Skrip memanggil `agy -p` (headless mode Antigravity CLI) dengan prompt yang
menginstruksikan peran reviewer, membaca handoff, dan menulis verdict.
Dibutuhkan: `agy` terpasang & login (lihat `.gemini/antigravity-cli/`).

## 7. Konvensi Task-ID

`<inisial-sprint>-<urutan>` — contoh: `alchemy-03`, `party-05`, `fix-ux-02`.
Tersimpan sebagai nama file: `outbox/alchemy-03.md` → `reviews/alchemy-03.md`.
