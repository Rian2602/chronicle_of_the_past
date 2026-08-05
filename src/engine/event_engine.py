from src.engine import quest_engine, rule_engine
from src.systems import memory_system
from src.ui import story_view

_ENDING_RECAPS = {
    "ending_a_done": "Kau memilih menjadi Penjaga Baru Jangkar.",
    "ending_b_done": "Kau menyerahkan pena sejarah kepada rakyat.",
    "ending_c_done": "Kau menutup rahasia waktu di bawah takhta.",
    "ending_d_done": "Kau membuka ilmu waktu bagi para cendekiawan.",
    "ending_e_done": "Kau menghancurkan Jangkar dan membiarkan dunia bebas.",
    "ending_f_done": "Kau menulis ulang sejarah dari akarnya.",
}


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
                flag_msg = quest_engine.complete_requirement(
                    game_state, "flag", action["flag"]
                )
                if flag_msg and flag_msg != "Tidak ada syarat yang sesuai.":
                    log_lines.append(flag_msg)
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
            elif kind == "fail_quest":
                if game_state.player is not None:
                    log_lines.append(
                        quest_engine.fail_quest(game_state, action["id"])
                    )
            elif kind == "log":
                log_lines.append(action["text"])
            elif kind == "play_scene":
                scene = _find_scene(game_state, action["id"])
                if scene is not None:
                    log_lines.append(story_view.render_scene(scene))
            elif kind == "recap":
                log_lines.extend(_recap_lines(game_state))
    return log_lines


def process_day_tick(game_state):
    """Proses event harian yang dipicu saat rest."""
    if "ultimatum_5_days" not in game_state.flags:
        return []
    if game_state.flags.get("ultimatum_resolved"):
        return []
    days = int(game_state.flags.get("ultimatum_days_passed", 0)) + 1
    game_state.flags["ultimatum_days_passed"] = days
    remaining = max(0, 5 - days)
    if remaining == 0:
        game_state.flags["ultimatum_expired"] = True
        return ["Ultimatum gereja habis. Inkuisisi mulai bergerak."]
    return [f"Ultimatum gereja tersisa {remaining} hari."]


def _find_scene(game_state, scene_id):
    for scene in getattr(game_state, "scenes", []):
        if scene.get("id") == scene_id:
            return scene
    return None


def _recap_lines(game_state):
    lines = ["Catatan perjalanan ditulis:"]
    for flag, text in _ENDING_RECAPS.items():
        if game_state.flags.get(flag):
            lines.append(f"- {text}")
            break
    else:
        lines.append(
            "- Jalan akhir belum jelas, tetapi jejakmu sudah tertinggal."
        )
    done = len(getattr(game_state.player, "quests_done", []))
    lines.append(f"- Quest selesai: {done}.")
    return lines
