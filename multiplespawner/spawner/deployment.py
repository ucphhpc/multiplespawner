import os
from multiplespawner.util import load_config


def get_spawner_deployment_path(path=None):
    if "MULTIPLE_SPAWNER_DEPLOYMENT_FILE" in os.environ:
        path = os.environ["MULTIPLE_SPAWNER_DEPLOYMENT_FILE"]
    else:
        # If no path is set programmatically
        if not path:
            path = os.path.join(
                os.path.expanduser("~"), ".multiple_spawner", "spawner_deployments.json"
            )
    return path


def get_spawner_deployment(resource_type, name=None, path=None):
    path = get_spawner_deployment_path(path)
    config = load_config(path=path)

    if not isinstance(config, dict):
        return None

    for deployment_type, deployment in config.items():
        if resource_type == deployment_type:
            if name:
                if name == deployment["name"]:
                    return deployment
            else:
                return deployment
    return None
