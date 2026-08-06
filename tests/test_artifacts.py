"""Pengujian untuk Sistem Artefak Roh (Spirit Artifacts) dan perintah equip."""

import random

from src.core.game_loop import GameSession
from src.core.input import Command
from src.core.state import GameState
from src.engine.items import add_artifact_xp
from src.models.player import Player


def test_cmd_equip_places_artifact_in_equipped(tmp_path):
    """Memastikan perintah equip memindahkan artefak ke slot equipped."""
    session = GameSession(save_dir=tmp_path, rng=random.Random(7))
    player = Player(name="Jin")
    state = GameState(player=player)
    session.state = state

    # Inject an artifact into items and artifacts dicts
    state.inventory["items"]["cermin_bayangan"] = 1
    state.inventory["artifacts"]["cermin_bayangan"] = {"level": 1, "xp": 0}
    cmd = Command(
        name="equip", args=("cermin_bayangan",), raw="equip cermin_bayangan"
    )

    # Akan gagal (RED) karena _cmd_equip belum diimplementasikan di GameSession
    result = session._cmd_equip(cmd)

    assert state.inventory["equipped"].get("cermin_bayangan") == 1
    assert "cermin_bayangan" not in state.inventory["items"]
    assert any("Memakai" in r for r in result)


def test_artifact_level_up(tmp_path):
    """Memastikan XP bertambah dan artefak naik level saat XP cukup."""
    player = Player(name="Jin")
    state = GameState(player=player)
    state.inventory["artifacts"]["cermin_bayangan"] = {"level": 1, "xp": 0}

    # Akan gagal (RED) karena logika add_artifact_xp masih kosong
    add_artifact_xp(state, "cermin_bayangan", 120)

    artifact = state.inventory["artifacts"]["cermin_bayangan"]
    assert artifact["level"] == 2
    assert artifact["xp"] == 20


def test_artifact_bonus_applied_to_stats(tmp_path):
    """Memastikan artefak yang di-equip memberikan bonus stat."""
    player = Player(name="Jin")
    state = GameState(player=player)

    # Base stat (attack) dari player baru biasanya 5
    state.inventory["equipped"]["cermin_bayangan"] = 1
    state.inventory["artifacts"]["cermin_bayangan"] = {"level": 3, "xp": 0}

    # Test property stat yang memperhitungkan equipment.
    # Akan gagal (RED) karena belum diimplementasikan.
    stats = player.effective_stats_with_gear(state)

    # Misalnya level 3 memberikan bonus stat attack.
    assert stats["attack"] > player.stats["attack"]
