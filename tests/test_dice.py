from src.utils.dice import roll

def test_roll_within_range():
    from src.core.randomizer import Randomizer
    r = Randomizer(seed=1)
    for _ in range(100):
        v = roll(r, 0, 5)
        assert 0 <= v <= 5


def test_weighted_choice_prefers_heavier_item():
    from src.core.randomizer import Randomizer
    r = Randomizer(seed=1)
    counts = {"a": 0, "b": 0}
    for _ in range(2000):
        item = r.weighted_choice([("a", 1), ("b", 9)])
        counts[item] += 1
    assert counts["b"] > counts["a"]


def test_weighted_choice_skips_non_positive_weights():
    from src.core.randomizer import Randomizer
    r = Randomizer(seed=1)
    assert r.weighted_choice([("a", 0), ("b", 1)]) == "b"
    assert r.weighted_choice([("a", -5)]) is None
