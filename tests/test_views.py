from src.core.game_state import GameState
from src.core.input_handler import parse_input
from src.models.command import Command
from src.models.player import Player
from src.models.enemy import Enemy
from src.models.item import Item
from src.ui import menu, combat_view, inventory_view, dialog_view
from src.engine.combat_engine import start_combat
from src.core.randomizer import Randomizer


def test_parse_number_to_command():
    c = parse_input("1")
    assert c.action == "select"
    assert c.index == 1


def test_parse_action_trimmed():
    c = parse_input("  attack  ")
    assert c.action == "attack"
    assert c.index is None


def test_parse_action_with_args():
    c = parse_input("go forest")
    assert c.action == "go"
    assert c.args == ["forest"]


def test_command_defaults():
    c = Command(action="rest")
    assert c.args == []
    assert c.index is None


def test_menu_main_highlight():
    out = menu.render_main(0)
    assert "> Permainan Baru" in out
    assert "\n  Lanjutkan" in out


def test_menu_arrow_wrap():
    assert menu.arrow(0, 5) == 1
    assert menu.arrow(4, 5) == 0


def test_class_card_bars():
    card = menu.render_class_card({"id": "warrior", "name": "Warrior",
                                   "stat_bars": {"attack": 4, "defense": 5}})
    assert "Warrior" in card
    assert "Attack" in card
    assert "█" in card


def test_combat_view_contains_actions():
    p = Player(name="Rian", class_id="warrior", hp=100, mp=10,
               base_stats={"hp": 100, "mp": 10, "attack": 12, "defense": 14,
                           "agility": 8, "intelligence": 7})
    e = Enemy(id="goblin", name="Goblin", level=2,
              stats={"attack": 5, "defense": 2, "hp": 5, "mp": 0,
                     "agility": 6, "intelligence": 3},
              loot=[], skills=[])
    state = start_combat(p, e, Randomizer(seed=1))
    out = combat_view.render(state)
    assert "Goblin" in out
    assert "Attack" in out
    assert "Escape" in out


def test_inventory_view_shows_equipment():
    p = Player(name="Rian", class_id="warrior", hp=100, mp=10, base_stats={},
               equipped={"weapon": "iron_sword"},
               inventory=[{"id": "herb", "qty": 2}])
    items = {
        "iron_sword": Item(id="iron_sword", name="Iron Sword", type="weapon",
                           slot="weapon", modifiers={"attack": 8}),
        "herb": Item(id="herb", name="Herb", type="consumable", heal=20),
    }
    out = inventory_view.render(p, items)
    assert "Iron Sword" in out
    assert "weapon" in out
    assert "Herb" in out


def test_dialog_view_numbers_choices():
    gs = GameState()
    dialog = {"id": "d", "lines": [{"speaker": "old_man", "text": "Halo."}],
              "choices": [{"text": "Siapa Anda?", "require_flags": [], "set_flags": [], "next": None}]}
    out = dialog_view.render(dialog, gs)
    assert "old_man" in out
    assert "1. Siapa Anda?" in out


def test_dialog_view_labels_speaker_other_than_npc():
    gs = GameState()
    dialog = {"id": "d",
              "lines": [
                  {"speaker": "old_man", "text": "Halo, pengembara."},
                  {"speaker": "player", "text": "Halo juga."},
              ],
              "choices": []}
    out = dialog_view.render(dialog, gs, npc_id="old_man", npc_name="Orang Tua")
    assert "Orang Tua:" in out
    assert "player:" in out
    assert out.count("Orang Tua:") == 1


def test_dialog_view_labels_npc_by_name():
    gs = GameState()
    dialog = {"id": "d", "lines": [{"speaker": "old_man", "text": "Halo."}],
              "choices": []}
    out = dialog_view.render(dialog, gs, npc_id="old_man", npc_name="Orang Tua")
    assert "Orang Tua:" in out


def test_dialog_view_labels_other_speaker_by_id(monkeypatch):
    import os
    monkeypatch.setenv("TERM", "xterm-256color")
    # Force reload so supports_unicode() picks up the new TERM value
    import importlib
    import src.ui.renderer as renderer_mod
    importlib.reload(renderer_mod)
    import src.ui.dialog_view as dv_mod
    importlib.reload(dv_mod)

    gs = GameState()
    dialog = {"id": "d",
              "lines": [{"speaker": "old_man", "text": "Halo."},
                        {"speaker": "player", "text": "Halo juga."},
                        {"speaker": "", "text": "lanjutan"}],
              "choices": []}
    out = dv_mod.render(dialog, gs, npc_id="old_man", npc_name="Orang Tua")
    assert "Orang Tua:\n\u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510\n\u2502 Halo. \u2502" in out
    assert "player:\n\u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510\n\u2502 Halo juga. \u2502" in out
