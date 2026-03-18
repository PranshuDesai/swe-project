class GameEngine:

    def __init__(self):
        self.state = "Idle"
        self.score = 0
        self.gameObjects = []

    def startGame(self, objects):
        self.gameObjects = objects
        self.state = "Running"
        print("\nGame Initialized")

    def updateState(self):
        self.score += 10
        print("Game State Updated | Score:", self.score)

    def endGame(self):
        self.state = "Finished"
        print("\nGame Over")
        print("Final Score:", self.score)