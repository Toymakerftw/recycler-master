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

def add_nfs_client(client_ip):
    """Add a client to the NFS exports file and restart NFS services."""
    try:
        os.makedirs(EXPORT_DIR, exist_ok=True)
        subprocess.run(['sudo', 'chown', 'nobody:nogroup', EXPORT_DIR], check=True)
        subprocess.run(['sudo', 'chmod', '755', EXPORT_DIR], check=True)

        with open('/etc/exports', 'a') as exports_file:
            exports_file.write(f"{EXPORT_DIR} {client_ip}({PERMISSIONS})\n")

        restart_nfs_service()
        return True
    except Exception as e:
        print(f"Error adding NFS client: {e}")
        return False

def remove_nfs_client(client_ip):
    """Remove a client from the NFS exports file and restart NFS services."""
    try:
        with open('/etc/exports', 'r') as exports_file:
            lines = exports_file.readlines()

        with open('/etc/exports', 'w') as exports_file:
            for line in lines:
                if f"{EXPORT_DIR} {client_ip}({PERMISSIONS})" not in line:
                    exports_file.write(line)

        restart_nfs_service()
        return True
    except Exception as e:
        print(f"Error removing NFS client: {e}")
        return False

def restart_nfs_service():
    """Restart NFS services."""
    subprocess.run(['sudo', 'exportfs', '-a'], check=True)
    subprocess.run(['sudo', 'systemctl', 'restart', 'nfs-kernel-server'], check=True)
    subprocess.run(['sudo', 'systemctl', 'enable', 'nfs-kernel-server'], check=True)
