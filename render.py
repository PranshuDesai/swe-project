class Renderer:

    def __init__(self):
        self.graphics = "Console"

    def renderGame(self, objects):
        print("\n--- Rendering Game ---")

        for obj in objects:
            print("Object:", obj["type"], "| Health:", obj["health"])

    def updateDisplay(self):
        print("Display Updated")