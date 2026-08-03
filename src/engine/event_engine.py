from src.engine import rule_engine
from src.systems import memory_system
from src.engine import quest_engine


def process_events(game_state, randomizer=None, events=None):
    if events is None:
        events = getattr(game_state, "events", [])
    log_lines = []
    for event in events:
        if not all(rule_engine.evaluate(c, game_state) for c in event["trigger"]):
            continue
        for action in event["actions"]:
            kind = action["kind"]
            if kind == "set_flag":
                game_state.flags[action["flag"]] = action.get("value", True)
            elif kind == "grant_memory":
                if game_state.player is not None:
                    memory_system.grant_memory(game_state, action["id"])
            elif kind == "start_quest":
                if game_state.player is not None:
                    log_lines.append(quest_engine.start_quest(game_state, action["id"]))
            elif kind == "log":
                log_lines.append(action["text"])
    return log_lines
