"""Chronicle of the Past - launcher entry point."""

import os
import sys

if os.name == "nt":
    import msvcrt  # Windows: baca keypress tanpa enter
else:
    import termios  # Unix: mode terminal raw untuk arrow key
    import tty

from src.core import save_manager, settings
from src.core.game import Game, GameQuit
from src.core.game_context import GameContext
from src.ui import animation, game_menu, menu, renderer, story_view
from src.utils.json_loader import ContentError

_NAV_HINT = (
    "Navigasi: \u2191/\u2193 atau w/s untuk berpindah. "
    "Enter untuk memilih. 'q' keluar."
)


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
        return _read_key_input_fallback()

    if os.name == "nt":
        try:
            return _read_key_windows()
        except OSError:
            # Git Bash / mintty: isatty() True tapi bukan console Windows
            # sungguhan — msvcrt gagal, jadi fallback ke input() biasa.
            return _read_key_input_fallback()
    return _read_key_unix()


def _read_key_input_fallback() -> str:
    """Baca satu baris input non-TTY dan petakan ke kunci navigasi."""
    line = input("> ").strip().lower()
    if line in ("w", "k"):
        return "UP"
    if line in ("s", "j"):
        return "DOWN"
    if line == "":
        return "ENTER"
    return line


def _read_key_windows() -> str:
    """Baca keypress di Windows (msvcrt); dukung arrow key & Enter."""
    ch = msvcrt.getwch()
    if ch in ("\xe0", "\x00"):  # prefix arrow key di Windows
        code = msvcrt.getwch()
        return {"H": "UP", "P": "DOWN"}.get(code, "")
    if ch in ("\r", "\n"):
        return "ENTER"
    if ch == "\x03":  # Ctrl+C
        raise KeyboardInterrupt
    if ch == "\x1b":  # ESC tunggal
        return ""
    return ch.lower()


