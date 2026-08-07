"""Test engine dialog data-driven (GDD §12.5) — load, state machine, aksi."""

import json
import random
from pathlib import Path

from src.core.game_loop import GameSession
from src.core.input import Command
from src.core.state import GameState
from src.engine.dialog import (
    apply_actions,
    find_dialog,
    get_node,
    load_dialogs,
    visible_choices,
)
from src.engine.event import EventResult
from src.models.player import Player


def _session(tmp_path) -> GameSession:
    """Sesi dengan rng deterministik dan folder save sementara."""
    return GameSession(save_dir=tmp_path, rng=random.Random(7))


def _dispatch(session: GameSession, raw: str) -> list[str]:
    """Parse + kirim perintah; kembalikan pesan."""
    command = Command(name=raw.split()[0], args=tuple(raw.split()[1:]), raw=raw)
    return session.dispatch(command)


DIALOG_DATA = {
    "id": "dialog_elder_mao_1",
    "npc": "elder_mao",
    "nodes": {
        "start": {
            "text": "Apa kamu sudah siap memulai jalan kultivasimu?",
            "choices": [
                {
                    "text": "Saya siap, Guru.",
                    "next": "ready",
                    "requires_flag": None,
                    "actions": [
                        {
                            "kind": "change_reputation",
                            "faction": "court",
                            "delta": -5,
                        }
                    ],
                },
                {"text": "Beri saya waktu.", "next": None},
                {
                    "text": "Ada rahasia yang ingin kutanyakan.",
                    "next": "secret",
                    "requires_flag": "path_unlocked_sword",
                },
            ],
        },
        "ready": {
            "text": "Bagus. Mulailah bermeditasi.",
            "choices": [
                {
                    "text": "[Tinggalkan ruangan]",
                    "next": None,
                    "actions": [{"kind": "start_quest", "id": "quest101"}],
                }
            ],
        },
        "secret": {"text": "Itu urusan masa lalu.", "choices": []},
    },
}


def _state() -> GameState:
    """State kosong untuk pengujian engine dialog."""
    return GameState(player=Player(name="Akar"))


def _tulis_dialog(tmp_path: Path) -> Path:
    """Tulis satu file dialog uji; kembalikan direktori data."""
    (tmp_path / "dialog_elder_mao_1.json").write_text(
        json.dumps(DIALOG_DATA, ensure_ascii=False), encoding="utf-8"
    )
    return tmp_path


def test_load_dialogs_membaca_file_json(tmp_path):
    """load_dialogs memuat semua file dialog keyed by id."""
    data_dir = _tulis_dialog(tmp_path)
    dialogs = load_dialogs(data_dir)
    assert "dialog_elder_mao_1" in dialogs
    assert dialogs["dialog_elder_mao_1"]["npc"] == "elder_mao"


def test_get_node_mengambil_node_yang_ada(tmp_path):
    """get_node mengembalikan dict node; KeyError untuk id tak dikenal."""
    data_dir = _tulis_dialog(tmp_path)
    dialog = load_dialogs(data_dir)["dialog_elder_mao_1"]
    node = get_node(dialog, "start")
    assert node["text"].startswith("Apa kamu")
    try:
        get_node(dialog, "tidak_ada")
    except KeyError:
        pass
    else:
        raise AssertionError("get_node harus KeyError untuk node tak dikenal")


def test_find_dialog_memilih_dialog_belum_selesai(tmp_path):
    """find_dialog memilih dialog untuk NPC yang belum pernah selesai."""
    data_dir = _tulis_dialog(tmp_path)
    dialogs = load_dialogs(data_dir)
    state = _state()
    found = find_dialog(dialogs, "elder_mao", state)
    assert found is not None
    assert found["id"] == "dialog_elder_mao_1"
    # Setelah selesai (talked_<id>), dialog tidak dipilih lagi (once).
    state.flags["talked_dialog_elder_mao_1"] = True
    assert find_dialog(dialogs, "elder_mao", state) is None


