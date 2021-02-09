import os
from multiplespawner.defaults import default_base_path


def get_configurer_resource_path(path=None, resource_types="playbooks"):
    if "MULTIPLE_SPAWNER_CONFIGURER_RESOURCES_PATH" in os.environ:
        path = os.environ["MULTIPLE_SPAWNER_CONFIGURER_RESOURCES_PATH"]
    else:
        # If no path is set programmatically
        if not path:
            path = os.path.join(default_base_path, "playbooks")
    return path
