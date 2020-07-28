class SessionConfiguration:

    # Number of minutes
    lifetime = 120

    @staticmethod
    def attributes():
        return ["lifetime"]

    @staticmethod
    def display_attributes():
        return {
            "lifetime": "How many minutes should it run for?",
        }
