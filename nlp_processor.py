class NLPProcessor:

    def __init__(self):
        self.tokens = []
        self.entities = []

    def processText(self, text):
        cleaned = ''.join(c for c in text if c.isalnum() or c.isspace())
        self.tokens = cleaned.lower().split()
        return self.tokens

    def extractEntities(self):
        entity_list = ["dragon", "monster", "treasure", "student", "teacher"]

        for token in self.tokens:
            if token in entity_list:
                self.entities.append(token)

        return self.entities

    def identifyIntent(self):
        if "fight" in self.tokens:
            return "battle"
        elif "collect" in self.tokens:
            return "collection"
        else:
            return "exploration"