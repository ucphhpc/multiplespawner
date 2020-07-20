def find_spawner(target_resource):
    # Load spawner template file
    spawner_template = None

    # Return the spawner
    return spawner_template


def find_provider(target_resource):
    provider = None

    return provider


def get_available_providers():
    # Load from the providers.json file
    providers = [
        {"name": "aws", "types": ["container", "virtual_machine"]},
        {"name": "oci", "types": ["container", "virtual_machine"]},
    ]
    return providers
