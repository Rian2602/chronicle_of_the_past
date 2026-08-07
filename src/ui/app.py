"""UI Textual — Chronicle of the Past (GDD §14.1).

App adalah shell tipis: semua logika di GameSession (diuji penuh).
Navigasi murni panah ↑↓←→ + Enter + klik mouse — tanpa mengetik
perintah. Menu aksi (OptionList) diisi data-driven dari
``GameSession.menu_actions()``; pertarungan & dialog berjalan sebagai
mode dalam GameScreen yang sama (satu layar, konten beralih).
"""

from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    Button,
    Collapsible,
    Footer,
    Header,
    Input,
    OptionList,
    ProgressBar,
    RichLog,
    Static,
    TabbedContent,
    TabPane,
)
from textual.widgets.option_list import Option

from src.core.game_loop import BattleFrame, GameSession, make_bar
from src.core.input import Command, CommandError, parse_command
from src.core.save import AUTOSAVE, SLOTS, slot_exists


class MainMenuScreen(Screen):
    """Menu utama: mulai baru, lanjutkan, muat save, keluar."""

    BINDINGS = [
        ("n", "new_game", "Mulai Baru"),
        ("c", "resume_game", "Lanjutkan"),
        ("l", "load_game", "Muat Save"),
        ("q", "quit_app", "Keluar"),
    ]

    def compose(self) -> ComposeResult:
        """Susun judul dan tombol menu.

        Tombol Lanjutkan selalu ada tapi disembunyikan bila tidak ada
        sesi berjalan (di-sync on_mount & on_screen_resume) — dengan
        begini Escape dari game langsung memunculkannya tanpa re-compose.
        """
        with Vertical(id="menu"):
            yield Static("[bold gold3]Chronicle of the Past[/]", id="title")
            yield Static(
                "RPG teks fantasi gelap dengan sistem kultivasi.",
                id="tagline",
            )
            yield Button("Mulai Baru (n)", id="new", variant="primary")
            yield Button("Lanjutkan (c)", id="resume")
            yield Button("Muat Save (l)", id="load")
            yield Button("Keluar (q)", id="quit")

    def on_mount(self) -> None:
        """Sinkronkan tombol Lanjutkan saat menu pertama kali tampil."""
        self._sync_resume_button()

    def on_screen_resume(self) -> None:
        """Saat menu di-reveal lagi (mis. Escape dari game): sinkronkan."""
        self._sync_resume_button()

    def _sync_resume_button(self) -> None:
        """Tampilkan tombol Lanjutkan hanya saat ada sesi berjalan."""
        resume = self.query_one("#resume", Button)
        active = self.app.session.state is not None
        resume.display = active
        resume.disabled = not active

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Teruskan klik tombol ke aksi yang sama dengan key binding."""
        if event.button.id == "new":
            self.action_new_game()
        elif event.button.id == "resume":
            self.action_resume_game()
        elif event.button.id == "load":
            self.action_load_game()
        elif event.button.id == "quit":
            self.action_quit_app()

    def action_new_game(self) -> None:
        """Buka layar input nama."""
        self.app.push_screen(NameScreen())

    def action_resume_game(self) -> None:
        """Lanjutkan sesi yang masih berjalan (state in-memory).

        Escape dari GameScreen tidak membuang sesi — tombol ini kembali
        ke permainan tanpa reload, mempertahankan seluruh state.
        """
        if self.app.session.state is None:
            self.notify(
                "Tidak ada permainan yang sedang berjalan.", severity="warning"
            )
            return
        # BUG-17: teruskan riwayat log sesi agar narasi tidak hilang.
        self.app.push_screen(GameScreen(initial_log=list(self.app.log_history)))

    def action_load_game(self) -> None:
        """Buka pemilih slot (save1-3 + autosave, GDD §19)."""
        self.app.push_screen(SlotPickerScreen(self.app.session.save_dir))

    def action_quit_app(self) -> None:
        """Keluar dari aplikasi."""
        self.app.exit()


class SlotPickerScreen(Screen):
    """Pemilih slot save (GDD §19): hanya slot yang ada + kembali."""

    BINDINGS = [("escape", "back", "Kembali")]

    def __init__(self, save_dir: Path) -> None:
        """Simpan direktori save untuk mengecek slot yang tersedia."""
        super().__init__()
        self._save_dir = save_dir

    def compose(self) -> ComposeResult:
        """Susun judul dan satu tombol per slot yang tersedia."""
        with Vertical(id="slot-box"):
            yield Static("Muat Save — pilih slot:", id="slot-title")
            for slot in (*SLOTS, AUTOSAVE):
                if slot_exists(slot, self._save_dir):
                    label = "Autosave" if slot == AUTOSAVE else slot.upper()
                    yield Button(label, id=f"slot-{slot}")
            yield Button("Kembali", id="slot-back")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Klik slot -> muat + buka game; Kembali -> pop screen."""
        if event.button.id == "slot-back":
            self.app.pop_screen()
            return
        slot = event.button.id.removeprefix("slot-")
        messages = self.app.session.load(slot)
        if self.app.session.state is not None:
            # BUG-17: muat save = sesi baru dari disk; riwayat dimulai
            # dari pesan hasil muat (bukan sisa sesi in-memory lama).
            self.app.log_history = list(messages)
            self.app.pop_screen()
            self.app.push_screen(GameScreen(initial_log=messages))
        else:
            self.notify(" ".join(messages), severity="error")

    def action_back(self) -> None:
        """Kembali ke menu utama tanpa memuat apa pun."""
        self.app.pop_screen()


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
        # BUG-17: mulai baru = riwayat log kosong.
        self.app.log_history = []
        self.app.pop_screen()
        self.app.push_screen(GameScreen())


