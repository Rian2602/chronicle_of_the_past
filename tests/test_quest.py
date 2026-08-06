"""Test engine quest data-driven (GDD §12) — objektif, penyelesaian, reward."""

import json

import pytest

from src.core.state import GameState
from src.engine.quest import (
    QUEST_KINDS,
    Quest,
    QuestObjective,
    active_quests,
    advance_quest,
    check_objective,
    complete_quest,
    load_quests,
    objective_label,
)
from src.models.player import Player


def _state() -> GameState:
    """State kosong untuk pengujian quest."""
    return GameState(player=Player(name="Akar"))


def _quest(
    objectives: list[QuestObjective] | None = None,
    *,
    quest_id: str = "quest101",
    rewards: dict | None = None,
    flags: list[str] | None = None,
    next_id: str | None = None,
    requires_flag: str | None = None,
) -> Quest:
    """Bangun quest uji ringkas."""
    return Quest(
        id=quest_id,
        title="Uji",
        type="main",
        description="Quest uji.",
        objectives=objectives or [],
        rewards=rewards or {},
        flags_on_complete=flags or [],
        next=next_id,
        category="main",
        requires_flag=requires_flag,
    )


def _obj(kind: str, target: str, count: int = 1) -> QuestObjective:
    """Bangun satu objektif ringkas."""
    return QuestObjective(kind=kind, target=target, count=count)


# ----------------------------------------------------------------------
# Parsing data
# ----------------------------------------------------------------------


