
async def schedule(spawner_configuration):
    # Instantiate the class
    class_name = spawner_configuration.class_name
    kwargs = spawner_configuration.kwargs
    ip, port = await class_name.start(**kwargs)
    return ip, port
