class Scheduler:

    task_template = {}

    process_handler = None
    process_options = {}

    def __init__(self, process_options=None, task_template=None):
        if not task_template:
            task_template = {}

        self.task_template = task_template
        if not process_options:
            process_options = {}
        self.process_options = process_options

    async def run(self):
        # Instantiate the class
        if "class_name" not in self.task_template:
            return None, None
        class_name = self.task_template["class_name"]
        self.process_handler = class_name(**self.process_options)

        if "kwargs" not in self.task_template:
            return None, None
        kwargs = self.task_template["kwargs"]
        return self.process_handler.submit(**kwargs)

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


def create_schedule_task_template(options=None):
    if not options:
        options = {}

    # Define class_name (of scheduler)

    task_template = {}
    task_template.update(options)
    return task_template


# Spawner options for the different ResourceTypes

SpawnerOptions = {}
