"""Uji perluasan quest_engine: kind collect, kill_count, escort (§12.1)."""

from src.core.game_state import GameState
from src.engine.quest_engine import (
    complete_requirement,
    progress_requirement,
    start_quest,
)
from src.models.player import Player


def make_player():
    return Player(
        name="Rian",
        class_id="warrior",
        hp=100,
        mp=10,
        base_stats={
            "attack": 12,
            "defense": 14,
            "hp": 100,
            "mp": 10,
            "agility": 8,
            "intelligence": 7,
        },
    )


def make_game_state(quests=None):
    gs = GameState()
    gs.player = make_player()
    gs.flags = {}
    gs.quests = quests or {}
    return gs


def quest(
    quest_id, requirements, rewards=None, flags_on_complete=None, next_=None
):
    return {
        "id": quest_id,
        "title": f"Quest {quest_id}",
        "type": "main",
        "description": "desc",
        "requirements": requirements,
        "rewards": rewards or {},
        "flags_on_complete": flags_on_complete,
        "next": next_,
    }


# --- collect -----------------------------------------------------------


def test_collect_progress_below_amount_not_completed():
    gs = make_game_state(
        {
            "quest009": quest(
                "quest009",
                [{"kind": "collect", "target": "rune_key", "amount": 2}],
            )
        }
    )
    start_quest(gs, "quest009")
    msg = progress_requirement(gs, "collect", "rune_key", amount=1)
    assert msg == "Tidak ada syarat yang sesuai."
    assert gs.player.quests_active["quest009"]["met"] == []
    assert gs.player.quests_active["quest009"]["progress"] == {"rune_key": 1}


def test_collect_progress_meets_amount_completes_quest():
    gs = make_game_state(
        {
            "quest009": quest(
                "quest009",
                [{"kind": "collect", "target": "rune_key", "amount": 1}],
                rewards={"xp": 70, "gold": 20},
                flags_on_complete=["map_ancient_ruins_unlocked"],
            )
        }
    )
    start_quest(gs, "quest009")
    msg = progress_requirement(gs, "collect", "rune_key", amount=1)
    assert msg == "Quest selesai: Quest quest009. Hadiah: 70 XP, 20 emas."
    assert gs.player.quests_done == ["quest009"]
    assert gs.flags.get("map_ancient_ruins_unlocked") is True


def test_collect_uses_absolute_ownership_not_cumulative():
    """amount = jumlah TOTAL dimiliki, bukan penambahan berulang."""
    gs = make_game_state(
        {
            "quest009": quest(
                "quest009",
                [{"kind": "collect", "target": "rune_key", "amount": 3}],
            )
        }
    )
    start_quest(gs, "quest009")
    progress_requirement(gs, "collect", "rune_key", amount=1)
    progress_requirement(gs, "collect", "rune_key", amount=2)
    # Total dimiliki sekarang 2 (bukan 1+2=3) -> belum selesai
    assert gs.player.quests_active["quest009"]["progress"] == {"rune_key": 2}
    progress_requirement(gs, "collect", "rune_key", amount=3)
    assert gs.player.quests_done == ["quest009"]


def test_collect_stays_complete_after_amount_drops():
    """Sekali met, penurunan amount berikutnya tidak membatalkan syarat."""
    gs = make_game_state(
        {
            "quest009": quest(
                "quest009",
                [{"kind": "collect", "target": "rune_key", "amount": 1}],
            )
        }
    )
    start_quest(gs, "quest009")
    progress_requirement(gs, "collect", "rune_key", amount=1)
    assert gs.player.quests_done == ["quest009"]
    # Item dijual lalu progress_requirement dipanggil lagi dengan amount 0 --
    # tidak relevan lagi karena quest sudah selesai dan dihapus dari active.
    msg = progress_requirement(gs, "collect", "rune_key", amount=0)
    assert msg == "Tidak ada syarat yang sesuai."


def test_collect_wrong_target_ignored():
    gs = make_game_state(
        {
            "quest009": quest(
                "quest009",
                [{"kind": "collect", "target": "rune_key", "amount": 1}],
            )
        }
    )
    start_quest(gs, "quest009")
    msg = progress_requirement(gs, "collect", "old_scroll", amount=1)
    assert msg == "Tidak ada syarat yang sesuai."


# --- kill_count ----------------------------------------------------------


