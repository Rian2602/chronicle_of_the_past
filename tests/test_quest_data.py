"""Validasi skema data quest (GDD §12.3, AGENTS.md §2.1, §5.1)."""

import json
import re
from pathlib import Path

from src.core.state import FACTIONS
from src.engine.quest import QUEST_KINDS

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "quests"
NPC_DIR = Path(__file__).resolve().parents[1] / "data" / "npc"
EXPECTED_QUESTS = {
    "quest101",
    "quest102",
    "quest103",
    "quest104",
    "quest105",
    "quest106",
    "quest107",
    "quest108",
    "quest201",
    "fquest_rebels_kiriman",
    "fquest_holyorder_mata",
    "fquest_hutan_ember",
    "fquest_abyssal",
    "fquest_kultisi",
    "fquest_pelipur",
    "fquest_fondasi",
}
REQUIRED_KEYS = {
    "id",
    "title",
    "type",
    "description",
    "objectives",
    "rewards",
    "flags_on_complete",
    "next",
    "category",
    "requires_flag",
}


def test_terdapat_file_quest_yang_diharapkan():
    """Harus ada quest Arc 1 sesuai rencana (quest101)."""
    files = sorted(path.name for path in DATA_DIR.glob("*.json"))
    expected = sorted(f"{quest_id}.json" for quest_id in EXPECTED_QUESTS)
    assert files == expected


def _validate_rewards(data: dict, path: Path) -> None:
    """Reward: insight/gold >= 0, reputasi ke faksi yang dikenal (§8)."""
    rewards = data.get("rewards")
    assert isinstance(rewards, dict), f"{path.name}: rewards wajib objek"
    insight = rewards.get("insight", 0)
    gold = rewards.get("gold", 0)
    assert isinstance(insight, int) and insight >= 0, (
        f"{path.name}: insight wajib int >= 0"
    )
    assert isinstance(gold, int) and gold >= 0, (
        f"{path.name}: gold wajib int >= 0"
    )
    for faction, delta in rewards.get("reputation", {}).items():
        assert faction in FACTIONS, (
            f"{path.name}: faksi {faction} tidak dikenal"
        )
        assert isinstance(delta, int), f"{path.name}: delta reputasi wajib int"


def test_quest_data_valid():
    """Wajib GDD §12.4: semua file JSON di data/quests/ ter-resolve."""
    for path in DATA_DIR.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        assert set(data) == REQUIRED_KEYS, f"{path.name}: kunci tidak sesuai"
        assert isinstance(data["id"], str) and data["id"] == path.stem
        assert isinstance(data["title"], str) and data["title"]
        assert data["type"] in ("main", "faction"), f"{path.name}: type invalid"
        assert isinstance(data["description"], str) and data["description"]
        assert isinstance(data["objectives"], list) and data["objectives"], (
            f"{path.name}: objectives wajib non-kosong"
        )
        for objective in data["objectives"]:
            assert isinstance(objective, dict)
            kind = objective.get("kind")
            assert kind in QUEST_KINDS, (
                f"{path.name}: kind {kind} tidak dikenal"
            )
            target = objective.get("target")
            assert isinstance(target, str) and target, (
                f"{path.name}: target wajib string"
            )
            count = objective.get("count", 1)
            assert isinstance(count, int) and count >= 1, (
                f"{path.name}: count wajib int >= 1"
            )
        _validate_rewards(data, path)
        assert isinstance(data["flags_on_complete"], list)
        assert f"{data['id']}_done" in data["flags_on_complete"], (
            f"{path.name}: wajib memuat quest<id>_done (konvensi §12.3)"
        )
        next_id = data.get("next")
        if next_id is not None:
            assert re.fullmatch(r"quest\d+", next_id), (
                f"{path.name}: next harus format quest<nomor>"
            )
        assert isinstance(data["category"], str) and data["category"]
        requires_flag = data.get("requires_flag")
        assert requires_flag is None or isinstance(requires_flag, str)


def test_referensi_talk_ter_resolve_ke_npc():
    """Target kind talk wajib ada sebagai file NPC di data/npc/."""
    for path in DATA_DIR.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        for objective in data["objectives"]:
            if objective["kind"] == "talk":
                npc_file = NPC_DIR / f"{objective['target']}.json"
                assert npc_file.is_file(), (
                    f"{path.name}: NPC {objective['target']} tidak ditemukan"
                )
