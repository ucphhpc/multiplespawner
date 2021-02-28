import asyncio
import os
import time
import requests
from functools import partial
from jupyterhub.spawner import Spawner
from traitlets import Dict, Unicode, default, Integer, directional_link, Instance, Bool
from multiplespawner.defaults import default_base_path
from multiplespawner.helpers import make, recursive_format
from multiplespawner.config.start import (
    prepare_multiplespawner_configs,
    prepare_multiplespawner_playbooks,
)
from multiplespawner.network import get_host_key
from multiplespawner.orchestration.orchestration import (
    create_pool,
    load_pool,
    supported_resource,
)
from multiplespawner.runtime.resource import ResourceSpecification, ResourceTypes
from multiplespawner.session import SessionConfiguration
from multiplespawner.spawner.scheduler import (
    Scheduler,
    format_task_template,
    create_notebook_task_template,
)
from multiplespawner.spawner.selection import get_available_providers
from multiplespawner.config.template import (
    get_spawner_template,
    get_spawner_template_path,
)
from multiplespawner.config.deployment import (
    get_spawner_deployment,
    get_spawner_deployment_path,
)
from corc.providers.types import get_orchestrator, get_provider_resource_creation_id
from corc.providers.config import get_provider_profile


def format_template(template, environment_kwargs=None):
    if not environment_kwargs:
        environment_kwargs = {}

    spawner_str_kwargs = {}
    configurer_options = {}
    authenticator_kwargs = {}

    if "spawner" in template and "kwargs" in template["spawner"]:
        spawner_str_kwargs = {
            k: v
            for k, v in template["spawner"]["kwargs"].items()
            if isinstance(v, str) or isinstance(v, list) or isinstance(v, dict)
        }

    if "configurer" in template and "options" in template["configurer"]:
        configurer_options = {
            k: v
            for k, v in template["configurer"]["options"].items()
            if isinstance(v, str) or isinstance(v, list) or isinstance(v, dict)
        }

    if "authenticator" in template and "kwargs" in template["authenticator"]:
        authenticator_kwargs = {
            k: v
            for k, v in template["authenticator"]["kwargs"].items()
            if isinstance(v, str) or isinstance(v, list) or isinstance(v, dict)
        }

    for key, value in environment_kwargs.items():
        try:
            recursive_format(spawner_str_kwargs, {key: value})
            recursive_format(configurer_options, {key: value})
            recursive_format(authenticator_kwargs, {key: value})
        except TypeError:
            pass

    if "spawner" in template and "kwargs" in template["spawner"]:
        template["spawner"]["kwargs"].update(spawner_str_kwargs)

    if "configurer" in template and "options" in template["configurer"]:
        template["configurer"]["options"].update(configurer_options)

    if "authenticator" in template and "kwargs" in template["authenticator"]:
        template["authenticator"]["kwargs"].update(authenticator_kwargs)

    return template


def get_host_information():
    # Public IP of this host
    ext_ip = requests.get("https://api.ipify.org").text
    # The ssh host_key
    host_key = get_host_key("127.0.0.1")
    known_host_str = "{endpoint} {key_type} {host_key}\n".format(
        endpoint=ext_ip, key_type=host_key.get_name(), host_key=host_key.get_base64(),
    )
    return dict(public_ip=ext_ip, host_key=known_host_str)


