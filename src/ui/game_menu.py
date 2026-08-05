"""Pembangun menu keyboard-only. Menghasilkan (label, target) untuk launcher.

target: str = perintah run_turn | callable() = submenu | None = keluar/kembali
"""

import os

from src.core import save_manager
from src.engine import dialog_engine
from src.systems import level_system, shop_system, travel_system

END_DIALOG = "!end_dialog"
END_SHOP = "!end_shop"

_SLOT_SAVE = "save saves/slot1.json"
_SLOT_LABELS = {"weapon": "Senjata", "armor": "Zirah", "helmet": "Helm"}


def build(game):
    """Bangun menu sesuai konteks game: level-up, combat, dialog, eksplorasi.

    Returns:
        List (label, target) untuk navigasi keyboard launcher.
    """
    if getattr(game, "_pending_levels", 0) > 0:
        return _level_up_menu(game)
    if getattr(game, "_combat", None) is not None:
        return _combat_menu(game)
    if getattr(game, "_shop_npc_id", None) is not None:
        return _shop_menu(game)
    if getattr(game, "_current_dialog", None) is not None:
        return _dialog_menu(game)
    return _explore_menu(game)


def _level_up_menu(game):
    """Menu pilihan bonus level-up; pilihan → perintah angka (select)."""
    items = []
    for index, (key, _) in enumerate(level_system.LEVEL_CHOICES, start=1):
        items.append((level_system.choice_label(key), str(index)))
    return items


def _explore_menu(game):
    """Menu eksplorasi: Lihat, Jelajah, Pergi, Bicara, dll."""
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
        if getattr(player, "skill_points", 0) > 0 and _has_unlearned_skills(
            game, player
        ):
            items.append(("Latih Skill", _learn_submenu(game, player)))
    items.extend(
        [
            ("Status", "status"),
            ("Bantuan", "help"),
            ("Simpan", _SLOT_SAVE),
        ]
    )
    if save_manager.save_paths():
        items.append(("Muat", _load_submenu()))
    items.append(("Keluar", None))
    return items


def _load_submenu():
    """Submenu berisi slot save yang tersedia.

    Pilihan → perintah 'load <path>'.
    """

    def submenu():
        items = []
        for path in save_manager.save_paths():
            items.append((os.path.basename(path), f"load {path}"))
        items.append(("Kembali", None))
        return items

    return submenu


def _go_submenu(game, exits):
    """Submenu peta tujuan yang tersedia dari peta saat ini.

    Peta terkunci (belum ada flag `map_<id>_unlocked`) tidak ditampilkan,
    sesuai §6 story-season1-spec.md.
    """

    def submenu():
        items = []
        for mid in exits:
            if not travel_system.can_travel(game.state, mid):
                continue
            name = game.ctx.maps.get(mid, {}).get("name", mid)
            items.append((name, f"go {mid}"))
        items.append(("Kembali", None))
        return items

    return submenu


def _talk_submenu(game, npcs):
    """Submenu NPC yang ada di peta saat ini."""

    def submenu():
        items = []
        for nid in npcs:
            name = game.ctx.npc.get(nid, {}).get("name", nid)
            items.append((name, f"talk {nid}"))
        items.append(("Kembali", None))
        return items

    return submenu


def _has_unlearned_skills(game, player) -> bool:
    """True bila masih ada skill kelas yang belum dipelajari pemain."""
    learnable = game.ctx.classes.get(player.class_id, {}).get(
        "learnable_skills", []
    )
    return any(sid not in player.learned_skills for sid in learnable)


def _learn_submenu(game, player):
    """Submenu skill yang bisa dipelajari kelas pemain (1 Skill Point)."""

    def submenu():
        class_id = player.class_id
        learnable = game.ctx.classes.get(class_id, {}).get(
            "learnable_skills", []
        )
        items = []
        for sid in learnable:
            if sid in player.learned_skills:
                continue
            skill = game.ctx.skills.get(sid, {})
            items.append((skill.get("name", sid), f"learn {sid}"))
        items.append(("Kembali", None))
        return items

    return submenu