class GameScreen(Screen):
    """Layar permainan no-typing: navigasi via OptionList & tombol.

    Satu layar dengan tiga mode (dunia / battle / dialog); konten panel
    beralih mengikuti ``GameSession``. Mode battle dipicu ``in_battle``;
    mode dialog dipicu flag ``pending_dialog``.
    """

    BINDINGS = [
        ("escape", "back_to_menu", "Menu Utama"),
    ]

    def __init__(self, initial_log: list[str] | None = None) -> None:
        """Simpan baris log awal (mis. pesan hasil muat save)."""
        super().__init__()
        self._initial_log = list(initial_log or [])
        # Stack sub-menu: daftar aksi induk saat menelusuri sub-menu.
        self._menu_stack: list[list[dict]] = []
        self._current_menu: list[dict] = []

    def compose(self) -> ComposeResult:
        """Susun sidebar kiri, HUD, tab konten, menu aksi, sidebar kanan."""
        yield Header(show_clock=True)
        with Horizontal(id="main-row"):
            with Vertical(id="nav-col"):
                yield Button("🎒\nTas", id="nav-tas")
                yield Button("📜\nQuest", id="nav-quest")
                yield Button("👥\nTim", id="nav-tim")
                yield Button("⚡\nKultiv", id="nav-kultiv")
                yield Button("💥\nBreak", id="nav-break")
                yield Button("💾\nSimpan", id="nav-simpan")
            with Vertical(id="center-col"):
                yield Static("", id="hud")
                with Horizontal(id="hud-bars"):
                    yield Static("HP", id="hp-label")
                    # BUG-20 (FIXED): show_eta=False agar bar tidak
                    # menampilkan placeholder '--:--:--' di kolom sempit.
                    yield ProgressBar(
                        id="hp-bar", show_percentage=False, show_eta=False
                    )
                    yield Static("Qi", id="qi-label")
                    yield ProgressBar(
                        id="qi-bar", show_percentage=False, show_eta=False
                    )
                yield Static("", id="combat-header")
                yield Static("", id="enemy")
                with TabbedContent(id="content-tabs"):
                    with TabPane("📖 Story", id="tab-story"):
                        # BUG-9: RichLog tanpa max_lines; log sesi panjang bisa
                        # menurunkan performa. Upgrade: set max_lines (mis. 500)
                        # bila terukur melambat di battle massal/sesi sangat
                        # panjang.
                        # BUG-16: min-height log ditangani via CSS (#game-log
                        # min-height:5) — Textual 8.2.8 tidak menerima argumen
                        # min_height di konstruktor RichLog.
                        yield RichLog(id="game-log", markup=True)
                    with TabPane("🧠 Memory", id="tab-memory"):
                        yield RichLog(id="memory-log", markup=True)
                    with TabPane("🗺 Map", id="tab-map"):
                        yield Static("", id="map-panel")
                yield OptionList(id="dlg-choices")
                yield OptionList(id="actions")
                with Horizontal(id="action-row"):
                    yield Button("⚡ Kultivasi", id="act-cultivate")
                    yield Button("🌙 Istirahat", id="act-rest")
                    yield Button("🗺 Peta", id="act-map")
            with Vertical(id="side-col"):
                yield Collapsible(
                    Static("", id="panel-quest"),
                    title="📜 Quest",
                    id="col-quest",
                )
                yield Collapsible(
                    Static("", id="panel-party"),
                    title="👥 Party",
                    id="col-party",
                )
        yield Footer()

    def on_mount(self) -> None:
        """Isi log awal, terapkan layout responsif, muat ulang panel."""
        log = self.query_one("#game-log", RichLog)
        for line in self._initial_log:
            log.write(line + "\n")
        self._apply_compact_layout()
        self._refresh()

    def on_resize(self, _event) -> None:
        """Resize terminal: terapkan ulang layout responsif."""
        self._apply_compact_layout()

    def _apply_compact_layout(self) -> None:
        """Layout responsif untuk terminal kecil (BUG-19/20, FIXED).

        Terminal pendek (tinggi <= 32) merampingkan area tetap sehingga
        menu aksi battle tidak terpotong footer; terminal sempit (lebar
        <= 100) menyembunyikan sidebar kanan agar HUD tidak me-wrap.
        Textual 8.2.8 tidak mendukung @media query, jadi pasang kelas
        Screen dari Python. Dipanggil saat mount dan setiap resize.
        """
        # Batas short 33 (bukan 32): di tinggi 33 layout default terukur
        # masih memotong action-row 1 baris (dead zone, putaran 4).
        self.set_class(self.size.height <= 33, "short-screen")
        self.set_class(self.size.width <= 100, "narrow-screen")

    # ------------------------------------------------------------------
    # Navigasi & aksi
    # ------------------------------------------------------------------
    def on_option_list_option_selected(
        self, event: OptionList.OptionSelected
    ) -> None:
        """Pilih opsi: dialog -> choose; menu aksi -> sub/command."""
        if event.option_list.id == "dlg-choices":
            self._choose_dialog_option(event.option.id)
            return
        self._select_action(event.option.id)

    def _select_action(self, option_id: str) -> None:
        """Jalankan aksi menu: buka sub-menu atau eksekusi command."""
        action = next(
            (a for a in self._current_menu if a["id"] == option_id), None
        )
        if action is None:
            return
        if action.get("sub"):
            self._menu_stack.append(self._current_menu)
            self._current_menu = list(action["sub"])
            self._populate_actions(self._current_menu)
            return
        self._run_command(action["command"])

    def _choose_dialog_option(self, option_id: str) -> None:
        """Pilih nomor pilihan dialog (choose <nomor>)."""
        session = self.app.session
        if session.state is None:
            return
        pending = session.state.flags.get("pending_dialog")
        if not pending:
            return
        self._run_command(f"choose {option_id}")

    def _populate_actions(self, items: list[dict]) -> None:
        """Isi OptionList #actions dari daftar aksi data-driven."""
        actions = self.query_one("#actions", OptionList)
        options = []
        for item in items:
            icon = item.get("icon", "")
            label = item.get("label", item["id"])
            prompt = f"{icon} {label}" if icon else label
            if item.get("sub"):
                prompt += " ▸"
            options.append(Option(prompt, id=item["id"]))
        actions.set_options(options)
        # BUG-15: set_options me-reset highlighted ke None -> Enter pada
        # opsi pertama tidak merespons. Auto-highlight opsi pertama agar
        # navigasi satu ketukan, bukan dua (regresi TUI hunt).
        if options:
            actions.highlighted = 0
        # BUG-19/20 (FIXED): visibilitas menu aksi & HUD di 80x24
        # ditangani kelas responsif _apply_compact_layout.

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Sidebar kiri & tombol aksi lokasi -> command terkait."""
        mapping = {
            "nav-tas": "inventory",
            "nav-quest": "quests",
            "nav-tim": "party",
            "nav-kultiv": "cultivate",
            "nav-break": "breakthrough",
            "nav-simpan": "save",
            "act-cultivate": "cultivate",
            "act-rest": "rest",
            "act-map": "map",
        }
        raw = mapping.get(event.button.id)
        if raw:
            self._run_command(raw)

    def _remember_log(self, line: str) -> None:
        """Catat baris log untuk dipulihkan saat resume (BUG-17).

        GameScreen baru (Lanjutkan) memakai ``app.log_history`` sebagai
        initial_log; tanpa ini narasi sesi hilang saat escape ke menu.
        Batas 200 baris menjaga memori tetap kecil (ponytail: hubungkan
        ke RichLog max_lines BUG-9 bila sesi jauh lebih panjang).
        """
        history = self.app.log_history
        history.append(line)
        if len(history) > 200:
            del history[: len(history) - 200]

    def _run_command(self, raw: str) -> None:
        """Eksekusi command: battle_step saat bertarung, dispatch dunia."""
        session = self.app.session
        log = self.query_one("#game-log", RichLog)
        if session.in_battle:
            self._battle_raw(raw, log)
            return
        try:
            command = parse_command(raw)
        except CommandError as exc:
            log.write(f"[red]{exc}[/]\n")
            self._remember_log(f"[red]{exc}[/]")
            return
        if command is None:
            return
        for line in session.dispatch(command):
            log.write(line + "\n")
            self._remember_log(line)
        self._refresh()
        if session.quit_requested:
            self.app.exit()

    def _battle_raw(self, raw: str, log: RichLog) -> None:
        """Satu langkah pertarungan dari aksi menu (GDD §18.3)."""
        session = self.app.session
        if raw == "quit":
            for line in session.dispatch(
                Command(name="quit", args=(), raw="quit")
            ):
                log.write(line + "\n")
                self._remember_log(line)
            self.app.exit()
            return
        if raw == "observe":
            frame = session.battle_frame()
            log.write("[cyan]Amatan:[/]\n")
            self._remember_log("[cyan]Amatan:[/]")
            for line in self._enemy_lines(frame):
                log.write(line + "\n")
                self._remember_log(line)
            self._refresh()
            return
        frame = session.battle_step(raw)
        # Battle mengganti isi log (bukan menumpuk): sinkronkan riwayat
        # agar resume menampilkan frame yang sama dengan layar terakhir.
        log.clear()
        self.app.log_history.clear()
        for line in frame.log:
            log.write(line + "\n")
            self._remember_log(line)
        if frame.error:
            log.write(f"[red]{frame.error}[/]\n")
            self._remember_log(f"[red]{frame.error}[/]")
        self._refresh()

    # ------------------------------------------------------------------
    # Render panel
    # ------------------------------------------------------------------
    def _refresh(self) -> None:
        """Muat ulang panel sesuai mode: dunia / battle / dialog."""
        session = self.app.session
        if session.state is None:
            return
        self._refresh_hud()
        self._refresh_sidebar()
        self._refresh_memory_and_map()
        if session.in_battle:
            self._refresh_battle()
        elif session.state.flags.get(
            "pending_dialog"
        ) or session.state.flags.get("pending_choice"):
            self._refresh_dialog()
        else:
            self._refresh_world()

    def _refresh_hud(self) -> None:
        """HUD: nama/lokasi/insight (status_lines) + bar HP/Qi."""
        session = self.app.session
        lines = session.status_lines()
        # BUG-20 (FIXED): di terminal pendek & sempit HUD dipangkas satu
        # baris (Insight/Gold/Meridian — tetap bisa dilihat via aksi
        # Status) agar seluruh panel battle muat di 80x24; layar lebar
        # (mis. 120x30) tetap 4 baris karena ada ruang.
        if self.has_class("short-screen") and self.has_class("narrow-screen"):
            lines = lines[:3]
        self.query_one("#hud", Static).update("\n".join(lines))
        player = session.state.player
        hp = session._ally.hp if session._ally is not None else player.hp
        qi = session._ally.qi if session._ally is not None else player.qi
        self.query_one("#hp-bar", ProgressBar).progress = (
            hp / player.hp_max if player.hp_max else 0
        )
        self.query_one("#qi-bar", ProgressBar).progress = (
            qi / player.qi_max if player.qi_max else 0
        )

    def _refresh_sidebar(self) -> None:
        """Sidebar kanan: quest aktif + komposisi tim (read-only)."""
        session = self.app.session
        quest_text = "\n".join(session.quest_lines())
        self.query_one("#panel-quest", Static).update(
            f"[bold gold3]Quest[/]\n{quest_text}"
        )
        self.query_one("#panel-party", Static).update(
            "\n".join(session.party_lines())
        )

    def _refresh_memory_and_map(self) -> None:
        """Tab Memory & Map diisi ringkas (read-only, tanpa efek)."""
        session = self.app.session
        memory_log = self.query_one("#memory-log", RichLog)
        memory_log.clear()
        for line in session._cmd_memories(
            Command(name="memories", args=(), raw="memories")
        ):
            memory_log.write(line + "\n")
        map_text = "\n".join(
            session._cmd_map(Command(name="map", args=(), raw="map"))
        )
        self.query_one("#map-panel", Static).update(map_text)

    def _refresh_world(self) -> None:
        """Mode dunia: menu aksi eksplorasi; panel battle/dialog kosong."""
        session = self.app.session
        self.query_one("#combat-header", Static).update("")
        self.query_one("#enemy", Static).update("")
        self.query_one("#dlg-choices", OptionList).display = False
        self._current_menu = session.menu_actions()
        self._menu_stack = []
        self._populate_actions(self._current_menu)
        self.query_one("#actions", OptionList).display = True
        self.query_one("#actions", OptionList).focus()

    def _refresh_battle(self) -> None:
        """Mode battle: log, header giliran, panel musuh, menu aksi."""
        session = self.app.session
        frame = session.battle_frame()
        self.query_one("#dlg-choices", OptionList).display = False
        turn = frame.active_ally_name or "—"
        self.query_one("#combat-header", Static).update(
            f"[bold red]⚔ PERTARUNGAN[/] — Giliran [gold3]{turn}[/]"
        )
        panel = "\n".join(self._enemy_lines(frame))
        self.query_one("#enemy", Static).update(panel)
        self._current_menu = session.menu_actions()
        self._menu_stack = []
        self._populate_actions(self._current_menu)
        self.query_one("#actions", OptionList).display = True
        self.query_one("#actions", OptionList).focus()

    def _refresh_dialog(self) -> None:
        """Mode keputusan: pilihan dialog/event di #dlg-choices (§12.5, §15.3).

        Satu panel untuk dua sumber keputusan: percakapan bercabang
        (``pending_dialog``) dan prompt_choice event (``pending_choice``)
        — keduanya dijawab lewat klik (choose <key>).
        """
        session = self.app.session
        is_choice = bool(session.state.flags.get("pending_choice"))
        title = "⚖ KEPUTUSAN" if is_choice else "💬 PERCAKAPAN"
        self.query_one("#combat-header", Static).update(
            f"[bold cyan]{title}[/]"
        )
        self.query_one("#enemy", Static).update("")
        self.query_one("#actions", OptionList).display = False
        choices = session.dialog_choices()
        dlg = self.query_one("#dlg-choices", OptionList)
        dlg.set_options(
            [
                Option(f"{choice['id']}. {choice['text']}", id=choice["id"])
                for choice in choices
            ]
        )
        # BUG-15: set_options me-reset highlighted ke None -> Enter pada
        # opsi pertama tidak merespons. Auto-highlight opsi pertama agar
        # navigasi satu ketukan, bukan dua (regresi TUI hunt).
        if choices:
            dlg.highlighted = 0
        dlg.display = True
        dlg.focus()

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
        """Escape: keluar sub-menu dulu, lalu kembali ke menu utama."""
        if self._menu_stack:
            self._current_menu = self._menu_stack.pop()
            self._populate_actions(self._current_menu)
            return
        self.app.pop_screen()


class ChronicleApp(App):
    """Aplikasi utama Chronicle of the Past."""

    TITLE = "Chronicle of the Past"
    CSS = """
    Screen { background: #0F0F0F; color: #E8E8E8; }
    #menu, #name-box, #slot-box {
        align: center middle;
        width: 60;
        padding: 1 2;
        border: round #D4AF37;
    }
    #title { text-align: center; text-style: bold; color: #D4AF37; }
    #tagline, #prompt, #slot-title { text-align: center; }
    Button { margin-top: 1; }
    #menu Button, #name-box Button, #slot-box Button { width: 100%; }

    /* Layout utama */
    #main-row { height: 1fr; }
    #nav-col {
        width: 14;
        border-right: solid #303030;
        background: #121212;
        padding: 0 1;
    }
    #nav-col Button {
        width: 100%;
        height: 4;
        min-height: 4;
        border: none;
        background: #1a1a1a;
        color: #9e9e9e;
        margin-top: 1;
    }
    #nav-col Button:hover, #nav-col Button:focus {
        background: #252525;
        color: #D4AF37;
        border: none;
    }
    #center-col { width: 3fr; }
    #side-col {
        width: 26;
        border-left: solid #303030;
        background: #121212;
    }

    /* HUD */
    #hud {
        background: #1a1a1a;
        padding: 0 1;
        border-bottom: solid #303030;
    }
    #hud-bars { height: 1; padding: 0 1; background: #161616; }
    #hp-label { color: #e53935; width: 3; }
    #qi-label { color: #00bcd4; width: 3; }
    #hp-bar { color: #e53935; }
    #qi-bar { color: #00bcd4; }

    /* Battle & dialog header */
    #combat-header {
        background: #1a0000;
        padding: 0 1;
        border-bottom: solid #4a0000;
    }
    #enemy {
        background: #110000;
        padding: 0 1;
        border-bottom: solid #4a0000;
        color: #ff5555;
    }

    /* Konten tab. BUG-16: min-height menjaga log terbaca di terminal
       pendek (terbukti tmux 120x30); trade-off lama: di bawah 15 baris
       menu aksi yang terpotong, bukan log — kini tertangani kelas
       responsif .short-screen (BUG-19/20, FIXED) yang merampingkan
       area tetap agar menu aksi battle tetap terlihat di 80x24. */
    #content-tabs { height: 1fr; min-height: 8; }
    #game-log { height: 1fr; min-height: 5; background: #0F0F0F; }
    #memory-log { height: 1fr; min-height: 5; background: #0F0F0F; }
    #map-panel { height: 1fr; min-height: 5; padding: 1; color: #00bcd4; }

    /* Sidebar kanan */
    #side-col Collapsible { margin-top: 1; }
    #panel-quest, #panel-party {
        padding: 0 1;
        background: #121212;
    }

    /* Menu aksi */
    #actions, #dlg-choices {
        height: 10;
        border: tall #303030;
        background: #151515;
    }
    #actions:focus, #dlg-choices:focus { border: tall #D4AF37; }
    #action-row { height: 5; padding: 0 1; }
    #action-row Button {
        width: 1fr;
        background: #1a1a1a;
        color: #E8E8E8;
        border: solid #303030;
    }
    #action-row Button:hover, #action-row Button:focus {
        background: #252525;
        color: #D4AF37;
        border: solid #D4AF37;
    }

    /* Layout responsif terminal kecil (BUG-19/20 FIXED). Terminal pendek
       (tinggi <= 33) merampingkan area tetap sehingga 6 aksi battle
       muat utuh (height 8 = 6 opsi + border tall); terminal sempit
       (lebar <= 100) menyembunyikan sidebar kanan agar kolom tengah
       cukup lebar sehingga HUD tidak me-wrap, sekaligus menyembunyikan
       jam header (redundan dengan waktu game di HUD 'Hari X, jam HH').
       Dipasang via kelas Screen dari _apply_compact_layout (Textual
       8.2.8 tidak mendukung @media query). */
    .short-screen #content-tabs { min-height: 2; }
    .short-screen #game-log, .short-screen #memory-log { min-height: 1; }
    .short-screen #map-panel { min-height: 1; }
    .short-screen #actions, .short-screen #dlg-choices { height: 8; }
    .short-screen #action-row { height: 3; }
    .narrow-screen #side-col { display: none; }
    .narrow-screen HeaderClock { display: none; }
    Footer { background: #121212; color: #9e9e9e; }
    """

    def __init__(self, session: GameSession | None = None) -> None:
        """Terima sesi (bisa disuntikkan untuk test)."""
        super().__init__()
        self.session = session if session is not None else GameSession()
        # Riwayat log untuk resume (BUG-17): GameScreen baru saat Lanjutkan
        # memakai initial_log dari sini, bukan dari widget yang dibuang.
        self.log_history: list[str] = []

    def on_mount(self) -> None:
        """Buka menu utama saat aplikasi dimulai."""
        self.push_screen(MainMenuScreen())
