from jupyterhub.spawner import Spawner


class DistributedSpawner(Spawner):

    #TODO add form_template


    #TODO options_template


    async def load_state(self, state):
        pass

    async def get_state(self):
        pass


    async def start(self):
        # user_options must be prepare here and container the nessesary data to
        # define how and more importantly where the spawner should be deployed

        # Receive instance configuration
        # Local - (VM, Container)
        # Cloud - (VM, Container)

        # Define Standard VM Spec

        # Define Standard Container Spec

        # OrchestrationManager = Get dynamic Cloud/Local implementation varient
        # Pass Spec to OrchestrationManager
        return None


    async def stop(self, now=False):
        # Retrieve where this instance is hosted
        # Use the OrchestrationManager to kill the instance
        return None


    async def poll(self):
        return None
