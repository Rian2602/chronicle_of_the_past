#!/usr/bin/env bash
# Smoke test CLI: navigasi menu 'Muat' di terminal nyata (tmux).
#
# Cara menjalankan:  bash tools/smoke_menu.sh
# Persyaratan:       tmux + python3 (pustaka standar saja).
#
# Skenario:
#   1. Ada save            → item 'Muat' muncul, submenu berisi slot, load berhasil.
#   2. Tanpa save          → item 'Muat' tidak muncul di menu eksplorasi.
#   3. Save saat bertarung → load memulihkan pertarungan (menu combat + aksi nyata).
#   4. Level-up interaktif → pemain memilih bonus stat, bukan auto-apply.
#
# Semua skenario berjalan di direktori kerja sementara yang terisolasi
# (symlink data/); tidak ada file yang ditulis ke folder saves/ proyek.

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SESSION="cotp_smoke_menu"
CAPTURE="/tmp/cotp_smoke_menu.txt"
WORKDIRS=()

command -v tmux >/dev/null 2>&1 || { echo "FAIL: tmux tidak tersedia"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "FAIL: python3 tidak tersedia"; exit 1; }

cleanup() {
  tmux kill-session -t "$SESSION" 2>/dev/null || true
  rm -f "$CAPTURE"
  local dir
  for dir in "${WORKDIRS[@]}"; do
    rm -rf "$dir"
  done
}
trap cleanup EXIT

fail() {
  echo "FAIL: $1"
  echo "--- layar terakhir ---"
  cat "$CAPTURE" 2>/dev/null || true
  exit 1
}

wait_for() {
  local pattern="$1" timeout="${2:-20}" i=0
  while [ "$i" -lt "$timeout" ]; do
    tmux capture-pane -t "$SESSION" -p > "$CAPTURE" 2>/dev/null || true
    if grep -qE "$pattern" "$CAPTURE" 2>/dev/null; then
      return 0
    fi
    sleep 0.3
    i=$((i + 1))
  done
  return 1
}

new_workdir() {
  local dir
  dir="$(mktemp -d)"
  ln -s "$PROJECT_DIR/data" "$dir/data"
  WORKDIRS+=("$dir")
  echo "$dir"
}

# Jalankan launcher di workdir lalu sampai di menu eksplorasi permainan baru.
start_explore_menu() {
  local workdir="$1"
  tmux kill-session -t "$SESSION" 2>/dev/null || true
  tmux new-session -d -s "$SESSION" -x 100 -y 40 -c "$workdir"
  sleep 0.5
  tmux send-keys -t "$SESSION" "python3 \"$PROJECT_DIR/launcher.py\"" Enter
  wait_for "CHRONICLE OF THE PAST" || fail "menu utama tidak muncul"
  tmux send-keys -t "$SESSION" Enter          # pilih "Permainan Baru"
  wait_for "Siapa namamu" || fail "prompt nama tidak muncul"
  tmux send-keys -t "$SESSION" "Smoke" Enter
  wait_for "Pilih Kelas" || fail "menu kelas tidak muncul"
  tmux send-keys -t "$SESSION" Enter          # kelas pertama (default = Assassin)
  sleep 0.5
  tmux send-keys -t "$SESSION" Enter          # lewati scene intro 1
  sleep 0.4
  tmux send-keys -t "$SESSION" Enter          # lewati scene intro 2
  sleep 0.5
}

# Tekan 's' sampai penanda berada pada item bernama $1.
select_menu_item() {
  local item="$1" i=0
  tmux capture-pane -t "$SESSION" -p > "$CAPTURE" || true
  while ! grep -qE "^> ${item}$" "$CAPTURE" 2>/dev/null; do
    tmux send-keys -t "$SESSION" "s"
    sleep 0.25
    tmux capture-pane -t "$SESSION" -p > "$CAPTURE" || true
    i=$((i + 1))
    if [ "$i" -ge 14 ]; then
      return 1
    fi
  done
  return 0
}

