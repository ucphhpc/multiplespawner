class SessionConfiguration:
    def __init__(self, lifetime=120):
        self.lifetime = lifetime

    @staticmethod
    def attributes():
        return ["lifetime"]

    @staticmethod
    def display_attributes():
        return {
            "lifetime": "How many minutes should it run for?",
        }
