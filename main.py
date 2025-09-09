#!/usr/bin/env python3
"""
SEO Bot Dashboard - Main Application Entry Point
"""

import logging
from flask import Flask
from flask_socketio import SocketIO
from src.api.routes import setup_routes
from src.api.websocket import setup_websocket_handlers
from src.utils.logging_config import setup_logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'seo-bot-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Setup logging
setup_logging(socketio)

# Setup routes and websocket handlers
setup_routes(app, socketio)
setup_websocket_handlers(socketio)

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 SEO Bot Dashboard Server")
    print("=" * 60)
    print("📊 Dashboard: http://localhost:8080")
    print("🔧 Make sure Kameleo.CLI is running on port 5050")
    print("💡 Press Ctrl+C to stop the server")
    print("=" * 60)
    
    # Run the Flask-SocketIO app
    socketio.run(app, host='0.0.0.0', port=8080, debug=False)