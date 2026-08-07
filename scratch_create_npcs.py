import json
import os
from pathlib import Path

DATA_DIR = Path("data")
NPC_DIR = DATA_DIR / "npc"
DIALOG_DIR = DATA_DIR / "dialogues"
COMPANION_DIR = DATA_DIR / "companions"

def create_npc(id_, name_, loc, greeting):
    return {
        "id": id_,
        "name": name_,
        "description": f"Karakter misterius: {name_}. Nada suram.",
        "location": loc,
        "greeting": greeting,
        "dialog": [f"Halo dari {name_}."]
    }

def create_dialog(id_, npc_id):
    return {
        "id": id_,
        "npc": npc_id,
        "nodes": {
            "start": {
                "text": f"Dialog utama {npc_id}. Dunia ini kejam.",
                "choices": [
                    {
                        "text": "Tinggalkan.",
                        "next": None
                    }
                ]
            }
        }
    }

def create_companion(id_, name_):
    return {
        "id": id_,
        "name": name_,
        "tier": "golden_core",
        "element": "metal",
        "stats": {
            "attack": 30,
            "defense": 30,
            "agility": 30,
            "intelligence": 30,
            "vitality": 30,
            "spirit": 30,
            "hp": 200,
            "qi": 100
        },
        "skills": ["qi_slash"]
    }

# Create NPCs
npcs = [
    ("inquisitor_vega", "Inquisitor Vega", "holy_cathedral", "Keadilan Orde buta, namun pedangku tidak."),
    ("sera_ember", "Sera Ember", "rebel_hideout", "Kami bersembunyi di bawah agar bisa menusuk dari kegelapan."),
    ("warden_kai", "Warden Kai", "rebel_hideout", "Banyak yang mati agar rahasia ini tetap aman.")
]

for nid, name, loc, greeting in npcs:
    with open(NPC_DIR / f"{nid}.json", "w", encoding="utf-8") as f:
        json.dump(create_npc(nid, name, loc, greeting), f, indent=2, ensure_ascii=False)
        
    did = f"dialog_{nid}_1"
    with open(DIALOG_DIR / f"{did}.json", "w", encoding="utf-8") as f:
        json.dump(create_dialog(did, nid), f, indent=2, ensure_ascii=False)

# Create kestrel companion
with open(COMPANION_DIR / "kestrel.json", "w", encoding="utf-8") as f:
    json.dump(create_companion("kestrel", "Kestrel"), f, indent=2, ensure_ascii=False)

print("Created NPCs, dialogues, and companion.")
