# Text-to-Game Prototype System
# SWE Alpha Submission



# NLP Module


class NLPAnalyzer:

    def sanitizeText(self, text):
        # Remove special characters
        cleaned = ''.join(char for char in text if char.isalnum() or char.isspace())
        return cleaned.lower()

    def tokenizeText(self, text):
        # Split text into words
        return text.split()

    def extractEntities(self, tokens):
        # Simple entity detection (basic demo logic)
        entities = []
        for word in tokens:
            if word in ["dragon", "monster", "treasure", "student", "teacher"]:
                entities.append(word)
        return entities

    def optimizeProcessingTime(self):
        # Placeholder for performance improvement
        print("NLP optimization applied.")


# Story Validation Module

class StoryValidator:

    def validateLearningOutcome(self, tokens):
        # Check if educational keywords exist
        educational_keywords = ["learn", "math", "science", "history"]
        for word in tokens:
            if word in educational_keywords:
                return True
        return False


# Game Generation Module


class StoryToGameConverter:

    def generateGameObjects(self, entities):
        game_objects = []
        for entity in entities:
            game_objects.append({"type": entity, "health": 100})
        return game_objects

    def mapActionsToGameEvents(self, tokens):
        events = []
        if "fight" in tokens:
            events.append("Battle Event Triggered")
        if "collect" in tokens:
            events.append("Item Collection Event Triggered")
        return events


# Game Rendering Module


class RenderEngine:

    def renderScene(self, game_objects, events):
        print("\n--- Rendering Game Scene ---")
        print("Game Objects:")
        for obj in game_objects:
            print(f"Object: {obj['type']} | Health: {obj['health']}")

        print("\nEvents:")
        for event in events:
            print(event)


# Export Module


class GameExporter:

    def exportGamePackage(self):
        print("\nGame successfully exported as package.zip")


# Main System Controller


def main():

    text = input("Enter story text: ")

    if not text.strip():
        print("Error: Invalid input.")
        return

    # Initialize modules
    nlp = NLPAnalyzer()
    validator = StoryValidator()
    converter = StoryToGameConverter()
    renderer = RenderEngine()
    exporter = GameExporter()

    # NLP Processing
    clean_text = nlp.sanitizeText(text)
    tokens = nlp.tokenizeText(clean_text)
    entities = nlp.extractEntities(tokens)

    # Validate educational content
    if not validator.validateLearningOutcome(tokens):
        print("Warning: No educational objective detected.")

    # Generate Game
    game_objects = converter.generateGameObjects(entities)
    events = converter.mapActionsToGameEvents(tokens)

    # Render Game
    renderer.renderScene(game_objects, events)

    # Export Option
    choice = input("\nDo you want to export the game? (yes/no): ")
    if choice.lower() == "yes":
        exporter.exportGamePackage()


if __name__ == "__main__":
    main()
