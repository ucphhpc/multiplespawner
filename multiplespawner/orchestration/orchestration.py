import flatten_dict
from multiplespawner.runtime.resource import ResourceTypes
from corc.orchestrator import factory


class Pool:

    members = {}

    def __init__(self, members):
        self.members = members

    def create(self, *args, **kwargs):
        raise NotImplementedError

    def find(self, *args, **kwargs):
        raise NotImplementedError

    def get(self, identifer):
        return self.members[identifer]

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

    proviers = []

    def __init__(self, providers):
        self.providers = providers

    def create(self, specifiation):
        pass

    def find(self, *args, **kwargs):
        pass

    def get(self, identifer):
        pass


ResourcePools = {ResourceTypes.CONTAINER: ContainerPool}


# TODO, resource pools should be put on persistent storage right after creation
# Need to ensure that we don't loose resources
# ALso that it is able to rediscover lost resources after exceptions
# Maybe introduce resourcepool into corc


def load_pool(provider, resource_type):
    return {"resources": {"id": {}}}


def create_pool(providers, resource_type, **kwargs):
    pool = ResourcePools[resource_type](providers)
    return pool


def create_orchestrator_pool(provider, resource_type, **options):
    # provider == {aws, oci}
    # resource_type == {Resource.Container, Resource.VM}
    # options == kwargs

    orchestrator = Orchestrator.factory(provider, resource_type, **options)
    Orchestrator
    return orchestrator
