class GameState:
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
