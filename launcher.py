"""Entry point game — Chronicle of the Past (GDD §14.1)."""

from src.ui.app import ChronicleApp


def main() -> int:
    """Jalankan aplikasi Textual dan kembalikan kode keluar 0."""
    ChronicleApp().run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
