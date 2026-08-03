import dataclasses
import datetime
import json
import os

from src.core.game_state import GameState
from src.models.player import Player

SCHEMA_VERSION = 1
CONTENT_VERSION = 1

class SaveError(Exception):
    pass


def default_player(game_context=None):
    if game_context is not None:
        return game_context.create_player("Pejalan Waktu", "warrior")
    return Player(name="Pejalan Waktu", class_id="warrior", hp=0, mp=0, base_stats={})


def _engine_state(game_state, combat=None):
    current_map = game_state.current_map
    combat_data = None
    if combat is not None:
        from src.engine.combat_interfaces import CombatResult, StatusEffect
        # Serialisasi statuses: konversi StatusEffect objects ke dict
        serialized_statuses = {}
        for target_id, effects in combat.statuses.items():
            serialized_statuses[target_id] = [
                {"kind": eff.kind, "duration": eff.duration, "power": eff.power}
                for eff in effects
            ]
        combat_data = {
            "round_no": combat.round_no,
            "turn_order": combat.turn_order,
            "current_index": combat.current_index,
            "over": combat.over,
            "result": combat.result.value if combat.result else None,
            "log": combat.log,
            "observe_used": combat.observe_used,
            "player_defending": combat.player_defending,
            "enemy_defending": combat.enemy_defending,
            "statuses": serialized_statuses,
            "xp": getattr(combat, "xp", 0),
            "gold": getattr(combat, "gold", 0),
            "loot": combat.loot or [],
            "observe_info": getattr(combat, "observe_info", None),
            "enemy_id": combat.enemy.id if hasattr(combat, "enemy") and combat.enemy else None,
            "enemy_hp": combat.enemy.stats.get("hp", 0) if hasattr(combat, "enemy") and combat.enemy else 0,
        }
    return {
        "current_map": current_map.id if hasattr(current_map, "id") else current_map,
        "current_time": game_state.time,
        "day": game_state.day,
        "random_seed": game_state.rng_seed,
        "active_events": [],
        "combat": combat_data,
    }


def save_game(game_state, path, schema_version=SCHEMA_VERSION, combat=None):
    data = {
        "schema_version": schema_version,
        "content_version": CONTENT_VERSION,
        "player": dataclasses.asdict(game_state.player) if game_state.player else None,
        "flags": game_state.flags,
        "engine_state": _engine_state(game_state, combat),
        "saved_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except OSError as e:
        raise SaveError(f"Gagal menyimpan ke {path}: {e}") from e
    return path


def load_game(path, game_context=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        raise SaveError(f"Save tidak dapat dimuat: {path}") from e
    if not isinstance(data, dict):
        raise SaveError(f"Bukan file save: {path}")
    schema_version = data.get("schema_version", data.get("version", 0))
    if schema_version > SCHEMA_VERSION:
        raise SaveError(f"Versi save tidak didukung: {schema_version}")
    gs = GameState()
    player_data = data.get("player") or {}
    if player_data:
        gs.player = _restore_player(player_data, game_context)
    gs.flags = data.get("flags", {})
    engine = data.get("engine_state", {})
    gs.current_map = engine.get("current_map")
    gs.time = engine.get("current_time", "morning")
    gs.day = engine.get("day", 1)
    gs.rng_seed = engine.get("random_seed")
    # Restore combat state jika ada
    combat_data = engine.get("combat")
    gs.combat_data = combat_data  # Simpan untuk direstore oleh Game class
    return gs


def _restore_player(player_data, game_context):
    if game_context is not None and player_data.get("class_id") in game_context.classes:
        p = game_context.create_player(
            player_data.get("name", "Pejalan Waktu"),
            player_data["class_id"],
        )
        overlay = dict(player_data)
        for key in ("base_stats", "attribute_bonuses", "equipped", "reputation",
                    "relationship", "flags", "quests_active"):
            overlay[key] = player_data.get(key, getattr(p, key))
        overlay["inventory"] = player_data.get("inventory", [])
        overlay["quests_done"] = player_data.get("quests_done", [])
        overlay["memories"] = player_data.get("memories", [])
        overlay["learned_skills"] = player_data.get("learned_skills", [])
        for field_name in ("hp", "mp", "level", "xp", "gold", "skill_points"):
            setattr(p, field_name, player_data.get(field_name, getattr(p, field_name)))
        for key, value in overlay.items():
            if hasattr(p, key):
                setattr(p, key, value)
        return p
    defaults = dict(
        name="Pejalan Waktu", class_id="warrior", hp=0, mp=0, base_stats={},
        attribute_bonuses={}, level=1, xp=0, gold=0, skill_points=0,
        equipped={}, inventory=[], reputation={}, relationship={}, flags={},
        quests_active={}, quests_done=[], memories=[], learned_skills=[],
    )
    defaults.update(player_data)
    return Player(**defaults)
