from flask import render_template, request, redirect, url_for, flash, jsonify, send_file, json
import sqlite3
import os
from database import DB_PATH
from nfs_utils import get_nfs_clients, add_nfs_client, remove_nfs_client
import glob
import pathlib

EXPORT_DIR = "/mnt/recyclebin"

def init_routes(app):
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
    def agent():
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
            return redirect(url_for('agent'))

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

        return render_template('agent.html', nfs_clients=nfs_clients)

    @app.route('/files/<client_ip>')
    def get_client_files(client_ip):
        """Get files for a specific client."""
        try:
            # Construct the path using client IP
            client_path = os.path.join(EXPORT_DIR, client_ip)

            # Get the relative path from query parameters, default to root
            rel_path = request.args.get('path', '')
            current_path = os.path.join(client_path, rel_path)

            # Ensure the path is still within the client's directory
            if not os.path.realpath(current_path).startswith(os.path.realpath(client_path)):
                return jsonify({'error': 'Invalid path'}), 403

            if not os.path.exists(current_path):
                return jsonify({'error': 'Path not found'}), 404

            files = []
            directories = []

            # List all files and directories in the current path
            for item in os.listdir(current_path):
                item_path = os.path.join(current_path, item)
                item_stat = os.stat(item_path)
                item_info = {
                    'name': item,
                    'size': item_stat.st_size,
                    'modified': item_stat.st_mtime,
                    'is_dir': os.path.isdir(item_path)
                }

                if item_info['is_dir']:
                    directories.append(item_info)
                else:
                    files.append(item_info)

            # Calculate breadcrumb data
            rel_path_parts = rel_path.split(os.sep) if rel_path else []
            breadcrumbs = []
            current = ''
            for part in rel_path_parts:
                if part:
                    current = os.path.join(current, part)
                    breadcrumbs.append({
                        'name': part,
                        'path': current
                    })

            return jsonify({
                'current_path': rel_path,
                'breadcrumbs': breadcrumbs,
                'directories': sorted(directories, key=lambda x: x['name']),
                'files': sorted(files, key=lambda x: x['name'])
            })

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/download/<client_ip>/<path:file_path>')
    def download_file(client_ip, file_path):
        """Download a file from a client's directory."""
        try:
            # Construct the full file path
            full_path = os.path.join(EXPORT_DIR, client_ip, file_path)

            # Ensure the path is still within the client's directory
            client_dir = os.path.join(EXPORT_DIR, client_ip)
            if not os.path.realpath(full_path).startswith(os.path.realpath(client_dir)):
                return jsonify({'error': 'Invalid path'}), 403

            if not os.path.exists(full_path) or os.path.isdir(full_path):
                return jsonify({'error': 'File not found'}), 404

            return send_file(full_path, as_attachment=True)

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/client_log')
    def client_log():
        """Serve the contents of the log file for the specified client."""
        client = request.args.get('client')
        log_file_path = os.path.join(EXPORT_DIR, client, 'cbin.log')
        if client and os.path.isfile(log_file_path):
            try:
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
            except Exception as e:
                return f"Error reading log file: {str(e)}", 500
        return "Log file not found.", 404

    return app