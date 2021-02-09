import os
import json
from multiplespawner.defaults import default_base_path
from multiplespawner.config.deployment import get_spawner_deployment_path
from multiplespawner.config.template import get_spawner_template_path
from multiplespawner.util import makedirs, write


def create_base_path(path=default_base_path):
    return makedirs(path)


def prepare_multiplespawner_configs(
    base_path=default_base_path, deployment_path=None, template_path=None
):
    if not os.path.exists(base_path) and not create_base_path(base_path):
        return False

    deployment_path = get_spawner_deployment_path(path=deployment_path)
    if not os.path.exists(deployment_path):
        if not write(deployment_path, "{}", handler=json):
            return False

    template_path = get_spawner_template_path(path=template_path)
    if not os.path.exists(template_path):
        if not write(template_path, "{}", handler=json):
            return False
    return True
