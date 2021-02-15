import paramiko
from multiplespawner.defaults import default_host_key_order


def get_host_key(endpoint, port=22, default_host_key_algos=default_host_key_order):
    transport = paramiko.transport.Transport("{}:{}".format(endpoint, port))
    transport.start_client()
    # Ensure that we use the same HostKeyAlgorithm order across
    # SSH implementations
    transport.get_security_options().key_types = tuple(default_host_key_algos)
    host_key = transport.get_remote_server_key()
    return host_key
