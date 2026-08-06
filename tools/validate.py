"""Validator aset data — Chronicle of the Past (GDD §25.3, AGENTS.md §1).

Menjalankan seluruh loader engine di atas ``data/`` lalu memeriksa
referensi silang antar data (quest -> NPC/peta, event -> quest/memori/
peta/tier/faksi, NPC -> peta, musuh -> tier/teknik). Keluar dengan
kode 0 bila semua valid, 1 bila ada temuan.

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
from src.engine.event import load_events  # noqa: E402
from src.engine.items import load_items  # noqa: E402
from src.engine.maps import load_maps  # noqa: E402
from src.engine.quest import load_quests  # noqa: E402
from src.engine.story import load_memories  # noqa: E402

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
            enemies/ (default data/ proyek).

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

    # Effek item yang dikenali (GDD §7 + §17). Efek tak dikenal = data
    # rusak / typo — ditangkap di sini (trust boundary data JSON).
    valid_item_effects = {
        "heal_hp",
        "restore_qi",
        "add_insight",
        "add_meridian",
        "buff_hp",
        "buff_defense",
        "buff_attack",
        "resist_poison",
        "cure_poison",
    }
    npcs = _npc_records(data_dir / "npc")
    tiers = {tier.id for tier in load_tiers(data_dir / "cultivation")}
    techniques = {
        technique.id for technique in load_techniques(data_dir / "techniques")
    }

    errors: list[str] = []
    for quest in quests.values():
        for objective in quest.objectives:
            target = objective.target
            if objective.kind == "talk" and target not in npcs:
                errors.append(f"{quest.id}: talk -> NPC {target} tidak ada")
            elif objective.kind == "map" and target not in map_ids:
                errors.append(f"{quest.id}: map -> peta {target} tidak ada")

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

    for npc_id, npc in npcs.items():
        if npc["location"] not in map_ids:
            errors.append(f"{npc_id}: lokasi {npc['location']} bukan peta")

    for enemy in enemies:
        if enemy.tier not in tiers:
            errors.append(f"{enemy.id}: tier {enemy.tier} tidak ada")
        for skill in enemy.skills:
            if skill not in techniques:
                errors.append(f"{enemy.id}: skill {skill} tidak ada")

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
