from jupyter_client.localinterfaces import public_ips

c = get_config()

c.JupyterHub.ip = "127.0.0.1"

c.JupyterHub.spawner_class = "multiplespawner.MultipleSpawner"
c.JupyterHub.hub_ip = public_ips()[0]
c.JupyterHub.hub_ip_connect = public_ips()[0]
c.JupyterHub.port = 8080


c.JupyterHub.authenticator_class = "jhubauthenticators.DummyAuthenticator"
c.DummyAuthenticator.password = "password"
