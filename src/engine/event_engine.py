from src.engine import quest_engine, rule_engine
from src.systems import memory_system


def process_events(game_state, randomizer=None, events=None):
    """Proses semua event yang kondisinya terpenuhi pada state saat ini.

    Args:
        game_state: State permainan berisi flags/quests/memories.
        randomizer: Tidak dipakai; dipertahankan untuk kompatibilitas API.
        events: Daftar event (default: game_state.events).

    Returns:
        List baris log yang dihasilkan aksi event (set_flag, kenangan, dll).
    """
    if events is None:
        events = getattr(game_state, "events", [])
    log_lines = []
    for event in events:
        if not all(
            rule_engine.evaluate(c, game_state) for c in event["trigger"]
        ):
            continue
        for action in event["actions"]:
            kind = action["kind"]
            if kind == "set_flag":
                game_state.flags[action["flag"]] = action.get("value", True)
            elif kind == "grant_memory":
                if game_state.player is not None:
                    memory = memory_system.grant_memory(
                        game_state, action["id"]
                    )
                    if memory is not None:
                        log_lines.append(
                            f"Kenangan terbuka: {memory['title']}."
                        )
            elif kind == "start_quest":
                if game_state.player is not None:
                    log_lines.append(
                        quest_engine.start_quest(game_state, action["id"])
                    )
            elif kind == "log":
                log_lines.append(action["text"])
    return log_lines
