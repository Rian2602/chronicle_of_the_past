"""Unit test fitur Phase 0: self-buff skill, bos tak bisa kabur, item baru.

Mencakup (§9.4/§19/§21 story-season1-spec.md):
- Skill target-self (war_cry/arcane_barrier/shadow_step/time_study) memakai
  field `buff` → stat naik sementara, durasi habis, XP bonus.
- Bos (tags: ["boss"]) tidak bisa dikaburi.
- Item time_tincture memulihkan MP; smoke_bomb kabur pasti berhasil.
- Save/load combat menyimpan buff.
"""

import pytest

from src.core.randomizer import Randomizer
from src.engine.combat_engine import (
    player_action,
    player_stats,
    start_combat,
    tick_buffs,
    use_item,
)
from src.models.combat_interfaces import CombatAction, CombatResult
from src.models.enemy import Enemy
from src.models.player import Player


def make_player(
    agility=8,
    intelligence=7,
    attack=10,
    defense=5,
    level=1,
    hp=None,
    mp=None,
    learned=None,
    xp_bonus=1.0,
):
    base = {
        "attack": attack,
        "defense": defense,
        "hp": 100,
        "mp": 20,
        "agility": agility,
        "intelligence": intelligence,
    }
    return Player(
        name="Rian",
        class_id="warrior",
        hp=base["hp"] if hp is None else hp,
        mp=base["mp"] if mp is None else mp,
        base_stats=base,
        level=level,
        learned_skills=learned or [],
        xp_bonus=xp_bonus,
    )


def make_enemy(
    hp=50,
    agility=6,
    attack=5,
    defense=2,
    intelligence=3,
    level=2,
    reward=None,
    tags=None,
):
    return Enemy(
        id="goblin",
        name="Goblin",
        level=level,
        stats={
            "attack": attack,
            "defense": defense,
            "hp": hp,
            "mp": 0,
            "agility": agility,
            "intelligence": intelligence,
        },
        loot=[],
        skills=[],
        reward=reward or {},
        tags=tags or [],
    )


def make_buff_skill(skill_id, stat, power, duration, cost=5, name="Buff"):
    return {
        "id": skill_id,
        "name": name,
        "type": "magic",
        "cost": cost,
        "power": 0,
        "target": "self",
        "effects": [],
        "buff": {"stat": stat, "power": power, "duration": duration},
        "requires": {},
        "description": "",
    }


# ---------------------------------------------------------------------------
# Self-buff skill
# ---------------------------------------------------------------------------


def test_self_buff_skill_applies_and_consumes_mp():
    player = make_player(mp=20, learned=["war_cry"])
    enemy = make_enemy()
    skill = make_buff_skill("war_cry", "attack", 5, 2, cost=8)
    state = start_combat(
        player, enemy, Randomizer(seed=7), skills={"war_cry": skill}
    )
    assert player_action(state, CombatAction.SKILL, "war_cry") is False
    assert player.mp == 20 - 8
    assert enemy.stats["hp"] == 50  # tidak menyerang
    buff = state.buffs["player"][0]
    assert buff.stat == "attack"
    assert buff.power == 5
    assert buff.duration == 2
    assert "Serangan meningkat" in state.log[-1]


def test_self_buff_raises_stats_in_player_stats():
    player = make_player(attack=10, learned=["war_cry"])
    state = start_combat(
        player,
        make_enemy(),
        Randomizer(seed=7),
        skills={"war_cry": make_buff_skill("war_cry", "attack", 5, 2, cost=8)},
    )
    player_action(state, CombatAction.SKILL, "war_cry")
    stats = player_stats(state)
    assert stats["attack"] == 15


def test_buff_expires_after_duration():
    player = make_player(mp=50, learned=["arcane_barrier"])
    state = start_combat(
        player,
        make_enemy(),
        Randomizer(seed=7),
        skills={
            "arcane_barrier": make_buff_skill(
                "arcane_barrier", "defense", 6, 1, cost=6
            )
        },
    )
    player_action(state, CombatAction.SKILL, "arcane_barrier")
    assert state.buffs["player"][0].duration == 1
    messages = tick_buffs(state, "player")
    assert any("Buff Pertahanan hilang" in m for m in messages)
    assert state.buffs["player"] == []


def test_duplicate_buff_extends_duration():
    """Aksi kedua: tick di awal giliran (2->1) lalu tambah 2 = 3."""
    player = make_player(mp=50, learned=["war_cry"])
    skill = make_buff_skill("war_cry", "attack", 5, 2, cost=8)
    state = start_combat(
        player,
        make_enemy(),
        Randomizer(seed=7),
        skills={"war_cry": skill},
    )
    player_action(state, CombatAction.SKILL, "war_cry")
    player_action(state, CombatAction.SKILL, "war_cry")
    assert len(state.buffs["player"]) == 1
    assert state.buffs["player"][0].duration == 3


