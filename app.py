from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
import os
import subprocess

app = Flask(__name__)
app.secret_key = 'your_secret_key'

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
    
@app.route('/client_files')
def client_files():
    client = request.args.get('client')
    client_dir = os.path.join(EXPORT_DIR, client)

    # List files if client directory exists
    file_list = []
    if os.path.exists(client_dir):
        for item in os.listdir(client_dir):
            item_path = os.path.join(client_dir, item)
            file_list.append({'name': item, 'path': item_path, 'is_dir': os.path.isdir(item_path)})

    return jsonify(files=file_list)

@app.route('/view_file')
def view_file():
    file_path = request.args.get('file_path')
    if file_path and os.path.isfile(file_path):
        return send_file(file_path, as_attachment=False)
    flash("File not found.", 'danger')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
