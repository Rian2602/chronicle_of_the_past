import random

class Randomizer:
    def __init__(self, seed: int | None = None):
        self._rng = random.Random(seed)
        self.seed = seed

    def roll(self, low: int, high: int) -> int:
        return self._rng.randint(low, high)

    def chance(self, percent: float) -> bool:
        return self._rng.random() * 100 < percent
