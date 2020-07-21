

class ResourceSpecification:

    memory = 1
    cpus = 1
    accelerators = []

    @staticmethod
    def attributes():
        return ["memory", "cpus", "accelerators"]


class ResourceTypes:

    BARE_METAL = "bare_metal"
    VIRTUAL_MACHINE = "virtual_machine"
    CONTAINER = "container"
