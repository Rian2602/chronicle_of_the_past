def test_render_scene_boxes_all_lines(monkeypatch):
    from src.ui import story_view
    monkeypatch.setenv("TERM", "xterm-256color")
    scene = {"id": "intro_test", "lines": ["Baris satu.", "Baris dua."]}
    out = story_view.render_scene(scene)
    assert "Baris satu." in out
    assert "Baris dua." in out
    assert out.splitlines()[0].startswith("┌")


def test_render_scene_ascii_fallback(monkeypatch):
    from src.ui import story_view
    monkeypatch.setenv("TERM", "dumb")
    scene = {"id": "intro_test", "lines": ["Halo."]}
    out = story_view.render_scene(scene)
    assert out.splitlines()[0].startswith("+")


def test_render_scene_empty_lines(monkeypatch):
    from src.ui import story_view
    out = story_view.render_scene({"id": "x", "lines": []})
    assert out == ""
