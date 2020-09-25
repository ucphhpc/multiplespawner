import os
import time
from jupyterhub.spawner import Spawner
from traitlets import Dict, Unicode, default, Integer, directional_link, Instance, Bool
from multiplespawner.helpers import make
from multiplespawner.orchestration.orchestration import (
    create_pool,
    load_pool,
    supported_resource,
)
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

    is_configured = Bool(default_value=False)

    notebook = Dict(default_value={}, config=False)

    resource_id = Unicode()

    resource_start_timeout = Integer(default_value=30, allow_none=False, config=True)

    resource_authenticator = None

    resource_is_configured = Bool(default_value=False)

    scheduler = Instance(Scheduler, allow_none=True)

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

    def run_configurer(self, endpoint, spawner_template, credentials=None):
        configurer = make(spawner_template["configurer"]["class"])
        configuration = configurer.gen_configuration(
            spawner_template["configurer"]["options"]
        )
        configurer.apply(endpoint, configuration=configuration, credentials=credentials)
        self.resource_is_configured = True

    def create_scheduler(self):
        # From https://github.com/jupyterhub/wrapspawner/blob/a8705e376dc9ecde3f2f99b44cd5b11c7ce1edd8/wrapspawner/wrapspawner.py#L86
        if self.scheduler is None:
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
                config=self.config,
            )

            # Each type of deployment has a range of available spawners
            # Merge the client spawner configuration into spawner_options
            # Extract which scheduler to use for spawning the notebook
            notebook_task_template = create_notebook_task_template(
                self.notebook["spawner_template"],
                self.notebook["spawner_deployment"],
                parent_spawner_config=parent_spawner_config,
            )

            # Scheduler, Launch the notebook
            self.scheduler = Scheduler(task_template=notebook_task_template)
            if not self.scheduler:
                raise RuntimeError("Failed to create the Notebook Scheduler")

            # Ensure that the state is reset since it will be this spawners state to begin with
            self.scheduler.call_sync_process("clear_state")
            if "state" in self.notebook:
                # Refresh the spawners state
                self.scheduler.call_sync_process("load_state", self.notebook["state"])

            # link traits common between self and child
            config_keys = set(self.notebook["spawner_deployment"].keys())
            common_traits = (
                set(self._trait_values.keys())
                & set(self.scheduler.process_handler._trait_values.keys()) - config_keys
            )
            for trait in common_traits:
                directional_link((self, trait), (self.scheduler.process_handler, trait))

        return self.scheduler

    def load_state(self, state):
        super().load_state(state)
        # Load the notebook
        self.notebook["state"] = state.get("state", {})
        self.notebook["spawner_template"] = state.get("spawner_template", {})
        self.notebook["spawner_deployment"] = state.get("spawner_deployment", {})
        if self.notebook["spawner_template"] and self.notebook["spawner_deployment"]:
            self.create_scheduler()

    def get_state(self):
        state = super().get_state()
        if self.scheduler:
            self.notebook["state"] = state["state"] = self.scheduler.call_sync_process(
                "get_state"
            )

        if "spawner_template" in self.notebook:
            state["spawner_template"] = self.notebook["spawner_template"]

        if "spawner_deployment" in self.notebook:
            state["spawner_deployment"] = self.notebook["spawner_deployment"]
        return state

    def clear_state(self):
        super().clear_state()
        if self.scheduler:
            self.scheduler.call_sync_process("clear_state")

        if self.notebook:
            self.notebook = {}

        self.scheduler = None
        self.notebook = {}

    def start(self):
        # Assign to-be notebook -> so that poll finds it
        spawn_options = self.user_options["spawn_options"]
        provider = spawn_options["provider"]
        resource_type = spawn_options["resource_type"]
        resource_specification = ResourceSpecification(
            **spawn_options["resource_specification"]
        )
        session_configuration = SessionConfiguration(
            **spawn_options["session_configuration"]
        )

        # Get available spawner templates and deployments
        spawner_template = get_spawner_template(provider, resource_type)
        if not spawner_template:
            raise RuntimeError("Failed to find an appropriate spawner template")
        self.notebook["spawner_template"] = spawner_template

        spawner_deployment = get_spawner_deployment(
            resource_type, name="oracle_linux_7_8"
        )
        if not spawner_deployment:
            raise RuntimeError("Failed to find an appropriate spawner deployment")
        self.notebook["spawner_deployment"] = spawner_deployment

        # Authenticator for accesing the resource that hosts the notebook
        credentials = None
        if not self.resource_authenticator:
            if "authenticator" in self.notebook["spawner_template"]:
                self.resource_authenticator = make(
                    self.notebook["spawner_template"]["authenticator"]
                )
        if self.resource_authenticator:
            credentials = getattr(self.resource_authenticator, "credentials", None)

        if not supported_resource(provider, resource_type):
            raise RuntimeError(
                "The selected resource option is not supported - provider: {}, type: {}".format(
                    provider, resource_type
                )
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

        # If resource_id and resource are set, load the ip/port from the session_pool
        # and return it straight away
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

            # Determine whether the resource needs to be orchestrated beforehand
            # Or whether the spawner will take care of it
            # Assign notebook ID to the state of the spawner
            identifier, resource = session_pool.create(
                orchestrator_klass,
                options,
                resource_config=resource_config,
                credentials=credentials,
            )
            self.resource_id, self.resource = identifier, resource

        if not self.resource and self.resource_id:
            self.resource = session_pool.get(self.resource_id)

        if not self.resource:
            raise RuntimeError(
                "Failed to find a resource that match the specified configuration"
            )

        # Give a while for the resource to be ready to return the endpoint
        num_attempts = 0
        endpoint = None
        while num_attempts < self.resource_start_timeout and not endpoint:
            endpoint = session_pool.endpoint(self.resource_id)
            time.sleep(1)
            num_attempts += 1

        # Configure the orchestratrated resource
        if endpoint and not self.resource_is_configured:
            self.run_configurer(
                endpoint, self.notebook["spawner_template"], credentials=credentials
            )

        # TODO, Configure the resource with the required dependencies
        # session_pool.configure(self.identifier)

        # kubernetes spawner -> nodelabels
        # dockerspawner -> node labels
        # SSH spawner
        # Fargate spawner

        if not self.scheduler:
            self.create_scheduler()
        return self.scheduler.run()

    async def stop(self, now=False):
        notebook = self.get_notebook()
        if not notebook:
            return None
        status = await self.poll()
        if status is not None:
            return

        if not self.scheduler:
            return None
        return await self.scheduler.call_async_process("stop")

    async def poll(self):
        # Returns:
        #   None if single-user process is running.
        #   Integer exit status (0 if unknown), if it is not running.
        current_status = 0
        notebook = self.get_notebook()
        if not notebook:
            return current_status

        if not self.scheduler:
            return current_status
        return await self.scheduler.call_async_process("poll")

    # TODO, add progress function
    def get_notebook(self):
        return self.notebook
