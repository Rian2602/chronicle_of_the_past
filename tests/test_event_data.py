"""Validasi skema data event (GDD §15, AGENTS.md §2.1, §5.1)."""

import json
from pathlib import Path

from src.core.state import FACTIONS
from src.engine.cultivation import load_tiers
from src.engine.event import ACTION_KINDS, FLAG_OPERATORS, TRIGGER_KINDS

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "events"
EXPECTED_EVENTS = {
    "unlock_ruin_shrine",
    "ashfall_memory",
    "day7_dawn",
    "quest101_intro",
    "quest101_done",
    "quest102_intro",
    "shrine_trial_start",
    "quest202_done",
    "shrine_reveal",
    "quest103_done",
    "quest104_intro",
    "quest104_done",
    "quest105_done",
    "quest106_done",
    "quest107_done",
    "quest108_done",
    "fquest_rebels_kiriman_done",
    "fquest_holyorder_mata_done",
    "fquest_hutan_ember_done",
    "fquest_abyssal_done",
    "fquest_kultisi_done",
    "fquest_pelipur_done",
    "fquest_fondasi_done",
    "fquest_hutan_ember_intro",
    "fquest_rebels_kiriman_intro",
    "fquest_pelipur_intro",
    "fquest_kultisi_intro",
    "fquest_holyorder_mata_intro",
    "fquest_abyssal_intro",
    "fquest_fondasi_intro",
    "lin_wei_recruit",
    "quest203_done",
    "quest204_done",
    "quest205_done",
    "quest206_done",
    "quest207_done",
    "quest208_done",
    "macan_baja_recruit",
    "memory_sekte_intrik",
    "fquest_gilda_kontrak_intro",
    "fquest_orde_arsip_intro",
    "fquest_pemberontak_obat_intro",
    "fquest_301_intro",
    "fquest_302_intro",
    "fquest_303_intro",
}
REQUIRED_KEYS = {"id", "trigger", "actions", "once"}


def test_terdapat_file_event_yang_diharapkan():
    """Harus ada event Arc 1 sesuai rencana (unlock, memori, quest, narasi)."""
    files = sorted(path.name for path in DATA_DIR.glob("*.json"))
    expected = sorted(f"{event_id}.json" for event_id in EXPECTED_EVENTS)
    assert files == expected


def test_event_quest_memakai_trigger_dan_aksi_quest():
    """Event quest: intro memakai start_quest, done memakai quest_done."""
    quests_data = {}
    for path in DATA_DIR.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        quests_data[data["id"]] = data
    intro = quests_data["quest101_intro"]
    assert any(
        condition["kind"] == "day_passed" for condition in intro["trigger"]
    )
    assert any(
        action["kind"] == "start_quest" and action["id"] == "quest101"
        for action in intro["actions"]
    )
    done = quests_data["quest101_done"]
    assert any(
        condition["kind"] == "quest_done" and condition["quest"] == "quest101"
        for condition in done["trigger"]
    )


def _validate_trigger(condition: dict, path: Path) -> None:
    """Periksa satu kondisi trigger: kind, operator, dan field wajib."""
    kind = condition.get("kind")
    assert kind in TRIGGER_KINDS, (
        f"{path.name}: kind trigger {kind} tidak dikenal"
    )
    if kind == "flag":
        flag = condition.get("flag")
        assert isinstance(flag, str) and flag, f"{path.name}: flag wajib string"
        operator = condition.get("operator")
        assert operator in FLAG_OPERATORS, (
            f"{path.name}: operator {operator} tidak dikenal"
        )
        if operator != "MISSING":
            assert "value" in condition, f"{path.name}: flag butuh value"
    elif kind == "quest_done":
        assert isinstance(condition.get("quest"), str) and condition["quest"], (
            f"{path.name}: quest wajib string"
        )
    elif kind == "tier_reached":
        assert isinstance(condition.get("tier"), str) and condition["tier"], (
            f"{path.name}: tier wajib string"
        )
    elif kind == "location_entered":
        assert isinstance(condition.get("map"), str) and condition["map"], (
            f"{path.name}: map wajib string"
        )
    elif kind == "day_passed":
        day = condition.get("day")
        assert isinstance(day, int) and day >= 1, (
            f"{path.name}: day wajib int >= 1"
        )


def _validate_action(action: dict, path: Path) -> None:
    """Periksa satu aksi: kind dan field wajib sesuai §15.3."""
    kind = action.get("kind")
    assert kind in ACTION_KINDS, f"{path.name}: kind aksi {kind} tidak dikenal"
    if kind in ("set_flag", "clear_flag"):
        flag = action.get("flag")
        assert isinstance(flag, str) and flag, f"{path.name}: flag wajib string"
        if kind == "set_flag":
            assert "value" in action, f"{path.name}: set_flag butuh value"
    elif kind == "unlock_map":
        target = action.get("target")
        assert isinstance(target, str) and target, (
            f"{path.name}: target wajib string"
        )
    elif kind == "start_quest":
        quest_id = action.get("id")
        assert isinstance(quest_id, str) and quest_id, (
            f"{path.name}: id quest wajib string"
        )
    elif kind == "grant_memory":
        memory_id = action.get("memory_id")
        assert isinstance(memory_id, str) and memory_id, (
            f"{path.name}: memory_id wajib string"
        )
    elif kind == "grant_item":
        item_id = action.get("id")
        count = action.get("count", 1)
        assert isinstance(item_id, str) and item_id, (
            f"{path.name}: id item wajib string"
        )
        assert isinstance(count, int) and count >= 1, (
            f"{path.name}: count wajib int >= 1"
        )
    elif kind == "grant_gold":
        amount = action.get("amount", 0)
        assert isinstance(amount, int) and amount >= 0, (
            f"{path.name}: amount wajib int >= 0"
        )
    elif kind == "change_reputation":
        faction = action.get("faction")
        delta = action.get("delta")
        assert isinstance(delta, int), f"{path.name}: delta wajib int"
        assert faction in FACTIONS, (
            f"{path.name}: faksi {faction} tidak dikenal"
        )
    elif kind == "start_dialog":
        dialog_id = action.get("dialog_id")
        assert isinstance(dialog_id, str) and dialog_id, (
            f"{path.name}: dialog_id wajib string"
        )
    elif kind == "log":
        text = action.get("text")
        assert isinstance(text, str) and text, f"{path.name}: text wajib string"


def test_semua_event_memenuhi_skema():
    """Setiap event memenuhi skema §15.1 dan konvensi AGENTS.md §5."""
    for path in DATA_DIR.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        assert set(data) == REQUIRED_KEYS, f"{path.name}: kunci tidak sesuai"
        assert isinstance(data["id"], str) and data["id"] == path.stem
        assert isinstance(data["once"], bool)
        assert isinstance(data["trigger"], list) and data["trigger"], (
            f"{path.name}: trigger wajib non-kosong"
        )
        assert isinstance(data["actions"], list) and data["actions"], (
            f"{path.name}: actions wajib non-kosong"
        )
        for condition in data["trigger"]:
            assert isinstance(condition, dict)
            _validate_trigger(condition, path)
        for action in data["actions"]:
            assert isinstance(action, dict)
            _validate_action(action, path)


def test_trigger_tier_mengacu_tingkatan_yang_ada():
    """Referensi tier di trigger wajib ter-resolve ke data/cultivation."""
    tier_ids = {tier.id for tier in load_tiers()}
    for path in DATA_DIR.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        for condition in data["trigger"]:
            if condition["kind"] == "tier_reached":
                assert condition["tier"] in tier_ids, (
                    f"{path.name}: tier {condition['tier']} tidak dikenal"
                )
