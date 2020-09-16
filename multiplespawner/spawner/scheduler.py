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

        spawner_config = {}
        if "config" in spawner:
            spawner_config = spawner["config"]

        klass_path = self.task_template["spawner"]["class"].split(".")
        klass = import_klass(".".join(klass_path[:-1]), klass_path[-1])
        if not klass:
            return None, None

        klass_config = {}
        for k, v in spawner_config.items():
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

    if "kwargs" in spawner_template:
        notebook_task_template["spawner"]["kwargs"].update(spawner_template["kwargs"])

    if "kwargs" in spawner_template_config:
        notebook_task_template["spawner"]["kwargs"].update(
            spawner_template_config["kwargs"]
        )
    return notebook_task_template