def test_xp_bonus_buff_increases_victory_xp():
    player = make_player(mp=50, learned=["time_study"], xp_bonus=1.0)
    enemy = make_enemy(hp=5, reward={"xp": 100, "gold": 0})
    state = start_combat(
        player,
        enemy,
        Randomizer(seed=7),
        skills={
            "time_study": make_buff_skill(
                "time_study", "xp_bonus", 0.2, 3, cost=4
            )
        },
    )
    player_action(state, CombatAction.SKILL, "time_study")
    player_action(state, CombatAction.ATTACK)
    assert state.result == CombatResult.VICTORY
    assert player.xp == 120  # 100 * (1 + 0.2)


def test_self_buff_skill_respects_mp_cost_and_unlearned():
    player = make_player(mp=3, learned=["war_cry"])
    state = start_combat(
        player,
        make_enemy(),
        Randomizer(seed=7),
        skills={"war_cry": make_buff_skill("war_cry", "attack", 5, 2, cost=8)},
    )
    assert player_action(state, CombatAction.SKILL, "war_cry") is False
    assert "MP tidak cukup" in state.log[-1]
    assert state.buffs == {}

    player2 = make_player(mp=50, learned=["slash"])
    state2 = start_combat(
        player2,
        make_enemy(),
        Randomizer(seed=7),
        skills={"war_cry": make_buff_skill("war_cry", "attack", 5, 2, cost=8)},
    )
    player_action(state2, CombatAction.SKILL, "war_cry")
    assert any("belum mempelajari" in m for m in state2.log)
    assert state2.buffs == {}


# ---------------------------------------------------------------------------
# Bos tidak bisa kabur
# ---------------------------------------------------------------------------


def test_boss_cannot_be_escaped():
    player = make_player(agility=100)
    enemy = make_enemy(tags=["boss"])
    state = start_combat(player, enemy, Randomizer(seed=7))
    assert player_action(state, CombatAction.ESCAPE) is False
    assert state.over is False
    assert state.result is None
    assert any("tidak bisa kabur" in m for m in state.log)


def test_regular_enemy_can_still_escape():
    player = make_player(agility=100)
    enemy = make_enemy()
    state = start_combat(player, enemy, Randomizer(seed=7))
    assert player_action(state, CombatAction.ESCAPE) is False
    assert state.result == CombatResult.ESCAPED
    assert state.over is True


# ---------------------------------------------------------------------------
# Item Phase 0: time_tincture & smoke_bomb
# ---------------------------------------------------------------------------


def _item_def(item_id, **kwargs):
    from src.models.item import Item

    base = {
        "id": item_id,
        "name": item_id,
        "type": "consumable",
        "slot": None,
        "modifiers": {},
        "price": 0,
        "description": "",
    }
    base.update(kwargs)
    return Item(**base)


def test_time_tincture_restores_mp_in_combat():
    player = make_player(mp=5)
    player.inventory.append({"id": "time_tincture", "qty": 1})
    state = start_combat(
        player,
        make_enemy(),
        Randomizer(seed=7),
        items={"time_tincture": _item_def("time_tincture", heal_mp=999)},
    )
    use_item(state, "time_tincture")
    assert player.mp == 20
    assert player.inventory == []
    assert "memulihkan 999 MP" in state.log[-1]


def test_smoke_bomb_guarantees_escape_in_combat():
    player = make_player()
    player.inventory.append({"id": "smoke_bomb", "qty": 1})
    state = start_combat(
        player,
        make_enemy(tags=["boss"]),
        Randomizer(seed=7),
        items={"smoke_bomb": _item_def("smoke_bomb", escape=True)},
    )
    use_item(state, "smoke_bomb")
    assert state.result == CombatResult.ESCAPED
    assert state.over is True
    assert player.inventory == []
    assert "melarikan diri" in state.log[-1]


def _wired_items():
    """Items dict berisi Item objects dari GameContext (seperti Game._wire)."""
    from src.core.game_context import GameContext
    from src.models.item import Item

    ctx = GameContext(data_dir="data")
    return {iid: Item(**data) for iid, data in ctx.items.items()}


def test_smoke_bomb_unusable_out_of_combat():
    from src.core.game_state import GameState
    from src.systems.inventory_system import use_consumable

    gs = GameState()
    gs.items = _wired_items()
    player = make_player()
    player.inventory.append({"id": "smoke_bomb", "qty": 1})
    entry = player.inventory[0]
    message = use_consumable(player, entry, gs)
    assert "hanya bisa dipakai saat bertarung" in message
    assert player.inventory != []


