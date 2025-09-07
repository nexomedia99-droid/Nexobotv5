
from flask import Flask, jsonify
import threading
import time

app = Flask(__name__)

@app.route('/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "NexoBot",
        "timestamp": time.time()
    })

@app.route('/')
def root():
    return jsonify({
        "message": "NexoBot is running",
        "status": "active"
    })

def run_health_server():
    """Run health check server in background"""
    app.run(host='0.0.0.0', port=8080, debug=False)

def start_health_server():
    """Start health server in separate thread"""
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()
    print("✅ Health check server started on port 8080")