def test_kill_count_accumulates_across_calls():
    gs = make_game_state(
        {
            "quest010": quest(
                "quest010",
                [
                    {
                        "kind": "kill_count",
                        "target": "ruins_scavenger",
                        "amount": 3,
                    }
                ],
            )
        }
    )
    start_quest(gs, "quest010")
    progress_requirement(gs, "kill_count", "ruins_scavenger")
    progress_requirement(gs, "kill_count", "ruins_scavenger")
    assert gs.player.quests_active["quest010"]["progress"] == {
        "ruins_scavenger": 2
    }
    msg = progress_requirement(gs, "kill_count", "ruins_scavenger")
    assert msg == "Quest selesai: Quest quest010."
    assert gs.player.quests_done == ["quest010"]


def test_kill_count_default_amount_is_one():
    gs = make_game_state(
        {
            "quest010": quest(
                "quest010",
                [{"kind": "kill_count", "target": "goblin", "amount": 1}],
            )
        }
    )
    start_quest(gs, "quest010")
    msg = progress_requirement(gs, "kill_count", "goblin")
    assert gs.player.quests_done == ["quest010"]
    assert "Quest selesai" in msg


def test_kill_count_mixed_with_talk_requirement():
    gs = make_game_state(
        {
            "quest010": quest(
                "quest010",
                [
                    {"kind": "talk", "target": "ancient_spirit"},
                    {
                        "kind": "kill_count",
                        "target": "ruins_scavenger",
                        "amount": 3,
                    },
                ],
            )
        }
    )
    start_quest(gs, "quest010")
    complete_requirement(gs, "talk", "ancient_spirit")
    for _ in range(3):
        msg = progress_requirement(gs, "kill_count", "ruins_scavenger")
    assert "Quest selesai" in msg
    assert gs.player.quests_done == ["quest010"]


# --- escort ---------------------------------------------------------------


def test_escort_completes_on_matching_from_and_to():
    gs = make_game_state(
        {
            "quest034": quest(
                "quest034",
                [
                    {
                        "kind": "escort",
                        "target": "tom",
                        "from": "burning_village",
                        "to": "rebel_camp",
                    }
                ],
                rewards={"xp": 180, "reputation": {"village": 10}},
            )
        }
    )
    start_quest(gs, "quest034")
    msg = progress_requirement(
        gs,
        "escort",
        "tom",
        to_map="rebel_camp",
        from_map="burning_village",
    )
    assert (
        msg
        == "Quest selesai: Quest quest034. Hadiah: 180 XP, 10 reputasi village."
    )
    assert gs.player.quests_done == ["quest034"]


def test_escort_wrong_destination_not_completed():
    gs = make_game_state(
        {
            "quest034": quest(
                "quest034",
                [
                    {
                        "kind": "escort",
                        "target": "tom",
                        "from": "burning_village",
                        "to": "rebel_camp",
                    }
                ],
            )
        }
    )
    start_quest(gs, "quest034")
    msg = progress_requirement(
        gs, "escort", "tom", to_map="village", from_map="burning_village"
    )
    assert msg == "Tidak ada syarat yang sesuai."
    assert gs.player.quests_active["quest034"]["met"] == []


def test_escort_wrong_origin_not_completed():
    gs = make_game_state(
        {
            "quest034": quest(
                "quest034",
                [
                    {
                        "kind": "escort",
                        "target": "tom",
                        "from": "burning_village",
                        "to": "rebel_camp",
                    }
                ],
            )
        }
    )
    start_quest(gs, "quest034")
    msg = progress_requirement(
        gs, "escort", "tom", to_map="rebel_camp", from_map="village"
    )
    assert msg == "Tidak ada syarat yang sesuai."


def test_escort_wildcard_target_matches_any_npc():
    """Dipakai oleh game.py: _cmd_go memanggil dengan target=None."""
    gs = make_game_state(
        {
            "quest034": quest(
                "quest034",
                [
                    {
                        "kind": "escort",
                        "target": "tom",
                        "from": "burning_village",
                        "to": "rebel_camp",
                    }
                ],
            )
        }
    )
    start_quest(gs, "quest034")
    msg = progress_requirement(
        gs, "escort", None, to_map="rebel_camp", from_map="burning_village"
    )
    assert gs.player.quests_done == ["quest034"]
    assert "Quest selesai" in msg


def test_progress_requirement_no_active_quests_returns_default_message():
    gs = make_game_state()
    assert (
        progress_requirement(gs, "collect", "rune_key", amount=1)
        == "Tidak ada syarat yang sesuai."
    )


def test_progress_requirement_no_player_returns_default_message():
    gs = GameState()
    assert (
        progress_requirement(gs, "kill_count", "goblin")
        == "Tidak ada syarat yang sesuai."
    )
