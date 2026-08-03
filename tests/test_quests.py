from src.core.game_state import GameState
from src.engine.quest_engine import complete_requirement, start_quest
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
        reputation={"village": 0},
    )


def make_game_state(quests=None):
    gs = GameState()
    gs.player = make_player()
    gs.flags = {}
    gs.quests = quests or {}
    return gs


def quest(quest_id, title=None, requirements=None, rewards=None,
          flags_on_complete=None, next_=None):
    return {
        "id": quest_id,
        "title": title or f"Quest {quest_id}",
        "type": "main",
        "description": "desc",
        "requirements": requirements or [],
        "rewards": rewards or {},
        "flags_on_complete": flags_on_complete,
        "next": next_,
    }


def test_start_quest_activates_with_empty_met():
    gs = make_game_state({"quest001": quest("quest001", title="Temui Kepala Desa")})
    msg = start_quest(gs, "quest001")
    assert msg == "Quest dimulai: Temui Kepala Desa."
    assert gs.player.quests_active == {"quest001": {"met": []}}


def test_start_quest_unknown_id():
    gs = make_game_state()
    assert start_quest(gs, "quest999") == "Quest tidak dikenal: quest999."


def test_start_quest_already_active():
    gs = make_game_state({"quest001": quest("quest001")})
    start_quest(gs, "quest001")
    assert start_quest(gs, "quest001") == "Quest sudah aktif."


def test_start_quest_already_done():
    gs = make_game_state({"quest001": quest("quest001")})
    gs.player.quests_done.append("quest001")
    assert start_quest(gs, "quest001") == "Quest sudah selesai."


def test_complete_requirement_talk_marks_met_and_completes():
    gs = make_game_state({
        "quest001": quest(
            "quest001",
            title="Temui Kepala Desa",
            requirements=[{"kind": "talk", "target": "village_chief"}],
            rewards={"xp": 50, "gold": 20, "reputation": {"village": 10}},
            flags_on_complete=["quest001_done"],
        ),
    })
    start_quest(gs, "quest001")
    msg = complete_requirement(gs, "talk", "village_chief")
    assert msg == "Quest selesai: Temui Kepala Desa."
    assert gs.player.quests_active == {}
    assert gs.player.quests_done == ["quest001"]
    assert gs.player.xp == 50
    assert gs.player.gold == 20
    assert gs.player.reputation == {"village": 10}
    assert gs.flags.get("quest001_done") is True


def test_complete_requirement_reputation_accumulates():
    gs = make_game_state({
        "quest001": quest(
            "quest001",
            requirements=[{"kind": "talk", "target": "village_chief"}],
            rewards={"reputation": {"village": 5}},
        ),
    })
    gs.player.reputation["village"] = 7
    start_quest(gs, "quest001")
    complete_requirement(gs, "talk", "village_chief")
    assert gs.player.reputation == {"village": 12}


def test_complete_requirement_multiple_requirements_need_all_met():
    gs = make_game_state({
        "quest003": quest(
            "quest003",
            requirements=[
                {"kind": "talk", "target": "village_chief"},
                {"kind": "flag", "target": "wolves_defeated"},
            ],
            rewards={"xp": 100},
        ),
    })
    start_quest(gs, "quest003")
    msg = complete_requirement(gs, "talk", "village_chief")
    assert msg == "Tidak ada syarat yang sesuai."
    assert gs.player.quests_active == {"quest003": {"met": [0]}}
    assert gs.player.quests_done == []
    msg = complete_requirement(gs, "flag", "wolves_defeated")
    assert msg == "Quest selesai: Quest quest003."
    assert gs.player.quests_active == {}
    assert gs.player.quests_done == ["quest003"]
    assert gs.player.xp == 100


def test_complete_requirement_flag_kind():
    gs = make_game_state({
        "quest002": quest(
            "quest002",
            title="Bahaya di Hutan",
            requirements=[{"kind": "flag", "target": "wolves_defeated"}],
            rewards={"xp": 40, "gold": 15, "reputation": {"village": 5}},
            flags_on_complete=["quest002_done"],
        ),
    })
    start_quest(gs, "quest002")
    gs.flags["wolves_defeated"] = True
    msg = complete_requirement(gs, "flag", "wolves_defeated")
    assert msg == "Quest selesai: Bahaya di Hutan."
    assert gs.player.quests_done == ["quest002"]
    assert gs.player.xp == 40
    assert gs.player.gold == 15
    assert gs.player.reputation == {"village": 5}
    assert gs.flags.get("quest002_done") is True


def test_complete_requirement_map_kind():
    gs = make_game_state({
        "quest004": quest(
            "quest004",
            requirements=[{"kind": "map", "target": "forest"}],
            rewards={"xp": 10},
        ),
    })
    start_quest(gs, "quest004")
    msg = complete_requirement(gs, "map", "forest")
    assert msg == "Quest selesai: Quest quest004."
    assert gs.player.quests_done == ["quest004"]
    assert gs.player.xp == 10


def test_complete_requirement_no_match():
    gs = make_game_state({
        "quest001": quest(
            "quest001",
            requirements=[{"kind": "talk", "target": "village_chief"}],
        ),
    })
    start_quest(gs, "quest001")
    msg = complete_requirement(gs, "talk", "old_man")
    assert msg == "Tidak ada syarat yang sesuai."
    assert gs.player.quests_active == {"quest001": {"met": []}}


def test_complete_requirement_next_triggers_start_quest():
    quests = {
        "quest001": quest(
            "quest001",
            title="Temui Kepala Desa",
            requirements=[{"kind": "talk", "target": "village_chief"}],
            flags_on_complete="quest001_done",
            next_="quest002",
        ),
        "quest002": quest(
            "quest002",
            title="Bahaya di Hutan",
            requirements=[{"kind": "flag", "target": "wolves_defeated"}],
            flags_on_complete=["quest002_done"],
        ),
    }
    gs = make_game_state(quests)
    start_quest(gs, "quest001")
    msg = complete_requirement(gs, "talk", "village_chief")
    assert msg == "Quest selesai: Temui Kepala Desa. Quest dimulai: Bahaya di Hutan."
    assert gs.player.quests_done == ["quest001"]
    assert gs.player.quests_active == {"quest002": {"met": []}}
    assert gs.flags.get("quest001_done") is True


def test_quest_data_files_load_via_load_json():
    from src.utils.json_loader import load_json

    quest001 = load_json("data/quests/quest001.json")
    quest002 = load_json("data/quests/quest002.json")
    assert quest001["id"] == "quest001"
    assert quest001["title"] == "Temui Kepala Desa"
    assert quest001["requirements"] == [{"kind": "talk", "target": "village_chief"}]
    assert quest001["next"] is None
    assert quest002["id"] == "quest002"
    assert quest002["title"] == "Bahaya di Hutan"
    assert quest002["requirements"] == [{"kind": "flag", "target": "wolves_defeated"}]
    assert quest002["next"] is None
