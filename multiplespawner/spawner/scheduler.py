async def schedule(spawner_configuration):

    # Instantiate the class
    class_name = spawner_configuration.class_name
    kwargs = spawner_configuration.kwargs
    yield class_name.start(**kwargs)
