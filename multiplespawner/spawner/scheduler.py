import copy
from multiplespawner.helpers import import_klass


class Scheduler:
    task_template = {}
    process_handler = None

    def __init__(self, task_template=None):
        if not task_template:
            self.task_template = {}
        self.task_template = task_template

        # Instantiate the class
        if "spawner" not in self.task_template:
            return None, None
        spawner = self.task_template["spawner"]

        if "class" not in spawner:
            return None, None

        klass_path = self.task_template["spawner"]["class"].split(".")
        klass = import_klass(".".join(klass_path[:-1]), klass_path[-1])
        if not klass:
            return None, None

        spawner_kwargs = {}
        if "kwargs" in spawner:
            spawner_kwargs = spawner["kwargs"]

        klass_config = {}
        for k, v in spawner_kwargs.items():
            if v == "True":
                v = True
            if v == "False":
                v = False
            if hasattr(klass, k):
                # If a @property -> does it have a setter?
                if isinstance(getattr(klass, k), property):
                    if getattr(klass, k).fset is not None:
                        klass_config[k] = v
                else:
                    klass_config[k] = v

        self.process_handler = klass(**klass_config)
        if "server" in klass_config:
            self.process_handler.server = klass_config["server"]

    async def run(self, options=None):
        if not options:
            options = {}

        return await self.process_handler.start()

    def call_sync_process(self, func_name, *args, **kwargs):
        if not self.process_handler:
            return None

        if hasattr(self.process_handler, func_name) and callable(
            getattr(self.process_handler, func_name)
        ):
            func = getattr(self.process_handler, func_name)
            if func:
                return func(*args, **kwargs)
        return None

    async def call_async_process(self, func_name, *args, **kwargs):
        if not self.process_handler:
            return None

        if hasattr(self.process_handler, func_name) and callable(
            getattr(self.process_handler, func_name)
        ):
            func = getattr(self.process_handler, func_name)
            if func:
                return await func(*args, **kwargs)
        return None


def format_task_template(task_template, **kwargs):
    spawner_str_kwargs = {k:v for k, v in task_template["spawner"]["kwargs"].items()
                          if isinstance(v, str) or isinstance(v, list) or isinstance(v, dict)}
    for key, value in kwargs.items():
        try:
            recursive_format(spawner_str_kwargs, {key: value})
        except TypeError:
            pass

    task_template["spawner"]["kwargs"].update(spawner_str_kwargs)
    return task_template


def create_notebook_task_template(
    spawner_template, spawner_template_config, parent_spawner_config=None
):
    notebook_task_template = {
        "spawner": {
            "class": "jupyterhub.spawner.SimpleLocalProcessSpawner",
            "kwargs": {},
        }
    }

    if "class" in spawner_template:
        notebook_task_template["spawner"]["class"] = spawner_template["class"]

    if parent_spawner_config:
        notebook_task_template["spawner"]["kwargs"].update(parent_spawner_config)

    if "kwargs" in spawner_template:
        notebook_task_template["spawner"]["kwargs"].update(spawner_template["kwargs"])

    if spawner_template_config:
        notebook_task_template["spawner"]["kwargs"].update(spawner_template_config)

    return notebook_task_template


def recursive_format(input, value):
    if isinstance(input, list):
        for item_index, item_value in enumerate(input):
            if isinstance(item_value, str):
                try:
                    input[item_index] = item_value.format(**value)
                except KeyError:
                    continue
            recursive_format(item_value, value)
    if isinstance(input, dict):
        for input_key, input_value in input.items():
            if isinstance(input_value, str):
                try:
                    input[input_key] = input_value.format(**value)
                except KeyError:
                    continue
            recursive_format(input_value, value)
    if hasattr(input, "__dict__"):
        recursive_format(input.__dict__, value)