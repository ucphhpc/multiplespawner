from multiplespawner.runtime.resource import ResourceTypes


class Pool:

    members = {}

    def __init__(self, members):
        self.members = members

    def create(self, *args, **kwargs):
        raise NotImplementedError

    def find(self, *args, **kwargs):
        raise NotImplementedError

    def get(self, identifer):
        if identifer in self.members:
            return self.members[identifer]
        return None

    # def create_resource(self, providers=None, type=None, spec=None):
    #     # {oci, aws}
    #     resource = None
    #     for provider in providers:
    #         # Load provider Orchestrator
    #         self.resources[pro] =

    #     # Create a resource and assign it to the pool,
    #     # if multiple providers are provided,
    #     #  usage roundrobin selection for now, given that the
    #     #   provider can create the specified type
    #     # Later look at QoS between providers
    #     # assign (provider, type, spec) as flat dictionary tuple keys
    #     return resource

    # def get_resource(self, providers=None, type=None, spec=None):
    #     # Try each provider to find the requsted type of resource
    #     pass

    # def migrate_resource(self, from_provider, to_provider):
    #     pass


class ContainerPool(Pool):

    providers = []

    def __init__(self, providers):
        self.providers = providers

    def create(self, specifiation):
        pass

    def find(self, *args, **kwargs):
        pass


class VMPool(Pool):
    def create(self, orchestrator_klass, orchestrator_options, resource_config):
        orchestrator_klass.validate_options(orchestrator_options)
        orchestrator = orchestrator_klass(orchestrator_options)
        # Blocking call
        orchestrator.setup(resource_config)
        if orchestrator.is_ready():
            identifier, resource = orchestrator.get_resource()
            self.members[identifier] = resource
            return identifier, resource
        return None, None


ResourcePools = {
    ResourceTypes.CONTAINER: ContainerPool,
    ResourceTypes.VIRTUAL_MACHINE: VMPool,
}


# TODO, resource pools should be put on persistent storage right after creation
# Need to ensure that we don't loose resources
# ALso that it is able to rediscover lost resources after exceptions
# Maybe introduce resourcepool into corc


def load_pool(provider, resource_type):
    pool = ResourcePools[resource_type](provider)
    return pool


def create_pool(providers, resource_type, **kwargs):
    pool = ResourcePools[resource_type](providers)
    return pool
