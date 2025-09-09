#!/usr/bin/env python3
"""
Logging configuration for the SEO bot
"""

import logging
import time
from datetime import datetime

class WebSocketLogger(logging.Handler):
    """Custom logging handler to send logs to web interface"""
    
    def __init__(self, socketio):
        super().__init__()
        self.socketio = socketio
    
    def emit(self, record):
        from src.utils.bot_status import bot_logs
        
        log_entry = {
            'time': datetime.now().strftime('%H:%M:%S'),
            'type': self.get_log_type(record.levelname),
            'message': record.getMessage(),
            'timestamp': time.time()
        }
        
        # Add to logs list
        bot_logs.insert(0, log_entry)
        
        # Keep only last 100 logs
        if len(bot_logs) > 100:
            bot_logs.pop()
        
        # Emit to web interface
        self.socketio.emit('new_log', log_entry)
    
    def get_log_type(self, levelname):
        mapping = {
            'INFO': 'info',
            'WARNING': 'warning',
            'ERROR': 'error',
            'CRITICAL': 'error',
            'DEBUG': 'info'
        }
        return mapping.get(levelname, 'info')

def setup_logging(socketio):
    """Setup logging configuration"""
    # Configure basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Add custom handler to bot logger
    web_handler = WebSocketLogger(socketio)
    bot_logger = logging.getLogger('bot_kameleo')
    bot_logger.addHandler(web_handler)
    bot_logger.setLevel(logging.INFO)
    
    return web_handler