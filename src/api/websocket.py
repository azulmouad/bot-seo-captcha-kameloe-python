#!/usr/bin/env python3
"""
WebSocket handlers for the SEO Bot Dashboard
"""

import logging
from flask_socketio import emit
from src.utils.bot_status import bot_status, bot_logs, bot_results
from src.utils.helpers import make_json_serializable

logger = logging.getLogger(__name__)

def setup_websocket_handlers(socketio):
    """Setup WebSocket event handlers"""
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        logger.info("Client connected to WebSocket")
        emit('status_update', make_json_serializable(bot_status))
        emit('logs_update', make_json_serializable(bot_logs))
        emit('results_update', make_json_serializable(bot_results))

    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        logger.info("Client disconnected from WebSocket")