def test_visible_choices_menyaring_requires_flag(tmp_path):
    """Pilihan dengan requires_flag tak terpenuhi tidak ditampilkan."""
    data_dir = _tulis_dialog(tmp_path)
    dialog = load_dialogs(data_dir)["dialog_elder_mao_1"]
    state = _state()
    choices = visible_choices(get_node(dialog, "start"), state)
    texts = [choice["text"] for choice in choices]
    assert "Ada rahasia" not in texts
    assert len(choices) == 2
    # Flag terpenuhi -> pilihan rahasia muncul.
    state.flags["path_unlocked_sword"] = True
    choices = visible_choices(get_node(dialog, "start"), state)
    assert any("Ada rahasia" in choice["text"] for choice in choices)


def test_apply_actions_mengeksekusi_aksi_event(tmp_path):
    """Aksi pilihan dialog dieksekusi via event apply (format §15.3)."""
    data_dir = _tulis_dialog(tmp_path)
    dialog = load_dialogs(data_dir)["dialog_elder_mao_1"]
    state = _state()
    result = EventResult()
    choice = get_node(dialog, "start")["choices"][0]
    apply_actions(choice["actions"], state, result, "dialog_elder_mao_1")
    assert state.reputation["court"] == -5


def test_talk_elder_mao_memulai_dialog_bercabang(tmp_path):
    """Talk ke NPC ber-dialog: tampilkan teks + pilihan bernomor, set flag."""
    session = _session(tmp_path)
    session.new_game("Akar")
    lines = _dispatch(session, "talk elder_mao")
    assert session.state.flags["talked_elder_mao"] is True
    assert any("siap memulai jalan" in line for line in lines)
    assert any("[1]" in line for line in lines)
    pending = session.state.flags.get("pending_dialog")
    assert pending is not None
    assert pending["dialog_id"] == "dialog_elder_mao_1"


def test_choose_memindahkan_node_dan_mengeksekusi_aksi(tmp_path):
    """Choose 1: aksi change_reputation jalan + node pindah ke 'ready'."""
    session = _session(tmp_path)
    session.new_game("Akar")
    _dispatch(session, "talk elder_mao")
    lines = _dispatch(session, "choose 1")
    assert session.state.reputation["court"] == -5
    assert any("mulailah bermeditasi" in line.lower() for line in lines)
    pending = session.state.flags["pending_dialog"]
    assert pending["node"] == "ready"


def test_choose_mengakhiri_dialog_dan_set_flag_once(tmp_path):
    """Choose dengan next null: dialog selesai, flag talked_<id> diset."""
    session = _session(tmp_path)
    session.new_game("Akar")
    _dispatch(session, "talk elder_mao")
    _dispatch(session, "choose 1")  # -> ready
    _dispatch(session, "choose 1")  # -> next null -> selesai
    assert session.state.flags["talked_dialog_elder_mao_1"] is True
    assert "pending_dialog" not in session.state.flags


def test_dialog_selesai_tidak_terulang_saat_talk_lagi(tmp_path):
    """Dialog 1 sekali jalan: talk berikutnya lanjut ke dialog 2 (Arc 1).

    Setelah `dialog_elder_mao_1` selesai, `find_dialog` memilih dialog
    berikutnya yang belum selesai (`dialog_elder_mao_2`) — bukan mengulang
    dialog 1, bukan fallback statis.
    """
    session = _session(tmp_path)
    session.new_game("Akar")
    _dispatch(session, "talk elder_mao")
    _dispatch(session, "choose 1")
    _dispatch(session, "choose 1")
    lines = _dispatch(session, "talk elder_mao")
    # Dialog 1 tidak terulang (flag once sudah diset), lanjut dialog 2.
    pending = session.state.flags.get("pending_dialog")
    assert pending is not None
    assert pending["dialog_id"] == "dialog_elder_mao_2"
    assert any("Sesepuh Mao" in line for line in lines)


def test_choose_validasi_nomor(tmp_path):
    """Choose nomor tak valid: pesan jelas, state dialog tidak berubah."""
    session = _session(tmp_path)
    session.new_game("Akar")
    _dispatch(session, "talk elder_mao")
    lines = _dispatch(session, "choose 9")
    assert any("tidak valid" in line for line in lines)
    assert session.state.flags["pending_dialog"]["node"] == "start"


# ---------------------------------------------------------------------------
# Data Dialog Arc 1 (TASK Arc 1) — konten data-driven di data/dialogues/
# ---------------------------------------------------------------------------

DIALOGUE_DIR = Path(__file__).resolve().parents[1] / "data" / "dialogues"

