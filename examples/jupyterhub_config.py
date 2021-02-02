import os
from jupyter_client.localinterfaces import public_ips

c = get_config()

c.JupyterHub.ip = "0.0.0.0"
c.JupyterHub.port = 8000
c.Spawner.start_timeout = 60 * 5

c.JupyterHub.spawner_class = "multiplespawner.MultipleSpawner"
c.JupyterHub.hub_connect_ip = public_ips()[0]

c.JupyterHub.authenticator_class = "jhubauthenticators.DummyAuthenticator"
c.DummyAuthenticator.password = "password"
