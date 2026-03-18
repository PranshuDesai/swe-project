class GameGenerator:

    def __init__(self):
        self.gameType = ""
        self.rules = ""

    def identifyGameType(self, intent):
        if intent == "battle":
            self.gameType = "Battle Game"
        elif intent == "collection":
            self.gameType = "Collection Game"
        else:
            self.gameType = "Exploration Game"

        return self.gameType

    def createGameRules(self):
        if self.gameType == "Battle Game":
            self.rules = "Defeat enemies to win."
        elif self.gameType == "Collection Game":
            self.rules = "Collect items to increase score."
        else:
            self.rules = "Explore the world."

        return self.rules

    def generateGame(self, entities):
        game_objects = []

        for entity in entities:
            game_objects.append({
                "type": entity,
                "health": 100
            })

        return game_objects