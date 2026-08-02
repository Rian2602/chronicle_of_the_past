from src.utils.dice import roll

def test_roll_within_range():
    from src.core.randomizer import Randomizer
    r = Randomizer(seed=1)
    for _ in range(100):
        v = roll(r, 0, 5)
        assert 0 <= v <= 5
