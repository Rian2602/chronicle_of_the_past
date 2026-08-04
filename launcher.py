"""Chronicle of the Past - launcher entry point."""

from src.core import save_manager
from src.core.game import Game
from src.core.game_context import GameContext
from src.ui import animation, menu
from src.utils.json_loader import ContentError


def _menu_selection():
    selection = 0
    total = len(menu.MAIN_ITEMS)
    while True:
        print()
        print(menu.render_main(selection))
        print("Navigasi: 'w'/'s' untuk berpindah. Enter untuk memilih. 'q' keluar.")
        key = input("> ").strip().lower()
        if key in ("w", "k"):
            selection = (selection - 1) % total if total > 0 else 0
        elif key in ("s", "j"):
            selection = menu.arrow(selection, total)
        elif key == "q":
            raise KeyboardInterrupt
        elif key == "":
            return selection


def _class_selection(ctx):
    class_ids = list(ctx.classes.keys())
    if not class_ids:
        return None
    selection = 0
    while True:
        print()
        print("Pilih Kelas:")
        for idx, class_id in enumerate(class_ids):
            marker = "> " if idx == selection else "  "
            print(f"{marker}{ctx.classes[class_id]['name']}")
        print()
        print(menu.render_class_card(ctx.classes[class_ids[selection]]))
        print()
        print("Navigasi: 'w'/'s' untuk berpindah. Enter untuk memilih.")
        key = input("> ").strip().lower()
        if key in ("w", "k"):
            selection = (selection - 1) % len(class_ids)
        elif key in ("s", "j"):
            selection = menu.arrow(selection, len(class_ids))
        elif key == "":
            return class_ids[selection]


def _game_loop(game):
    print("\n" + "=" * 26)
    print("Mulai! Ketik 'help' untuk bantuan, 'quit' untuk keluar.")
    while True:
        try:
            text = input("\n> ").strip()
        except EOFError:
            print("\nSampai jumpa!")
            return
        if not text:
            continue
        if text.lower() in ("quit", "keluar", "exit"):
            if getattr(game, "_combat", None) is not None:
                answer = input(
                    "Kamu sedang bertarung. Keluar tanpa menyimpan? (y/n) "
                ).strip().lower()
                if answer not in ("y", "ya"):
                    continue
            print("Sampai jumpa!")
            return
        try:
            print(game.run_turn(text))
        except save_manager.SaveError as e:
            print(f"Gagal menyimpan: {e}")
        except ContentError as e:
            print(f"Konten tidak valid: {e}")
        except Exception as e:  # ponytail: jaring terakhir, lanjutkan sesi
            print(f"Terjadi kesalahan: {e}")


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
    print("\n" + game.new_game(name, class_id))
    _game_loop(game)


def _continue_game(ctx):
    import os
    print("\n=== Lanjutkan ===")
    path = input("Lokasi file save (mis. saves/slot1.json): ").strip()
    if not path:
        path = "saves/slot1.json"
    game = Game(ctx)
    try:
        print("\n" + game.continue_game(path))
        _game_loop(game)
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
        while True:
            choice = _menu_selection()
            if choice == 0:
                _new_game(ctx)
            elif choice == 1:
                _continue_game(ctx)
            elif choice == 2:
                print("Pengaturan belum tersedia.")
            elif choice == 3:
                print("Kredit: Chronicle of the Past - RPG CLI tentang perjalanan waktu.")
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
