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
from src.utils.cookie_manager import CookieManager

logger = logging.getLogger(__name__)

# Global variables
bot_instance = None
bot_thread = None
cookie_manager = CookieManager()

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
            
            # Check if cookies should be enabled
            use_cookies = data.get('useCookies', False)
            logger.info(f"🍪 Cookie management requested: {use_cookies}")
            
            # Create bot instance with cookie support
            bot_instance = EnhancedGoogleSearchBot(keyword, domain, proxy_list, max_pages, google_domain, device_profile, use_cookies)
            logger.info(f"🍪 Bot created with cookie support: {bot_instance.use_cookies}")
            
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

    @app.route('/api/cookies/summary')
    def get_cookie_summary():
        """Get summary of all saved cookies"""
        try:
            proxies_with_cookies = cookie_manager.get_all_proxies_with_cookies()
            summary = {
                'total_proxies_with_cookies': len(proxies_with_cookies),
                'proxies': proxies_with_cookies
            }
            return jsonify(summary)
        except Exception as e:
            logger.error(f"Error getting cookie summary: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/cookies/proxy/<proxy_id>')
    def get_proxy_cookies(proxy_id):
        """Get cookie information for specific proxy"""
        try:
            has_cookies = cookie_manager.has_cookies(proxy_id)
            if has_cookies:
                cookies = cookie_manager.load_cookies(proxy_id)
                return jsonify({
                    'has_cookies': True,
                    'count': len(cookies) if cookies else 0,
                    'proxy_id': proxy_id,
                    'cookies': cookies
                })
            else:
                return jsonify({
                    'has_cookies': False,
                    'count': 0,
                    'proxy_id': proxy_id,
                    'cookies': []
                })
        except Exception as e:
            logger.error(f"Error getting proxy cookies: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/cookies/clear', methods=['POST'])
    def clear_all_cookies():
        """Clear all saved cookies"""
        try:
            success = cookie_manager.clear_all_cookies()
            if success:
                logger.info("All cookies cleared via API")
                return jsonify({'message': 'All cookies cleared successfully'})
            else:
                return jsonify({'error': 'Failed to clear cookies'}), 500
        except Exception as e:
            logger.error(f"Error clearing cookies: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/cookies/clear/<proxy_id>', methods=['POST'])
    def clear_proxy_cookies(proxy_id):
        """Clear cookies for specific proxy"""
        try:
            success = cookie_manager.delete_cookies(proxy_id)
            if success:
                logger.info(f"Cookies cleared for proxy: {proxy_id}")
                return jsonify({'message': f'Cookies cleared for proxy: {proxy_id}'})
            else:
                return jsonify({'error': f'Failed to clear cookies for proxy: {proxy_id}'}), 500
        except Exception as e:
            logger.error(f"Error clearing proxy cookies: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/cookies/cleanup', methods=['POST'])
    def cleanup_expired_cookies():
        """Clean up expired cookies across all proxies"""
        try:
            cleaned_count = cookie_manager.cleanup_expired_cookies()
            logger.info(f"Cleaned expired cookies from {cleaned_count} proxies")
            return jsonify({
                'message': f'Cleaned expired cookies from {cleaned_count} proxies',
                'cleaned_proxies': cleaned_count
            })
        except Exception as e:
            logger.error(f"Error cleaning up expired cookies: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/cookies/stats')
    def get_cookie_stats():
        """Get comprehensive cookie statistics"""
        try:
            stats = cookie_manager.get_cookie_stats()
            return jsonify(stats)
        except Exception as e:
            logger.error(f"Error getting cookie stats: {str(e)}")
            return jsonify({'error': str(e)}), 500