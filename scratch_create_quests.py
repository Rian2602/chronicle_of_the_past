import json
import os
from pathlib import Path

DATA_DIR = Path("data")
QUEST_DIR = DATA_DIR / "quests"
EVENT_DIR = DATA_DIR / "events"

def create_quest(id_, type_, prev_id=None, next_id=None):
    return {
        "id": id_,
        "title": f"Quest {id_} Title",
        "type": type_,
        "category": type_,
        "description": f"Deskripsi untuk {id_}. Bernada grimdark.",
        "requires_flag": f"{prev_id}_done" if prev_id else None,
        "objectives": [
            {
                "kind": "enemy",
                "target": "kultis_bayangan",
                "count": 1
            }
        ],
        "rewards": {
            "insight": 10,
            "gold": 50,
            "reputation": {"holy_order": 5} if type_ == "faction" else {}
        },
        "flags_on_complete": [f"{id_}_done"],
        "next": next_id
    }

def create_event(id_, quest_id):
    return {
        "id": id_,
        "trigger": [
            {
                "kind": "quest_done",
                "quest": "quest208"
            }
        ],
        "actions": [
            {
                "kind": "start_quest",
                "id": quest_id
            }
        ]
    }

# Main Quests
for i in range(1, 9):
    qid = f"quest30{i}"
    prev_id = f"quest30{i-1}" if i > 1 else "quest208"
    next_id = f"quest30{i+1}" if i < 8 else None
    
    with open(QUEST_DIR / f"{qid}.json", "w", encoding="utf-8") as f:
        json.dump(create_quest(qid, "main", prev_id, next_id), f, indent=2, ensure_ascii=False)

# Faction Quests
for i in range(1, 4):
    qid = f"fquest_30{i}"
    with open(QUEST_DIR / f"{qid}.json", "w", encoding="utf-8") as f:
        json.dump(create_quest(qid, "faction", "quest208", None), f, indent=2, ensure_ascii=False)
        
    eid = f"{qid}_intro"
    with open(EVENT_DIR / f"{eid}.json", "w", encoding="utf-8") as f:
        json.dump(create_event(eid, qid), f, indent=2, ensure_ascii=False)

print("Created 11 quests and 3 intro events.")
