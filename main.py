from user_input.user_input import UserInput
from nlp.nlp_processor import NLPProcessor
from game.game_generator import GameGenerator
from game.game_engine import GameEngine
from rendering.renderer import Renderer
from player.player import Player


def main():

    userInput = UserInput()
    nlp = NLPProcessor()
    generator = GameGenerator()
    engine = GameEngine()
    renderer = Renderer()
    player = Player()

    text = userInput.getInput()

    if text.strip() == "":
        print("Error: Invalid Input")
        return

    tokens = nlp.processText(text)
    entities = nlp.extractEntities()

    intent = nlp.identifyIntent()
    gameType = generator.identifyGameType(intent)

    rules = generator.createGameRules()

    print("\nGame Type:", gameType)
    print("Game Rules:", rules)

    objects = generator.generateGame(entities)

    engine.startGame(objects)
    renderer.renderGame(objects)

    while engine.state == "Running":

        player.makeMove()
        engine.updateState()
        renderer.updateDisplay()

        if engine.score >= 50:
            engine.endGame()


if __name__ == "__main__":
    main()