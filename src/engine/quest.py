"""Engine quest: validasi, kemajuan, dan penyelesaian quest.

Acuan desain: GDD §12 (quest), §15 (event), §24.1 (flag naming).
Interface mengikuti GDD §12.4 (wajib): QuestObjective, Quest,
load_quests, active_quests, check_objective, advance_quest,
complete_quest.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.core.state import GameState

QUEST_DIR = Path(__file__).resolve().parents[2] / "data" / "quests"

# 8 kind requirement (GDD §12.2); dipakai guard engine + validator data.
QUEST_KINDS = {
    "talk",
    "enemy",
    "map",
    "flag",
    "collect",
    "kill_count",
    "escort",
    "breakthrough",
}

_LABEL_PREFIX = {
    "talk": "Bicaralah dengan",
    "enemy": "Kalahkan",
    "map": "Datanglah ke",
    "flag": "Penuhi kondisi",
    "collect": "Kumpulkan",
    "kill_count": "Kalahkan",
    "escort": "Kawal",
    "breakthrough": "Lakukan breakthrough ke",
}


@dataclass(frozen=True)
class QuestObjective:
    """Satu syarat dalam sebuah quest."""

    kind: str  # 8 kind requirement, lihat QUEST_KINDS (GDD §12.2)
    target: str
    count: int = 1


@dataclass(frozen=True)
class Quest:
    """Satu quest (main atau faksi). Skema lengkap di §12.3."""

    id: str
    title: str
    type: str  # 'main' | 'faction'
    description: str
    objectives: list[QuestObjective]
    rewards: dict[str, Any]
    flags_on_complete: list[str]
    next: str | None
    category: str
    requires_flag: str | None = None


def load_quests(data_dir: Path = QUEST_DIR) -> list[Quest]:
    """Muat semua quest dari data/quests/, urut berdasarkan id."""
    quests: list[Quest] = []
    for path in sorted(data_dir.glob("*.json")):
        raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        objectives = [
            QuestObjective(**objective) for objective in raw["objectives"]
        ]
        quests.append(Quest(**{**raw, "objectives": objectives}))
    return quests


def active_quests(state: GameState, quests: list[Quest]) -> list[Quest]:
    """Quest yang started tapi belum done dan requires_flag-nya terpenuhi."""
    active: list[Quest] = []
    for quest in quests:
        if quest.id in state.quests.done:
            continue
        if quest.id not in state.quests.started:
            continue
        if quest.requires_flag and not state.flags.get(quest.requires_flag):
            continue
        active.append(quest)
    return active


def check_objective(state: GameState, quest: Quest, obj_idx: int) -> bool:
    """Kembalikan True bila objective ke-obj_idx sudah terpenuhi di state.

    Semantik per kind (§12.2): talk -> flag talked_<target>; enemy ->
    counter kills >= 1; kill_count -> kills >= count; map -> lokasi saat
    ini; flag -> nilai True; collect -> jumlah item di tas; escort ->
    flag escorted_<target>; breakthrough -> tier pemain. Kind di luar
    daftar ditolak keras (guard di titik evaluasi JSON).
    """
    objective = quest.objectives[obj_idx]
    kind = objective.kind
    if kind not in QUEST_KINDS:
        raise ValueError(f"kind objektif tidak dikenal: {kind}")
    if kind == "talk":
        return state.flags.get(f"talked_{objective.target}") is True
    if kind == "enemy":
        # Honorer count bila diset; default satu kali kalahkan (GDD §12.2).
        return state.kills.get(objective.target, 0) >= max(1, objective.count)
    if kind == "kill_count":
        return state.kills.get(objective.target, 0) >= objective.count
    if kind == "map":
        return state.location == objective.target
    if kind == "flag":
        return state.flags.get(objective.target) is True
    if kind == "collect":
        items = state.inventory.get("items", {})
        return items.get(objective.target, 0) >= objective.count
    if kind == "escort":
        return state.flags.get(f"escorted_{objective.target}") is True
    # kind == "breakthrough"
    return state.player.tier_id == objective.target


def advance_quest(state: GameState, quest: Quest) -> list[str]:
    """Cek semua objective. Bila semua selesai, panggil complete_quest().

    Kembalikan list baris narasi untuk ditampilkan UI. Quest yang sudah
    selesai tidak pernah dievaluasi ulang (idempoten). Semantik
    all([]) = True: quest tanpa objektif langsung selesai (data dengan
    objektif kosong dicegah validator).
    """
    if quest.id in state.quests.done:
        return []
    if all(
        check_objective(state, quest, index)
        for index in range(len(quest.objectives))
    ):
        return complete_quest(state, quest)
    return []


def complete_quest(state: GameState, quest: Quest) -> list[str]:
    """Set quest<id>_done flag, terapkan rewards, set flags_on_complete.

    Tambah quest ke state.quests.done; hapus dari state.quests.started.
    Reward item memakai ``grant_items`` (list) atau ``grant_item``
    (tunggal, kompatibilitas); keduanya menambah inventory.
    Kembalikan list baris narasi.
    """
    if quest.id in state.quests.done:
        return []
    rewards = quest.rewards
    insight = rewards.get("insight", 0)
    gold = rewards.get("gold", 0)
    state.player.add_insight(insight)
    state.player.gold += gold
    for faction, delta in rewards.get("reputation", {}).items():
        state.add_reputation(faction, delta)
    grant_item_lines = []
    raw_grants = rewards.get("grant_items", [])
    if not isinstance(raw_grants, list):
        raise ValueError("grant_items wajib berupa list")
    grants = list(raw_grants)
    if rewards.get("grant_item"):
        grants.append(rewards["grant_item"])
    for grant in grants:
        item_id = grant["id"]
        count = grant.get("count", 1)
        items = state.inventory.setdefault("items", {})
        items[item_id] = items.get(item_id, 0) + count
        grant_item_lines.append(f"Item +{count}: {item_id}.")
    # Flag kelulusan otomatis engine (§12.2) — tidak tergantung data.
    state.flags[f"{quest.id}_done"] = True
    for flag in quest.flags_on_complete:
        state.flags[flag] = True
    if quest.id in state.quests.started:
        state.quests.started.remove(quest.id)
    state.quests.done.append(quest.id)
    lines = [f"Quest selesai: {quest.title}"]
    if insight:
        lines.append(f"Insight +{insight}.")
    if gold:
        lines.append(f"Gold +{gold}.")
    for faction, delta in rewards.get("reputation", {}).items():
        lines.append(f"Reputasi {faction} {delta:+d}.")
    lines.extend(grant_item_lines)
    return lines


def objective_label(objective: QuestObjective) -> str:
    """Label naratif singkat untuk satu objektif (tampilan pemain)."""
    prefix = _LABEL_PREFIX.get(objective.kind, objective.kind)
    if objective.kind in ("kill_count", "collect"):
        return f"{prefix} {objective.target} ({objective.count}x)"
    return f"{prefix} {objective.target}"
