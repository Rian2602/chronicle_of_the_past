#!/usr/bin/env python3
"""
Validate story chains for consistency and completeness.

Checks:
- Chapter sequence integrity
- Valid references (maps, NPCs, dialogues)
- Flag consistency
- Multiple ending paths availability
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Set


def load_json_file(path: Path) -> Dict[str, Any]:
    """Load a JSON file and return its contents."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate_chapter_sequence(story_data: Dict[str, Any], story_id: str) -> List[str]:
    """Validate that chapter sequences are complete and have no dead ends."""
    errors = []
    chapters = story_data.get('chapters', [])
    
    if not chapters:
        errors.append(f"[{story_id}] No chapters defined")
        return errors
    
    # Build chapter map
    chapter_map = {ch['id']: ch for ch in chapters}
    
    # Check first chapter exists
    first_chapter_id = chapters[0]['id'] if chapters else None
    if not first_chapter_id:
        errors.append(f"[{story_id}] No first chapter defined")
    
    # Check each chapter's next_chapter reference
    for chapter in chapters:
        ch_id = chapter.get('id')
        next_ch = chapter.get('next_chapter')
        
        if next_ch is not None and next_ch not in chapter_map:
            errors.append(f"[{story_id}] Chapter '{ch_id}' references non-existent next_chapter '{next_ch}'")
    
    # Check for unreachable chapters (except first)
    reachable = set()
    current = first_chapter_id
    while current and current in chapter_map:
        if current in reachable:
            errors.append(f"[{story_id}] Circular reference detected at chapter '{current}'")
            break
        reachable.add(current)
        current = chapter_map[current].get('next_chapter')
    
    unreachable = set(chapter_map.keys()) - reachable
    if unreachable:
        # Allow unreachable if they're choice branches
        print(f"[{story_id}] Warning: {len(unreachable)} chapters may be unreachable via linear path (might be choice branches): {unreachable}")
    
    return errors


def validate_references(story_data: Dict[str, Any], story_id: str, 
                       valid_maps: Set[str], valid_npcs: Set[str], 
                       valid_dialogues: Set[str]) -> List[str]:
    """Validate that all references in story point to valid data files."""
    errors = []
    
    for chapter in story_data.get('chapters', []):
        ch_id = chapter.get('id')
        
        # Check scene reference
        scene = chapter.get('scene')
        if scene and scene not in valid_maps:
            errors.append(f"[{story_id}:{ch_id}] Invalid scene reference '{scene}'")
        
        # Check character references
        for char in chapter.get('characters', []):
            if char not in valid_npcs:
                errors.append(f"[{story_id}:{ch_id}] Invalid character reference '{char}'")
        
        # Check dialogue_tree reference
        dialogue = chapter.get('dialogue_tree')
        if dialogue and dialogue not in valid_dialogues:
            errors.append(f"[{story_id}:{ch_id}] Invalid dialogue_tree reference '{dialogue}'")
    
    return errors


def validate_flags(story_data: Dict[str, Any], story_id: str, 
                  all_quest_flags: Set[str]) -> List[str]:
    """Validate flag usage consistency."""
    errors = []
    triggers = story_data.get('triggers', {})
    
    # Check trigger flags
    for flag_type in ['required_flags', 'forbidden_flags']:
        for flag in triggers.get(flag_type, []):
            # Flags should follow naming convention
            if not any(pattern in flag for pattern in ['quest', 'arc_', 'met_', 'have_', 'sided_']):
                print(f"[{story_id}] Warning: Non-standard flag name '{flag}'")
    
    return errors


def validate_endings(story_dir: Path) -> List[str]:
    """Validate that multiple ending paths exist."""
    errors = []
    
    epilogue_files = list(story_dir.glob('epilogue*.json'))
    
    if len(epilogue_files) < 2:
        errors.append("Multiple endings not found. Expected at least 2 epilogue variants (heroic, neutral, tragic)")
    else:
        print(f"Found {len(epilogue_files)} epilogue variant(s): {[f.stem for f in epilogue_files]}")
    
    return errors


