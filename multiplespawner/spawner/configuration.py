class SpawnerConfiguration:

    class_name = ""
    kwargs = {}


def configure_spawner(spawner_template, provider=None, resource_specification=None):

    spawner_configuration = SpawnerConfiguration()
    spawner_configuration.class_name = spawner_template["class"]
    spawner_configuration.kwargs = spawner_template["kwargs"]

    return spawner_configuration
