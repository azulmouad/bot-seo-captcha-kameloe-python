#!/usr/bin/env python3
"""
Bot Status - Global state management for the SEO bot
"""

# Global variables to track bot state
bot_status = {
    'is_running': False,
    'is_paused': False,
    'message': 'Bot ready to start',
    'found': 0,
    'total': 0,
    'completed': 0,
    'start_time': None,
    'current_proxy': None
}

bot_results = []
bot_logs = []