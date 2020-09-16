import os
from jupyter_client.localinterfaces import public_ips

c = get_config()

c.JupyterHub.ip = "0.0.0.0"
c.JupyterHub.port = 8000

c.JupyterHub.debug_proxy = True

c.JupyterHub.spawner_class = "multiplespawner.MultipleSpawner"
# c.JupyterHub.spawner_class = 'dockerspawner.DockerSpawner'
c.JupyterHub.hub_connect_ip = public_ips()[0]

# c.DockerSpawmer.use_internal_ip = True
# c.DockerSpawner.hub_ip_connect = public_ips()[0]
# c.DockerSpawner.image = 'nielsbohr/python-notebook:latest'

c.JupyterHub.authenticator_class = "jhubauthenticators.DummyAuthenticator"
c.DummyAuthenticator.password = "password"
