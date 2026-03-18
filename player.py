class Player:

    def __init__(self):
        self.name = "Player1"
        self.score = 0

    def makeMove(self):
        move = input("\nPlayer Move: ")
        return move