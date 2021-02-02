===============
multiplespawner
===============

A JupyterHub Spawner that allows to select which resource their notebook should be spawned on.
Internally it then uses spawner specific configurations to orchestrate the user on the given resources.

Currently the plan is to support either a VM or container deployment on a set of user selectable hardware configurations

-----
Usage
-----

To use the MultipleSpawner, the JupyterHub configuration has to specify that it should use the MultipleSpawner::

    c = get_config()
    c.JupyterHub.spawner_class = "multiplespawner.MultipleSpawner"


-------------
Configuration
-------------

To configure which Spawners the MultipleSpawner should support and how a particular Notebook should be spawned, the Spawner expects two configuration files.
Namely the Spawner Template configuration and the Spawner Deployment configurations.

By default, the spawner expects these to be present in the ``~/.multiplespawner`` directory as the ``spawner_templates.json`` and ``spawner_deployment.json`` files.
It is however possible, to override this expectation by defining other paths via the ``MULTIPLE_SPAWNER_TEMPLATE_FILE`` and ``MULTIPLE_SPAWNER_DEPLOYMENT_FILE`` environment variables.


Spawner Template Configuration
------------------------------
This configuration defines which Spawner should be supported and how they should be utilized.
The expected structure of this configuration file can be seen below::

    [
        {
            "name": "",                 # Name to show
            "resource_type": "",        # (virtual_machine,container,bare_metal)
            "providers": [""],          # Which cloud providers support this spawner?
            "spawner": {
                "class": "",            # The Spawner class that should be used by the MultipleSpawner to spawn the instance
                "kwargs": {}            # The property values that should be set for the specified Spawner.
            },
            "configurer": {             # If so required, the configurer to apply to the target resource
                "class": "",            # Configurer class
                                        # Any additional keys will be applied to the class at instantiation

            },
            "authenticator": {          # A required field for specifying which authenticator should be used to configure the resource
                                        # and before the MultipleSpawner can connect to the resource
                "class": "",            # Class path to the designated authenticator
                "kwargs": {}            # Kwargs that should be passed to the constructor 
            }
        }
    ]

An example of how such a file might be defined can be seen in the following example::

    [
        {
            "name": "VirtualMachine Spawner",
            "resource_type": "virtual_machine",
            "providers": ["oci"],
            "spawner": {
                "class": "sshspawner.sshspawner.SSHSpawner",
                "kwargs": {
                    "remote_hosts": ["{endpoint}"],
                    "remote_port": "22",
                    "ssh_keyfile": "~/.corc/ssh/id_rsa",
                    "remote_port_command": "/usr/bin/python3 \
                        /usr/local/bin/get_port.py"
                }
            },
            "configurer": {
                "class": "corc.configurer.AnsibleConfigurer",
                "options": {
                    "host_variables": {
                        "ansible_user": "opc",
                        "ansible_become": "yes",
                        "ansible_become_method": "sudo",
                        "new_username": "{JUPYTERHUB_USER}"
                    },
                    "host_settings": {
                        "group": "compute",
                        "port": "22"
                    },
                    "apply_kwargs": {
                        "playbook_path": "setup_ssh_spawner.yml"
                    }
                }
            },
            "authenticator": {
                "class": "corc.authenticator.SSHAuthenticator",
                "kwargs": {"create_certificate": "True"}
            }
        }
    ]

As shown in the above example, the Spawner Template Configuration supports the 
definition of multiple Spawners via the encapsulating list that contains each individual
spawner's configuration as a dictionary.

In the provided example, a ``VirtualMachine Spawner`` is introduced.
It is configured to use be supports by the ``oci`` cloud provider.
Furthermore, it uses the ``SSHSpawner`` to spawn the Notebook,
in addition, because the ``SSHSpawner`` expects a number of attributes to be defined before it can connect to a given resource,
the ``kwargs`` key defines which attributes that should be passed to the ``SSHSpaner``'s constructor at instantiation. The same approach applies to the ``configurer`` and the ``authenticator`` keys in the dictionary.

Spawner Deployment Configuration
--------------------------------

The Spawner Deployment Configuration is for defining how a particular Jupyter session should be spawned.

An example of the deployment configuration file structure can be seen below::

    {
        "": [   # The key must defined the ``resource_type`` that the subdeployment configurations uses

            {} # The underlying list contains the set of attributes and their values 
               # that should be passed to the Spawner before it spawns the Jupyter Session
        ]
    }

Currently the MultipleSpawner supports three different kinds of ``resource_types`` (`container`, `virtual_machine`, and `bare_metal`) as defined by the
 ``multiplespawner.runtime.resource.ResourceTypes`` class.

A hello world example of the Spawner Deployment Configuration can be seen below::

    {
        "container": [
            {
                "name": "python_notebook",
                "image": "nielsbohr/python-notebook"
            }
        ],
        "virtual_machine": [
            {
                "name": "oracle_linux_7_8",
                "provider": "oci",
                "image": "Oracle Linux 7.8"
            }
        ],
        "bare_metal": [
            {
                "name": "local_machine",
                "provider": "local"
            }
        ]
    }

------
Status
------

The MultipleSpawner still needs additional testings and refinement to ensure that it is stable and versitile enough for large
scale deployment