REQUIRED_ARC1_DIALOGS = {
    "dialog_elder_mao_2",
    "dialog_lin_wei_1",
    "dialog_penjaga_makam_1",
}


def test_arc1_dialog_lengkap_di_data():
    """Dialog kunci Arc 1 tersedia di data/dialogues/ (TASK Arc 1)."""
    dialogs = load_dialogs(DIALOGUE_DIR)
    missing = REQUIRED_ARC1_DIALOGS - set(dialogs)
    assert not missing, f"dialog Arc 1 belum ada: {sorted(missing)}"


def test_dialog_elder_mao_2_terikat_quest101():
    """Dialog lanjutan Mao memakai requires_flag quest101_done (TASK)."""
    dialog = load_dialogs(DIALOGUE_DIR)["dialog_elder_mao_2"]
    start = get_node(dialog, "start")
    required = [
        c.get("requires_flag")
        for c in start["choices"]
        if c.get("requires_flag")
    ]
    assert "quest101_done" in required
    # Setidaknya satu aksi nyata terpasang pada pilihan lanjutan.
    all_actions = [
        a
        for node in dialog["nodes"].values()
        for c in node.get("choices", [])
        for a in c.get("actions", [])
    ]
    assert all_actions, "dialog_elder_mao_2 tanpa aksi event"


def test_talk_lin_wei_memulai_dialog_lore(tmp_path):
    """Talk ke Lin Wei memulai dialog lore (bukan fallback statis)."""
    session = _session(tmp_path)
    session.new_game("Akar")
    lines = _dispatch(session, "talk lin_wei")
    pending = session.state.flags.get("pending_dialog")
    assert pending is not None
    assert pending["dialog_id"] == "dialog_lin_wei_1"
    assert any("Lin Wei" in line for line in lines)


def test_penjaga_makam_dialog_ada_dan_grimdark():
    """Dialog bos pra-pertarungan memakai nada grimdark (AGENTS §8)."""
    dialog = load_dialogs(DIALOGUE_DIR)["dialog_penjaga_makam_1"]
    start = get_node(dialog, "start")
    assert start["text"]
    # Lore entitas kuno tersebar di graf (start atau node lanjutan).
    all_text = " ".join(
        node["text"] for node in dialog["nodes"].values()
    ).lower()
    assert "entitas" in all_text or "kuno" in all_text
    # Ujung dialog (next: null) ada — tidak ada jalan keluar mudah.
    assert any(
        c.get("next") is None
        for node in dialog["nodes"].values()
        for c in node.get("choices", [])
    )


def test_dialog_keputusan_kunci_menambah_ending_points():
    """Pilihan keputusan kunci memuat aksi add_ending_points valid (§21.1)."""
    import json
    from pathlib import Path

    dialogues_dir = Path(__file__).resolve().parents[1] / "data" / "dialogues"
    for dialog_id in [
        "dialog_elder_mao_1",
        "dialog_fang_yue_1",
        "dialog_kestrel_1",
        "dialog_sera_ember_1",
        "dialog_inquisitor_vega_1",
        "dialog_warden_kai_1",
        "dialog_the_voice_1",
    ]:
        raw = json.loads(
            (dialogues_dir / f"{dialog_id}.json").read_text(encoding="utf-8")
        )
        found = False
        for node in raw["nodes"].values():
            for choice in node.get("choices", []):
                for action in choice.get("actions", []):
                    if action.get("kind") == "add_ending_points":
                        assert action["path"] in {"defy", "seal", "reconcile"}
                        found = True
        assert found, f"{dialog_id}: tidak ada keputusan kunci ending"


def test_keputusan_kunci_menambah_poin_saat_dieksekusi():
    """Aksi add_ending_points benar-benar menambah poin saat dieksekusi.

    Bukti runtime (§21.1): pilihan keputusan kunci the_voice menambah 15
    poin ke jalur defy — bukan hanya ada di data.
    """
    dialogues_dir = Path(__file__).resolve().parents[1] / "data" / "dialogues"
    dialog = load_dialogs(dialogues_dir)["dialog_the_voice_1"]
    state = _state()
    result = EventResult()
    choice = get_node(dialog, "start")["choices"][0]
    apply_actions(choice["actions"], state, result, "dialog_the_voice_1")
    assert state.ending_points["defy"] == 15
