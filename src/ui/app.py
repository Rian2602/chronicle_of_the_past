"""UI Textual — Chronicle of the Past (GDD §14.1).

App adalah shell tipis: semua logika di GameSession (diuji penuh);
layar hanya meneruskan perintah dan menampilkan hasilnya.
"""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, RichLog, Static

from src.core.game_loop import BattleFrame, GameSession, make_bar
from src.core.input import Command, CommandError, parse_command


class MainMenuScreen(Screen):
    """Menu utama: mulai baru, muat save, keluar."""

    BINDINGS = [
        ("n", "new_game", "Mulai Baru"),
        ("l", "load_game", "Muat Save"),
        ("q", "quit_app", "Keluar"),
    ]

    def compose(self) -> ComposeResult:
        """Susun judul dan tombol menu."""
        with Vertical(id="menu"):
            yield Static("[bold cyan]Chronicle of the Past[/]", id="title")
            yield Static(
                "RPG teks fantasi gelap dengan sistem kultivasi.",
                id="tagline",
            )
            yield Button("Mulai Baru (n)", id="new", variant="primary")
            yield Button("Muat Save (l)", id="load")
            yield Button("Keluar (q)", id="quit")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Teruskan klik tombol ke aksi yang sama dengan key binding."""
        if event.button.id == "new":
            self.action_new_game()
        elif event.button.id == "load":
            self.action_load_game()
        elif event.button.id == "quit":
            self.action_quit_app()

    def action_new_game(self) -> None:
        """Buka layar input nama."""
        self.app.push_screen(NameScreen())

    def action_load_game(self) -> None:
        """Muat save slot 1; gagal -> notifikasi."""
        messages = self.app.session.load("save1")
        if self.app.session.state is not None:
            self.app.push_screen(GameScreen(initial_log=messages))
        else:
            self.notify(" ".join(messages), severity="error")

    def action_quit_app(self) -> None:
        """Keluar dari aplikasi."""
        self.app.exit()


class NameScreen(Screen):
    """Input nama kultivator sebelum permainan dimulai."""

    BINDINGS = [("escape", "back", "Kembali")]

    def action_back(self) -> None:
        """Kembali ke menu utama tanpa memulai permainan."""
        self.app.pop_screen()

    def compose(self) -> ComposeResult:
        """Susun prompt nama dan tombol mulai."""
        with Vertical(id="name-box"):
            yield Static("Siapa namamu, kultivator?", id="prompt")
            yield Input(placeholder="Nama (contoh: Akar)", id="name")
            yield Button("Mulai", id="start", variant="primary")

    def on_mount(self) -> None:
        """Fokuskan input nama saat layar dibuka."""
        self.query_one("#name", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Enter pada input nama memulai permainan."""
        self._start(event.value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Klik Mulai memulai permainan."""
        if event.button.id == "start":
            name_input = self.query_one("#name", Input)
            self._start(name_input.value)

    def _start(self, name: str) -> None:
        """Buat permainan baru dan buka layar game.

        Layar nama ditutup dulu agar escape dari game kembali ke menu,
        bukan ke layar nama yang basi.
        """
        self.app.session.new_game(name)
        self.app.pop_screen()
        self.app.push_screen(GameScreen())


class GameScreen(Screen):
    """Layar permainan: HUD, log, dan input perintah.

    Pertarungan berjalan di layar yang sama (mode battle): input dialihkan
    ke battle_step selama ada pertarungan aktif.
    """

    BINDINGS = [("escape", "back_to_menu", "Menu Utama")]

    def __init__(self, initial_log: list[str] | None = None) -> None:
        """Simpan baris log awal (mis. pesan hasil muat save)."""
        super().__init__()
        self._initial_log = list(initial_log or [])

    def compose(self) -> ComposeResult:
        """Susun HUD, log, sidebar quest/party, dan input perintah."""
        yield Static("", id="hud")
        yield Static("", id="enemy")
        with Horizontal(id="main-row"):
            yield RichLog(id="game-log", markup=True)
            with Vertical(id="side-col"):
                yield Static("", id="panel-quest")
                yield Static("", id="panel-party")
        yield Input(placeholder="Ketik perintah (help untuk bantuan)", id="cmd")

    def on_mount(self) -> None:
        """Isi log awal, muat HUD, dan fokuskan input perintah."""
        log = self.query_one("#game-log", RichLog)
        for line in self._initial_log:
            log.write(line + "\n")
        self._refresh()
        self.query_one("#cmd", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Parse perintah: arahkan ke battle atau dunia sesuai kondisi."""
        self.query_one("#cmd", Input).clear()
        raw = event.value
        if not raw.strip():
            return
        try:
            command = parse_command(raw)
        except CommandError as exc:
            self.query_one("#game-log", RichLog).write(f"[red]{exc}[/]\n")
            return
        if command is None:
            return
        if self.app.session.in_battle:
            self._battle_command(command)
        else:
            self._world_command(command)

    def _world_command(self, command: Command) -> None:
        """Kirim perintah dunia; tangani keluar dan mulai pertarungan."""
        session = self.app.session
        for line in session.dispatch(command):
            self.query_one("#game-log", RichLog).write(line + "\n")
        self._refresh()
        if session.quit_requested:
            self.app.exit()

    def _battle_command(self, command: Command) -> None:
        """Satu langkah pertarungan dari input pemain (GDD §18.3)."""
        session = self.app.session
        log = self.query_one("#game-log", RichLog)
        if command.name == "quit":
            # Perintah global: pemain boleh keluar kapan pun (§18.1).
            for line in session.dispatch(command):
                log.write(line + "\n")
            self.app.exit()
            return
        if command.name == "observe":
            frame = session.battle_frame()
            log.write("[cyan]Amatan:[/]\n")
            for line in self._enemy_lines(frame):
                log.write(line + "\n")
        else:
            frame = session.battle_step(self._battle_action(command))
            log.clear()
            for line in frame.log:
                log.write(line + "\n")
            if frame.error:
                log.write(f"[red]{frame.error}[/]\n")
        self._refresh()

    def _battle_action(self, command: Command) -> str:
        """Ubah perintah menjadi aksi battle: attack/defend/technique:x."""
        if command.name == "technique":
            arg = command.args[0] if command.args else ""
            return f"technique:{arg}"
        return command.name

    def _refresh(self) -> None:
        """Muat ulang HUD status, sidebar, dan panel musuh."""
        session = self.app.session
        if session.state is None:
            return
        # HUD memakai status_lines (bukan dispatch) agar tidak terblokir
        # guard battle — stat tetap terlihat selama pertarungan.
        self.query_one("#hud", Static).update("\n".join(session.status_lines()))
        # Sidebar: quest aktif + komposisi tim (read-only, tanpa efek).
        quest_text = "\n".join(session.quest_lines())
        self.query_one("#panel-quest", Static).update(
            f"[bold gold3]Quest[/]\n{quest_text}"
        )
        party_text = "\n".join(session.party_lines())
        self.query_one("#panel-party", Static).update(
            f"[bold cyan]Partai[/]\n{party_text}"
        )
        if session.in_battle:
            frame = session.battle_frame()
            panel = "\n".join(self._enemy_lines(frame))
            self.query_one("#enemy", Static).update(
                f"[yellow]PERTARUNGAN[/]\n{panel}"
            )
        else:
            self.query_one("#enemy", Static).update("")

    def _enemy_lines(self, frame: BattleFrame) -> list[str]:
        """Baris info musuh dengan bar HP visual (GDD §6.1)."""
        lines: list[str] = []
        for enemy in frame.enemies:
            bar = make_bar(enemy["hp"], enemy["hp_max"], 12)
            lines.append(
                f"[bold red]{enemy['name']}[/] HP [red]{bar}[/] "
                f"{enemy['hp']}/{enemy['hp_max']} | Qi {enemy['qi']} "
                f"| Elemen {enemy['element']}"
            )
        return lines

    def action_back_to_menu(self) -> None:
        """Kembali ke menu utama (konfirmasi simpan menyusul)."""
        self.app.pop_screen()


class ChronicleApp(App):
    """Aplikasi utama Chronicle of the Past."""

    TITLE = "Chronicle of the Past"
    CSS = """
    Screen { background: #0F0F0F; color: #E8E8E8; }
    #menu, #name-box {
        align: center middle;
        width: 60;
        padding: 1 2;
        border: round #D4AF37;
    }
    #title { text-align: center; text-style: bold; color: #D4AF37; }
    #tagline, #prompt { text-align: center; }
    Button { width: 100%; margin-top: 1; }
    #hud { background: #1a1a1a; padding: 0 1; border-bottom: solid #303030; }
    #enemy { background: #1a0000; padding: 0 1; border-bottom: solid #4a0000;
             color: #ff5555; }
    #main-row { height: 1fr; }
    #game-log { width: 2fr; border: round #D4AF37; background: #0F0F0F; }
    #side-col { width: 1fr; border-left: solid #303030; }
    #panel-quest, #panel-party {
        height: 1fr;
        padding: 0 1;
        border-bottom: solid #303030;
        background: #121212;
    }
    #cmd { border: tall #303030; background: #151515; }
    #cmd:focus { border: tall #D4AF37; }
    """

    def __init__(self, session: GameSession | None = None) -> None:
        """Terima sesi (bisa disuntikkan untuk test)."""
        super().__init__()
        self.session = session if session is not None else GameSession()

    def on_mount(self) -> None:
        """Buka menu utama saat aplikasi dimulai."""
        self.push_screen(MainMenuScreen())
