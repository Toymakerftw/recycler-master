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

# Function to add client to NFS exports
def add_nfs_client(client_ip):
    try:
        # Check if the export directory exists, create if not
        if not os.path.exists(EXPORT_DIR):
            os.makedirs(EXPORT_DIR)
            subprocess.run(['sudo', 'chown', 'nobody:nogroup', EXPORT_DIR], check=True)
            subprocess.run(['sudo', 'chmod', '755', EXPORT_DIR], check=True)

        # Add export entry to /etc/exports
        with open('/etc/exports', 'a') as exports_file:
            exports_file.write(f"{EXPORT_DIR} {client_ip}({PERMISSIONS})\n")

        # Restart NFS service
        subprocess.run(['sudo', 'exportfs', '-a'], check=True)
        subprocess.run(['sudo', 'systemctl', 'restart', 'nfs-kernel-server'], check=True)
        subprocess.run(['sudo', 'systemctl', 'enable', 'nfs-kernel-server'], check=True)

        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

# Function to remove client from NFS exports
def remove_nfs_client(client_ip):
    try:
        # Read the current exports file
        with open('/etc/exports', 'r') as exports_file:
            lines = exports_file.readlines()

        # Filter out the line with the client IP
        with open('/etc/exports', 'w') as exports_file:
            for line in lines:
                if f"{EXPORT_DIR} {client_ip}({PERMISSIONS})" not in line:
                    exports_file.write(line)

        # Restart NFS service
        subprocess.run(['sudo', 'exportfs', '-a'], check=True)
        subprocess.run(['sudo', 'systemctl', 'restart', 'nfs-kernel-server'], check=True)
        subprocess.run(['sudo', 'systemctl', 'enable', 'nfs-kernel-server'], check=True)

        return True
    except Exception as e:
        print(f"Error: {e}")
        return False