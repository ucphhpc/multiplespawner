===============
multiplespawner
===============

A JupyterHub Spawner that allows to select which resource their notebook should be spawned on.
Internally it then uses spawner specific configurations to orchestrate the user on the given resources.

Currently the plan is to support either a VM or container deployment on a set of user selectable hardware configurations
