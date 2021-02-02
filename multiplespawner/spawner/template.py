import os
from multiplespawner.util import load_config


def get_spawner_template_path(path=None):
    if "MULTIPLE_SPAWNER_TEMPLATE_FILE" in os.environ:
        path = os.environ["MULTIPLE_SPAWNER_TEMPLATE_FILE"]
    else:
        # If no path is set programmatically
        if not path:
            path = os.path.join(
                os.path.expanduser("~"), ".multiplespawner", "spawner_templates.json"
            )
    return path


def get_spawner_template(provider, resource_type, path=None):
    path = get_spawner_template_path(path)
    templates = load_config(path=path)

    if not isinstance(templates, list):
        return None

    for template in templates:
        if (
            template["resource_type"] == resource_type
            and provider in template["providers"]
        ):
            return template
    return None