class MultipleSpawner(Spawner):

    configuration_directory = Unicode(
        trait=Unicode(),
        default_value=default_base_path,
        help="Path to the default directory where "
        "MultipleSpawner finds its configuration files",
    )

    is_configured = Bool(default_value=False)

    notebook = Dict(default_value={}, config=False)

    resource = Dict(default_value={}, config=False)

    resource_authenticator = None

    resource_start_timeout = Integer(default_value=30, allow_none=False, config=True)

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
            label_attribute = (
                '<small class="form-text text-muted">'
                "{session_conf_description}:</small>"
            )
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

    def _init_spawner_configs(self):
        # Ensure that the MultipleSpawner default configration
        # Directory is there and that atleast the required configuration
        # files exists
        if not prepare_multiplespawner_configs(base_path=self.configuration_directory):
            raise RuntimeError(
                "Failed to prepare the MultipleSpawner configurations for spawning"
            )

        if not prepare_multiplespawner_playbooks(
            base_path=self.configuration_directory
        ):
            raise RuntimeError(
                "Failed to prepare the MultipleSpawner playbooks"
                " directory for configuring resources"
            )

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

    def run_configurer(
        self, endpoint, spawner_template, credentials=None, host_information=None
    ):
        configurer = make(spawner_template["configurer"]["class"])
        configuration = configurer.gen_configuration(
            spawner_template["configurer"]["options"]
        )

        format_kwargs = dict(auth_key=credentials.public_key)

        if host_information:
            if "public_ip" in host_information:
                format_kwargs.update(
                    {"server_public_ip": host_information["public_ip"]}
                )

            if "host_key" in host_information:
                format_kwargs.update({"server_host_key": host_information["host_key"]})

        configuration = configurer.format_configuration(
            configuration, kwargs=format_kwargs
        )

        return configurer.apply(
            endpoint, configuration=configuration, credentials=credentials
        )

    def create_scheduler(self):
        # From https://github.com/jupyterhub/wrapspawner/blob
        # /a8705e376dc9ecde3f2f99b44cd5b11c7ce1edd8/wrapspawner/wrapspawner.py#L86
        if self.scheduler is None:
            # Use spawner to schedule the notebook on the orchestrated resource
            # Pass on the spawner options
            # https://github.com/jupyterhub/wrapspawner/blob
            # /master/wrapspawner/wrapspawner.py
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
            task_template = create_notebook_task_template(
                self.notebook["spawner_template"],
                self.notebook["spawner_deployment"],
                parent_spawner_config=parent_spawner_config,
            )

            # Format the notebook task template with the orchestrated resource details
            formatted_task_template = format_task_template(
                task_template, kwargs=self.resource["details"]
            )
            # Scheduler, Launch the notebook
            self.scheduler = Scheduler(task_template=formatted_task_template)
            if not self.scheduler:
                raise RuntimeError("Failed to create the Notebook Scheduler")

            # Ensure that the state is reset since it will be this spawners
            #  state to begin with
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

        if self.resource and "details" in self.resource:
            if (
                "endpoint" in self.resource["details"]
                and self.resource["details"]["endpoint"]
            ):
                if (
                    self.resource_authenticator
                    and self.resource_authenticator.is_prepared
                ):
                    endpoint = self.resource["details"]["endpoint"]
                    cleaned = self.resource_authenticator.cleanup(endpoint)
                    self.log.info(
                        "result of cleaning the resource authenticators: {}".format(
                            cleaned
                        )
                    )

        self.is_configured = False
        self.notebook = {}
        self.resource = {}
        self.resource_authenticator = None
        self.resource_is_configured = False
        self.scheduler = None

    async def start(self):
        # Assign to-be notebook -> so that poll finds it
        spawn_options = self.user_options["spawn_options"]
        provider = spawn_options["provider"]
        resource_type = spawn_options["resource_type"]
        resource_specification = ResourceSpecification(
            **spawn_options["resource_specification"]
        )

        self._init_spawner_configs()
        host_information = get_host_information()
        if not self.hub.public_host:
            self.hub.public_host = host_information["public_ip"]

        # Contains information about the session
        _ = SessionConfiguration(**spawn_options["session_configuration"])

        spawner_template_path = get_spawner_template_path()
        if not os.path.exists(spawner_template_path):
            raise RuntimeError("The required Spawner template path does not exist")

        # Get available spawner templates and deployments
        spawner_template = get_spawner_template(
            provider, resource_type, path=spawner_template_path
        )
        if not spawner_template:
            raise RuntimeError("Failed to find an appropriate spawner template")

        # Dynamicly format the spawner_template options with the environment options
        environment = self.get_env()
        spawner_template = format_template(
            spawner_template, environment_kwargs=environment
        )
        self.notebook["spawner_template"] = spawner_template

        deployment_path = get_spawner_deployment_path()
        if not os.path.exists(deployment_path):
            raise RuntimeError("The required Spawner deployment path does not exist")

        spawner_deployment = get_spawner_deployment(
            resource_type, name="python_notebook", path=deployment_path
        )
        if not spawner_deployment:
            raise RuntimeError("Failed to find an appropriate spawner deployment")
        self.notebook["spawner_deployment"] = spawner_deployment

        # Authenticator for accesing the resource that hosts the notebook
        credentials = None
        auth_class, auth_args, auth_kwargs = None, [], {}
        if (
            "authenticator" in self.notebook["spawner_template"]
            and "class" in self.notebook["spawner_template"]["authenticator"]
        ):
            auth_class = self.notebook["spawner_template"]["authenticator"]["class"]

        if (
            "authenticator" in self.notebook["spawner_template"]
            and "args" in self.notebook["spawner_template"]["authenticator"]
        ):
            auth_args = self.notebook["spawner_template"]["authenticator"]["args"]

        if (
            "authenticator" in self.notebook["spawner_template"]
            and "kwargs" in self.notebook["spawner_template"]["authenticator"]
        ):
            auth_kwargs = self.notebook["spawner_template"]["authenticator"]["kwargs"]

        if not self.resource_authenticator:
            if auth_class:
                self.resource_authenticator = make(
                    auth_class, *auth_args, **auth_kwargs
                )

        if self.resource_authenticator:
            credentials = getattr(self.resource_authenticator, "credentials", None)

        if not supported_resource(provider, resource_type):
            raise RuntimeError(
                "The selected resource option is not supported "
                "- provider: {}, type: {}".format(provider, resource_type)
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

        # If resource is set, load the ip/port from the session_pool
        # and return it straight away
        if not self.resource:
            # Might take a long time, hence we ensure there is a adequate start_time
            # TODO, create correcly formatted provider table
            # Same applies to resource_type: VM -> INSTANCE

            # Memory, CPU, Accelerators
            orchestrator_klass, options = get_orchestrator(resource_type, provider)
            provider_profile = get_provider_profile(provider)
            unique_creation_id = get_provider_resource_creation_id(
                provider, resource_type
            )
            provider_kwargs = {unique_creation_id: self.user.name}

            resource_config = orchestrator_klass.make_resource_config(
                provider,
                provider_profile=provider_profile,
                provider_kwargs=provider_kwargs,
                cpu=float(resource_specification.cpu),
                memory=float(resource_specification.memory),
                gpus=int(resource_specification.gpu),
            )

            # Determine whether the resource needs to be orchestrated beforehand
            # Or whether the spawner will take care of it
            # Assign notebook ID to the state of the spawner
            # See if we can grap the event loop
            loop = asyncio.get_running_loop()
            identifier, resource = await loop.run_in_executor(
                None,
                partial(
                    session_pool.create,
                    orchestrator_klass,
                    options,
                    resource_config=resource_config,
                    credentials=[credentials],
                ),
            )
            self.resource["id"], self.resource["object"] = identifier, resource

        if (
            "object" not in self.resource
            and not self.resource["object"]
            and self.resource["id"]
        ):
            self.resource["object"] = session_pool.get(self.resource["id"])

        if "object" not in self.resource or not self.resource["object"]:
            raise RuntimeError(
                "Failed to find a resource that match the specified configuration"
            )

        if "details" not in self.resource:
            self.resource["details"] = {}

        # Give a while for the resource to be ready to return the endpoint
        num_attempts = 0
        while (
            num_attempts < self.resource_start_timeout
            and "endpoint" not in self.resource["details"]
            or not self.resource["details"]["endpoint"]
        ):
            self.resource["details"]["endpoint"] = session_pool.endpoint(
                self.resource["id"]
            )
            time.sleep(1)
            num_attempts += 1

        endpoint = None
        # Verify if the authenticator is prepared for the endpoint.
        # Configure the orchestratrated resource.
        if (
            "endpoint" in self.resource["details"]
            and self.resource["details"]["endpoint"]
        ):
            endpoint = self.resource["details"]["endpoint"]
            if not self.resource_authenticator.is_prepared:
                self.resource_authenticator.prepare(endpoint)
            # TODO Test that the resource_authenticator works
            if not self.resource_is_configured:
                if self.run_configurer(
                    endpoint,
                    self.notebook["spawner_template"],
                    credentials=credentials,
                    host_information=host_information,
                ):
                    self.resource_is_configured = True

        if not self.resource_is_configured:
            raise RuntimeError("The target resource was not properly configured")

        # TODO, Configure the resource with the required dependencies
        # session_pool.configure(self.identifier)
        # kubernetes spawner -> nodelabels
        # dockerspawner -> node labels
        # SSH spawner
        # Fargate spawner
        if not self.scheduler:
            self.create_scheduler()

        # Connect via the endpoint if provided
        if endpoint:
            ip, port = await self.scheduler.run()
            return endpoint, port
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
