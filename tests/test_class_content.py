from src.core.game_context import GameContext

SPEC_LEARNABLE = {
    "warrior": ["shield_bash", "war_cry"],
    "mage": ["frost_bolt", "arcane_barrier"],
    "assassin": ["poison_blade", "shadow_step"],
    "ranger": ["multishot", "snare"],
    "scholar": ["lore_strike", "time_study"],
}


def test_class_learnable_skills_exist():
    ctx = GameContext(data_dir="data")
    for cid, cls in ctx.classes.items():
        for sid in cls.get("learnable_skills", []):
            assert sid in ctx.skills, f"{cid} missing learnable skill {sid}"


def test_class_learnable_skills_match_spec():
    ctx = GameContext(data_dir="data")
    for cid, expected in SPEC_LEARNABLE.items():
        assert ctx.classes[cid].get("learnable_skills", []) == expected
