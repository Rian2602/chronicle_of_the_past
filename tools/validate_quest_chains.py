#!/usr/bin/env python3
"""
Validasi quest chains untuk mendeteksi circular dependencies.
Enhancement #4 dari evaluasi data/quests.
"""
import json
import os
import sys
from collections import defaultdict


def load_quests(quest_dir='data/quests'):
    """Load semua quest files."""
    quests = {}
    for fname in os.listdir(quest_dir):
        if not fname.endswith('.json'):
            continue
        fpath = os.path.join(quest_dir, fname)
        with open(fpath) as f:
            data = json.load(f)
            quests[data['id']] = data
    return quests

def build_dependency_graph(quests):
    """Bangun graph dependency dari quests."""
    graph = defaultdict(list)  # quest_id -> list of quest_ids yang dibutuhkan

    for qid, quest in quests.items():
        requirements = quest.get('requirements', [])

        # Extract flag requirements yang merujuk ke quest lain
        for req in requirements:
            if isinstance(req, dict):
                target = req.get('target', '')
                kind = req.get('kind', '')

                # Quest dependencies via flags
                if kind == 'flag' and target.startswith('quest')\
                        and target.endswith('_done'):
                    dep_quest = target.replace('_done', '')
                    graph[qid].append(dep_quest)

        # Next quest pointer
        next_quest = quest.get('next')
        if next_quest:
            # Ini adalah forward pointer, bukan dependency
            pass

    return graph

def detect_cycles(graph, quests):
    """Detect circular dependencies menggunakan DFS."""
    visited = set()
    rec_stack = set()
    cycles = []

    def dfs(node, path):
        if node in rec_stack:
            # Cycle detected
            cycle_start = path.index(node)
            cycle = [*path[cycle_start:], node]
            cycles.append(cycle)
            return True

        if node in visited:
            return False

        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for neighbor in graph.get(node, []):
            if neighbor in quests:  # Only check valid quests
                dfs(neighbor, path)

        path.pop()
        rec_stack.remove(node)
        return False

    for node in quests.keys():
        if node not in visited:
            dfs(node, [])

    return cycles

def validate_quest_references(quests):
    """Validasi semua referensi dalam quest."""
    issues = []

    # Load all NPCs, maps, items, enemies for validation
    npcs = set()
    maps = set()
    items = set()
    enemies = set()

    # Load NPCs
    npc_dir = 'data/npc'
    if os.path.exists(npc_dir):
        for fname in os.listdir(npc_dir):
            if fname.endswith('.json'):
                with open(os.path.join(npc_dir, fname)) as f:
                    data = json.load(f)
                    npcs.add(data['id'])

    # Load Maps
    map_dir = 'data/maps'
    if os.path.exists(map_dir):
        for fname in os.listdir(map_dir):
            if fname.endswith('.json'):
                with open(os.path.join(map_dir, fname)) as f:
                    data = json.load(f)
                    maps.add(data['id'])

    # Load Items
    item_dir = 'data/items'
    if os.path.exists(item_dir):
        for fname in os.listdir(item_dir):
            if fname.endswith('.json'):
                with open(os.path.join(item_dir, fname)) as f:
                    data = json.load(f)
                    items.add(data['id'])

    # Load Enemies
    enemy_dir = 'data/enemies'
    if os.path.exists(enemy_dir):
        for fname in os.listdir(enemy_dir):
            if fname.endswith('.json'):
                with open(os.path.join(enemy_dir, fname)) as f:
                    data = json.load(f)
                    enemies.add(data['id'])

    # Validate each quest
    for qid, quest in quests.items():
        # Check giver
        giver = quest.get('giver')
        if giver and giver not in npcs:
            issues.append(f"{qid}: giver '{giver}' tidak ditemukan di NPCs")

        # Check objectives
        objectives = quest.get('objectives', [])
        for obj in objectives:
            if isinstance(obj, dict):
                obj_type = obj.get('type')
                target = obj.get('target')

                if obj_type == 'talk_to' and target and target not in npcs:
                    issues.append(f"{qid}: objective talk_to '{target}' tidak ditemukan")

                elif obj_type == 'go_to' and target and target not in maps:
                    issues.append(f"{qid}: objective go_to '{target}' tidak ditemukan")

                elif obj_type == 'kill' and target and target not in enemies:
                    issues.append(f"{qid}: objective kill '{target}' tidak ditemukan")

                elif obj_type == 'collect' and target and target not in items:
                    issues.append(f"{qid}: objective collect '{target}' tidak ditemukan")

                elif obj_type == 'use_item' and target and target not in items:
                    issues.append(f"{qid}: objective use_item '{target}' tidak ditemukan")


        # Check next quest
        next_quest = quest.get('next')
        if next_quest and next_quest not in quests:
            issues.append(f"{qid}: next quest '{next_quest}' tidak ditemukan")

    return issues

def main():
    print("=" * 60)
    print("QUEST CHAIN VALIDATION TOOL")
    print("=" * 60)

    quest_dir = 'data/quests'
    if not os.path.exists(quest_dir):
        print(f"❌ Error: Directory {quest_dir} tidak ditemukan")
        sys.exit(1)

    # Load quests
    quests = load_quests(quest_dir)
    print(f"\n📦 Loaded {len(quests)} quests")

    # Build dependency graph
    graph = build_dependency_graph(quests)
    edge_count = sum(len(v) for v in graph.values())
    print(f"🔗 Built dependency graph dengan {edge_count} edges")

    # Detect cycles
    print("\n🔍 Detecting circular dependencies...")
    cycles = detect_cycles(graph, quests)

    if cycles:
        print(f"\n❌ DITEMUKAN {len(cycles)} CIRCULAR DEPENDENCIES:")
        for i, cycle in enumerate(cycles, 1):
            print(f"   Cycle {i}: {' -> '.join(cycle)}")
        sys.exit(1)
    else:
        print("✅ Tidak ada circular dependencies terdeteksi")

    # Validate references
    print("\n🔍 Validating quest references...")
    issues = validate_quest_references(quests)

    if issues:
        print(f"\n❌ DITEMUKAN {len(issues)} MASALAH REFERENSI:")
        for issue in issues:
            print(f"   - {issue}")
        sys.exit(1)
    else:
        print("✅ Semua referensi valid")

    # Check for orphaned quests (no incoming references)
    print("\n🔍 Checking for orphaned quests...")
    incoming = defaultdict(list)
    for qid, quest in quests.items():
        next_q = quest.get('next')
        if next_q:
            incoming[next_q].append(qid)

    # Main quest chain should start from quest001
    orphans = []
    for qid in quests:
        if qid == '001':  # Starting quest is allowed to have no incoming
            continue
        if qid not in incoming and not any(
            'quest' + qid in str(quests[q].get('requirements', []))
            for q in quests
        ):
            # Check if it's a side quest (no giver might indicate standalone)
            if not quests[qid].get('giver'):
                orphans.append(qid)

    if orphans:
        orphans_str = ', '.join(orphans)
        print(f"⚠️  Quests tanpa incoming reference: {orphans_str}")
    else:
        print("✅ Semua quests terhubung dalam chain")

    print("\n" + "=" * 60)
    print("✅ VALIDATION PASSED - Semua quest chains valid!")
    print("=" * 60)
    return 0

if __name__ == '__main__':
    sys.exit(main())
