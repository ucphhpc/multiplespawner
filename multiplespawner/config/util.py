import json
import os


def save_config(config, path=None):
    if "MULTIPLESPAWNER_CONFIG_FILE" in os.environ:
        path = os.environ["MULTIPLESPAWNER_CONFIG_FILE"]
    else:
        if not path:
            # Ensure the directory path is there
            path = os.path.join(os.path.expanduser("~"), ".multiplespawner", "config")
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
    if "MULTIPLESPAWNER_CONFIG_FILE" in os.environ:
        path = os.environ["MULTIPLESPAWNER_CONFIG_FILE"]
    else:
        if not path:
            # Ensure the directory path is there
            path = os.path.join(os.path.expanduser("~"), ".multiplespawner", "config")

    if not os.path.exists(path):
        raise Exception("Trying to update a config that doesn't exist")

    if not config:
        return False

    # Load config
    existing_config = load_config(path=path)
    if not existing_config:
        return False

    try:
        with open(path, "w") as fh:
            json.dump(config, fh)
    except Exception as err:
        print("Failed to save config: {}".format(err))
        return False
    return True


def load_config(path=None):
    config = {}
    if "MULTIPLESPAWNER_CONFIG_FILE" in os.environ:
        path = os.environ["MULTIPLESPAWNER_CONFIG_FILE"]
    else:
        if not path:
            path = os.path.join(os.path.expanduser("~"), ".multiplespawner", "config")

    if not os.path.exists(path):
        return False
    try:
        with open(path, "r") as fh:
            config = json.load(fh)
    except Exception as err:
        print("Failed to load config: {}".format(err))
    return config


def config_exists(path=None):
    if "MULTIPLESPAWNER_CONFIG_FILE" in os.environ:
        path = os.environ["MULTIPLESPAWNER_CONFIG_FILE"]
    else:
        if not path:
            path = os.path.join(os.path.expanduser("~"), ".multiplespawner", "config")

    if not path:
        return False

    return os.path.exists(path)


def remove_config(path=None):
    if "MULTIPLESPAWNER_CONFIG_FILE" in os.environ:
        path = os.environ["MULTIPLESPAWNER_CONFIG_FILE"]
    else:
        if not path:
            path = os.path.join(os.path.expanduser("~"), ".multiplespawner", "config")

    if not os.path.exists(path):
        return True
    try:
        os.remove(path)
    except Exception as err:
        print("Failed to remove config: {}".format(err))
        return False
    return True