# Keluar aplikasi dengan bersih (menangani konfirmasi saat bertarung).
quit_app() {
  tmux send-keys -t "$SESSION" "q"
  local i=0
  while [ "$i" -lt 20 ]; do
    tmux capture-pane -t "$SESSION" -p > "$CAPTURE" || true
    if grep -qE "CHRONICLE OF THE PAST" "$CAPTURE" 2>/dev/null; then
      # sudah di menu utama → keluar aplikasi
      tmux send-keys -t "$SESSION" "q"
      wait_for "Sampai jumpa" || fail "aplikasi tidak keluar dengan bersih"
      return 0
    fi
    if grep -qE "Kamu sedang bertarung" "$CAPTURE" 2>/dev/null; then
      tmux send-keys -t "$SESSION" Enter      # "Ya, keluar"
      wait_for "CHRONICLE OF THE PAST" || fail "tidak kembali ke menu utama"
      tmux send-keys -t "$SESSION" "q"
      wait_for "Sampai jumpa" || fail "aplikasi tidak keluar dengan bersih"
      return 0
    fi
    sleep 0.3
    i=$((i + 1))
  done
  fail "tidak bisa keluar dari permainan"
}

# ===== Skenario 1: ada save → 'Muat' muncul, submenu, load =====
WORKDIR="$(new_workdir)"
python3 - <<PY || fail "save sementara gagal dibuat"
from src.core.game_context import GameContext
from src.core.game import Game
from src.core import save_manager
ctx = GameContext(data_dir="$WORKDIR/data")
g = Game(ctx)
g.new_game("Smoke", "warrior")
save_manager.save_game(g.state, "$WORKDIR/saves/slot1.json")
PY
start_explore_menu "$WORKDIR"
select_menu_item "Muat" || fail "[1/4] item Muat tidak dapat dijangkau (harusnya ada)"
echo "OK [1/4]: item Muat muncul saat ada save"
tmux send-keys -t "$SESSION" Enter
wait_for "slot1.json" || fail "[1/4] slot save tidak muncul di submenu Muat"
echo "OK [1/4]: submenu Muat menampilkan slot"
tmux send-keys -t "$SESSION" Enter
wait_for "dimuat" || fail "[1/4] pesan muat tidak muncul"
echo "OK [1/4]: save berhasil dimuat"
quit_app
echo "OK [1/4]: keluar aplikasi dengan bersih"

# ===== Skenario 2: tanpa save → 'Muat' tersembunyi =====
WORKDIR="$(new_workdir)"
start_explore_menu "$WORKDIR"
tmux capture-pane -t "$SESSION" -p > "$CAPTURE" || true
grep -qE "^Aksi:" "$CAPTURE" || fail "[2/4] menu eksplorasi tidak tampil"
grep -qE "^[ >] Simpan" "$CAPTURE" || fail "[2/4] menu eksplorasi tidak lengkap (Simpan hilang)"
grep -qE "^[ >] Keluar" "$CAPTURE" || fail "[2/4] menu eksplorasi tidak lengkap (Keluar hilang)"
if grep -qE "^[ >] Muat" "$CAPTURE"; then
  fail "[2/4] item Muat muncul padahal tidak ada save"
fi
# Putar satu siklus penuh menu: pastikan 'Muat' tidak pernah muncul
i=0
while [ "$i" -lt 10 ]; do
  tmux send-keys -t "$SESSION" "s"
  sleep 0.2
  tmux capture-pane -t "$SESSION" -p > "$CAPTURE" || true
  if grep -qE "^[ >] Muat" "$CAPTURE"; then
    fail "[2/4] item Muat muncul saat memutar menu (tanpa save)"
  fi
  i=$((i + 1))
done
echo "OK [2/4]: item Muat tidak muncul saat tidak ada save"
quit_app
echo "OK [2/4]: keluar aplikasi dengan bersih"

