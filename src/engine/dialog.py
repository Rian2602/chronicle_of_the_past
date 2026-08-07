"""Engine dialog data-driven: percakapan bercabang (GDD §12.5).

Dialog disimpan di ``data/dialogues/`` sebagai JSON satu percakapan utuh
(graf node). Pilihan pemain mengeksekusi aksi dengan format yang sama
dengan Event Engine (§15.3) lewat ``event.apply_action`` — satu sumber
kebenaran aksi, tanpa duplikasi logika.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.core.state import GameState
from src.core.utils import load_json_dir

DIALOGUE_DIR = Path(__file__).resolve().parents[2] / "data" / "dialogues"


def load_dialogs(data_dir: Path = DIALOGUE_DIR) -> dict[str, dict[str, Any]]:
    """Muat semua dialog dari data/dialogues/ keyed by id (§12.5).

    Args:
        data_dir: Direktori berisi JSON dialog (default data/dialogues/).

    Returns:
        Mapping dialog_id -> dict dialog mentah (id, npc, nodes).
    """
    return load_json_dir(data_dir)


def find_dialog(
    dialogs: dict[str, dict[str, Any]], npc_id: str, state: GameState
) -> dict[str, Any] | None:
    """Dialog untuk NPC yang belum selesai, atau None bila tidak ada.

    Percakapan yang sudah selesai (flag ``talked_<dialog_id>``) tidak
    dipilih ulang — sifat sekali jalan (§12.5). Bila beberapa dialog
    cocok, yang pertama (urutan abjad id) menang; `ponytail:` upgrade ke
    prioritas eksplisit bila konten Arc 2 membutuhkan banyak dialog per
    NPC.

    Args:
        dialogs: Hasil ``load_dialogs``.
        npc_id: ID NPC yang diajak bicara.
        state: State pemain (untuk cek flag selesai).

    Returns:
        Dict dialog mentah, atau None bila tidak ada yang tersedia.
    """
    for dialog in dialogs.values():
        if dialog.get("npc") != npc_id:
            continue
        if state.flags.get(f"talked_{dialog['id']}"):
            continue
        return dialog
    return None


def visible_choices(
    node: dict[str, Any], state: GameState
) -> list[dict[str, Any]]:
    """Pilihan node yang bisa dipilih pemain saat ini.

    Pilihan dengan ``requires_flag`` disaring: hanya muncul jika flag
    tersebut bernilai True di state (§12.5).

    Args:
        node: Dict node dialog.
        state: State pemain.

    Returns:
        Daftar pilihan (dict) yang memenuhi syarat.
    """
    visible: list[dict[str, Any]] = []
    for choice in node.get("choices", []):
        required = choice.get("requires_flag")
        if required and not state.flags.get(required):
            continue
        visible.append(choice)
    return visible
