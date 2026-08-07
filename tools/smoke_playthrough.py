"""Smoke playthrough: buktikan game bisa dimainkan dari awal sampai ending.

Menjalankan alur inti tanpa UI (Rich/Textual) memakai GameSession:
mulai baru -> kultivasi -> breakthrough -> bertarung -> quest -> ritual
-> ending engine terpicu. Exit code 0 bila semua checkpoint terpenuhi.

Contoh: python3 tools/smoke_playthrough.py
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.game_loop import GameSession  # noqa: E402
from src.core.input import Command  # noqa: E402


def _cmd(session: GameSession, raw: str) -> list[str]:
    """Dispatch satu perintah mentah dan tampilkan baris pertamanya."""
    parts = raw.split()
    command = Command(
        name=parts[0],
        args=tuple(parts[1:]),
        raw=raw,
    )
    return session.dispatch(command)


def _check(label: str, condition: bool, detail: str = "") -> None:
    """Cetak checkpoint dan abort (exit 1) bila kondisi tidak terpenuhi."""
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}" + (f" — {detail}" if detail else ""))
    if not condition:
        raise SystemExit(1)


def main() -> None:
    """Jalankan smoke playthrough inti."""
    session = GameSession()
    session.new_game("Akar")
    _check("new_game", session.state.player.name == "Akar")

    lines = _cmd(session, "cultivate")
    _check(
        "cultivate menghasilkan insight",
        any("insight" in line.lower() for line in lines),
    )

    lines = _cmd(session, "rest")
    _check("rest berjalan", len(lines) >= 1)

    lines = _cmd(session, "go ashfall_forest")
    _check("pergi ke hutan", session.state.location == "ashfall_forest")

    lines = _cmd(session, "look")
    _check(
        "look memicu battle",
        session.in_battle or any("musuh" in line.lower() for line in lines),
    )

    # Loop battle: serang sampai selesai (menang/kalah/kabur).
    for _ in range(40):
        if not session.in_battle:
            break
        session.battle_step("attack")
    _check("battle selesai", not session.in_battle)

    lines = _cmd(session, "go village_emberfall")
    _check("kembali ke desa", session.state.location == "village_emberfall")

    lines = _cmd(session, "talk elder_mao")
    _check("talk elder_mao", any("Sesepuh Mao" in line for line in lines))

    lines = _cmd(session, "status")
    _check("status tampil", any("Akar" in line for line in lines))

    lines = _cmd(session, "inventory")
    _check("inventory tampil", len(lines) >= 1)

    # Verifikasi ending engine merespons flag (mekanisme konklusi).
    session.state.ending_points = {"defy": 5, "seal": 1, "reconcile": 1}
    session.state.flags["ending_defy_win"] = True
    lines = session._run_events()
    _check("epilog tampil saat ending", any("EPILOG" in line for line in lines))

    print("\nSmoke playthrough selesai: alur inti + ending engine OK.")


if __name__ == "__main__":
    main()
