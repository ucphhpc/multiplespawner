class Providers:

    OCI = "oci"
    KU = "ku"
    LOCAL = "local"


def find_spawner(target_resource):
    # Load spawner template file
    spawner_template = None

    # Return the spawner
    return spawner_template


def find_provider(target_resource):
    provider = None
    return provider


def get_available_providers():
    # TODO Load from the providers.json file
    providers = [
        {
            "name": Providers.OCI,
            "display_name": "Oracle Cloud",
            "types": ["container", "virtual_machine"],
        },
        {
            "name": Providers.KU,
            "display_name": "KU Cloud",
            "types": ["container", "virtual_machine"],
        },
        {
            "name": Providers.LOCAL,
            "display_name": "Local machine",
            "types": ["container", "virtual_machine"],
        },
    ]
    return providers
