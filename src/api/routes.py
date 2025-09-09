#!/usr/bin/env python3
"""
API Routes for the SEO Bot Dashboard
"""

import threading
import logging
from flask import request, jsonify, send_from_directory
from src.bot.enhanced_bot import EnhancedGoogleSearchBot
from src.bot.bot_runner import BotRunner
from src.utils.bot_status import bot_status, bot_results, bot_logs
from src.utils.helpers import make_json_serializable

logger = logging.getLogger(__name__)

# Global variables
bot_instance = None
bot_thread = None

def setup_routes(app, socketio):
    """Setup all API routes"""
    
    @app.route('/')
    def index():
        """Serve the dashboard"""
        return send_from_directory('.', 'dashboard.html')

    @app.route('/api/status')
    def get_status():
        """Get current bot status"""
        return jsonify(bot_status)

    @app.route('/api/results')
    def get_results():
        """Get bot results"""
        return jsonify(bot_results)

    @app.route('/api/logs')
    def get_logs():
        """Get bot logs"""
        return jsonify(bot_logs)

    @app.route('/api/start', methods=['POST'])
    def start_bot():
        """Start the bot with given configuration"""
        global bot_instance, bot_thread
        
        if bot_status['is_running']:
            return jsonify({'error': 'Bot is already running'}), 400
        
        try:
            data = request.json
            keyword = data.get('keyword', '').strip()
            domain = data.get('domain', '').strip()
            google_domain = data.get('googleDomain', 'google.com.tr').strip()
            device_profile = data.get('deviceProfile', 'desktop').strip()
            max_pages = int(data.get('maxPages', 3))
            proxy_list_text = data.get('proxyList', '').strip()
            
            # Validate inputs
            if not keyword or not domain:
                return jsonify({'error': 'Keyword and domain are required'}), 400
            
            # Parse proxy list
            proxy_list = [p.strip() for p in proxy_list_text.split('\n') if p.strip()]
            if not proxy_list:
                return jsonify({'error': 'At least one proxy is required'}), 400
            
            # Clear previous results and logs
            bot_results.clear()
            bot_logs.clear()
            
            # Create bot instance
            bot_instance = EnhancedGoogleSearchBot(keyword, domain, proxy_list, max_pages, google_domain, device_profile)
            
            # Create bot runner and start in separate thread
            bot_runner = BotRunner(bot_instance, socketio)
            bot_thread = threading.Thread(target=bot_runner.run_with_web_updates)
            bot_thread.daemon = True
            bot_thread.start()
            
            return jsonify({'message': 'Bot started successfully'})
            
        except Exception as e:
            logger.error(f"Error starting bot: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/stop', methods=['POST'])
    def stop_bot():
        """Stop the running bot"""
        if not bot_status['is_running']:
            return jsonify({'error': 'Bot is not running'}), 400
        
        bot_status['is_running'] = False
        bot_status['is_paused'] = False
        bot_status['message'] = 'Bot stopped by user'
        
        # Close browser if running
        if bot_instance and bot_instance.driver:
            try:
                bot_instance.close_browser()
            except:
                pass
        
        socketio.emit('status_update', make_json_serializable(bot_status))
        logger.info("Bot stopped by user")
        
        return jsonify({'message': 'Bot stopped successfully'})

    @app.route('/api/pause', methods=['POST'])
    def pause_bot():
        """Pause the running bot"""
        if not bot_status['is_running']:
            return jsonify({'error': 'Bot is not running'}), 400
        
        if bot_status['is_paused']:
            return jsonify({'error': 'Bot is already paused'}), 400
        
        bot_status['is_paused'] = True
        bot_status['message'] = 'Bot paused - Browser available for manual interaction'
        
        socketio.emit('status_update', make_json_serializable(bot_status))
        logger.info("Bot paused by user - Browser available for manual interaction")
        
        return jsonify({'message': 'Bot paused successfully'})

    @app.route('/api/resume', methods=['POST'])
    def resume_bot():
        """Resume the paused bot"""
        if not bot_status['is_running']:
            return jsonify({'error': 'Bot is not running'}), 400
        
        if not bot_status['is_paused']:
            return jsonify({'error': 'Bot is not paused'}), 400
        
        bot_status['is_paused'] = False
        bot_status['message'] = 'Bot resumed - Continuing automated operation'
        
        socketio.emit('status_update', make_json_serializable(bot_status))
        logger.info("Bot resumed by user - Continuing automated operation")
        
        return jsonify({'message': 'Bot resumed successfully'})