def _inventory_submenu(game, player):
    """Submenu inventaris: pakai/pasang item dan lepas perlengkapan."""

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
            items.append(
                (
                    f"Lepas {_SLOT_LABELS.get(slot, slot)}: {name}",
                    f"unequip {slot}",
                )
            )
        items.append(("Kembali", None))
        return items

    return submenu


def _combat_menu(game):
    """Menu combat: Serang, Skill/Sihir, Item, Amati, Kabur, Bertahan."""
    state = game._combat
    items = [("Serang", "attack")]
    player = getattr(getattr(game, "state", None), "player", None)
    learned = getattr(player, "learned_skills", None) or []
    if learned:
        physical = [
            sid
            for sid in learned
            if state.skills.get(sid, {}).get("type") != "magic"
        ]
        magic = [
            sid
            for sid in learned
            if state.skills.get(sid, {}).get("type") == "magic"
        ]
        if physical:
            items.append(("Skill", _skill_submenu(game, physical, "skill")))
        if magic:
            items.append(("Sihir", _skill_submenu(game, magic, "magic")))
    if player is not None:
        consumables = [
            e["id"]
            for e in player.inventory
            if game.state.items.get(e["id"], None) is not None
            and (
                game.state.items[e["id"]].heal
                or getattr(game.state.items[e["id"]], "heal_mp", 0)
            )
        ]
        if consumables:
            items.append(("Item", _item_submenu(game, consumables)))
    items.extend(
        [
            ("Amati", "observe"),
            ("Kabur", "escape"),
            ("Bertahan", "defend"),
            ("Simpan", _SLOT_SAVE),
        ]
    )
    return items


def _skill_submenu(game, skill_ids, verb):
    """Submenu skill/sihir dengan biaya MP masing-masing."""

    def submenu():
        items = []
        for sid in skill_ids:
            skill = game.ctx.skills.get(sid, {})
            name = skill.get("name", sid)
            items.append(
                (f"{name} ({skill.get('cost', 0)} MP)", f"{verb} {sid}")
            )
        items.append(("Kembali", None))
        return items

    return submenu


def _item_submenu(game, item_ids):
    """Submenu item pemulih yang bisa dipakai saat bertarung."""

    def submenu():
        items = []
        for iid in item_ids:
            item = game.state.items.get(iid)
            items.append((item.name, f"item {iid}"))
        items.append(("Kembali", None))
        return items

    return submenu


def _dialog_menu(game):
    """Menu pilihan dialog yang tersedia + Akhiri Percakapan."""
    dialog = game._current_dialog
    items = []
    for idx, choice in enumerate(
        dialog_engine.available_choices(dialog, game.state), start=1
    ):
        items.append((choice.get("text", str(idx)), str(idx)))
    npc = game.ctx.npc.get(game._talk_npc_id) if game._talk_npc_id else None
    if shop_system.has_shop(npc):
        items.append(("Berbelanja", "shop"))
    items.append(("Akhiri Percakapan", END_DIALOG))
    return items


def _shop_menu(game):
    """Menu toko untuk NPC yang sedang dibuka."""
    npc = game.ctx.npc.get(game._shop_npc_id)
    if not shop_system.has_shop(npc):
        return [("Keluar Toko", END_SHOP)]
    items = []
    buy_list = shop_system.list_buy(game.state, npc)
    if buy_list:
        items.append(("Beli", _buy_submenu(buy_list)))
    sell_list = shop_system.list_sell(game.state, npc)
    if sell_list:
        items.append(("Jual", _sell_submenu(sell_list)))
    items.append(("Keluar Toko", END_SHOP))
    return items


def _buy_submenu(buy_list):
    def submenu():
        items = [
            (f"{name} - {price} emas", f"buy {item_id}")
            for item_id, name, price in buy_list
        ]
        items.append(("Kembali", None))
        return items

    return submenu


def _sell_submenu(sell_list):
    def submenu():
        items = [
            (f"{name} x{qty} - {price} emas", f"sell {item_id}")
            for item_id, name, price, qty in sell_list
        ]
        items.append(("Kembali", None))
        return items

    return submenu
