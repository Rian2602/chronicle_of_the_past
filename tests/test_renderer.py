from src.core.game_state import GameState
from src.models.map import Map
from src.models.player import Player
from src.ui import animation, hud
from src.ui.renderer import bar, box


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


def test_bar_and_box_consistent_in_auto_windows(monkeypatch):
    # Regresi: di mode auto+Windows, box memakai ASCII (via supports_unicode)
    # tapi bar lama memakai Unicode karena cek _render_mode == "ascii".
    # Keduanya harus konsisten (sama-sama ASCII).
    from src.ui import renderer

    renderer.set_render_mode("auto")
    monkeypatch.setattr(renderer, "supports_unicode", lambda: False)
    try:
        assert box("hai").splitlines()[0] == "+-----+"
        assert bar(1, 2, width=4) == "##.."
    finally:
        renderer.set_render_mode("auto")


def test_box_contains_lines():
    out = box("baris satu\nbaris dua")
    assert "baris satu" in out and "baris dua" in out


def test_hud_shows_core_info():
    p = Player(
        name="Rian",
        class_id="warrior",
        hp=80,
        mp=5,
        gold=30,
        base_stats={"hp": 100, "mp": 10},
    )
    gs = GameState()
    gs.player = p
    gs.current_map = Map(
        id="village",
        name="Ashen Village",
        region="1",
        threat_level=0,
        description="",
        ascii_art="",
        exits=[],
        npcs=[],
        enemy_pool=[],
    )
    out = hud.render(p, gs)
    assert "Rian" in out
    assert "Warrior" in out
    assert "Ashen Village" in out
    assert "morning" in out


def test_hud_no_map_shows_dash():
    p = Player(
        name="Rian",
        class_id="warrior",
        hp=80,
        mp=5,
        base_stats={"hp": 100, "mp": 10},
    )
    gs = GameState()
    gs.player = p
    assert "—" in hud.render(p, gs)


def test_progress_returns_frames():
    frames = animation.progress("Menyimpan", frames=3)
    assert frames == ["Menyimpan █░░", "Menyimpan ██░", "Menyimpan ███"]


def test_ascii_render_mode_changes_borders_and_bars():
    from src.ui import renderer

    renderer.set_render_mode("ascii")
    try:
        assert box("hai").splitlines()[0] == "+-----+"
        assert bar(1, 2, width=4) == "##.."
    finally:
        renderer.set_render_mode("auto")


def test_unicode_render_mode_forces_unicode_characters():
    from src.ui import renderer

    renderer.set_render_mode("unicode")
    try:
        assert renderer.supports_unicode() is True
        assert box("hai").splitlines()[0] == "┌─────┐"
        assert bar(1, 2, width=4) == "██░░"
    finally:
        renderer.set_render_mode("auto")


def test_animation_delays():
    assert animation.delay_for("normal") == 0.05
    assert animation.delay_for("fast") == 0.01
    assert animation.delay_for("off") is None
