from flask import Flask
from threading import Thread
from database import init_db
from metrics import collect_metrics
from routes import init_routes

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Configuration
EXPORT_DIR = "/mnt/recyclebin"
PERMISSIONS = "rw,sync,no_subtree_check"
DB_PATH = 'database.db'

if __name__ == '__main__':
    init_db()
    Thread(target=collect_metrics, daemon=True).start()
    init_routes(app)
    app.run(host='0.0.0.0', port=5000, debug=True)