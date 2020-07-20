from corc import Orchestrator


class ResourcePool:

    resources = {}

    def __init__(self, resources):
        self.resources = resources

    def create_resource(self, providers=None, type=None, spec=None):
        resource = None
        # Create a resource and assign it to the pool,
        # if multiple providers are provided,
        #  usage roundrobin selection for now, given that the
        #   provider can create the specified type
        # Later look at QoS between providers
        # assign (provider, type, spec) as flat dictionary tuple keys
        return resource

    def get_resource(self, providers=None, type=None, spec=None):
        # Try each provider to find the requsted type of resource
        pass


# TODO, resource pools should be put on persistent storage right after creation
# Need to ensure that we don't loose resources
# ALso that it is able to rediscover lost resources after exceptions
# Maybe introduce resourcepool into corc


def create_orchestrator_pool(provider, resource_type, **options):
    # provider == {aws, oci}
    # resource_type == {Resource.Container, Resource.VM}
    # options == kwargs
    orchestrator = Orchestrator.factory(provider, resource_type, **options)
    Orchestrator
    return orchestrator
