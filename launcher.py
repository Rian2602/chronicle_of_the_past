"""Chronicle of the Past - launcher entry point."""

import os
import sys
import termios
import tty

from src.core import save_manager
from src.core.game import Game
from src.core.game_context import GameContext
from src.ui import animation, game_menu, menu, story_view
from src.utils.json_loader import ContentError

_NAV_HINT = "Navigasi: \u2191/\u2193 atau w/s untuk berpindah. Enter untuk memilih. 'q' keluar."


def _clear_screen():
    """Bersihkan terminal interaktif sebelum satu layar game digambar ulang."""
    if sys.stdout.isatty():
        os.system("cls" if os.name == "nt" else "clear")


def _read_key() -> str:
    """Baca satu keypress dari stdin.

    Di TTY nyata (terminal interaktif): gunakan raw mode untuk baca
    karakter langsung tanpa buffering — arrow key bekerja real-time.
    Di non-TTY (pipe/redirect/pytest): fallback ke input() satu baris.

    Mengembalikan: 'UP', 'DOWN', 'ENTER', 'q', atau karakter tunggal.
    """
    if not sys.stdin.isatty():
        # Fallback untuk non-TTY (pytest, pipe, redirect)
        line = input("> ").strip().lower()
        if line in ("w", "k"):
            return "UP"
        if line in ("s", "j"):
            return "DOWN"
        if line == "":
            return "ENTER"
        return line

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        ch = sys.stdin.read(1)
        if ch == "\x1b":            # ESC byte — mulai sequence arrow key
            ch2 = sys.stdin.read(1)
            if ch2 == "[":
                ch3 = sys.stdin.read(1)
                return {"A": "UP", "B": "DOWN"}.get(ch3, "")
            return ""               # ESC tanpa sequence yang dikenal → abaikan
        if ch in ("\r", "\n"):
            return "ENTER"
        if ch == "\x03":            # Ctrl+C
            raise KeyboardInterrupt
        return ch.lower()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def _menu_loop(render_fn, total: int, hint: str, screen: str = "") -> int:
    """Loop navigasi menu generik dengan arrow key support.

    Args:
        render_fn: callable(selection) → str teks menu untuk dicetak.
        total: jumlah item dalam menu.
        hint: teks petunjuk navigasi yang ditampilkan di bawah menu.

    Returns:
        Index item yang dipilih (0-based).
    """
    selection = 0
    while True:
        _clear_screen()
        rendered = render_fn(selection)
        if screen:
            print(screen)
            print()
        print(rendered)
        print(hint, flush=True)

        key = _read_key()
        if key in ("UP", "w", "k"):
            selection = (selection - 1) % total if total > 0 else 0
        elif key in ("DOWN", "s", "j"):
            selection = (selection + 1) % total if total > 0 else 0
        elif key in ("ENTER", ""):
            return selection
        elif key == "q":
            raise KeyboardInterrupt


def _menu_selection(screen: str = "") -> int:
    total = len(menu.MAIN_ITEMS)
    return _menu_loop(
        render_fn=menu.render_main,
        total=total,
        hint="Navigasi: \u2191/\u2193 atau w/s untuk berpindah. Enter untuk memilih. 'q' keluar.",
        screen=screen,
    )


def _class_selection(ctx):
    class_ids = list(ctx.classes.keys())
    if not class_ids:
        return None

    def render(selection):
        lines = ["Pilih Kelas:"]
        for idx, class_id in enumerate(class_ids):
            marker = "> " if idx == selection else "  "
            lines.append(f"{marker}{ctx.classes[class_id]['name']}")
        lines.append("")
        lines.append(menu.render_class_card(ctx.classes[class_ids[selection]]))
        return "\n".join(lines)

    idx = _menu_loop(
        render_fn=render,
        total=len(class_ids),
        hint="Navigasi: \u2191/\u2193 atau w/s untuk berpindah. Enter untuk memilih.",
    )
    return class_ids[idx]


def _play_intro(ctx):
    """Putar cutscene intro (scene berawalan 'intro_') — Enter lanjut, q lewati."""
    scenes = [s for s in ctx.scenes if s.get("id", "").startswith("intro_")]
    for scene in scenes:
        _clear_screen()
        print(story_view.render_scene(scene))
        key = _read_key()
        if key == "q":
            break
    print()


