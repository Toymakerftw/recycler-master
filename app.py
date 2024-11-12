from flask import Flask, render_template, request, redirect, url_for, flash
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

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        client_ip = request.form['client_ip']
        if add_nfs_client(client_ip):
            flash(f"NFS Client {client_ip} added successfully!", 'success')
        else:
            flash(f"Failed to add NFS Client {client_ip}.", 'danger')
        return redirect(url_for('index'))
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
