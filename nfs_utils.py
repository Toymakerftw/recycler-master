import os
import subprocess

EXPORT_DIR = "/mnt/recyclebin"
PERMISSIONS = "rw,sync,no_subtree_check"

def get_nfs_clients():
    """Retrieve NFS clients from the /etc/exports file."""
    clients = set()
    if os.path.exists('/etc/exports'):
        with open('/etc/exports', 'r') as exports_file:
            for line in exports_file:
                if EXPORT_DIR in line:
                    client_ip = line.strip().split()[1].split('(')[0]
                    clients.add(client_ip)
    return clients