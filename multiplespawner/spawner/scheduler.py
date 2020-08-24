from multiplespawner.helpers import import_klass

class Scheduler:

    task_template = {}

    process_handler = None
    runner_config = {}

    def __init__(self, runner_config=None, task_template=None):
        
        if not task_template:
            self.task_template = {}
        self.task_template = task_template

        if not runner_config:
            runner_config = {}
        self.runner_config = runner_config

    async def run(self, options=None):
        if not options:
            options = {}

        # Instantiate the class
        if "spawner" not in self.task_template:
            return None, None
        spawner = self.task_template["spawner"]

        if "class" not in spawner:
            return None, None

        klass_path = self.task_template["spawner"]["class"].split(".")
        klass = import_klass(klass_path[:-1], klass_path[-1])
        if not klass:
            return None, None

        self.process_handler = klass(**self.runner_config)
        return self.process_handler.start(**options)

    async def call_process(self, func_name, **kwargs):
        if not self.process_handler:
            return None

        if hasattr(self.process_handler, func_name) and callable(
            self.process_handler + ".{}".format(func_name)
        ):
            func = getattr(self.process_handler, func_name)
            if func:
                return func(**kwargs)
        return None


# async def schedule(configuration=None):
#     if not configuration:
#         configuration = {}

#     # Instantiate the class
#     if 'class_name' not in configuration:
#         return None, None
#     class_name = configuration["class_name"]

#     if "kwargs" not in configuration:
#         return None, None
#     kwargs = configuration["kwargs"]

#     ip, port = await class_name.start(**kwargs)
#     return ip, port


def create_schedule_task_template(task_template=None):
    if not task_template:
        task_template = {}

    # Define class_name (of scheduler)
    task_template = {}
    task_template.update(runner_config)
    return task_template


# Spawner runner_config for the different ResourceTypes
