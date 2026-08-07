"""Validator aset data — Chronicle of the Past (GDD §25.3, AGENTS.md §1).

Menjalankan seluruh loader engine di atas ``data/`` lalu memeriksa
referensi silang antar data (quest -> NPC/peta, event -> quest/memori/
peta/tier/faksi, NPC -> peta/toko, musuh -> tier/teknik, toko -> item
berharga). Keluar dengan kode 0 bila semua valid, 1 bila ada temuan.

Usage:
    python tools/validate.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# E402: impor src baru sah setelah sys.path menunjuk ke root proyek.
from src.core.state import FACTIONS  # noqa: E402
from src.engine.combat import load_enemies, load_techniques  # noqa: E402
from src.engine.cultivation import load_tiers  # noqa: E402
from src.engine.dialog import load_dialogs  # noqa: E402
from src.engine.event import ACTION_KINDS, load_events  # noqa: E402
from src.engine.items import load_items  # noqa: E402
from src.engine.maps import load_maps  # noqa: E402
from src.engine.quest import load_quests  # noqa: E402
from src.engine.shop import load_shops  # noqa: E402
from src.engine.story import load_memories  # noqa: E402
from src.models.party import load_companions  # noqa: E402
from src.systems.formation import load_formations  # noqa: E402

DATA_DIR = ROOT / "data"


def _npc_records(npc_dir: Path) -> dict[str, dict]:
    """Muat semua NPC dari data/npc/ keyed by id.

    Args:
        npc_dir: Direktori berisi JSON NPC.

    Returns:
        Mapping npc_id -> data mentah dari file.
    """
    npcs: dict[str, dict] = {}
    for path in sorted(npc_dir.glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        npcs[raw["id"]] = raw
    return npcs


def collect_errors(data_dir: Path = DATA_DIR) -> list[str]:
    """Kumpulkan semua temuan referensi silang antar data.

    Args:
        data_dir: Direktori root ``data`` berisi subfolder quests/,
            events/, story/, maps/, npc/, cultivation/, techniques/,
            enemies/, formations/ (default data/ proyek).

    Returns:
        Daftar temuan terurut abjad; kosong bila semua referensi valid.

    Raises:
        json.JSONDecodeError: Bila ada file JSON rusak.
        KeyError: Bila skema wajib (mis. ``id``) hilang dari sebuah file.
        TypeError: Bila data tidak cocok dengan dataclass loader.
    """
    quests = {quest.id: quest for quest in load_quests(data_dir / "quests")}
    events = load_events(data_dir / "events")
    memories = set(load_memories(data_dir / "story"))
    maps = load_maps(data_dir / "maps")
    map_ids = set(maps)
    enemies = load_enemies(data_dir / "enemies")
    enemy_ids = {enemy.id for enemy in enemies}
    items = load_items(data_dir / "items")
    shops = load_shops(data_dir / "shops")

    # Effek item yang dikenali (GDD §7 + §17). Efek tak dikenal = data
    # rusak / typo — ditangkap di sini (trust boundary data JSON).
    valid_item_effects = {
        "heal_hp",
        "restore_qi",
        "add_insight",
        "add_meridian",
        "learn_recipe",
        "buff_hp",
        "buff_defense",
        "buff_attack",
        "buff_agility",
        "buff_qi_max",
        "resist_poison",
        "resist_dark",
        "cure_poison",
        "status_inflict",
        "growth_stat",
        "max_level",
        "hatch_companion",
    }
    npcs = _npc_records(data_dir / "npc")
    dialogs = load_dialogs(data_dir / "dialogues")
    tiers = {tier.id for tier in load_tiers(data_dir / "cultivation")}
    techniques = {
        technique.id for technique in load_techniques(data_dir / "techniques")
    }
    companions = load_companions(data_dir / "companions")
    formations = load_formations(data_dir / "formations")

    errors: list[str] = []
    for quest in quests.values():
        for objective in quest.objectives:
            target = objective.target
            if objective.kind == "talk" and target not in npcs:
                errors.append(f"{quest.id}: talk -> NPC {target} tidak ada")
            elif objective.kind == "map" and target not in map_ids:
                errors.append(f"{quest.id}: map -> peta {target} tidak ada")
            elif objective.kind in ("enemy", "kill_count") and (
                target not in enemy_ids
            ):
                errors.append(
                    f"{quest.id}: {objective.kind} -> musuh {target} tidak ada"
                )
            elif objective.kind == "collect" and target not in items:
                errors.append(f"{quest.id}: collect -> item {target} tidak ada")
            elif objective.kind == "breakthrough" and target not in tiers:
                errors.append(
                    f"{quest.id}: breakthrough -> tier {target} tidak ada"
                )
        grant_item = quest.rewards.get("grant_item")
        if grant_item and grant_item.get("id") not in items:
            errors.append(
                f"{quest.id}: reward grant_item -> {grant_item['id']} tidak ada"
            )

    for event in events:
        for condition in event.trigger:
            kind = condition["kind"]
            if kind == "quest_done" and condition["quest"] not in quests:
                errors.append(
                    f"{event.id}: trigger quest_done -> {condition['quest']}"
                )
            elif kind == "location_entered" and condition["map"] not in map_ids:
                errors.append(
                    f"{event.id}: trigger location -> {condition['map']}"
                )
            elif kind == "tier_reached" and condition["tier"] not in tiers:
                errors.append(
                    f"{event.id}: trigger tier -> {condition['tier']}"
                )
            elif kind == "reputation_reached" and (
                condition["faction"] not in FACTIONS
            ):
                errors.append(
                    f"{event.id}: trigger reputation -> {condition['faction']}"
                )
        for action in event.actions:
            kind = action["kind"]
            if kind == "start_quest" and action["id"] not in quests:
                errors.append(f"{event.id}: start_quest -> {action['id']}")
            elif kind == "unlock_map" and action["target"] not in map_ids:
                errors.append(f"{event.id}: unlock_map -> {action['target']}")
            elif kind == "grant_memory" and action["memory_id"] not in memories:
                errors.append(
                    f"{event.id}: grant_memory -> {action['memory_id']}"
                )
            elif kind == "change_reputation" and (
                action["faction"] not in FACTIONS
            ):
                errors.append(
                    f"{event.id}: change_reputation -> {action['faction']}"
                )
            elif kind == "grant_item" and action["id"] not in items:
                errors.append(
                    f"{event.id}: grant_item -> {action['id']} tidak ada"
                )
            elif kind == "add_companion" and action["id"] not in {
                companion.id for companion in companions
            }:
                errors.append(
                    f"{event.id}: add_companion -> {action['id']} tidak ada"
                )

    # Dialog (GDD §12.5): npc, node `next`, dan aksi wajib ter-resolve.
    for dialog_id, dialog in dialogs.items():
        npc_id = dialog.get("npc")
        if npc_id not in npcs:
            errors.append(f"{dialog_id}: npc {npc_id} tidak ada")
        nodes = dialog.get("nodes", {})
        for node_id, node in nodes.items():
            for choice in node.get("choices", []):
                next_id = choice.get("next")
                if next_id is not None and next_id not in nodes:
                    errors.append(
                        f"{dialog_id}: node {node_id} -> next "
                        f"{next_id} tidak ada"
                    )
                for action in choice.get("actions", []):
                    kind = action.get("kind")
                    if kind not in ACTION_KINDS:
                        errors.append(
                            f"{dialog_id}: node {node_id} -> kind "
                            f"aksi '{kind}' tak dikenal"
                        )
                        continue
                    if kind == "start_quest" and action["id"] not in quests:
                        errors.append(
                            f"{dialog_id}: start_quest -> {action['id']}"
                        )
                    elif kind == "unlock_map" and (
                        action["target"] not in map_ids
                    ):
                        errors.append(
                            f"{dialog_id}: unlock_map -> {action['target']}"
                        )
                    elif kind == "grant_memory" and (
                        action["memory_id"] not in memories
                    ):
                        errors.append(
                            f"{dialog_id}: grant_memory -> "
                            f"{action['memory_id']}"
                        )
                    elif kind == "change_reputation" and (
                        action["faction"] not in FACTIONS
                    ):
                        errors.append(
                            f"{dialog_id}: change_reputation -> "
                            f"{action['faction']}"
                        )
                    elif kind == "grant_item" and action["id"] not in items:
                        errors.append(
                            f"{dialog_id}: grant_item -> "
                            f"{action['id']} tidak ada"
                        )
                    elif kind == "add_companion" and action["id"] not in {
                        companion.id for companion in companions
                    }:
                        errors.append(
                            f"{dialog_id}: add_companion -> "
                            f"{action['id']} tidak ada"
                        )

    # Aksi dalam option prompt_choice (GDD §15.3): referensi wajib
    # ter-resolve — format aksi sama dengan event/dialog (apply_action).
    for event in events:
        for action in event.actions:
            if action.get("kind") != "prompt_choice":
                continue
            for opt in action.get("options", []):
                for opt_action in opt.get("actions", []):
                    kind = opt_action.get("kind")
                    if kind not in ACTION_KINDS:
                        errors.append(
                            f"{event.id}: prompt_choice -> kind "
                            f"'{kind}' tak dikenal"
                        )
                        continue
                    if kind == "start_quest" and (
                        opt_action["id"] not in quests
                    ):
                        errors.append(
                            f"{event.id}: prompt_choice start_quest -> "
                            f"{opt_action['id']}"
                        )
                    elif kind == "unlock_map" and (
                        opt_action["target"] not in map_ids
                    ):
                        errors.append(
                            f"{event.id}: prompt_choice unlock_map -> "
                            f"{opt_action['target']}"
                        )
                    elif kind == "grant_memory" and (
                        opt_action["memory_id"] not in memories
                    ):
                        errors.append(
                            f"{event.id}: prompt_choice grant_memory -> "
                            f"{opt_action['memory_id']}"
                        )
                    elif kind == "change_reputation" and (
                        opt_action["faction"] not in FACTIONS
                    ):
                        errors.append(
                            f"{event.id}: prompt_choice reputation -> "
                            f"{opt_action['faction']}"
                        )
                    elif kind == "grant_item" and (
                        opt_action["id"] not in items
                    ):
                        errors.append(
                            f"{event.id}: prompt_choice grant_item -> "
                            f"{opt_action['id']} tidak ada"
                        )
                    elif kind == "add_companion" and opt_action["id"] not in {
                        companion.id for companion in companions
                    }:
                        errors.append(
                            f"{event.id}: prompt_choice companion -> "
                            f"{opt_action['id']} tidak ada"
                        )

    for npc_id, npc in npcs.items():
        if npc["location"] not in map_ids:
            errors.append(f"{npc_id}: lokasi {npc['location']} bukan peta")
        shop_id = npc.get("shop")
        if shop_id and shop_id not in shops:
            errors.append(f"{npc_id}: shop {shop_id} tidak ada")

    for enemy in enemies:
        if enemy.tier not in tiers:
            errors.append(f"{enemy.id}: tier {enemy.tier} tidak ada")
        for skill in enemy.skills:
            if skill not in techniques:
                errors.append(f"{enemy.id}: skill {skill} tidak ada")

    # Rekan (GDD §20.3): tier, elemen, teknik, dan evolusi wajib resolve.
    valid_elements = {"metal", "wood", "earth", "water", "fire", "netral"}
    companion_ids = {companion.id for companion in companions}
    for companion in companions:
        if companion.tier not in tiers:
            errors.append(f"{companion.id}: tier {companion.tier} tidak ada")
        if companion.element not in valid_elements:
            errors.append(
                f"{companion.id}: elemen {companion.element} tidak valid"
            )
        for skill in companion.skills:
            if skill not in techniques:
                errors.append(f"{companion.id}: skill {skill} tidak ada")
        evolution = companion.evolution
        if evolution:
            trigger_tier = evolution.get("trigger_tier")
            if trigger_tier not in tiers:
                errors.append(
                    f"{companion.id}: evolution trigger_tier "
                    f"{trigger_tier} tidak ada"
                )
            if evolution.get("evolved_id") not in companion_ids:
                errors.append(
                    f"{companion.id}: evolution evolved_id "
                    f"{evolution.get('evolved_id')} tidak ada"
                )

    # Formasi (GDD §7): buff wajib dict stat, skill aktif wajib ada.
    for formation_id, formation in formations.items():
        buff = formation.get("buff")
        if not isinstance(buff, dict) or not buff:
            errors.append(
                f"formations: {formation_id} -> buff wajib dict non-kosong"
            )
            continue
        skill = formation.get("skill")
        if skill is not None and skill not in techniques:
            errors.append(
                f"formations: {formation_id} -> skill {skill} tidak ada"
            )

    for map_id, raw in maps.items():
        for entry in raw.get("enemies", []):
            if entry["enemy"] not in enemy_ids:
                errors.append(
                    f"{map_id}: enemies -> musuh {entry['enemy']} tidak ada"
                )

    for item_id, item in items.items():
        effect = item.get("effect")
        if isinstance(effect, dict):
            for key in effect:
                if key not in valid_item_effects:
                    errors.append(
                        f"items: {item_id} -> effect key '{key}' tak dikenal"
                    )
            target = effect.get("learn_recipe")
            if target is not None and target not in items:
                errors.append(
                    f"items: {item_id} -> learn_recipe target "
                    f"'{target}' tidak ada"
                )
            hatched = effect.get("hatch_companion")
            if hatched is not None and hatched not in companion_ids:
                errors.append(
                    f"items: {item_id} -> hatch_companion target "
                    f"'{hatched}' tidak ada"
                )
        recipe = item.get("recipe")
        if isinstance(recipe, list):
            for req in recipe:
                ingredient = req.get("item")
                if ingredient is not None and ingredient not in items:
                    errors.append(
                        f"items: {item_id} -> resep butuh "
                        f"'{ingredient}' yang tidak ada"
                    )
                elif ingredient is not None and (
                    items.get(ingredient, {}).get("type") != "material"
                ):
                    errors.append(
                        f"items: {item_id} -> resep butuh "
                        f"'{ingredient}' yang bukan material"
                    )

    # Toko (GDD §7): stok wajib merujuk item yang ada dan berharga.
    for shop_id, shop in shops.items():
        for entry in shop.get("stock", []):
            item_id = entry["item"]
            if item_id not in items:
                errors.append(f"{shop_id}: stock -> item {item_id} tidak ada")
                continue
            price = items[item_id].get("price")
            if not isinstance(price, int) or price < 1:
                errors.append(
                    f"{shop_id}: stock -> {item_id} tanpa harga beli valid"
                )
            count = entry.get("count")
            if not isinstance(count, int) or count < 1:
                errors.append(
                    f"{shop_id}: stock -> {item_id} count tidak valid"
                )

    return sorted(errors)


def main() -> int:
    """Jalankan validasi dan cetak laporan; kembalikan kode keluar."""
    try:
        errors = collect_errors()
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        print(f"GAGAL: data tidak valid — {exc}")
        return 1
    if not errors:
        print("OK: semua data valid, referensi ter-resolve.")
        return 0
    print("TEMUAN:")
    for error in errors:
        print(f"  - {error}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
