"""Entry point game — Chronicle of the Past.

Menampilkan judul dan status pembangunan. Logika permainan (Fase 0)
belum tersedia; launcher diperluas mengikuti roadmap GDD §23.
"""

from rich.console import Console


def main() -> int:
    """Cetak judul game dan pesan status, lalu kembalikan kode keluar 0."""
    console = Console()
    console.print("[bold cyan]Chronicle of the Past[/bold cyan]")
    console.print("RPG teks fantasi gelap dengan sistem kultivasi.")
    console.print(
        "[dim]Fase 0 (MVP) sedang dikembangkan — lihat GDD §23.[/dim]"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
