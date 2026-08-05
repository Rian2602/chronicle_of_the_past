"""Uji hook engine baru: add_item(collect), combat kill_count, go(escort),
dan hint toko di dialog (§12.1/§12.2 story-season1-spec.md).
"""

from src.core.game import Game
from src.core.game_context import GameContext
from src.core.game_state import GameState
from src.engine.combat_engine import start_combat
from src.models.item import Item
from src.models.player import Player
from src.systems import loot_system
from src.systems.inventory_system import add_item
from src.systems.shop_system import buy

POTION = Item("potion", "Potion", "consumable", heal=50, price=30)
RUNE_KEY = Item("rune_key", "Kunci Batu", "quest", price=0)


def make_player(gold=100):
    return Player(
        name="Rian",
        class_id="warrior",
        hp=100,
        mp=20,
        base_stats={
            "attack": 10,
            "defense": 5,
            "hp": 100,
            "mp": 20,
            "agility": 8,
            "intelligence": 7,
        },
        gold=gold,
    )


def quest(quest_id, requirements, rewards=None):
    return {
        "id": quest_id,
        "title": f"Quest {quest_id}",
        "type": "main",
        "description": "desc",
        "requirements": requirements,
        "rewards": rewards or {},
        "flags_on_complete": None,
        "next": None,
    }


# --- inventory_system.add_item hook (collect) -----------------------------


def test_add_item_without_game_state_unchanged_behavior():
    p = make_player()
    assert add_item(p, "rune_key", 1) is True
    assert p.inventory == [{"id": "rune_key", "qty": 1}]


def test_add_item_with_game_state_progresses_collect_quest():
    gs = GameState()
    gs.player = make_player()
    gs.items = {"rune_key": RUNE_KEY}
    gs.quests = {
        "quest009": quest(
            "quest009",
            [{"kind": "collect", "target": "rune_key", "amount": 1}],
            rewards={"gold": 20},
        )
    }
    from src.engine.quest_engine import start_quest

    start_quest(gs, "quest009")
    add_item(gs.player, "rune_key", 1, game_state=gs)
    assert gs.player.quests_done == ["quest009"]


# --- shop_system.buy hook (collect) ---------------------------------------


def test_shop_buy_progresses_collect_quest():
    gs = GameState()
    gs.player = make_player(gold=100)
    gs.items = {"potion": POTION}
    gs.quests = {
        "quest_buy": quest(
            "quest_buy",
            [{"kind": "collect", "target": "potion", "amount": 2}],
        )
    }
    from src.engine.quest_engine import start_quest

    start_quest(gs, "quest_buy")
    npc = {
        "id": "marcus",
        "name": "Marcus",
        "shop": {"buy": [{"item": "potion", "price": 25}]},
    }
    buy(gs, npc, "potion", 2)
    assert gs.player.quests_done == ["quest_buy"]


# --- game.py integration: go (escort) --------------------------------------


def test_cmd_go_completes_escort_quest(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    g.state.quests["quest_escort"] = quest(
        "quest_escort",
        [
            {
                "kind": "escort",
                "target": "tom",
                "from": "village",
                "to": "forest",
            }
        ],
        rewards={"xp": 100},
    )
    from src.engine.quest_engine import start_quest

    start_quest(g.state, "quest_escort")
    out = g.run_turn("go forest")
    assert "Forest" in out
    assert "quest_escort" in g.state.player.quests_done


def test_cmd_go_wrong_origin_does_not_complete_escort(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    g.state.quests["quest_escort"] = quest(
        "quest_escort",
        [
            {
                "kind": "escort",
                "target": "tom",
                "from": "somewhere_else",
                "to": "forest",
            }
        ],
    )
    from src.engine.quest_engine import start_quest

    start_quest(g.state, "quest_escort")
    g.run_turn("go forest")
    assert "quest_escort" not in g.state.player.quests_done
    assert g.state.player.quests_active["quest_escort"]["met"] == []


# --- game.py integration: combat victory (kill_count) -----------------------


def test_combat_victory_progresses_kill_count_quest(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    g.state.quests["quest_kc"] = quest(
        "quest_kc",
        [{"kind": "kill_count", "target": "wild_wolf", "amount": 2}],
    )
    from src.engine.quest_engine import start_quest

    start_quest(g.state, "quest_kc")
    wolf = g.state.enemies["wild_wolf"]
    for _ in range(2):
        g._combat = start_combat(
            g.state.player,
            wolf,
            g.randomizer,
            skills=ctx.skills,
            loot_resolver=loot_system.roll_loot,
            items=g.state.items,
        )
        g._combat.enemy.stats["hp"] = 1
        g.run_turn("attack")
    assert "quest_kc" in g.state.player.quests_done


# --- dialog_view shop hint via game.py --------------------------------------


def test_talk_shows_shop_hint_when_npc_has_shop(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    ctx.npc["test_merchant"] = {
        "id": "test_merchant",
        "name": "Marcus",
        "location": "village",
        "dialogs": ["dialog_test_merchant"],
        "shop": {"buy": [{"item": "potion", "price": 25}]},
    }
    ctx.dialogues["dialog_test_merchant"] = {
        "id": "dialog_test_merchant",
        "lines": [{"speaker": "test_merchant", "text": "Selamat datang!"}],
        "choices": [],
    }
    g.state.world["village"].npcs = [
        *g.state.world["village"].npcs,
        "test_merchant",
    ]
    out = g.run_turn("talk test_merchant")
    assert "berbelanja" in out
    assert "shop" in out


def test_talk_no_shop_hint_for_npc_without_shop(tmp_path):
    ctx = GameContext(data_dir="data")
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    out = g.run_turn("talk old_man")
    # Dialog non-pedagang tidak menawarkan ajakan berbelanja (hint khusus
    # dialog_view, ditandai teks "Ketik 'shop'"). HUD tetap boleh
    # menampilkan hint toko per peta (§12.2) — itu hint level-peta yang
    # independen dari NPC yang sedang diajak bicara, jadi tidak diuji di
    # sini (lihat test_hud_shows_shop_hint_with_catalog di
    # test_phase1_content.py).
    assert "Ketik 'shop'" not in out
