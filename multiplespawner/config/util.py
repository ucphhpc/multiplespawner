import json
import os
from multiplespawner.defaults import default_base_path
from multiplespawner.util import makedirs, write, load, remove


def get_config_path(path=None):
    if "MULTIPLE_SPAWNER_CONFIG_FILE" in os.environ:
        path = os.environ["MULTIPLE_SPAWNER_CONFIG_FILE"]
    else:
        # If no path is set programmatically
        if not path:
            path = os.path.join(default_base_path, "config")
    return path


def save_config(config, path=None):
    path = get_config_path(path=path)

    if not os.path.exists(path) and not makedirs(path):
        return False
    if not config:
        return False
    if not write(path, config, handler=json):
        return False
    return True


def update_config(config, path=None):
    path = get_config_path(path=path)
    if not os.path.exists(path):
        raise Exception("Trying to update a config that doesn't exist")

    if not config:
        return False

    # Load config
    existing_config = load_config(path)
    if not existing_config:
        return False

    if not write(path, config, handler=json):
        return False
    return True


def load_config(path=None):
    path = get_config_path(path=path)
    if not os.path.exists(path):
        return False
    return load(path, handler=json)


def config_exists(path=None):
    path = get_config_path(path=path)
    return os.path.exists(path)


def remove_config(path=None):
    path = get_config_path(path=path)
    if not os.path.exists(path):
        return True
    return remove(path)
