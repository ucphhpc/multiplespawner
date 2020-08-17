import os


def spawner_template_path():
    if "MULTIPLESPAWNER_TEMPLATE_FILE" in os.environ:
        path = os.environ["MULTIPLESPAWNER_TEMPLATE_FILE"]
    else:
        path = os.path.join(
            os.path.expanduser("~"), ".multiplespawner", "spawner_templates.json"
        )
    return path
