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
        resource_types = ResourceTypes
        default_resource_type = resource_types[0]
        option_resource_type = (
            '<option value="{resource_type}" {selected}>{resource_type}</option>'
        )
        resource_type_options = [
            option_resource_type.format(
                resource_type=resource_type,
                selected="selected" if resource_type == default_resource_type else "",
            )
            for resource_type in resource_types
        ]

        # Resource Specification
        resource_spec = ResourceSpecification()
        resource_spec_attrs = ResourceSpecification.attributes()

        resource_spec_options = []
        for resource_attr in resource_spec_attrs:
            input_attribute = (
                '<input name="{resource_attr}" type="text" value="{resource_value}">'
            )
            resource_spec_options.append(
                input_attribute.format(
                    resource_attr=resource_attr,
                    resource_value=getattr(resource_spec, resource_attr),
                )
            )

        # Runtime configuration
        session_conf = SessionConfiguration()
        session_conf_attrs = SessionConfiguration.attributes()

        session_options = []
        for session_conf_attr in session_conf_attrs:
            input_attribute = '<input name="{session_conf_attr}" type="text" value="{session_conf_value}">'
            session_options.append(
                input_attribute.format(
                    session_conf_attr=session_conf_attr,
                    session_conf_value=getattr(session_conf, session_conf_attr),
                )
            )

        # Resource type deployments
        # TODO, dynamically provide the deployment dropdown after the
        # selection of a resource type

        form = """
            <label for="resource_type">Resource Type:</label>
            <select class="form-control" name="resource_type" required>
                {resource_type_options}
            </select>

            <label for="resource_specification">Resource Specification:</label>
            {resource_spec_options}

            <label for="session_configuration">Session Configuration:</label>
            {session_options}
        """.format(
            resource_type_options=resource_type_options,
            resource_spec_options=resource_spec_options,
            session_options=session_options,
        )
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
        self.set_notebook(status="starting")
        resource_type = None
        resource_specification = None
        spawner_template = find_spawner(resource_type)
        # if not a required provider, find an appropriate one

        provider = None
        if "provider" in spawner_template:
            provider = find_provider(resource_type)

        spawner_configuration = configure_spawner(
            spawner_template,
            provider=provider,
            resource_specification=resource_specification,
        )

        # start_timeout (if orchestration -> set this, because the server needs to be running)
        # when the start function returns
        ip, port = await schedule(
            spawner_configuration, **spawner_configuration["kwargs"]
        )

        if not ip or not port:
            self.set_notebook(status="failed")
            raise Exception("")

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
