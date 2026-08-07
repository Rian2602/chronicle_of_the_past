from src.core.game_loop import GameSession


def test_direct_dispatch():
    session = GameSession()
    session.new_game("Akar")

    result = session.dispatch("status", [])
    assert len(result) > 0
