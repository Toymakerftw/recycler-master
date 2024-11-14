import psutil
import sqlite3
import time
from datetime import datetime
from database import DB_PATH

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