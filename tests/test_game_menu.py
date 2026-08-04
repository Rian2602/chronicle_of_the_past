import pytest

from src.core.game import Game
from src.core.game_context import GameContext
from src.engine.combat_engine import start_combat
from src.systems import loot_system
from src.ui import game_menu


@pytest.fixture
def ctx():
    return GameContext(data_dir="data")


@pytest.fixture
def game(ctx):
    g = Game(ctx)
    g.new_game("Rian", "warrior")
    return g


def test_build_dispatches_explore_menu(game):
    labels = [label for label, _ in game_menu.build(game)]
    assert labels[0] == "Lihat"
    assert "Jelajah" in labels
    assert "Bantuan" in labels
    assert "Keluar" in labels


def test_build_dispatches_combat_menu(game):
    wolf = game.state.enemies["wild_wolf"]
    game._combat = start_combat(
        game.state.player,
        wolf,
        game.randomizer,
        skills=game.ctx.skills,
        loot_resolver=loot_system.roll_loot,
        items=game.state.items,
    )
    labels = [label for label, _ in game_menu.build(game)]
    assert labels[0] == "Serang"
    assert "Kabur" in labels
    assert "Bertahan" in labels


def test_build_dispatches_dialog_menu(game):
    game.run_turn("talk old_man")
    items = game_menu.build(game)
    labels = [label for label, _ in items]
    assert "Akhiri Percakapan" in labels
    assert game_menu.END_DIALOG in [target for _, target in items]


def test_go_submenu_shows_map_names(game):
    items = game_menu.build(game)
    go_targets = [target for label, target in items if label == "Pergi"]
    assert len(go_targets) == 1
    submenu = go_targets[0]()
    labels = [label for label, _ in submenu]
    targets = [target for _, target in submenu]
    assert "Ashen Forest" in labels
    assert "go forest" in targets
    assert None in targets  # Kembali


def test_talk_submenu_shows_npc_names(game):
    items = game_menu.build(game)
    talk_targets = [target for label, target in items if label == "Bicara"]
    assert len(talk_targets) == 1
    submenu = talk_targets[0]()
    labels = [label for label, _ in submenu]
    targets = [target for _, target in submenu]
    assert "Aria" in labels
    assert "Kepala Desa" in labels
    assert "talk old_man" in targets
    assert None in targets


def test_skill_and_magic_split_by_type(ctx):
    warrior = Game(ctx)
    warrior.new_game("Rian", "warrior")
    mage = Game(ctx)
    mage.new_game("Mia", "mage")
    for g in (warrior, mage):
        wolf = g.state.enemies["wild_wolf"]
        g._combat = start_combat(
            g.state.player,
            wolf,
            g.randomizer,
            skills=g.ctx.skills,
            loot_resolver=loot_system.roll_loot,
            items=g.state.items,
        )
    warrior_labels = [label for label, _ in game_menu.build(warrior)]
    mage_labels = [label for label, _ in game_menu.build(mage)]
    assert "Skill" in warrior_labels  # slash = fisik
    assert "Sihir" not in warrior_labels
    assert "Skill" not in mage_labels  # fireball = magic
    assert "Sihir" in mage_labels


def test_item_submenu_only_consumables(game):
    game.state.player.inventory = [
        {"id": "herb", "qty": 2},
        {"id": "iron_sword", "qty": 1},
    ]
    wolf = game.state.enemies["wild_wolf"]
    game._combat = start_combat(
        game.state.player,
        wolf,
        game.randomizer,
        skills=game.ctx.skills,
        loot_resolver=loot_system.roll_loot,
        items=game.state.items,
    )
    items = game_menu.build(game)
    item_targets = [target for label, target in items if label == "Item"]
    submenu = item_targets[0]()
    labels = [label for label, _ in submenu]
    targets = [target for _, target in submenu]
    assert "item herb" in targets
    assert "item iron_sword" not in targets
    assert "Herb" in labels


def test_builder_defensive_without_state():
    class FakeGame:
        pass

    items = game_menu.build(FakeGame())
    labels = [label for label, _ in items]
    assert "Lihat" in labels
    assert "Keluar" in labels


def test_memories_and_quests_conditional(game):
    labels = [label for label, _ in game_menu.build(game)]
    assert "Kenangan" not in labels
    assert "Quest" not in labels
    game.state.player.memories = [{"title": "M", "text": "T"}]
    game.state.player.quests_active = {"quest001": {}}
    labels = [label for label, _ in game_menu.build(game)]
    assert "Kenangan" in labels
    assert "Quest" in labels
