#!/usr/bin/env bash
# Agent Relay — jalankan review Antigravity untuk satu task (PROTOCOL.md §6).
#
# Memanggil `agy -p` (headless Antigravity CLI) dengan peran REVIEWER,
# membaca handoff Freebuff, dan menulis verdict ke .agent-sync/reviews/.
#
# Penggunaan:
#   tools/agent_review.sh <task-id> [--prompt "instruksi tambahan"]
#
# Exit codes:
#   0  verdict ditulis (APPROVED atau NEEDS_FIX)
#   1  argumen/setup tidak valid
#   2  agy gagal / verdict tidak ditulis
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

TASK_ID=""
EXTRA_PROMPT=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --prompt)
            EXTRA_PROMPT="$2"
            shift 2
            ;;
        *)
            TASK_ID="$1"
            shift
            ;;
    esac
done

if [[ -z "$TASK_ID" ]]; then
    echo "Penggunaan: $0 <task-id> [--prompt 'instruksi tambahan']" >&2
    exit 1
fi

OUTBOX=".agent-sync/outbox/${TASK_ID}.md"
REVIEW=".agent-sync/reviews/${TASK_ID}.md"

if [[ ! -f "$OUTBOX" ]]; then
    echo "ERROR: handoff tidak ditemukan: $OUTBOX" >&2
    exit 1
fi
if ! command -v agy >/dev/null 2>&1; then
    echo "ERROR: agy (Antigravity CLI) tidak ada di PATH" >&2
    exit 1
fi

if [[ -f "$REVIEW" ]]; then
    rm -f "$REVIEW"
fi

# Prompt yang menginstruksikan peran reviewer — bukan eksekutor.
PROMPT="Kamu adalah REVIEWER kode proyek 'Chronicle of the Past' (Python,
TDD, data-driven JSON). Peranmu: memverifikasi dan mengevaluasi — BUKAN
menulis kode. Ikuti docs/agent-sync/PROTOCOL.md dan AGENTS.md.

Langkah:
1. Baca handoff eksekutor di: ${OUTBOX}
2. Verifikasi klaimnya: cek commit yang disebut (git show), file yang
   disebut, dan jalankan gerbang bila perlu (pytest -q, ruff check,
   ruff format --check, python tools/validate.py).
3. Nilai kepatuhan terhadap GDD.md (sebutkan nomor bagian §) dan AGENTS.md.
4. Tulis verdict ke: ${REVIEW}

Format verdict (wajib persis):
# Verdict: APPROVED | NEEDS_FIX
## Critical (blokir penyelesaian)
## Important (wajib dibenahi sebelum push)
## Minor (opsional, boleh dicatat ponytail:)
## Verifikasi reviewer

JANGAN mengubah file apa pun selain menulis file verdict di atas. JANGAN
commit atau push. Jawabanmu hanya perlu mengonfirmasi verdict yang ditulis.
${EXTRA_PROMPT:+Instruksi tambahan user: ${EXTRA_PROMPT}}"

echo "==> Memanggil agy headless (task: ${TASK_ID})..."
echo "==> Handoff : ${OUTBOX}"
echo "==> Verdict : ${REVIEW}"

agy -p "$PROMPT" \
    --print-timeout 5m \
    --output-format text \
    > ".agent-sync/logs/${TASK_ID}.log" 2>&1
AGY_EXIT=$?

if [[ $AGY_EXIT -ne 0 ]]; then
    echo "ERROR: agy gagal (exit $AGY_EXIT). Log: .agent-sync/logs/${TASK_ID}.log" >&2
    tail -5 ".agent-sync/logs/${TASK_ID}.log" >&2 || true
    exit 2
fi

if [[ ! -f "$REVIEW" ]]; then
    echo "ERROR: verdict tidak ditulis oleh agy. Log: .agent-sync/logs/${TASK_ID}.log" >&2
    exit 2
fi

echo "==> Verdict tersedia:"
cat "$REVIEW"
echo
if grep -q "Verdict: APPROVED" "$REVIEW"; then
    echo "==> Hasil: APPROVED"
else
    echo "==> Hasil: NEEDS_FIX (baca verdict untuk daftar temuan)"
fi
exit 0
