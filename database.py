import sqlite3

DB_PATH = 'database.db'

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