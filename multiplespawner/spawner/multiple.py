import os
from jupyterhub.spawner import Spawner
from traitlets import Dict, Unicode, default
from multiplespawner.orchestration.orchestration import create_orchestrator_pool
from multiplespawner.runtime.resource import ResourceSpecification, ResourceTypes
from multiplespawner.session import SessionConfiguration
from multiplespawner.spawner.scheduler import Scheduler, create_schedule_task_template
from multiplespawner.spawner.selection import get_available_providers


class MultipleSpawner(Spawner):

    config_file = Unicode(
        trait=Unicode(),
        default_value=os.path.join(
            os.path.expanduser(".multiplespawner"), "config.json"
        ),
        help="Path to the MultipleSpawner json configuration file",
    )

    notebook = Dict(default_value={}, config=False)

    # TODO, Dynamically load the config file and populate
    # the class properties when the options_form is being rendered
    @default("options_form")
    def _default_options_form(self):
        # Available providers
        providers = get_available_providers()
        default_provider = providers[0]
        option_provider = '<option value="{provider}" {selected}>{provider}</option>'
        provider_options = [
            option_provider.format(
                provider=provider,
                selected="selected" if provider == default_provider else "",
            )
            for provider in providers
        ]

        # Resource Types
        resource_types = ResourceTypes
        default_resource_type = ResourceTypes.CONTAINER
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
            input_entry = '<div class="form-group">'
            label_attribute = (
                '<small class="form-text text-muted">{resource_attr}:</small>'
            )
            input_attribute = '<input name="{resource_attr}" class="form-control" \
                              "type="text" value="{resource_value}" \
                              "placeholder="{resource_attr}">'
            input_end = "</div>"

            resource_spec_options.append(input_entry)
            resource_spec_options.append(
                label_attribute.format(resource_attr=resource_attr)
            )
            resource_spec_options.append(
                input_attribute.format(
                    resource_attr=resource_attr,
                    resource_value=getattr(resource_spec, resource_attr),
                )
            )
            resource_spec_options.append(input_end)

        # Runtime configuration
        session_conf = SessionConfiguration()
        session_conf_attrs = SessionConfiguration.attributes()

        session_options = []
        for session_conf_attr in session_conf_attrs:
            input_entry = '<div class="form-group">'
            label_attribute = (
                '<small class="form-text text-muted">{session_conf_attr}:</small>'
            )
            input_attribute = '<input name="{session_conf_attr}" \
                              "type="text" value="{session_conf_value}" \
                              "placeholder="{session_conf_attr}">'
            input_end = "</div>"
            session_options.append(input_entry)
            session_options.append(
                label_attribute.format(session_conf_attr=session_conf_attr)
            )
            session_options.append(
                input_attribute.format(
                    session_conf_attr=session_conf_attr,
                    session_conf_value=getattr(session_conf, session_conf_attr),
                )
            )
            session_options.append(input_end)

        # Resource type deployments
        # TODO, dynamically provide the deployment dropdown after the
        # selection of a resource type
        form = """
            <label for="provider">Provider:</label>
            <select class="form-control" name="provider" required>
                {provider_options}
            </select>

            <label for="resource_type">Resource Type:</label>
            <select class="form-control" name="resource_type" required>
                {resource_type_options}
            </select>

            <br>
            <label for="resource_specification">Resource Specification:</label>
            {resource_spec_options}

            <br>
            <label for="session_configuration">Session Configuration:</label>
            {session_options}
            <br>
        """.format(
            provider_options=provider_options,
            resource_type_options=resource_type_options,
            resource_spec_options="".join(resource_spec_options),
            session_options="".join(session_options),
        )
        return form

    async def options_from_form(self, formdata):
        """ """
        options = {"spawn_options": {}}

        if "provider" in formdata:
            options["spawn_options"]["provider"] = formdata["provider"][0]

        if "resource_type" in formdata:
            options["spawn_options"]["resource_type"] = formdata["resource_type"][0]

        if "resource_spec" in formdata:
            options["spawn_options"]["resource_spec"] = formdata["resource_spec"][0]
        return options

    def load_state(self, state):
        super().load_state(state)
        self.set_notebook(notebook=state.get("notebook", {}))
        return state

    def get_state(self):
        state = super().get_state()
        notebook = self.get_notebook()
        if notebook:
            state["notebook"] = notebook
            if "scheduler" in notebook:
                state = state["notebook"]["state"] = notebook["scheduler"].call_process(
                    "get_state"
                )
                self.set_notebook(state)
        return state

    def clear_state(self):
        super().clear_state()
        self.set_notebook(clear=True)

    async def start(self):
        # Assign to-be notebook -> so that poll finds it
        self.set_notebook(status="starting")
        spawn_options = self.user_options["spawn_options"]

        resource_type = spawn_options["resource_type"]
        resource_specification = spawn_options["resource_spec"]
        provider = spawn_options["provider"]

        # Resource pools are externally defined and managed

        orchestrator_pool = create_orchestrator_pool(provider, resource_type)
        if not orchestrator_pool:
            raise RuntimeError(
                "Failed to find a orchestrator for provider: {}".format(provider)
            )

        resource = orchestrator_pool.find_resource(
            resource_type, resource_specification
        )
        # The orchesrator will allocate a resource if
        #  none of the specific type or spec is available
        # Might take a long time, hence we ensure there is a adequate start_time
        if not resource:
            # Can take time
            resource = orchestrator_pool.create_resource(
                resource_type, resource_specification
            )
        if not resource:
            raise RuntimeError(
                "Failed to find a resource that match the specified configuration"
            )

        # Pass on the spawner options
        # https://github.com/jupyterhub/wrapspawner/blob/master/wrapspawner/wrapspawner.py
        spawner_options = dict(
            user=self.user,
            db=self.db,
            hub=self.hub,
            authenticator=self.authenticator,
            oauth_client_id=self.oauth_client_id,
            server=self._server,
            config=self.config,
        )

        task_template = create_schedule_task_template(spawner_options)
        if not task_template:
            raise RuntimeError("Failed to configure the scheduler task template")

        self.scheduler = Scheduler(task_template=task_template)
        self.set_notebook(scheduler=self.scheduler)
        ip, port = await self.scheduler.run()

        if not ip or not port:
            self.set_notebook(status="failed")
            raise Exception("Faiiled to schedule the Notebook")

        # TODO, start depends on the spawner used
        self.set_notebook(ip=ip, port=port, status="started")
        return ip, port

    async def stop(self, now=False):
        notebook = self.get_notebook()
        if not notebook:
            return None
        status = await self.poll()
        if status is not None:
            return

        if "scheduler" not in notebook:
            return None

        scheduler = notebook["scheduler"]
        return scheduler.call_process("stop")

    async def poll(self):
        # Returns:
        #   None if single-user process is running.
        #   Integer exit status (0 if unknown), if it is not running.
        current_status = 0
        notebook = self.get_notebook()
        if not notebook:
            return current_status

        if "scheduler" not in notebook:
            return current_status

        scheduler = notebook["scheduler"]
        return scheduler.call_process("poll")

    def get_notebook(self):
        return self.notebook

    def set_notebook(self, clear=False, **kwargs):
        if clear:
            self.notebook.clear()
        else:
            self.notebook.update(**kwargs)
