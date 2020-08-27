import os
import json


def get_config_path(path=None):
    if "MULTIPLE_SPAWNER_CONFIG_FILE" in os.environ:
        path = os.environ["MULTIPLE_SPAWNER_CONFIG_FILE"]
    else:
        # If no path is set programmatically
        if not path:
            path = os.path.join(os.path.expanduser("~"), ".multiplespawner", "config")
    return path


def save_config(config, path=None):
    path = get_config_path(path)
    dir_path = os.path.dirname(path)
    if not os.path.exists(dir_path):
        try:
            os.makedirs(os.path.dirname(path))
        except Exception as err:
            print("Failed to create config directory: {}".format(err))

    if not config:
        return False

    try:
        with open(path, "w") as fh:
            json.dump(config, fh)
    except Exception as err:
        print("Failed to save config: {}".format(err))
        return False
    return True


def update_config(config, path=None):
    path = get_config_path(path)
    if not config:
        return False

    try:
        with open(path, "w") as fh:
            json.dump(config, fh)
    except Exception as err:
        print("Failed to save config: {}".format(err))
        return False
    return True


def load_config(path=None):
    path = get_config_path(path)
    if not os.path.exists(path):
        return False

    config = {}
    try:
        with open(path, "r") as fh:
            config = json.load(fh)
    except Exception as err:
        print("Failed to load config: {}".format(err))
    return config


def config_exists(path=None):
    path = get_config_path(path)
    if not path:
        return False
    return os.path.exists(path)


def remove_config(path=None):
    path = get_config_path(path=path)

    if not os.path.exists(path):
        return True
    try:
        os.remove(path)
    except Exception as err:
        print("Failed to remove config: {}".format(err))
        return False
    return True
