import os
import json
from multiplespawner.defaults import default_base_path
from multiplespawner.util import load


def get_spawner_template_path(path=None):
    if "MULTIPLE_SPAWNER_TEMPLATE_FILE" in os.environ:
        path = os.environ["MULTIPLE_SPAWNER_TEMPLATE_FILE"]
    else:
        # If no path is set programmatically
        if not path:
            path = os.path.join(default_base_path, "spawner_templates.json")
    return path


def get_spawner_template(provider, resource_type, path=None):
    if not path:
        path = get_spawner_template_path(path=path)

    templates = load(path, handler=json)
    if not isinstance(templates, list):
        return None
    for template in templates:
        if (
            template["resource_type"] == resource_type
            and provider in template["providers"]
        ):
            return template
    return None


def has_configurer(spawner_template):
    if isinstance(spawner_template, dict):
        return "configurer" in spawner_template
    return False
