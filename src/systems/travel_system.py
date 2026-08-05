from src.engine.time_engine import advance_time

# Peta yang selalu bisa diakses tanpa flag unlock (Arc 1 + peta dasar).
# Semua peta lain memerlukan flag `map_<id>_unlocked` di game_state.flags
# sebelum bisa dimasuki — sesuai §6 story-season1-spec.md.
_OPEN_MAPS = frozenset(
    {
        "village",
        "forest",
        # Gerbang Arc 2, terbuka sejak awal: syarat quest009 adalah
        # `map ruins_entrance`. Interior (ancient_ruins) dikunci via
        # `map_ancient_ruins_unlocked` dari quest009.
        "ruins_entrance",
    }
)


def _map_accessible(game_state, target: str) -> bool:
    """True bila peta target bisa diakses saat ini.

    Peta dalam _OPEN_MAPS selalu bisa diakses. Peta lain memerlukan
    flag `map_<target>_unlocked` sudah ada di game_state.flags.
    """
    if target in _OPEN_MAPS:
        return True
    return game_state.flags.get(f"map_{target}_unlocked", False)


def can_travel(game_state, target):
    """True bila target ada di jalan keluar peta saat ini DAN bisa diakses.

    Sebuah peta bisa dituju hanya jika:
    1. target tercantum di `exits` peta saat ini, DAN
    2. peta target sudah dibuka (dalam _OPEN_MAPS atau flag unlock ada).
    """
    current = game_state.current_map
    if current is None:
        return False
    if target not in current.exits:
        return False
    return _map_accessible(game_state, target)


def travel(game_state, target):
    """Pindah ke peta target lalu majukan waktu satu langkah.

    Args:
        game_state: State permainan berisi peta saat ini.
        target: ID peta tujuan.

    Returns:
        Pesan kedatangan dalam Bahasa Indonesia.

    Raises:
        ValueError: Bila tidak ada jalan menuju target atau belum terbuka.
    """
    current = game_state.current_map
    if current is None or target not in current.exits:
        raise ValueError(f"Tidak ada jalan ke {target}.")
    if not _map_accessible(game_state, target):
        raise ValueError(
            f"Jalan ke {target} masih terkunci. "
            "Selesaikan quest yang relevan untuk membukanya."
        )
    game_state.current_map = game_state.world[target]
    advance_time(game_state, 1)
    return f"Kamu tiba di {game_state.current_map.name}."