# ===== Skenario 3: load save saat bertarung memulihkan pertarungan =====
WORKDIR="$(new_workdir)"
python3 - <<PY || fail "save pertarungan gagal dibuat"
from src.core.game_context import GameContext
from src.core.game import Game
from src.core import save_manager
from src.engine.combat_engine import start_combat
from src.systems import loot_system
ctx = GameContext(data_dir="$WORKDIR/data")
g = Game(ctx)
g.new_game("Smoke", "warrior")
enemy = g.state.enemies["wild_wolf"]
enemy.stats["hp"] = 50  # biar satu serangan tidak langsung membunuh
g._combat = start_combat(
    g.state.player, enemy, g.randomizer,
    skills=ctx.skills, loot_resolver=loot_system.roll_loot,
    items=g.state.items,
)
save_manager.save_game(g.state, "$WORKDIR/saves/combat_slot.json", combat=g._combat)
PY
start_explore_menu "$WORKDIR"
select_menu_item "Muat" || fail "[3/4] item Muat tidak dapat dijangkau"
tmux send-keys -t "$SESSION" Enter
wait_for "combat_slot.json" || fail "[3/4] slot combat tidak muncul di submenu Muat"
tmux send-keys -t "$SESSION" Enter
wait_for "dimuat" || fail "[3/4] pesan muat tidak muncul"
# Pertarungan pulih: menu berubah menjadi menu combat
wait_for "^Aksi:" || fail "[3/4] menu tidak muncul setelah load"
tmux capture-pane -t "$SESSION" -p > "$CAPTURE" || true
grep -qE "^[ >] Serang" "$CAPTURE" || fail "[3/4] menu combat tidak muncul setelah load"
grep -qE "^[ >] Kabur" "$CAPTURE" || fail "[3/4] menu combat tidak lengkap (Kabur hilang)"
# Jalankan aksi nyata: Serang → tampilan combat (Wild Wolf) muncul
tmux send-keys -t "$SESSION" Enter
wait_for "Wild Wolf" || fail "[3/4] aksi combat tidak berfungsi setelah load"
echo "OK [3/4]: load save saat bertarung memulihkan pertarungan"
quit_app
echo "OK [3/4]: keluar aplikasi dengan bersih"

# ===== Skenario 4: level-up interaktif via quest (deterministik, tanpa RNG) =====
WORKDIR="$(new_workdir)"
start_explore_menu "$WORKDIR"
# Bicara → Aria → 2× pilihan pertama → quest001 dimulai
select_menu_item "Bicara" || fail "[4/4] item Bicara tidak dapat dijangkau"
tmux send-keys -t "$SESSION" Enter
wait_for "Aria" || fail "[4/4] submenu Bicara tidak muncul"
tmux send-keys -t "$SESSION" Enter          # pilih Aria → dialog
wait_for "Siapa Anda" || fail "[4/4] dialog Aria tidak muncul"
tmux send-keys -t "$SESSION" Enter          # pilihan pertama (Siapa Anda?)
wait_for "Terima kasih" || fail "[4/4] dialog lanjutan Aria tidak muncul"
tmux send-keys -t "$SESSION" Enter          # pilihan pertama → dialog selesai
sleep 0.4
# Bicara → Kepala Desa → pilihan pertama → quest001 selesai → level-up
select_menu_item "Bicara" || fail "[4/4] item Bicara kedua tidak dijangkau"
tmux send-keys -t "$SESSION" Enter
select_menu_item "Kepala Desa" || fail "[4/4] item Kepala Desa tidak dijangkau"
tmux send-keys -t "$SESSION" Enter          # Kepala Desa → dialog
wait_for "Semoga kau berhasil" || fail "[4/4] dialog Kepala Desa tidak muncul"
tmux send-keys -t "$SESSION" Enter          # selesaikan quest → level-up pending
wait_for "Pilih bonus level-up" || fail "[4/4] prompt pilihan bonus tidak muncul"
echo "OK [4/4]: prompt pilihan bonus level-up muncul"
tmux send-keys -t "$SESSION" Enter          # pilih bonus pertama (Serangan +2)
wait_for "Bonus dipilih" || fail "[4/4] bonus level-up tidak diterapkan"
echo "OK [4/4]: bonus level-up diterapkan"
quit_app
echo "OK [4/4]: keluar aplikasi dengan bersih"

echo
echo "PASS: seluruh skenario smoke test berhasil"
