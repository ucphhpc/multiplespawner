import enum


class ResourceSpecification:

    memory = 1
    cpus = 1
    accelerators = []

    @staticmethod
    def attributes():
        return ["memory", "cpus", "accelerators"]


class ResourceTypes(enum.Enum):

    BARE_METAL = 1
    VIRTUAL_MACHINE = 2
    CONTAINER = 3
