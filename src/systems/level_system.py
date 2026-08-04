def xp_to_next(level: int) -> int:
    """Jumlah XP yang dibutuhkan untuk naik dari level tertentu."""
    return 50 * level


def award_xp(player, amount: int) -> int:
    """Terapkan bonus XP kelas pada jumlah XP mentah."""
    # Apply class XP bonus (single source of truth for the multiplier)
    return int(amount * getattr(player, "xp_bonus", 1.0))


def gain_xp(player, amount: int, randomizer=None) -> list:
    """Tambahkan XP dan kembalikan daftar level baru yang dicapai.

    Args:
        player: Pemain yang menerima XP.
        amount: XP mentah sebelum bonus kelas.
        randomizer: Tidak dipakai; dipertahankan untuk kompatibilitas API.

    Returns:
        List level yang berhasil dicapai (kosong bila tidak naik level).
    """
    player.xp += award_xp(player, amount)
    levels = []
    while player.xp >= xp_to_next(player.level):
        player.xp -= xp_to_next(player.level)
        player.level += 1
        levels.append(player.level)
    return levels


LEVEL_CHOICES = [
    ("attack", 2),
    ("defense", 2),
    ("agility", 2),
    ("intelligence", 2),
    ("hp", 20),
    ("mp", 10),
    ("skill_point", 1),
]

LEVEL_CHOICE_LABELS = {
    "attack": "Serangan",
    "defense": "Pertahanan",
    "agility": "Kelincahan",
    "intelligence": "Kecerdasan",
    "hp": "HP",
    "mp": "MP",
    "skill_point": "Skill Point",
}

_VALID_KEYS = {choice[0] for choice in LEVEL_CHOICES}


def choice_label(choice_key: str) -> str:
    """Label tampilan (Indonesia) untuk satu pilihan bonus level-up."""
    for key, value in LEVEL_CHOICES:
        if key == choice_key:
            name = LEVEL_CHOICE_LABELS.get(key, key.title())
            if key == "skill_point":
                return f"{name} +1"
            return f"{name} +{value}"
    raise ValueError(f"Pilihan tidak dikenal: {choice_key}")


def apply_choice(player, choice_key: str) -> None:
    """Terapkan satu pilihan bonus level-up ke pemain.

    Args:
        player: Pemain yang menerima bonus.
        choice_key: Salah satu kunci di LEVEL_CHOICES.

    Raises:
        ValueError: Bila choice_key tidak dikenal.
    """
    if choice_key not in _VALID_KEYS:
        pilihan = ", ".join(sorted(_VALID_KEYS))
        raise ValueError(
            f"Pilihan tidak valid: '{choice_key}'. "
            f"Pilihan yang tersedia: {pilihan}."
        )
    if choice_key == "skill_point":
        player.skill_points += 1
    else:
        player.attribute_bonuses[choice_key] = (
            player.attribute_bonuses.get(choice_key, 0)
            + dict(LEVEL_CHOICES)[choice_key]
        )
