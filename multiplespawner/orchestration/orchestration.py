from multiplespawner.spawner.selection import Providers
from multiplespawner.runtime.resource import ResourceTypes


class Pool:

    members = {}

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


class CorcPool(Pool):

    # identifier, (orchestrator, resource)
    def create(
        self,
        orchestrator_klass,
        orchestrator_options,
        resource_config=None,
        credentials=None,
    ):
        orchestrator_klass.validate_options(orchestrator_options)
        orchestrator = orchestrator_klass(orchestrator_options)
        # Blocking call
        orchestrator.setup(resource_config=resource_config, credentials=credentials)
        if orchestrator.is_ready():
            identifier, resource = orchestrator.get_resource()
            self.members[identifier] = (orchestrator, resource)
            return identifier, resource
        return None, None

    def endpoint(self, identifier):
        if identifier in self.members:
            orchestrator, resource = self.members[identifier]
            orchestrator.poll()
            if orchestrator.is_reachable():
                return orchestrator.endpoint()
        return None


ResourcePools = {
    ResourceTypes.BARE_METAL: {Providers.LOCAL: CorcPool},
    ResourceTypes.CONTAINER: {},
    ResourceTypes.VIRTUAL_MACHINE: {Providers.OCI: CorcPool},
}

# TODO, resource pools should be put on persistent storage right after creation
# Need to ensure that we don't loose resources
# ALso that it is able to rediscover lost resources after exceptions
# Maybe introduce resourcepool into corc


def load_pool(provider, resource_type):
    pool = None
    if resource_type in ResourcePools:
        pool_type = ResourcePools[resource_type]
        if provider in pool_type:
            pool = pool_type[provider]()
    return pool


def create_pool(providers, resource_type, **kwargs):
    pool = ResourcePools[resource_type](providers)
    return pool


def supported_resource(provider, resource_type):
    if resource_type in ResourcePools and provider in ResourcePools[resource_type]:
        return True
    return False
