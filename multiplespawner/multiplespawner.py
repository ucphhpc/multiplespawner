import os
from jupyterhub.spawner import Spawner
from traitlets import (
    Any,
    Bool,
    CaselessStrEnum,
    String,
    Dict,
    List,
    Int,
    Unicode,
    Union,
    default,
    observe,
    validate,
)


class MultipleSpawner(Spawner):

    resource_types = List(
        trait=Unicode(),
        allow_none=False,
        default_value=["Virtual Machine", "Container"],
        help="The list of available resource types",
    )

    resource_specs = List(
        trait=Unicode(),
        allow_none=False,
        default_value=[],
        help="The list of available resource specifications",
    )

    # [{"name": "Default",
    #     "disk": "10_gb",
    #     "memory": "2_gb"
    #     "accelerators": []}]

    config_file = String(
        trait=Unicode(),
        default_value=os.path.join(
            os.path.expanduser(".jupyterhub/multiplespawner.json ")
        ),
        help="Path to the Multiple Spawner json configuration file",
    )

    notebook = Dict(default_value=None, config=False)

    # TODO, Dynamically load the config file and populate the class properties when the options_form is being rendered
    @default("options_form")
    def _default_options_form(self):
        resource_types = self._get_resource_types()
        default_type = resource_types[0]

        resource_specs = self._get_resource_specs()
        default_spec = resource_specs[0]

        # TODO, add resource_lifetime, hours, min, secs

        option_type = (
            '<option value="{resource_type}" {selected}>{resource_type}</option>'
        )
        type_options = [
            option_type.format(
                resource_type=resource_type,
                selected="selected" if resource_type == default_type else "",
            )
            for resource_type in resource_types
        ]

        option_spec = (
            '<option value="{resource_spec}" {selected}>{resource_spec}</option>'
        )
        spec_options = [
            option_spec.format(
                resource_spec=resource_spec,
                selected="selected" if resource_spec == default_spec else "",
            )
            for resource_spec in resource_specs
        ]

        form = """
            <label for="resource_type">Select a Resource Type:</label>
            <select class="form-control" name="resource_type" required autofocus>
                {type_options}
            </select>

            <label for="resource_spec">Select a Resource Spec:</label>
            <select class="form-control" name="resource_spec" required>
                {spec_options}
            </select>
        """.format(
            type_options=type_options, spec_options=spec_options
        )

        # TODO, add javascript to form -> present either option to select environment or image
        return form

    async def options_from_form(self, formdata):
        """ """
        options = {}
        if "resource_type" in formdata:
            options["resource_type"] = formdata["resource_type"][0]

        if "resource_spec" in formdata:
            options["resource_spec"] = formdata["resource_spec"][0]

        return options

    def _get_resource_types(self):
        return self.resource_types

    def _get_resource_specs(self):
        return self.resource_specs

    def load_state(self):
        state = super(MultipleSpawner, self).load_state(self)
        self.set_notebook(id=state.get("notebook_id", ""))
        return state

    def get_state(self):
        state = super(MultipleSpawner, self).get_state()
        notebook = yield self.get_notebook()
        if notebook["id"]:
            state["notebook_id"] = notebook["id"]
        return state

    def clear_state(self):
        super(MultipleSpawner, self).clear_state()
        self.set_notebook(clear=True)

    async def start(self):
        # Assign to-be notebook -> so that poll finds it
        self.set_notebook(status="starting")
        ip, port = ("0", 80)

        # TODO, start depends on the spawner used

        self.set_notebook(ip=ip, port=port, status="started")
        return ip, port

    async def stop(self, now=False):
        status = await self.poll()
        if status is not None:
            return
        # TODO, stop depends on the specific spawner used
        return None

    async def poll(self):
        # Returns:
        #   None if single-user process is running.
        #   Integer exit status (0 if unknown), if it is not running.
        current_status = 0
        notebook = yield self.get_notebook()
        if not notebook:
            return current_status

        if notebook["status"] == "starting" or notebook["status"] == "started":
            return None

        return current_status

    async def get_notebook(self):
        return self.notebook

    def set_notebook(self, clear=False, **kwargs):
        if clear:
            self.notebook.clear()
        else:
            self.notebook.update(**kwargs)