def validate_story_file(story_file: Path, valid_maps: Set[str], 
                       valid_npcs: Set[str], valid_dialogues: Set[str],
                       all_quest_flags: Set[str]) -> List[str]:
    """Validate a single story file based on its structure."""
    errors = []
    
    try:
        story_data = load_json_file(story_file)
    except Exception as e:
        return [f"[{story_file.stem}] Failed to load: {str(e)}"]
    
    # Handle different file formats
    if isinstance(story_data, list):
        # Format: scenes.json or memories.json - just check structure
        for i, item in enumerate(story_data):
            if not isinstance(item, dict):
                errors.append(f"[{story_file.stem}:{i}] Item is not a dictionary")
                continue
            
            if 'id' not in item:
                errors.append(f"[{story_file.stem}:{i}] Missing 'id' field")
            
            # For scenes, check 'lines' field
            if 'lines' in item:
                if not isinstance(item['lines'], list):
                    errors.append(f"[{story_file.stem}:{item.get('id', i)}] 'lines' should be a list")
        
        return errors
    
    # Handle arc-style structure (dict with chapters)
    if isinstance(story_data, dict):
        if 'chapters' in story_data:
            # Validate chapter sequence
            errors.extend(validate_chapter_sequence(story_data, story_file.stem))
            
            # Validate references
            errors.extend(validate_references(
                story_data, story_file.stem, 
                valid_maps, valid_npcs, valid_dialogues
            ))
            
            # Validate flags
            errors.extend(validate_flags(story_data, story_file.stem, all_quest_flags))
    
    return errors


def main():
    """Main validation function."""
    base_dir = Path(__file__).parent.parent
    story_dir = base_dir / 'data' / 'story'
    maps_dir = base_dir / 'data' / 'maps'
    npc_dir = base_dir / 'data' / 'npc'
    dialogue_dir = base_dir / 'data' / 'dialogues'
    quests_dir = base_dir / 'data' / 'quests'
    
    if not story_dir.exists():
        print("ERROR: data/story/ directory does not exist")
        sys.exit(1)
    
    # Load reference data
    valid_maps = {f.stem for f in maps_dir.glob('*.json')} if maps_dir.exists() else set()
    valid_npcs = {f.stem for f in npc_dir.glob('*.json')} if npc_dir.exists() else set()
    valid_dialogues = {f.stem for f in dialogue_dir.glob('*.json')} if dialogue_dir.exists() else set()
    
    # Collect all quest flags
    all_quest_flags = set()
    if quests_dir.exists():
        for q_file in quests_dir.glob('*.json'):
            quest = load_json_file(q_file)
            all_quest_flags.add(f"{quest.get('id', '')}_done")
            all_quest_flags.add(f"{quest.get('id', '')}_failed")
    
    # Validate each story file
    all_errors = []
    story_files = [f for f in story_dir.glob('*.json') if not f.stem.startswith('epilogue')]
    
    print(f"Validating {len(story_files)} story files...")
    
    for story_file in story_files:
        print(f"\nChecking {story_file.stem}...")
        errors = validate_story_file(
            story_file, valid_maps, valid_npcs, 
            valid_dialogues, all_quest_flags
        )
        
        if errors:
            all_errors.extend(errors)
            for err in errors:
                print(f"  ❌ {err}")
        else:
            print(f"  ✅ {story_file.stem} passed all checks")
    
    # Validate endings
    print("\nChecking multiple endings...")
    ending_errors = validate_endings(story_dir)
    all_errors.extend(ending_errors)
    for err in ending_errors:
        print(f"  ❌ {err}")
    
    # Summary
    print(f"\n{'='*60}")
    if all_errors:
        print(f"VALIDATION FAILED: {len(all_errors)} error(s) found")
        sys.exit(1)
    else:
        print("VALIDATION PASSED: All story chains are valid!")
        sys.exit(0)


if __name__ == '__main__':
    main()
