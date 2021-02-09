import os
import json
from multiplespawner.defaults import default_base_path
from multiplespawner.util import load


def get_spawner_deployment_path(path=None):
    if "MULTIPLE_SPAWNER_DEPLOYMENT_FILE" in os.environ:
        path = os.environ["MULTIPLE_SPAWNER_DEPLOYMENT_FILE"]
    else:
        # If no path is set programmatically
        if not path:
            path = os.path.join(default_base_path, "spawner_deployments.json")
    return path


def get_spawner_deployment(resource_type, name=None, path=None):
    if not path:
        path = get_spawner_deployment_path(path)
    config = load(path, handler=json)
    if not isinstance(config, dict):
        return None

    for deployment_type, deployments in config.items():
        if resource_type == deployment_type:
            for deployment in deployments:
                if "name" in deployment and name == deployment["name"]:
                    return deployment
    return None