def _read_key_unix() -> str:
    """Baca keypress di Unix (termios); dukung arrow key & Enter."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        ch = sys.stdin.read(1)
        if ch == "\x1b":  # ESC byte — mulai sequence arrow key
            ch2 = sys.stdin.read(1)
            if ch2 == "[":
                ch3 = sys.stdin.read(1)
                return {"A": "UP", "B": "DOWN"}.get(ch3, "")
            return ""  # ESC tanpa sequence yang dikenal → abaikan
        if ch in ("\r", "\n"):
            return "ENTER"
        if ch == "\x03":  # Ctrl+C
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
    """Loop menu utama; kembalikan indeks item yang dipilih."""
    total = len(menu.MAIN_ITEMS)
    return _menu_loop(
        render_fn=menu.render_main,
        total=total,
        hint=_NAV_HINT,
        screen=screen,
    )


def _apply_settings(current_settings):
    """Terapkan mode tampilan dari pengaturan ke renderer global."""
    renderer.set_render_mode(current_settings.render_mode)


def _settings_menu(current_settings, path=settings.SETTINGS_PATH):
    """Tampilkan dan terapkan pengaturan global secara langsung."""
    labels = {
        "auto": "Auto",
        "unicode": "Unicode",
        "ascii": "ASCII",
        "normal": "Normal",
        "fast": "Cepat",
        "off": "Mati",
    }
    feedback = ""
    while True:
        items = [
            ("Tampilan", "render_mode", settings.RENDER_MODES),
            ("Animasi", "animation_mode", settings.ANIMATION_MODES),
            ("Reset ke Default", None, None),
            ("Kembali", None, None),
        ]

        # Bind eksplisit: render dibuat ulang tiap iterasi loop, jadi nilai
        # default arg selalu yang terkini (lihat "Reset ke Default").
        def render(selection, items=items, current_settings=current_settings):
            lines = ["Pengaturan:"]
            for index, (label, attribute, _) in enumerate(items):
                marker = "> " if index == selection else "  "
                value = (
                    f": {labels[getattr(current_settings, attribute)]}"
                    if attribute
                    else ""
                )
                lines.append(f"{marker}{label}{value}")
            return "\n".join(lines)

        choice = _menu_loop(render, len(items), _NAV_HINT, screen=feedback)
        feedback = ""
        if choice == 3:
            return current_settings, feedback
        if choice == 2:
            current_settings = settings.Settings()
            feedback = "Pengaturan dikembalikan ke default."
        else:
            _, attribute, choices = items[choice]
            setattr(
                current_settings,
                attribute,
                settings.next_choice(
                    getattr(current_settings, attribute), choices
                ),
            )
            feedback = f"{items[choice][0]} diperbarui."
        _apply_settings(current_settings)
        try:
            settings.save_settings(current_settings, path)
            feedback += " Tersimpan."
        except settings.SettingsError as error:
            feedback += f" Gagal disimpan: {error}"


def _class_selection(ctx):
    """Pilih kelas lewat menu navigasi; kembalikan ID kelas atau None."""
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
        hint=(
            "Navigasi: \u2191/\u2193 atau w/s untuk berpindah. "
            "Enter untuk memilih."
        ),
    )
    return class_ids[idx]


def _play_intro(ctx):
    """Putar cutscene intro; Enter lanjut, 'q' lewati."""
    scenes = [s for s in ctx.scenes if s.get("id", "").startswith("intro_")]
    for scene in scenes:
        _clear_screen()
        print(story_view.render_scene(scene))
        key = _read_key()
        if key == "q":
            break
    print()


def _navigate(game, last_output: str = ""):
    """Navigasi menu game bertingkat dengan arrow key.

    Returns:
        Perintah untuk run_turn, atau None untuk keluar ke menu utama.
    """
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
    """Loop utama sesi game: navigasi menu → run_turn sampai keluar."""
    last_output = initial_output
    while True:
        try:
            cmd = _navigate(game, last_output)
        except KeyboardInterrupt:
            if (
                getattr(game, "_combat", None) is not None
                and not _confirm_quit()
            ):
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
        except GameQuit:
            print("\nSampai jumpa!")
            return
        except Exception as e:  # ponytail: jaring terakhir, lanjutkan sesi
            last_output = f"Terjadi kesalahan: {e}"


def _new_game(ctx):
    """Alur Permainan Baru: nama → kelas → intro → sesi game."""
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
    """Alur Lanjutkan: pilih slot save lalu lanjutkan sesi game."""
    print("\n=== Lanjutkan ===")
    paths = save_manager.save_paths()
    if not paths:
        print(
            "Tidak ada save ditemukan. Gunakan 'Permainan Baru' untuk memulai."
        )
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
            print(
                "Gunakan 'Permainan Baru' untuk memulai, atau "
                "periksa lokasi file save."
            )
        else:
            print(
                f"Save tidak dapat dimuat: {path} "
                "(file mungkin rusak atau tidak kompatibel)"
            )


def main():
    """Titik masuk launcher: muat pengaturan, tampilkan menu utama.

    Returns:
        Kode keluar proses (0 sukses, 1 gagal memuat data).
    """
    settings_message = ""
    try:
        try:
            current_settings = settings.load_settings()
        except settings.SettingsError as error:
            current_settings = settings.Settings()
            settings_message = (
                f"Pengaturan tidak valid; memakai default. ({error})"
            )
        _apply_settings(current_settings)
        delay = animation.delay_for(current_settings.animation_mode)
        if delay is not None:
            animation.animate(
                animation.progress("Menghubungkan..."), delay=delay
            )
        ctx = GameContext(data_dir="data")
    except ContentError as e:
        print(f"Gagal memuat data: {e}")
        return 1
    try:
        last_output = settings_message
        while True:
            choice = _menu_selection(last_output)
            last_output = ""
            if choice == 0:
                _new_game(ctx)
            elif choice == 1:
                _continue_game(ctx)
            elif choice == 2:
                current_settings, last_output = _settings_menu(current_settings)
            elif choice == 3:
                last_output = (
                    "Kredit: Chronicle of the Past - "
                    "RPG CLI tentang perjalanan waktu."
                )
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
