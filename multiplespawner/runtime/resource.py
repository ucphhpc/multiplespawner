import enum


class ResourceSpecification:

    memory = 1
    cpu = 1
    accelerators = []

    @staticmethod
    def attributes():
        return ["memory", "cpu", "accelerators"]


class ResourceTypes(enum.Enum):

    BARE_METAL = 1
    VIRTUAL_MACHINE = 2
    CONTAINER = 3