def test_load_quests_urut_berdasarkan_id(tmp_path):
    """Quest dimuat urut id; objektif di-parse ke QuestObjective."""
    (tmp_path / "quest102.json").write_text(
        json.dumps(
            {
                "id": "quest102",
                "title": "Dua",
                "type": "main",
                "description": "d",
                "objectives": [{"kind": "map", "target": "ruin_shrine"}],
                "rewards": {},
                "flags_on_complete": [],
                "next": None,
                "category": "main",
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "quest101.json").write_text(
        json.dumps(
            {
                "id": "quest101",
                "title": "Satu",
                "type": "main",
                "description": "d",
                "objectives": [
                    {"kind": "talk", "target": "tuan_shi"},
                    {"kind": "breakthrough", "target": "qi_condensation"},
                ],
                "rewards": {"insight": 50},
                "flags_on_complete": ["quest101_done"],
                "next": "quest102",
                "category": "main",
            }
        ),
        encoding="utf-8",
    )
    quests = load_quests(tmp_path)
    assert [quest.id for quest in quests] == ["quest101", "quest102"]
    assert quests[0].objectives == [
        QuestObjective(kind="talk", target="tuan_shi"),
        QuestObjective(kind="breakthrough", target="qi_condensation"),
    ]
    assert quests[0].next == "quest102"


def test_quest_kinds_memuat_delapan_kind():
    """QUEST_KINDS memuat 8 kind requirement (§12.2)."""
    assert QUEST_KINDS == {
        "talk",
        "enemy",
        "map",
        "flag",
        "collect",
        "kill_count",
        "escort",
        "breakthrough",
    }


# ----------------------------------------------------------------------
# check_objective — 8 kind requirement (§12.2)
# ----------------------------------------------------------------------


def test_objective_talk_memakai_flag_talked():
    """talk: terpenuhi bila flag talked_<target> diset."""
    state = _state()
    objective = _obj("talk", "tuan_shi")
    assert not check_objective(state, _quest([objective]), 0)
    state.flags["talked_tuan_shi"] = True
    assert check_objective(state, _quest([objective]), 0)


def test_objective_enemy_memakai_counter_kills():
    """enemy: terpenuhi bila musuh pernah dikalahkan (kills >= 1)."""
    state = _state()
    state.kills["bandit_perbatasan"] = 1
    objective = _obj("enemy", "bandit_perbatasan")
    assert check_objective(state, _quest([objective]), 0)


def test_objective_kill_count_memakai_jumlah():
    """kill_count: terpenuhi bila jumlah kill mencapai count."""
    state = _state()
    state.kills["bandit_perbatasan"] = 2
    objective = _obj("kill_count", "bandit_perbatasan", count=3)
    assert not check_objective(state, _quest([objective]), 0)
    state.kills["bandit_perbatasan"] = 3
    assert check_objective(state, _quest([objective]), 0)


def test_objective_map_memakai_lokasi_saat_ini():
    """map: terpenuhi bila lokasi pemain sama dengan target."""
    state = _state()
    state.location = "ruin_shrine"
    objective = _obj("map", "ruin_shrine")
    assert check_objective(state, _quest([objective]), 0)


def test_objective_flag_memakai_nilai_true():
    """flag: terpenuhi bila flag target bernilai True."""
    state = _state()
    state.flags["path_unlocked_sword"] = True
    objective = _obj("flag", "path_unlocked_sword")
    assert check_objective(state, _quest([objective]), 0)


def test_objective_collect_memakai_inventory():
    """collect: terpenuhi bila item terkumpul sejumlah count."""
    state = _state()
    state.inventory["items"]["pill_insight"] = 2
    objective = _obj("collect", "pill_insight", count=3)
    assert not check_objective(state, _quest([objective]), 0)
    state.inventory["items"]["pill_insight"] = 3
    assert check_objective(state, _quest([objective]), 0)


def test_objective_escort_memakai_flag_escorted():
    """escort: terpenuhi bila flag escorted_<target> diset."""
    state = _state()
    state.flags["escorted_mei"] = True
    objective = _obj("escort", "mei")
    assert check_objective(state, _quest([objective]), 0)


def test_objective_breakthrough_memakai_tier():
    """breakthrough: terpenuhi bila tier pemain sama dengan target."""
    state = _state()
    objective = _obj("breakthrough", "qi_condensation")
    assert not check_objective(state, _quest([objective]), 0)
    state.player.tier_id = "qi_condensation"
    assert check_objective(state, _quest([objective]), 0)


def test_kind_objective_tidak_dikenal_memunculkan_error():
    """Guard engine: kind objektif di luar daftar ditolak, bukan senyap."""
    state = _state()
    objective = _obj("bogus", "x")
    with pytest.raises(ValueError):
        check_objective(state, _quest([objective]), 0)


# ----------------------------------------------------------------------
# Penyelesaian quest (§12.2, §12.4)
# ----------------------------------------------------------------------


def test_advance_quest_all_objectives_done():
    """advance_quest memanggil complete_quest saat semua objektif selesai."""
    state = _state()
    state.flags["talked_tuan_shi"] = True
    state.player.tier_id = "qi_condensation"
    quest = _quest(
        [
            _obj("talk", "tuan_shi"),
            _obj("breakthrough", "qi_condensation"),
        ],
        quest_id="quest101",
        rewards={"insight": 50, "gold": 20, "reputation": {"ancient_order": 5}},
        flags=["path_unlocked_sword"],
        next_id="quest102",
    )
    state.quests.started.append("quest101")
    lines = advance_quest(state, quest)
    assert lines
    assert state.quests.done == ["quest101"]
    assert state.quests.started == []


def test_quest_complete_sets_flag():
    """Wajib GDD: setelah complete_quest, state.flags[quest101_done] True."""
    state = _state()
    quest = _quest(quest_id="quest101")
    complete_quest(state, quest)
    assert state.flags["quest101_done"] is True


def test_quest_rewards_applied():
    """Wajib GDD: insight, gold, dan reputasi berubah sesuai rewards."""
    state = _state()
    quest = _quest(
        rewards={"insight": 50, "gold": 20, "reputation": {"ancient_order": 5}},
        flags=["path_unlocked_sword"],
    )
    complete_quest(state, quest)
    assert state.player.insight == 50
    assert state.player.gold == 20
    assert state.reputation["ancient_order"] == 5
    assert state.flags["path_unlocked_sword"] is True


def test_advance_quest_belum_semua_tidak_menyelesaikan():
    """advance_quest tanpa semua objektif selesai: tidak menyelesaikan."""
    state = _state()
    state.flags["talked_tuan_shi"] = True  # breakthrough belum
    quest = _quest(
        [
            _obj("talk", "tuan_shi"),
            _obj("breakthrough", "qi_condensation"),
        ],
        quest_id="quest101",
    )
    state.quests.started.append("quest101")
    lines = advance_quest(state, quest)
    assert lines == []
    assert state.quests.started == ["quest101"]
    assert state.quests.done == []


def test_advance_quest_set_flag_quest_done_sendiri():
    """advance_quest men-set quest<id>_done walau tak di flags_on_complete."""
    state = _state()
    state.flags["talked_tuan_shi"] = True
    state.player.tier_id = "qi_condensation"
    quest = _quest(
        [_obj("talk", "tuan_shi"), _obj("breakthrough", "qi_condensation")],
        quest_id="quest101",
    )
    state.quests.started.append("quest101")
    advance_quest(state, quest)
    assert state.flags["quest101_done"] is True


def test_quest_selesai_tidak_dievaluasi_ulang():
    """Quest yang sudah selesai tidak memberi reward dua kali (idempoten)."""
    state = _state()
    quest = _quest(rewards={"insight": 50})
    complete_quest(state, quest)
    again = advance_quest(state, quest)
    assert again == []
    assert state.player.insight == 50


def test_complete_quest_memindahkan_started_ke_done():
    """complete_quest menghapus dari started dan menambah ke done."""
    state = _state()
    quest = _quest(quest_id="quest101")
    state.quests.started.append("quest101")
    complete_quest(state, quest)
    assert state.quests.done == ["quest101"]
    assert state.quests.started == []


# ----------------------------------------------------------------------
# active_quests & label tampilan
# ----------------------------------------------------------------------


def test_active_quests_hanya_started_belum_done():
    """active_quests: quest yang mulai tapi belum selesai."""
    state = _state()
    state.quests.started.append("quest101")
    state.quests.done.append("quest102")
    quests = [_quest(quest_id="quest101"), _quest(quest_id="quest102")]
    assert [q.id for q in active_quests(state, quests)] == ["quest101"]


def test_active_quests_menghormati_requires_flag():
    """active_quests: quest dengan requires_flag menunggu flag terbuka."""
    state = _state()
    quest = _quest(quest_id="quest101", requires_flag="arc1_open")
    state.quests.started.append("quest101")
    assert active_quests(state, [quest]) == []
    state.flags["arc1_open"] = True
    assert [q.id for q in active_quests(state, [quest])] == ["quest101"]


def test_objective_label_menghasilkan_teks_pemain():
    """objective_label memberi label naratif untuk tampilan pemain."""
    assert "tuan_shi" in objective_label(_obj("talk", "tuan_shi"))
    label = objective_label(_obj("kill_count", "bandit_perbatasan", count=3))
    assert label == "Kalahkan bandit_perbatasan (3x)"
