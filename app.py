from flask import Flask, render_template, jsonify
import psutil
import sqlite3
from datetime import datetime
import time
from threading import Thread

app = Flask(__name__)

# Database setup
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            cpu_usage REAL,
            memory_usage REAL,
            disk_usage REAL
        )
    ''')
    conn.commit()
    conn.close()

# Collect metrics and store in the database
def collect_metrics():
    while True:
        cpu_usage = psutil.cpu_percent(interval=1)
        memory_usage = psutil.virtual_memory().percent
        disk_usage = psutil.disk_usage('/').percent

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('INSERT INTO metrics (timestamp, cpu_usage, memory_usage, disk_usage) VALUES (?, ?, ?, ?)',
                  (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), cpu_usage, memory_usage, disk_usage))
        conn.commit()
        conn.close()
        time.sleep(30)  # Collect metrics every minute

@app.route('/')
def dashboard():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT * FROM metrics ORDER BY timestamp DESC LIMIT 1')
    latest_metrics = c.fetchone()
    conn.close()

    if latest_metrics:
        last_updated = latest_metrics[1]
        cpu_usage = latest_metrics[2]
        memory_usage = latest_metrics[3]
        disk_usage = latest_metrics[4]
    else:
        last_updated = 'No data available'
        cpu_usage = 0
        memory_usage = 0
        disk_usage = 0

    return render_template('index.html', last_updated=last_updated, cpu_usage=cpu_usage, memory_usage=memory_usage, disk_usage=disk_usage)

@app.route('/metrics')
def get_metrics():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT timestamp, cpu_usage, memory_usage, disk_usage FROM metrics ORDER BY timestamp ASC')
    metrics = c.fetchall()
    conn.close()

    timestamps = [row[0] for row in metrics]
    cpu_usages = [row[1] for row in metrics]
    memory_usages = [row[2] for row in metrics]
    disk_usages = [row[3] for row in metrics]

    return jsonify({
        'timestamps': timestamps,
        'cpu_usages': cpu_usages,
        'memory_usages': memory_usages,
        'disk_usages': disk_usages
    })

if __name__ == '__main__':
    init_db()
    # Start the metrics collection in a separate thread
    Thread(target=collect_metrics, daemon=True).start()
    app.run(debug=True)
