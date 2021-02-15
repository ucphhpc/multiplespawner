import os

# Package name
PACKAGE_NAME = "multiplespawner"

default_base_path = os.path.join(os.path.expanduser("~"), ".{}".format(PACKAGE_NAME))

# Default HostKeyAlgorithm order to use across SSH implementations
# if no external configuration is given.
# The order is defined by recommendations from
# https://infosec.mozilla.org/guidelines/openssh.html
default_host_key_order = [
    "ssh-ed25519-cert-v01@openssh.com",
    "ssh-rsa-cert-v01@openssh.com",
    "ssh-ed25519",
    "ssh-rsa",
    "ecdsa-sha2-nistp521-cert-v01@openssh.com",
    "ecdsa-sha2-nistp384-cert-v01@openssh.com",
    "ecdsa-sha2-nistp256-cert-v01@openssh.com",
    "ecdsa-sha2-nistp521",
    "ecdsa-sha2-nistp384",
    "ecdsa-sha2-nistp256",
]
