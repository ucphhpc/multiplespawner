c = get_config()


c.JupyterHub.spawner_class = "multiplespawner.MultipleSpawner"
c.Spawner.debug = True

c.JupyterHub.authenticator_class = "jhubauthenticators.DummyAuthenticator"
c.DummyAuthenticator.password = "password"
