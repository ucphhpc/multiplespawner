class ResourceSpecification:
    def __init__(self, memory=1, cpu=1, gpu=0):
        self.memory = memory
        self.cpu = cpu
        self.gpu = gpu

    @staticmethod
    def attributes():
        return ["memory", "cpu", "gpu"]

    @staticmethod
    def display_attributes():
        return {
            "memory": "Amount of memory (GB)",
            "cpu": "Number of CPU cores",
            "gpu": "Number of GPUs",
        }


class ResourceTypes:

    BARE_METAL = "bare_metal"
    VIRTUAL_MACHINE = "virtual_machine"
    CONTAINER = "container"

    @staticmethod
    def get(resource_type):
        if hasattr(ResourceTypes, resource_type):
            return getattr(ResourceTypes, resource_type)

    @staticmethod
    def display_attributes():
        return {
            ResourceTypes.BARE_METAL: "Bare Metal Machine",
            ResourceTypes.VIRTUAL_MACHINE: "Virtual Machine",
            ResourceTypes.CONTAINER: "Container",
        }
