import json
import os

from src.core.constants import FACTIONS
from src.core.game_context import GameContext


def _load_all_jsons(root):
    results = []
    for dirpath, _dirs, files in os.walk(root):
        for name in files:
            if name.endswith(".json"):
                results.append(os.path.join(dirpath, name))
    return results


def test_class_starting_skills_exist():
    ctx = GameContext(data_dir="data")
    for cid, cls in ctx.classes.items():
        for s in cls.get("starting_skills", []):
            assert s in ctx.skills, f"{cid} missing skill {s}"


def test_map_exits_resolve():
    ctx = GameContext(data_dir="data")
    for mid, m in ctx.maps.items():
        for e in m.get("exits", []):
            assert e in ctx.maps, f"{mid} bad exit {e}"


def test_map_npc_and_enemy_pool_resolve():
    ctx = GameContext(data_dir="data")
    for mid, m in ctx.maps.items():
        for n in m.get("npcs", []):
            assert n in ctx.npc, f"{mid} bad npc {n}"
        for entry in m.get("enemy_pool", []):
            eid = entry if isinstance(entry, str) else entry.get("id")
            assert eid in ctx.enemies, f"{mid} bad enemy {eid}"


def test_npc_dialogs_resolve():
    ctx = GameContext(data_dir="data")
    for nid, npc in ctx.npc.items():
        for d in npc.get("dialogs", []):
            assert d in ctx.dialogues, f"{nid} bad dialog {d}"


def test_dialog_next_and_flags_resolve():
    ctx = GameContext(data_dir="data")
    for did, dlg in ctx.dialogues.items():
        for choice in dlg.get("choices", []):
            nxt = choice.get("next")
            if nxt is not None:
                assert nxt in ctx.dialogues, f"{did} bad next {nxt}"


def test_quest_reputation_uses_valid_factions():
    ctx = GameContext(data_dir="data")
    for qid, quest in ctx.quests.items():
        for faction in quest.get("rewards", {}).get("reputation", {}):
            assert faction in FACTIONS, (
                f"{qid} bad reputation faction {faction}"
            )


def test_quest_requirement_kinds():
    ctx = GameContext(data_dir="data")
    valid_kinds = {"talk", "map", "flag", "enemy"}
    for qid, quest in ctx.quests.items():
        for req in quest.get("requirements", []):
            assert req.get("kind") in valid_kinds, (
                f"{qid} bad requirement kind {req.get('kind')}"
            )


def test_enemy_skills_exist():
    ctx = GameContext(data_dir="data")
    for eid, enemy in ctx.enemies.items():
        for s in enemy.get("skills", []):
            assert s in ctx.skills, f"{eid} missing skill {s}"


def test_enemy_loot_items_exist():
    ctx = GameContext(data_dir="data")
    for eid, enemy in ctx.enemies.items():
        for entry in enemy.get("loot", []):
            assert entry.get("item") in ctx.items, (
                f"{eid} bad loot {entry.get('item')}"
            )


def test_event_actions_resolve():
    ctx = GameContext(data_dir="data")
    memory_ids = {m["id"] for m in ctx.memories}
    for ev in ctx.events:
        for action in ev.get("actions", []):
            if action.get("kind") == "grant_memory":
                assert action["id"] in memory_ids, (
                    f"{ev['id']} bad memory {action['id']}"
                )
            if action.get("kind") == "start_quest":
                assert action["id"] in ctx.quests, (
                    f"{ev['id']} bad quest {action['id']}"
                )


def test_ascii_art_files_exist():
    """Setiap map yang terdaftar di GameContext punya file ASCII art."""
    for map_id in GameContext(data_dir="data").maps.keys():
        path = os.path.join("assets", "ascii", f"{map_id}.txt")
        assert os.path.isfile(path), f"missing ascii art {path}"


def test_no_orphan_ascii_files():
    """Setiap file ASCII art di assets/ascii/ direferens oleh map yang ada."""
    map_ids = set(GameContext(data_dir="data").maps.keys())
    ascii_dir = os.path.join("assets", "ascii")
    for filename in os.listdir(ascii_dir):
        if not filename.endswith(".txt"):
            continue
        map_id = filename[:-4]
        assert map_id in map_ids, (
            f"assets/ascii/{filename} tidak direferens oleh map mana pun"
        )


def test_all_json_files_parse():
    for path in _load_all_jsons("data"):
        with open(path, encoding="utf-8") as f:
            json.load(f)
