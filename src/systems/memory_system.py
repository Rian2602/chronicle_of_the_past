def grant_memory(game_state, memory_id, memory=None) -> dict:
    if memory is None:
        memory = next(
            (entry for entry in game_state.memories if entry["id"] == memory_id),
            None,
        )
    if memory is None:
        return None
    player = game_state.player
    if player is None:
        return None
    if any(entry["id"] == memory_id for entry in player.memories):
        return memory
    for key in memory["flags_set"]:
        game_state.flags[key] = True
    player.memories.append(memory)
    return memory


def has_memory(game_state, memory_id) -> bool:
    player = game_state.player
    if player is None:
        return False
    return any(entry["id"] == memory_id for entry in player.memories)
