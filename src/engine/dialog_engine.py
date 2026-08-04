def available_choices(dialog, game_state):
    """Filter pilihan dialog yang tersedia sesuai flag & reputasi pemain.

    Returns:
        List pilihan (dict) yang lolos semua persyaratan.
    """
    result = []
    player = game_state.player
    for choice in dialog["choices"]:
        if any(
            f not in game_state.flags for f in choice.get("require_flags", [])
        ):
            continue
        if any(
            f in game_state.flags for f in choice.get("require_not_flags", [])
        ):
            continue
        rep = choice.get("require_reputation", {})
        if player is not None and any(
            player.reputation.get(f, 0) < v for f, v in rep.items()
        ):
            continue
        result.append(choice)
    return result


def choose(game_state, dialog, choice_index):
    """Terapkan pilihan dialog: set flag lalu kembalikan ID dialog berikut.

    Args:
        game_state: State permainan tempat flag diset.
        dialog: Dialog yang sedang aktif.
        choice_index: Indeks pilihan di dialog["choices"].

    Returns:
        ID dialog berikutnya, atau None bila percakapan berakhir.
    """
    if choice_index < 0 or choice_index >= len(dialog["choices"]):
        return None
    choice = dialog["choices"][choice_index]
    for flag in choice.get("set_flags", []):
        game_state.flags[flag] = True
    return choice.get("next")
