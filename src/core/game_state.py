class GameState:
    """Semua data permainan yang bisa disimpan/dimuat."""

    def __init__(self):
        self.player = None
        self.world = {}
        self.flags = {}
        self.time = "morning"
        self.day = 1
        self.current_map = None
        self.enemies = {}
        self.items = {}
        self.quests = {}
        self.memories = []
        self.events = []
        self.rng_seed = None
        self.combat_data = None
