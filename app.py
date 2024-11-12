from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_cors import CORS
import os
import subprocess
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
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

        # Create client-specific directory
        client_dir = os.path.join(EXPORT_DIR, f"client_{client_ip}")
        if not os.path.exists(client_dir):
            os.makedirs(client_dir)

        # Add export entry to /etc/exports
        with open('/etc/exports', 'a') as exports_file:
            exports_file.write(f"{client_dir} {client_ip}({PERMISSIONS})\n")

        # Restart NFS service
        subprocess.run(['sudo', 'exportfs', '-a'], check=True)
        subprocess.run(['sudo', 'systemctl', 'restart', 'nfs-kernel-server'], check=True)
        subprocess.run(['sudo', 'systemctl', 'enable', 'nfs-kernel-server'], check=True)

        return True, "Client added successfully"
    except Exception as e:
        return False, str(e)

# Function to remove client from NFS exports
def remove_nfs_client(client_ip):
    try:
        client_dir = os.path.join(EXPORT_DIR, f"client_{client_ip}")
        
        # Read the current exports file
        with open('/etc/exports', 'r') as exports_file:
            lines = exports_file.readlines()

        # Filter out the line with the client IP
        with open('/etc/exports', 'w') as exports_file:
            for line in lines:
                if client_dir not in line:
                    exports_file.write(line)

        # Remove client directory if empty
        if os.path.exists(client_dir) and not os.listdir(client_dir):
            os.rmdir(client_dir)

        # Restart NFS service
        subprocess.run(['sudo', 'exportfs', -'a'], check=True)
        subprocess.run(['sudo', 'systemctl', 'restart', 'nfs-kernel-server'], check=True)

        return True, "Client removed successfully"
    except Exception as e:
        return False, str(e)

# API Routes

@app.route('/api/clients', methods=['GET'])
def get_clients():
    """Get list of all NFS clients and their statistics"""
    clients = []
    if os.path.exists('/etc/exports'):
        with open('/etc/exports', 'r') as exports_file:
            for line in exports_file:
                if EXPORT_DIR in line:
                    parts = line.strip().split()
                    if len(parts) > 1:
                        client_ip = parts[1].split('(')[0]
                        client_dir = os.path.join(EXPORT_DIR, f"client_{client_ip}")
                        
                        # Get client statistics
                        total_files = 0
                        total_size = 0
                        if os.path.exists(client_dir):
                            for root, dirs, files in os.walk(client_dir):
                                total_files += len(files)
                                total_size += sum(os.path.getsize(os.path.join(root, name)) for name in files)
                        
                        clients.append({
                            'ip': client_ip,
                            'total_files': total_files,
                            'total_size': total_size,
                            'last_active': datetime.fromtimestamp(os.path.getmtime(client_dir)).isoformat() if os.path.exists(client_dir) else None
                        })
    
    return jsonify({
        'clients': clients,
        'total_clients': len(clients)
    })

@app.route('/api/clients', methods=['POST'])
def add_client():
    """Add a new NFS client"""
    data = request.get_json()
    client_ip = data.get('client_ip')
    
    if not client_ip:
        return jsonify({'success': False, 'message': 'Client IP is required'}), 400
    
    success, message = add_nfs_client(client_ip)
    return jsonify({'success': success, 'message': message})

@app.route('/api/clients/<client_ip>', methods=['DELETE'])
def remove_client(client_ip):
    """Remove an NFS client"""
    success, message = remove_nfs_client(client_ip)
    return jsonify({'success': success, 'message': message})

@app.route('/api/clients/<client_ip>/files', methods=['GET'])
def get_client_files(client_ip):
    """Get file structure for a specific client"""
    client_dir = os.path.join(EXPORT_DIR, f"client_{client_ip}")
    
    def get_directory_structure(path):
        """Recursively build directory structure"""
        items = []
        try:
            for entry in os.scandir(path):
                item = {
                    'name': entry.name,
                    'type': 'folder' if entry.is_dir() else 'file',
                    'size': os.path.getsize(entry.path),
                    'modified': datetime.fromtimestamp(os.path.getmtime(entry.path)).isoformat()
                }
                
                if entry.is_dir():
                    item['children'] = get_directory_structure(entry.path)
                
                items.append(item)
        except Exception as e:
            print(f"Error scanning directory {path}: {e}")
        
        return items
    
    if not os.path.exists(client_dir):
        return jsonify({'success': False, 'message': 'Client directory not found'}), 404
    
    file_structure = get_directory_structure(client_dir)
    return jsonify({
        'success': True,
        'files': file_structure
    })

@app.route('/api/clients/<client_ip>/files/<path:file_path>', methods=['GET'])
def download_file(client_ip, file_path):
    """Download a specific file"""
    full_path = os.path.join(EXPORT_DIR, f"client_{client_ip}", file_path)
    
    if not os.path.exists(full_path) or not os.path.isfile(full_path):
        return jsonify({'success': False, 'message': 'File not found'}), 404
    
    return send_file(full_path, as_attachment=True)

# Serve React app
@app.route('/')
def serve_app():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)