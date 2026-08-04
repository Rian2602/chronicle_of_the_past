from src.engine.time_engine import advance_time
from src.engine.world_engine import get_map


def can_travel(game_state, target):
    """True bila target ada di daftar jalan keluar peta saat ini."""
    current = game_state.current_map
    if current is None:
        return False
    return target in current.exits


def travel(game_state, target):
    """Pindah ke peta target lalu majukan waktu satu langkah.

    Args:
        game_state: State permainan berisi peta saat ini.
        target: ID peta tujuan.

    Returns:
        Pesan kedatangan dalam Bahasa Indonesia.

    Raises:
        ValueError: Bila tidak ada jalan menuju target.
    """
    if not can_travel(game_state, target):
        raise ValueError(f"Tidak ada jalan ke {target}.")
    game_state.current_map = get_map(game_state, target)
    advance_time(game_state, 1)
    return f"Kamu tiba di {game_state.current_map.name}."
