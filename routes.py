from flask import render_template, request, redirect, url_for, flash, jsonify, send_file, json
import sqlite3
import os
from database import DB_PATH
from nfs_utils import get_nfs_clients

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
