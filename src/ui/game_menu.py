"""Pembangun menu keyboard-only. Menghasilkan (label, target) untuk launcher.

target: str = perintah run_turn | callable() = submenu | None = keluar/kembali
"""

from src.engine import dialog_engine

END_DIALOG = "!end_dialog"

_SLOT_SAVE = "save saves/slot1.json"
_SLOT_LABELS = {"weapon": "Senjata", "armor": "Zirah", "helmet": "Helm"}


def build(game):
    if getattr(game, "_combat", None) is not None:
        return _combat_menu(game)
    if getattr(game, "_current_dialog", None) is not None:
        return _dialog_menu(game)
    return _explore_menu(game)


def _explore_menu(game):
    items = [
        ("Lihat", "look"),
        ("Jelajah", "explore"),
    ]
    m = getattr(getattr(game, "state", None), "current_map", None)
    if m is not None:
        exits = getattr(m, "exits", None) or []
        if exits:
            items.append(("Pergi", _go_submenu(game, exits)))
        npcs = getattr(m, "npcs", None) or []
        if npcs:
            items.append(("Bicara", _talk_submenu(game, npcs)))
    items.append(("Istirahat", "rest"))
    player = getattr(getattr(game, "state", None), "player", None)
    if player is not None:
        if player.inventory or player.equipped:
            items.append(("Inventori", _inventory_submenu(game, player)))
        if getattr(player, "memories", None):
            items.append(("Kenangan", "memories"))
        if getattr(player, "quests_active", None):
            items.append(("Quest", "quests"))
    items.extend([
        ("Status", "status"),
        ("Bantuan", "help"),
        ("Simpan", _SLOT_SAVE),
        ("Keluar", None),
    ])
    return items


def _go_submenu(game, exits):
    def submenu():
        items = []
        for mid in exits:
            name = game.ctx.maps.get(mid, {}).get("name", mid)
            items.append((name, f"go {mid}"))
        items.append(("Kembali", None))
        return items
    return submenu


def _talk_submenu(game, npcs):
    def submenu():
        items = []
        for nid in npcs:
            name = game.ctx.npc.get(nid, {}).get("name", nid)
            items.append((name, f"talk {nid}"))
        items.append(("Kembali", None))
        return items
    return submenu


def _inventory_submenu(game, player):
    def submenu():
        items = []
        for entry in player.inventory:
            item = game.state.items.get(entry["id"])
            name = item.name if item else entry["id"]
            qty = entry.get("qty", 1)
            if item is not None and item.slot is None:
                items.append((f"Pakai {name} x{qty}", f"use {entry['id']}"))
            else:
                items.append((f"Pasang {name}", f"equip {entry['id']}"))
        for slot, item_id in player.equipped.items():
            item = game.state.items.get(item_id)
            name = item.name if item else item_id
            items.append((f"Lepas {_SLOT_LABELS.get(slot, slot)}: {name}", f"unequip {slot}"))
        items.append(("Kembali", None))
        return items
    return submenu


def _combat_menu(game):
    state = game._combat
    items = [("Serang", "attack")]
    player = getattr(getattr(game, "state", None), "player", None)
    learned = getattr(player, "learned_skills", None) or []
    if learned:
        physical = [sid for sid in learned if state.skills.get(sid, {}).get("type") != "magic"]
        magic = [sid for sid in learned if state.skills.get(sid, {}).get("type") == "magic"]
        if physical:
            items.append(("Skill", _skill_submenu(game, physical, "skill")))
        if magic:
            items.append(("Sihir", _skill_submenu(game, magic, "magic")))
    if player is not None:
        consumables = [
            e["id"] for e in player.inventory
            if game.state.items.get(e["id"], None) is not None
            and game.state.items[e["id"]].heal
        ]
        if consumables:
            items.append(("Item", _item_submenu(game, consumables)))
    items.extend([
        ("Amati", "observe"),
        ("Kabur", "escape"),
        ("Bertahan", "defend"),
        ("Simpan", _SLOT_SAVE),
    ])
    return items


def _skill_submenu(game, skill_ids, verb):
    def submenu():
        items = []
        for sid in skill_ids:
            skill = game.ctx.skills.get(sid, {})
            name = skill.get("name", sid)
            items.append((f"{name} ({skill.get('cost', 0)} MP)", f"{verb} {sid}"))
        items.append(("Kembali", None))
        return items
    return submenu


def _item_submenu(game, item_ids):
    def submenu():
        items = []
        for iid in item_ids:
            item = game.state.items.get(iid)
            items.append((item.name, f"item {iid}"))
        items.append(("Kembali", None))
        return items
    return submenu


def _dialog_menu(game):
    dialog = game._current_dialog
    items = []
    for idx, choice in enumerate(dialog_engine.available_choices(dialog, game.state), start=1):
        items.append((choice.get("text", str(idx)), str(idx)))
    items.append(("Akhiri Percakapan", END_DIALOG))
    return items
