import os
from jupyterhub.spawner import Spawner
from textwrap import dedent
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
from multiplespawner.runtime.resource import ResourceSpecification, ResourceTypes
from multiplespawner.session import SessionConfiguration


class MultipleSpawner(Spawner):

    config_file = String(
        trait=Unicode(),
        default_value=os.path.join(
            os.path.expanduser(".multiplespawner"), "config.json"
        ),
        help="Path to the MultipleSpawner json configuration file",
    )

    notebook = Dict(default_value=None, config=False)

    # TODO, Dynamically load the config file and populate
    # the class properties when the options_form is being rendered
    @default("options_form")
    def _default_options_form(self):
        # Resource Types
        # resource_types = ResourceTypes

        # # Resource Specification
        # resource_spec = ResourceSpecification()
        # resource_spec_attrs = ResourceSpecification.attributes()

        # resource_options = []
        # for resource_attr in resource_spec_attrs:
        #     option_attribute = (
        #         '<option value="{resource_attr}">{resource_attr}</option>'
        #     )
        #     resource_options.append(
        #         option_attribute.format(
        #             resource_attr=getattr(resource_spec, resource_attr),
        #         )
        #     )

        # # Runtime configuration
        # # Resource specs
        # option_spec = (
        #     '<option value="{resource_spec}" {selected}>{resource_spec}</option>'
        # )
        # spec_options = [
        #     option_spec.format(
        #         resource_spec=resource_spec,
        #         selected="selected" if resource_spec == default_spec else "",
        #     )
        #     for resource_spec in resource_specs
        # ]

        # session_conf_attrs = SessionConfiguration.attributes()

        # form = """ """
        # for 


        # form = """
        #     <label for="resource_options">Resource Configuration:</label>
        #     <input ></input>

        #     <select class="form-control" name="resource_options" required autofocus>
        #         {resource_options}
        #     </select>

        #     <label for="resource_spec">Select a Resource Spec:</label>
        #     <select class="form-control" name="resource_spec" required>
        #         {spec_options}
        #     </select>
        # """.format(
        #     type_options=type_options,
        #     spec_options=spec_options
        # )

        form = """ """
        # TODO, add javascript to form -> present either
        # option to select environment or image
        return form

    async def options_from_form(self, formdata):
        """ """
        options = {}
        if "resource_type" in formdata:
            options["resource_type"] = formdata["resource_type"][0]

        if "resource_spec" in formdata:
            options["resource_spec"] = formdata["resource_spec"][0]

        return options


    def load_state(self, state):
        super(MultipleSpawner, self).load_state(state)
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
        # Combine both resource specification
        # Depends on specified resource type on how we request the resource specification
        self.set_notebook(status="starting")
        ip, port = ("0", 80)

        # Translate the resource type into a Spawner type
        # Find a plausible Spawner configuration
        # Same resource type
        resource_type = None
        spawner = select_spawner(resource_type)
        # if not a required provider, find an appropriate one
        provider = find_provider(resource_type)

        scheduled = schedule(spawner)


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
