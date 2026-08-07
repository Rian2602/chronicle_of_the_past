from src.core.game_loop import GameSession


def test_direct_dispatch():
    session = GameSession()
    session.new_game("Akar")

    result = session.dispatch("status", [])
    assert len(result) > 0


def test_dispatch_none_args():
    session = GameSession()
    session.new_game("Akar")

    # None or omitted args should default safely
    result = session.dispatch("status")
    assert len(result) > 0
    result_none = session.dispatch("status", None)
    assert len(result_none) > 0


def test_empty_action_handling():
    session = GameSession()
    session.new_game("Akar")

    # Dispatching unknown or empty action returns UNAVAILABLE
    result = session.dispatch("")
    assert result == ["Belum tersedia (Fase 1)."]
