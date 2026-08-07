"""Test tools/validate.py — validator aset data (GDD §25.3).

Menjalankan ``collect_errors`` pada pohon data minimal untuk membuktikan
perilaku: referensi gantung tertangkap, pohon valid lolos.
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.validate import collect_errors  # noqa: E402

QUEST = {
    "id": "q_test",
    "title": "Quest Uji",
    "type": "main",
    "description": "Quest untuk menguji validator.",
    "objectives": [{"kind": "talk", "target": "npc_hantu"}],
    "rewards": {"insight": 10, "gold": 0},
    "flags_on_complete": ["q_test_done"],
    "next": None,
    "category": "main",
    "requires_flag": None,
}


def _pohon_data(tmp_path: Path) -> Path:
    """Bangun pohon data minimal (subfolder kosong kecuali quest)."""
    data = tmp_path / "data"
    for sub in (
        "quests",
        "events",
        "story",
        "maps",
        "npc",
        "cultivation",
        "techniques",
        "enemies",
        "dialogues",
    ):
        (data / sub).mkdir(parents=True)
    (data / "quests" / "q_test.json").write_text(
        json.dumps(QUEST, ensure_ascii=False),
        encoding="utf-8",
    )
    return data


def test_validator_menangkap_referensi_gantung(tmp_path):
    """Referensi talk -> NPC yang tidak ada harus dilaporkan."""
    errors = collect_errors(_pohon_data(tmp_path))
    assert any("npc_hantu" in error for error in errors)


def test_validator_menangkap_trigger_reputation_reached_faksi_tak_ada(tmp_path):
    """Trigger reputation_reached ke faksi tak dikenal wajib dilaporkan."""
    data = _pohon_data(tmp_path)
    (data / "events" / "ev_rep.json").write_text(
        json.dumps(
            {
                "id": "ev_rep",
                "trigger": [
                    {
                        "kind": "reputation_reached",
                        "faction": "sekte_gelap",
                        "threshold": 30,
                    }
                ],
                "actions": [{"kind": "log", "text": "x"}],
                "once": True,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    errors = collect_errors(data)
    assert any("sekte_gelap" in error for error in errors)


def test_validator_menangkap_prompt_choice_action_ref_tak_ada(tmp_path):
    """Aksi dalam option prompt_choice ke item tak dikenal dilaporkan."""
    data = _pohon_data(tmp_path)
    (data / "events" / "ev_choice.json").write_text(
        json.dumps(
            {
                "id": "ev_choice",
                "trigger": [
                    {
                        "kind": "flag",
                        "flag": "x",
                        "operator": "EQUALS",
                        "value": True,
                    }
                ],
                "actions": [
                    {
                        "kind": "prompt_choice",
                        "options": [
                            {
                                "key": "a",
                                "text": "Ambil",
                                "actions": [
                                    {"kind": "grant_item", "id": "pil_hantu"}
                                ],
                            }
                        ],
                    }
                ],
                "once": True,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    errors = collect_errors(data)
    assert any("pil_hantu" in error for error in errors)


def test_validator_pohon_valid_lolos(tmp_path):
    """Pohon data yang referensinya lengkap tidak menghasilkan temuan."""
    data = _pohon_data(tmp_path)
    (data / "npc" / "npc_hantu.json").write_text(
        json.dumps(
            {
                "id": "npc_hantu",
                "name": "Hantu",
                "location": "map_test",
                "greeting": "Halo.",
                "dialog": ["Satu kalimat."],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (data / "maps" / "map_test.json").write_text(
        json.dumps(
            {
                "id": "map_test",
                "name": "Peta Uji",
                "description": "Tempat uji.",
                "tier": 1,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    assert collect_errors(data) == []


def test_validator_menangkap_ref_map_enemy(tmp_path):
    """Map dengan enemies merujuk musuh tak dikenal wajib dilaporkan."""
    data = _pohon_data(tmp_path)
    (data / "maps" / "map_test.json").write_text(
        json.dumps(
            {
                "id": "map_test",
                "name": "Peta Uji",
                "description": "Tempat uji.",
                "tier": 1,
                "enemies": [{"enemy": "hantu_kuno"}],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    assert any("hantu_kuno" in e for e in collect_errors(data))


def test_validator_menangkap_ref_item(tmp_path):
    """Event grant_item ke item tak dikenal wajib dilaporkan."""
    data = _pohon_data(tmp_path)
    (data / "events" / "ev_test.json").write_text(
        json.dumps(
            {
                "id": "ev_test",
                "trigger": [],
                "actions": [{"kind": "grant_item", "id": "pil_hantu"}],
                "once": True,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    assert any("pil_hantu" in e for e in collect_errors(data))


def test_validator_menangkap_ref_quest_enemy(tmp_path):
    """Objektif quest enemy ke musuh tak dikenal wajib dilaporkan."""
    data = _pohon_data(tmp_path)
    (data / "quests" / "q_enemy.json").write_text(
        json.dumps(
            {
                "id": "q_enemy",
                "title": "Buruan",
                "type": "faction",
                "description": "Buru hantu kuno.",
                "objectives": [{"kind": "enemy", "target": "hantu_kuno"}],
                "rewards": {"insight": 10, "gold": 0},
                "flags_on_complete": ["q_enemy_done"],
                "next": None,
                "category": "faction",
                "requires_flag": None,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    assert any("hantu_kuno" in e for e in collect_errors(data))


def test_validator_menangkap_ref_quest_collect(tmp_path):
    """Objektif quest collect ke item tak dikenal wajib dilaporkan."""
    data = _pohon_data(tmp_path)
    (data / "quests" / "q_collect.json").write_text(
        json.dumps(
            {
                "id": "q_collect",
                "title": "Koleksi",
                "type": "faction",
                "description": "Kumpulkan batu hantu.",
                "objectives": [{"kind": "collect", "target": "batu_hantu"}],
                "rewards": {"insight": 10, "gold": 0},
                "flags_on_complete": ["q_collect_done"],
                "next": None,
                "category": "faction",
                "requires_flag": None,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    assert any("batu_hantu" in e for e in collect_errors(data))


def test_validator_menangkap_ref_quest_reward_grant_item(tmp_path):
    """Reward quest grant_item ke item tak dikenal wajib dilaporkan."""
    data = _pohon_data(tmp_path)
    (data / "quests" / "q_reward.json").write_text(
        json.dumps(
            {
                "id": "q_reward",
                "title": "Hadiah",
                "type": "faction",
                "description": "Hadiah misterius.",
                "objectives": [{"kind": "talk", "target": "npc_hantu"}],
                "rewards": {
                    "insight": 10,
                    "gold": 0,
                    "grant_item": {"id": "pil_hantu", "count": 1},
                },
                "flags_on_complete": ["q_reward_done"],
                "next": None,
                "category": "faction",
                "requires_flag": None,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    assert any("pil_hantu" in e for e in collect_errors(data))


def _pohon_toko(
    tmp_path: Path,
    stock: list[dict],
    item_price: int | None = 10,
) -> Path:
    """Pohon data + folder items/shops dengan satu toko uji."""
    data = _pohon_data(tmp_path)
    (data / "items").mkdir()
    item: dict = {"id": "pil_dasar", "name": "Pil Dasar"}
    if item_price is not None:
        item["price"] = item_price
    (data / "items" / "pil_dasar.json").write_text(
        json.dumps(item, ensure_ascii=False),
        encoding="utf-8",
    )
    (data / "shops").mkdir()
    (data / "shops" / "toko_uji.json").write_text(
        json.dumps(
            {"id": "toko_uji", "name": "Toko Uji", "stock": stock},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return data


def test_validator_menangkap_stok_item_tanpa_harga(tmp_path):
    """Stok toko ke item tanpa price wajib dilaporkan."""
    data = _pohon_toko(tmp_path, [{"item": "pil_dasar"}], item_price=None)
    errors = collect_errors(data)
    assert any("pil_dasar" in e and "harga" in e for e in errors)


def test_validator_menangkap_stok_item_tak_dikenal(tmp_path):
    """Stok toko ke item tak dikenal wajib dilaporkan."""
    data = _pohon_toko(tmp_path, [{"item": "pil_hantu"}])
    assert any("pil_hantu" in e for e in collect_errors(data))


def test_validator_menangkap_count_stok_tidak_positif(tmp_path):
    """Count stok toko <= 0 wajib dilaporkan."""
    data = _pohon_toko(tmp_path, [{"item": "pil_dasar", "count": 0}])
    assert any("count" in e for e in collect_errors(data))


def test_validator_menangkap_ref_npc_shop_tak_ada(tmp_path):
    """NPC dengan field shop ke toko tak dikenal wajib dilaporkan."""
    data = _pohon_data(tmp_path)
    (data / "npc" / "npc_hantu.json").write_text(
        json.dumps(
            {
                "id": "npc_hantu",
                "name": "Hantu",
                "location": "map_test",
                "shop": "toko_hantu",
                "greeting": "Halo.",
                "dialog": ["Satu kalimat."],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (data / "maps" / "map_test.json").write_text(
        json.dumps(
            {
                "id": "map_test",
                "name": "Peta Uji",
                "description": "Tempat uji.",
                "tier": 1,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    errors = collect_errors(data)
    assert any("shop" in e and "toko_hantu" in e for e in errors)


def test_validator_menangkap_ref_quest_breakthrough(tmp_path):
    """Objektif quest breakthrough ke tier tak dikenal wajib dilaporkan."""
    data = _pohon_data(tmp_path)
    (data / "quests" / "q_tier.json").write_text(
        json.dumps(
            {
                "id": "q_tier",
                "title": "Terobosan",
                "type": "main",
                "description": "Naik ke tier misterius.",
                "objectives": [
                    {"kind": "breakthrough", "target": "tier_hantu"}
                ],
                "rewards": {"insight": 10, "gold": 0},
                "flags_on_complete": ["q_tier_done"],
                "next": None,
                "category": "main",
                "requires_flag": None,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    assert any("tier_hantu" in e for e in collect_errors(data))


def test_validator_menangkap_item_effect_tidak_dikenal(tmp_path):
    """Item dengan effect key tak dikenal wajib dilaporkan."""
    data = _pohon_data(tmp_path)
    items_dir = data / "items"
    items_dir.mkdir(exist_ok=True)
    (items_dir / "pil_broken.json").write_text(
        json.dumps(
            {
                "id": "pil_broken",
                "name": "Pil Rusak",
                "effect": {"heal_hp": 5, "kunci_gila": 1},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    errors = collect_errors(data)
    assert any("pil_broken" in e and "kunci_gila" in e for e in errors)


def test_validator_menerima_efek_learn_recipe(tmp_path):
    """Efek learn_recipe (item resep) wajib diterima validator (GDD 25.3)."""
    data = _pohon_data(tmp_path)
    items_dir = data / "items"
    items_dir.mkdir(exist_ok=True)
    (items_dir / "pil_uji.json").write_text(
        json.dumps({"id": "pil_uji", "name": "Pil Uji"}, ensure_ascii=False),
        encoding="utf-8",
    )
    (items_dir / "resep_uji.json").write_text(
        json.dumps(
            {
                "id": "resep_uji",
                "name": "Resep Uji",
                "type": "recipe",
                "effect": {"learn_recipe": "pil_uji"},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    errors = collect_errors(data)
    assert not any("learn_recipe" in e for e in errors)


def test_validator_menangkap_ref_resep_ingredient(tmp_path):
    """Recipe dengan ingredient item tak dikenal wajib dilaporkan."""
    data = _pohon_data(tmp_path)
    items_dir = data / "items"
    items_dir.mkdir(exist_ok=True)
    (items_dir / "pil_uji.json").write_text(
        json.dumps(
            {
                "id": "pil_uji",
                "name": "Pil Uji",
                "recipe": [{"item": "bahan_hantu", "qty": 2}],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    errors = collect_errors(data)
    assert any("bahan_hantu" in e for e in errors)


def test_validator_menangkap_resep_ingredient_bukan_material(tmp_path):
    """Recipe dengan ingredient non-material wajib ditolak validator."""
    data = _pohon_data(tmp_path)
    items_dir = data / "items"
    items_dir.mkdir(exist_ok=True)
    (items_dir / "pil_dasar.json").write_text(
        json.dumps(
            {
                "id": "pil_dasar",
                "name": "Pil Dasar",
                "type": "consumable",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (items_dir / "pil_uji.json").write_text(
        json.dumps(
            {
                "id": "pil_uji",
                "name": "Pil Uji",
                "recipe": [{"item": "pil_dasar", "qty": 1}],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    errors = collect_errors(data)
    assert any("bukan material" in e for e in errors)


def test_validator_menangkap_ref_learn_recipe_target(tmp_path):
    """Item resep dengan learn_recipe ke item tak dikenal wajib dilaporkan."""
    data = _pohon_data(tmp_path)
    items_dir = data / "items"
    items_dir.mkdir(exist_ok=True)
    (items_dir / "resep_uji.json").write_text(
        json.dumps(
            {
                "id": "resep_uji",
                "name": "Resep Uji",
                "type": "recipe",
                "effect": {"learn_recipe": "pil_hantu"},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    errors = collect_errors(data)
    assert any("pil_hantu" in e for e in errors)


def test_validator_menangkap_ref_add_companion(tmp_path):
    """Event add_companion ke rekan tak dikenal wajib dilaporkan."""
    data = _pohon_data(tmp_path)
    (data / "events" / "ev_rekrut.json").write_text(
        json.dumps(
            {
                "id": "ev_rekrut",
                "trigger": [],
                "actions": [{"kind": "add_companion", "id": "lin_wei_hantu"}],
                "once": True,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    assert any("lin_wei_hantu" in e for e in collect_errors(data))


def test_validator_menangkap_ref_skill_rekan(tmp_path):
    """Rekan dengan skill tak dikenal wajib dilaporkan (GDD §20.3)."""
    data = _pohon_data(tmp_path)
    (data / "companions").mkdir()
    (data / "companions" / "rekan_test.json").write_text(
        json.dumps(
            {
                "id": "rekan_test",
                "name": "Rekan Uji",
                "tier": "qi_condensation",
                "element": "fire",
                "stats": {"hp": 20, "qi": 5},
                "skills": ["hantu_kuno"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    assert any("hantu_kuno" in e for e in collect_errors(data))


def test_validator_menangkap_ref_hatch_companion(tmp_path):
    """Item hatch_companion ke rekan tak dikenal wajib dilaporkan."""
    data = _pohon_data(tmp_path)
    items_dir = data / "items"
    items_dir.mkdir(exist_ok=True)
    (items_dir / "telur_hantu.json").write_text(
        json.dumps(
            {
                "id": "telur_hantu",
                "name": "Telur Hantu",
                "effect": {"hatch_companion": "phoenix_hantu"},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    errors = collect_errors(data)
    assert any("phoenix_hantu" in e for e in errors)


def test_validator_menangkap_ref_evolution_evolved_id(tmp_path):
    """Evolution evolved_id ke rekan tak dikenal wajib dilaporkan."""
    data = _pohon_data(tmp_path)
    (data / "cultivation" / "qi_condensation.json").write_text(
        json.dumps(
            {
                "id": "qi_condensation",
                "name": "Qi Condensation",
                "order": 1,
                "insight_required": 50,
                "stat_bonus": {},
                "unlocks": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (data / "companions").mkdir()
    (data / "companions" / "rekan_evolve.json").write_text(
        json.dumps(
            {
                "id": "rekan_evolve",
                "name": "Rekan Evolve",
                "tier": "qi_condensation",
                "element": "water",
                "stats": {"hp": 20, "qi": 5},
                "skills": [],
                "evolution": {
                    "trigger_tier": "qi_condensation",
                    "evolved_id": "hantu_tidak_ada",
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    errors = collect_errors(data)
    assert any("hantu_tidak_ada" in e for e in errors)


def test_validator_menangkap_evolution_trigger_tier_tak_ada(tmp_path):
    """Evolution trigger_tier ke tier tak dikenal wajib dilaporkan."""
    data = _pohon_data(tmp_path)
    (data / "companions").mkdir()
    (data / "companions" / "rekan_evolve.json").write_text(
        json.dumps(
            {
                "id": "rekan_evolve",
                "name": "Rekan Evolve",
                "tier": "qi_condensation",
                "element": "water",
                "stats": {"hp": 20, "qi": 5},
                "skills": [],
                "evolution": {
                    "trigger_tier": "tier_hantu",
                    "evolved_id": "rekan_evolve",
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    errors = collect_errors(data)
    assert any("tier_hantu" in e for e in errors)


def test_validator_menangkap_ref_dialog_npc_tak_ada(tmp_path):
    """Dialog merujuk NPC tak dikenal wajib dilaporkan."""
    data = _pohon_data(tmp_path)
    (data / "dialogues" / "dlg_test.json").write_text(
        json.dumps(
            {
                "id": "dlg_test",
                "npc": "hantu_npc",
                "nodes": {"start": {"text": "Halo.", "choices": []}},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    assert any("hantu_npc" in e for e in collect_errors(data))


def test_validator_menangkap_ref_dialog_next_node_tak_ada(tmp_path):
    """Pilihan dialog menuju node tak dikenal wajib dilaporkan."""
    data = _pohon_data(tmp_path)
    (data / "dialogues" / "dlg_test.json").write_text(
        json.dumps(
            {
                "id": "dlg_test",
                "npc": "elder_mao",
                "nodes": {
                    "start": {
                        "text": "Halo.",
                        "choices": [{"text": "Lanjut", "next": "ghost_node"}],
                    }
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    assert any("ghost_node" in e for e in collect_errors(data))


def test_validator_menangkap_ref_dialog_action_item(tmp_path):
    """Aksi dialog grant_item ke item tak dikenal wajib dilaporkan."""
    data = _pohon_data(tmp_path)
    (data / "dialogues" / "dlg_test.json").write_text(
        json.dumps(
            {
                "id": "dlg_test",
                "npc": "elder_mao",
                "nodes": {
                    "start": {
                        "text": "Halo.",
                        "choices": [
                            {
                                "text": "Terima",
                                "next": None,
                                "actions": [
                                    {"kind": "grant_item", "id": "pil_hantu"}
                                ],
                            }
                        ],
                    }
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    assert any("pil_hantu" in e for e in collect_errors(data))


def test_validator_menangkap_buff_formasi_bukan_dict(tmp_path):
    """Formasi dengan buff non-dict/bukan stat wajib dilaporkan."""
    data = _pohon_data(tmp_path)
    formations_dir = data / "formations"
    formations_dir.mkdir(exist_ok=True)
    (formations_dir / "f_uji.json").write_text(
        json.dumps(
            {
                "id": "f_uji",
                "name": "Formasi Uji",
                "element": "earth",
                "description": "Uji.",
                "buff": "bukan_stat",
                "skill": None,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    errors = collect_errors(data)
    assert any("f_uji" in e and "buff" in e for e in errors)


def test_validator_data_lulus(tmp_path):
    """Validator berjalan tanpa temuan dan keluar kode 0 (AGENTS.md §1)."""
    result = subprocess.run(
        [sys.executable, "tools/validate.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "OK" in result.stdout
