import json
from pathlib import Path

TECH_DIR = Path("data/techniques")
TECH_DIR.mkdir(parents=True, exist_ok=True)

techniques = [
    ("pukulan_beruntun", "Pukulan Beruntun", "sword", "metal"),
    ("serapan_akar", "Serapan Akar", "formation", "wood"),
    ("dinding_tanah", "Dinding Tanah", "formation", "earth"),
    ("tebasan_cahaya", "Tebasan Cahaya", "sword", "fire"),
    ("pelindung_suci", "Pelindung Suci", "formation", "metal"),
    ("panah_bayangan", "Panah Bayangan", "sword", "water"),
    ("aura_penekan", "Aura Penekan", "soul", "earth"),
    ("langkah_hantu", "Langkah Hantu", "spirit", "water"),
    ("ledakan_qi", "Ledakan Qi", "sword", "fire")
]

def create_technique(id_, name, path, element):
    return {
        "id": id_,
        "name": name,
        "path": path,
        "element": element,
        "type": "technique",
        "qi_cost": 25,
        "power": 45,
        "effects": [],
        "requires": {
            "tier": "golden_core"
        }
    }

for tid, name, path, elem in techniques:
    with open(TECH_DIR / f"{tid}.json", "w", encoding="utf-8") as f:
        json.dump(create_technique(tid, name, path, elem), f, indent=2, ensure_ascii=False)

print("Created 9 techniques.")
