def test_fixture_wiring(randomizer, game_state):
    roll = randomizer.roll(0, 5)
    assert 0 <= roll <= 5
    assert game_state.time == "morning"