def test_time_tincture_usable_out_of_combat():
    from src.core.game_state import GameState
    from src.systems.inventory_system import use_consumable

    gs = GameState()
    gs.items = _wired_items()
    player = make_player(mp=3)
    player.inventory.append({"id": "time_tincture", "qty": 1})
    entry = player.inventory[0]
    message = use_consumable(player, entry, gs)
    assert "memulihkan 999 MP" in message
    assert player.mp == 20
    assert player.inventory == []


def test_defense_buff_reduces_incoming_damage():
    """arcane_barrier: pertahanan buff menurunkan damage yang diterima."""
    from src.engine.combat_engine import enemy_turn

    def loss_after_enemy_turn(buffed):
        player = make_player(mp=50, defense=5, learned=["arcane_barrier"])
        state = start_combat(
            player,
            make_enemy(attack=20, agility=0, defense=0),
            Randomizer(seed=7),
            skills={
                "arcane_barrier": make_buff_skill(
                    "arcane_barrier", "defense", 6, 1, cost=6
                )
            },
        )
        if buffed:
            player_action(state, CombatAction.SKILL, "arcane_barrier")
        hp_before = player.hp
        enemy_turn(state)
        return hp_before - player.hp

    unbuffed = loss_after_enemy_turn(False)
    buffed = loss_after_enemy_turn(True)
    assert buffed < unbuffed


def test_enemy_buff_increases_its_attack_damage():
    """war_cry musuh: buff attack ikut dipakai saat musuh menyerang."""
    from src.engine import combat_engine
    from src.engine.combat_engine import enemy_turn

    def damage_with_enemy_buff(buffed):
        player = make_player(hp=200)
        enemy = make_enemy(attack=10, agility=100, defense=0)
        enemy.stats["mp"] = 8
        skill = make_buff_skill("war_cry", "attack", 5, 2, cost=8)
        state = start_combat(
            player,
            enemy,
            Randomizer(seed=7),
            skills={"war_cry": skill} if buffed else {},
        )
        if buffed:
            combat_engine._use_enemy_skill(state, skill)
        hp_before = player.hp
        enemy_turn(state)
        return hp_before - player.hp

    buffed = damage_with_enemy_buff(True)
    unbuffed = damage_with_enemy_buff(False)
    assert buffed > unbuffed


def test_enemy_defense_buff_reduces_player_damage():
    """arcane_barrier musuh: buff defense menurunkan damage dari pemain."""
    from src.engine import combat_engine

    def player_damage_with_enemy_buff(buffed):
        player = make_player(hp=200, agility=100, attack=10)
        enemy = make_enemy(attack=0, agility=100, defense=0, hp=500)
        enemy.stats["mp"] = 8
        skill = make_buff_skill("arcane_barrier", "defense", 6, 1, cost=8)
        state = start_combat(
            player,
            enemy,
            Randomizer(seed=7),
            skills={"arcane_barrier": skill} if buffed else {},
        )
        if buffed:
            combat_engine._use_enemy_skill(state, skill)
        hp_before = state.enemy.stats["hp"]
        player_action(state, CombatAction.ATTACK)
        return hp_before - state.enemy.stats["hp"]

    buffed = player_damage_with_enemy_buff(True)
    unbuffed = player_damage_with_enemy_buff(False)
    assert buffed < unbuffed


def test_combat_buffs_survive_save_load():
    """Buff combat tersimpan & direstorasi lewat save/load."""
    from src.core import save_manager
    from src.core.game import Game
    from src.core.game_context import GameContext

    ctx = GameContext(data_dir="data")
    g = Game(ctx, rng_seed=7)
    g.new_game("Rian", "warrior")
    g.state.player.learned_skills.append("war_cry")
    combat = start_combat(
        g.state.player,
        g.state.enemies["goblin"],
        g.randomizer,
        skills=ctx.skills,
        items=g.state.items,
    )
    player_action(combat, CombatAction.SKILL, "war_cry")
    assert combat.buffs["player"][0].stat == "attack"

    import tempfile

    save_path = f"{tempfile.mkdtemp()}/save.json"
    save_manager.save_game(g.state, save_path, combat=combat)
    g2 = Game(ctx, rng_seed=7)
    g2.continue_game(save_path)
    assert g2._combat is not None
    restored = g2._combat.buffs.get("player", [])
    assert restored and restored[0].stat == "attack"
    assert restored[0].duration == combat.buffs["player"][0].duration


def test_item_missing_raises_value_error():
    state = start_combat(make_player(), make_enemy(), Randomizer(seed=7))
    with pytest.raises(ValueError, match="Item tidak dimiliki"):
        use_item(state, "nope")
