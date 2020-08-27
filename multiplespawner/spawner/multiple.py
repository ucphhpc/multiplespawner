import os
import time
from jupyterhub.spawner import Spawner
from traitlets import Dict, Unicode, default, Integer
from multiplespawner.orchestration.orchestration import create_pool, load_pool
from multiplespawner.runtime.resource import ResourceSpecification, ResourceTypes
from multiplespawner.session import SessionConfiguration
from multiplespawner.spawner.scheduler import Scheduler, create_notebook_task_template
from multiplespawner.spawner.selection import get_available_providers
from multiplespawner.spawner.template import get_spawner_template
from multiplespawner.spawner.deployment import get_spawner_deployment

from corc.providers.types import get_orchestrator
from corc.providers.config import get_provider_profile


class MultipleSpawner(Spawner):

    config_file = Unicode(
        trait=Unicode(),
        default_value=os.path.join(
            os.path.expanduser(".multiplespawner"), "config.json"
        ),
        help="Path to the MultipleSpawner json configuration file",
    )

    notebook = Dict(default_value={}, config=False)

    resource_id = Unicode()

    resource_configuration_timeout = Integer(
        default_value=30, allow_none=False, config=True
    )

    # TODO, Dynamically load the config file and populate
    # the class properties when the options_form is being rendered
    @default("options_form")
    def _default_options_form(self):
        # Available providers
        providers = get_available_providers()
        default_provider = providers[0]
        option_provider = (
            '<option value="{provider}" {selected}>{provider_description}</option>'
        )
        provider_options = [
            option_provider.format(
                provider=provider["name"],
                provider_description=provider["display_name"],
                selected="selected" if provider == default_provider else "",
            )
            for provider in providers
        ]

        # Resource Types
        resource_types = ResourceTypes.display_attributes()
        default_resource_type = ResourceTypes.VIRTUAL_MACHINE
        option_resource_type = (
            '<option value="{resource_type}" {selected}>{resource_description}</option>'
        )
        resource_type_options = [
            option_resource_type.format(
                resource_type=resource_type,
                resource_description=display_value,
                selected="selected" if resource_type == default_resource_type else "",
            )
            for resource_type, display_value in resource_types.items()
        ]

        # Resource Specification
        resource_spec = ResourceSpecification()
        resource_spec_attrs = ResourceSpecification.display_attributes()

        resource_spec_options = []
        input_entry = '<div class="form-group" name="resource_specification">'
        resource_spec_options.append(input_entry)
        for resource_attr, display_value in resource_spec_attrs.items():
            label_attribute = (
                '<small class="form-text text-muted">{resource_description}:</small>'
            )
            input_attribute = '<input name="{resource_attr}" class="form-control" \
                              "type="text" value="{resource_value}" \
                              "placeholder="{resource_description}">'
            resource_spec_options.append(
                label_attribute.format(resource_description=display_value)
            )
            resource_spec_options.append(
                input_attribute.format(
                    resource_attr=resource_attr,
                    resource_description=display_value,
                    resource_value=getattr(resource_spec, resource_attr),
                )
            )
        input_end = "</div>"
        resource_spec_options.append(input_end)

        # Runtime configuration
        session_conf = SessionConfiguration()
        session_conf_attrs = SessionConfiguration.display_attributes()

        session_options = []
        for session_conf_attr, display_value in session_conf_attrs.items():
            input_entry = '<div class="form-group" name="session_configuration">'
            label_attribute = '<small class="form-text text-muted">{session_conf_description}:</small>'
            input_attribute = '<input name="{session_conf_attr}" class="form-control" \
                              "type="text" value="{session_conf_value}" \
                              "placeholder="{session_conf_description}">'
            input_end = "</div>"
            session_options.append(input_entry)
            session_options.append(
                label_attribute.format(session_conf_description=display_value)
            )
            session_options.append(
                input_attribute.format(
                    session_conf_attr=session_conf_attr,
                    session_conf_description=display_value,
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
        options = {"spawn_options": {}}

        if "provider" in formdata:
            options["spawn_options"]["provider"] = formdata["provider"][0]

        if "resource_type" in formdata:
            options["spawn_options"]["resource_type"] = formdata["resource_type"][0]

        options["spawn_options"]["resource_specification"] = {}
        for attr in ResourceSpecification.attributes():
            if attr in formdata:
                options["spawn_options"]["resource_specification"][attr] = formdata[
                    attr
                ][0]

        options["spawn_options"]["session_configuration"] = {}
        for attr in SessionConfiguration.attributes():
            if attr in formdata:
                options["spawn_options"]["session_configuration"][attr] = formdata[
                    attr
                ][0]

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
        provider = spawn_options["provider"]
        resource_type = spawn_options["resource_type"]
        resource_specification = ResourceSpecification(
            **spawn_options["resource_specification"]
        )
        session_configuration = SessionConfiguration(
            **spawn_options["session_configuration"]
        )

        # Resource pools are externally defined and managed
        # Made persistent on local disk for now
        session_pool = load_pool(provider, resource_type)
        if not session_pool:
            session_pool = create_pool(provider, resource_type)
            if not session_pool:
                raise RuntimeError(
                    "Failed to create a pool for provider: {} "
                    "for resource type: {}".format(provider, resource_type)
                )

        if not self.resource_id:
            # Might take a long time, hence we ensure there is a adequate start_time
            # TODO, create correcly formatted provider table
            # Same applies to resource_type: VM -> INSTANCE

            # Memory, CPU, Accelerators
            orchestrator_klass, options = get_orchestrator(resource_type, provider)
            provider_profile = get_provider_profile(provider)
            resource_config = orchestrator_klass.make_resource_config(
                provider_profile=provider_profile,
                cpu=resource_specification.cpu,
                memory=resource_specification.memory,
                gpus=resource_specification.gpu,
            )
            # Assign notebook ID to the state of the spawner
            identifier, resource = session_pool.create(
                orchestrator_klass, options, resource_config
            )
            self.resource_id, self.resource = identifier, resource
        else:
            self.resource = session_pool.get(self.resource_id)

        if not self.resource:
            raise RuntimeError(
                "Failed to find a resource that match the specified configuration"
            )

        # Give a while to
        num_attempts = 0
        endpoint = None
        while num_attempts < self.resource_configuration_timeout and not endpoint:
            endpoint = session_pool.endpoint(self.resource_id)
            time.sleep(1)
            num_attempts += 1

        # TODO, Configure the resource with the required dependencies
        # session_pool.configure(self.identifier)

        # Get available spawner templates and deployments
        spawner_template = get_spawner_template(provider, resource_type)
        spawner_deployment_configuration = get_spawner_deployment(
            resource_type,
            name="local_machine"
        )
        # kubernetes spawner -> nodelabels
        # dockerspawner -> node labels
        # SSH spawner
        # Fargate spawner

        # Use spawner to schedule the notebook on the orchestrated resource
        # Pass on the spawner options
        # https://github.com/jupyterhub/wrapspawner/blob/master/wrapspawner/wrapspawner.py
        parent_spawner_config = dict(
            user=self.user,
            db=self.db,
            hub=self.hub,
            authenticator=self.authenticator,
            oauth_client_id=self.oauth_client_id,
            server=self._server,
            config=self.config
        )

        # Each type of deployment has a range of available spawners
        # Merge the client spawner configuration into spawner_options
        # Extract which scheduler to use for spawning the notebook
        notebook_task_template = create_notebook_task_template(
            spawner_template,
            spawner_deployment_configuration,
            parent_spawner_config=parent_spawner_config
        )
        if not notebook_task_template:
            raise RuntimeError("Failed to configure the scheduler task template")

        # Scheduler, Launch the notebook
        self.scheduler = Scheduler(
            task_template=notebook_task_template
        )
        self.set_notebook(scheduler=self.scheduler)
        return self.scheduler.run()

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

    # TODO, add progress function
    def get_notebook(self):
        return self.notebook

    def set_notebook(self, clear=False, **kwargs):
        if clear:
            self.notebook.clear()
        else:
            self.notebook.update(**kwargs)
