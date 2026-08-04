import random


class Randomizer:
    """Pembungkus acak yang deterministik per seed."""

    def __init__(self, seed: int | None = None):
        self._rng = random.Random(seed)
        self.seed = seed

    def roll(self, low: int, high: int) -> int:
        """Bilangan bulat acak dalam rentang [low, high] (inklusif)."""
        return self._rng.randint(low, high)

    def chance(self, percent: float) -> bool:
        """True dengan peluang `percent` persen."""
        return self._rng.random() * 100 < percent

    def weighted_choice(self, entries) -> object:
        """Pilih satu item sesuai bobot (item, weight)."""
        weighted = [(item, w) for item, w in entries if w > 0]
        if not weighted:
            return None
        total = sum(w for _, w in weighted)
        pick = self._rng.uniform(0, total)
        cumulative = 0
        for item, w in weighted:
            cumulative += w
            if cumulative >= pick:
                return item
        return weighted[-1][0]