def _navigate(game, last_output: str = ""):
    """Navigasi menu game bertingkat dengan arrow key. Return perintah atau None (keluar)."""
    stack = []  # list (items, title)
    while True:
        if stack:
            items, title = stack[-1]
        else:
            items = game_menu.build(game)
            title = "Aksi"

        def render(selection, items=items, title=title):
            lines = [f"{title}:"]
            for idx, (label, _) in enumerate(items):
                marker = "> " if idx == selection else "  "
                lines.append(marker + label)
            return "\n".join(lines)

        idx = _menu_loop(
            render_fn=render,
            total=len(items),
            hint=_NAV_HINT,
            screen=last_output,
        )
        label, target = items[idx]
        if callable(target):
            stack.append((target(), label))
        elif target is None:
            if stack:
                stack.pop()
            else:
                return None
        else:
            return target


def _confirm_quit() -> bool:
    """Konfirmasi keluar saat bertarung. Return True jika benar-benar keluar."""
    options = [("Ya, keluar", True), ("Tidak, lanjut bertarung", False)]

    def render(selection):
        lines = ["Kamu sedang bertarung. Keluar tanpa menyimpan?"]
        for idx, (label, _) in enumerate(options):
            marker = "> " if idx == selection else "  "
            lines.append(marker + label)
        return "\n".join(lines)

    try:
        idx = _menu_loop(render_fn=render, total=len(options), hint=_NAV_HINT)
    except KeyboardInterrupt:
        return False  # 'q' di konfirmasi = lanjut bertarung
    return options[idx][1]


def _game_loop(game, initial_output: str = ""):
    last_output = initial_output
    while True:
        try:
            cmd = _navigate(game, last_output)
        except KeyboardInterrupt:
            if getattr(game, "_combat", None) is not None and not _confirm_quit():
                continue
            print("\nSampai jumpa!")
            return
        if cmd is None:
            print("\nSampai jumpa!")
            return
        if cmd == game_menu.END_DIALOG:
            game._current_dialog = None
            cmd = "look"
        try:
            last_output = game.run_turn(cmd)
        except save_manager.SaveError as e:
            last_output = f"Gagal menyimpan: {e}"
        except ContentError as e:
            last_output = f"Konten tidak valid: {e}"
        except Exception as e:  # ponytail: jaring terakhir, lanjutkan sesi
            last_output = f"Terjadi kesalahan: {e}"


def _new_game(ctx):
    print("\n=== Permainan Baru ===")
    name = input("Siapa namamu, pengembara? ").strip()
    if not name:
        name = "Pejalan Waktu"
    class_id = _class_selection(ctx)
    if class_id is None:
        print("Tidak ada kelas tersedia.")
        return
    game = Game(ctx)
    out = game.new_game(name, class_id)
    _play_intro(ctx)
    initial_output = f"{game.run_turn('look')}\n\n{out}"
    _game_loop(game, initial_output)


def _continue_game(ctx):
    import os
    import glob
    print("\n=== Lanjutkan ===")
    paths = sorted(glob.glob("saves/*.json"))
    if not paths:
        print("Tidak ada save ditemukan. Gunakan 'Permainan Baru' untuk memulai.")
        return

    def render(selection):
        lines = ["Pilih slot save:"]
        for idx, path in enumerate(paths):
            marker = "> " if idx == selection else "  "
            lines.append(f"{marker}{os.path.basename(path)}")
        return "\n".join(lines)

    idx = _menu_loop(render_fn=render, total=len(paths), hint=_NAV_HINT)
    path = paths[idx]
    game = Game(ctx)
    try:
        out = game.continue_game(path)
        initial_output = f"{game.run_turn('look')}\n\n{out}"
        _game_loop(game, initial_output)
    except save_manager.SaveError:
        if not os.path.exists(path):
            print(f"File save tidak ditemukan: {path}")
            print("Gunakan 'Permainan Baru' untuk memulai, atau periksa lokasi file save.")
        else:
            print(f"Save tidak dapat dimuat: {path} (file mungkin rusak atau tidak kompatibel)")


def main():
    try:
        animation.animate(animation.progress("Menghubungkan..."))
        ctx = GameContext(data_dir="data")
    except ContentError as e:
        print(f"Gagal memuat data: {e}")
        return 1
    try:
        last_output = ""
        while True:
            choice = _menu_selection(last_output)
            last_output = ""
            if choice == 0:
                _new_game(ctx)
            elif choice == 1:
                _continue_game(ctx)
            elif choice == 2:
                last_output = "Pengaturan belum tersedia."
            elif choice == 3:
                last_output = "Kredit: Chronicle of the Past - RPG CLI tentang perjalanan waktu."
            elif choice == 4:
                print("Sampai jumpa!")
                break
    except save_manager.SaveError as e:
        print(f"Error: {e}")
    except ContentError as e:
        print(f"Konten tidak valid: {e}")
    except KeyboardInterrupt:
        print("\nSampai jumpa!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
