from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
import os
import subprocess

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key

# Define variables
EXPORT_DIR = "/mnt/recyclebin"
PERMISSIONS = "rw,sync,no_subtree_check"

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

# Route to list NFS clients and handle adding/removing clients
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'add_client' in request.form:
            client_ip = request.form['client_ip']
            if add_nfs_client(client_ip):
                flash(f"NFS Client {client_ip} added successfully!", 'success')
            else:
                flash(f"Failed to add NFS Client {client_ip}.", 'danger')
        elif 'remove_client' in request.form:
            client_ip = request.form['remove_client']
            if remove_nfs_client(client_ip):
                flash(f"NFS Client {client_ip} removed successfully!", 'success')
            else:
                flash(f"Failed to remove NFS Client {client_ip}.", 'danger')
        return redirect(url_for('index'))

    # Read current NFS clients from /etc/exports
    nfs_clients = []
    if os.path.exists('/etc/exports'):
        with open('/etc/exports', 'r') as exports_file:
            for line in exports_file:
                if EXPORT_DIR in line:
                    parts = line.strip().split()
                    if len(parts) > 1:
                        # Extract client IP address by removing the permissions part
                        client_ip = parts[1].split('(')[0]
                        nfs_clients.append(client_ip)

    return render_template('index.html', nfs_clients=nfs_clients)

# Route to fetch files for a specific client directory
@app.route('/client_files')
def client_files():
    client = request.args.get('client')
    client_dir = os.path.join(EXPORT_DIR, client)

    # List files if client directory exists
    def list_files(path):
        files = []
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                files.append({
                    'name': item,
                    'path': item_path,
                    'is_dir': True,
                    'children': list_files(item_path)
                })
            else:
                files.append({
                    'name': item,
                    'path': item_path,
                    'is_dir': False
                })
        return files

    file_list = []
    if os.path.exists(client_dir):
        file_list = list_files(client_dir)

    return jsonify(files=file_list)

# Route to view a specific file's contents or download
@app.route('/view_file')
def view_file():
    file_path = request.args.get('file_path')
    if file_path and os.path.isfile(file_path):
        return send_file(file_path, as_attachment=False)
    flash("File not found.", 'danger')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
