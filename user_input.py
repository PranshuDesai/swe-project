class UserInput:

    def __init__(self):
        self.text = ""

    def getInput(self):
        self.text = input("Enter Text Description: ")
        return self.text