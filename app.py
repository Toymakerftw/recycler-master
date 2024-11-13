from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, json
import psutil
import sqlite3
import os
import subprocess
from datetime import datetime
import time
from threading import Thread

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key

# Configuration
EXPORT_DIR = "/mnt/recyclebin"
PERMISSIONS = "rw,sync,no_subtree_check"
DB_PATH = 'database.db'

# Database setup
def init_db():
    """Initialize the database and create the metrics table if it doesn't exist."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                cpu_usage REAL,
                memory_usage REAL,
                disk_usage REAL
            )
        ''')

# NFS Utilities
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

# Metrics Collection
def collect_metrics():
    """Continuously collect and store system metrics in the database."""
    while True:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cpu_usage = psutil.cpu_percent(interval=1)
        memory_usage = psutil.virtual_memory().percent
        disk_usage = psutil.disk_usage('/').percent

        with sqlite3.connect(DB_PATH) as conn:
            conn.execute('INSERT INTO metrics (timestamp, cpu_usage, memory_usage, disk_usage) VALUES (?, ?, ?, ?)',
                         (timestamp, cpu_usage, memory_usage, disk_usage))
        time.sleep(30)  # Collect every 30 seconds

# Routes
@app.route('/')
def dashboard():
    """Render the main dashboard page with the latest metrics."""
    with sqlite3.connect(DB_PATH) as conn:
        latest_metrics = conn.execute('SELECT * FROM metrics ORDER BY timestamp DESC LIMIT 1').fetchone()

    if latest_metrics:
        data = {
            'last_updated': latest_metrics[1],
            'cpu_usage': latest_metrics[2],
            'memory_usage': latest_metrics[3],
            'disk_usage': latest_metrics[4]
        }
    else:
        data = {
            'last_updated': 'No data available',
            'cpu_usage': 0,
            'memory_usage': 0,
            'disk_usage': 0
        }
    return render_template('index.html', **data)

@app.route('/metrics')
def get_metrics():
    """Fetch and return metrics data and the count of connected agents as JSON."""
    with sqlite3.connect(DB_PATH) as conn:
        metrics = conn.execute('SELECT timestamp, cpu_usage, memory_usage, disk_usage FROM metrics ORDER BY timestamp ASC LIMIT 50').fetchall()

    data = {
        'timestamps': [row[0] for row in metrics],
        'cpu_usages': [row[1] for row in metrics],
        'memory_usages': [row[2] for row in metrics],
        'disk_usages': [row[3] for row in metrics],
        'agent_count': len(get_nfs_clients())
    }
    return jsonify(data)

@app.route('/agent', methods=['GET', 'POST'])
def manage_agents():
    """List, add, or remove NFS clients."""
    if request.method == 'POST':
        client_ip = request.form.get('client_ip')
        if 'add_client' in request.form and client_ip:
            success = add_nfs_client(client_ip)
            flash(f"NFS Client {client_ip} {'added' if success else 'not added'}.", 'success' if success else 'danger')
        elif 'remove_client' in request.form:
            success = remove_nfs_client(client_ip)
            flash(f"NFS Client {client_ip} {'removed' if success else 'not removed'}.", 'success' if success else 'danger')
        return redirect(url_for('manage_agents'))

    return render_template('agent.html', nfs_clients=get_nfs_clients())

def find_client_dir(client_ip):
    """Find the directory for the client based on the private IP."""
    for item in os.listdir(EXPORT_DIR):
        if item.startswith(client_ip):  # Match the private IP part
            return os.path.join(EXPORT_DIR, item)
    return None

@app.route('/client_files')
def client_files():
    """Retrieve files in the specified client's directory and return as JSON."""
    client_ip = request.args.get('client')
    client_dir = find_client_dir(client_ip)
    
    if not client_dir:
        return jsonify(files=[], error="Client directory not found.")

    def list_files(path):
        """List all files and directories within a given path."""
        files = []
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            files.append({
                'name': item,
                'path': item_path,
                'is_dir': os.path.isdir(item_path),
                'children': list_files(item_path) if os.path.isdir(item_path) else None
            })
        return files

    return jsonify(files=list_files(client_dir))

@app.route('/client_log')
def client_log():
    """Serve the contents of the log file for the specified client."""
    client_ip = request.args.get('client')
    client_dir = find_client_dir(client_ip)
    
    if not client_dir:
        return "Client directory not found.", 404

    log_file_path = os.path.join(client_dir, 'cbin.log')
    if os.path.isfile(log_file_path):
        with open(log_file_path, 'r') as log_file:
            log_entries = [json.loads(line) for line in log_file]

        # Format log entries as a table
        table = "<table><tr><th>Time</th><th>Level</th><th>Message</th></tr>"
        for entry in log_entries:
            # Add a class attribute to the table row based on the log level
            row_class = 'bg-red-100' if entry['level'] == 'error' else ''
            table += f"<tr class='{row_class}'><td>{entry['time']}</td><td>{entry['level']}</td><td>{entry['msg']}</td></tr>"
        table += "</table>"

        return table

    return "Log file not found.", 404

@app.route('/view_file')
def view_file():
    """Serve a specific file's contents for viewing or downloading."""
    file_path = request.args.get('file_path')
    if file_path and os.path.isfile(file_path):
        return send_file(file_path, as_attachment=False)
    flash("File not found.", 'danger')
    return redirect(url_for('manage_agents'))

if __name__ == '__main__':
    init_db()
    Thread(target=collect_metrics, daemon=True).start()
    app.run(debug=True)
