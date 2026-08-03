from src.models.player import Player
from src.models.map import Map
from src.core.game_state import GameState
from src.ui.renderer import bar, box, ANSI
from src.ui import hud
from src.ui import animation


def test_bar_fraction():
    assert bar(50, 100, width=4) == "██░░"


def test_bar_full_and_empty():
    assert bar(100, 100, width=4) == "████"
    assert bar(0, 100, width=4) == "░░░░"


def test_bar_zero_total():
    assert bar(5, 0, width=4) == "░░░░"


def test_box_ascii_fallback(monkeypatch):
    from src.ui import renderer
    monkeypatch.setattr(renderer, "supports_unicode", lambda: False)
    out = box("hai")
    assert out.splitlines()[0] == "+-----+"
    assert "| hai |" in out


def test_box_contains_lines():
    out = box("baris satu\nbaris dua")
    assert "baris satu" in out and "baris dua" in out


def test_hud_shows_core_info():
    p = Player(name="Rian", class_id="warrior", hp=80, mp=5, gold=30,
               base_stats={"hp": 100, "mp": 10})
    gs = GameState()
    gs.player = p
    gs.current_map = Map(id="village", name="Ashen Village", region="1",
                         threat_level=0, description="", ascii_art="",
                         exits=[], npcs=[], enemy_pool=[])
    out = hud.render(p, gs)
    assert "Rian" in out
    assert "Warrior" in out
    assert "Ashen Village" in out
    assert "morning" in out


def test_hud_no_map_shows_dash():
    p = Player(name="Rian", class_id="warrior", hp=80, mp=5,
               base_stats={"hp": 100, "mp": 10})
    gs = GameState()
    gs.player = p
    assert "—" in hud.render(p, gs)


def test_progress_returns_frames():
    frames = animation.progress("Menyimpan", frames=3)
    assert frames == ["Menyimpan █░░", "Menyimpan ██░", "Menyimpan ███"]
