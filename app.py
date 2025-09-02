#!/usr/bin/env python3
"""
Flask web application to serve the SEO Bot Dashboard and handle bot execution
"""

import os
import json
import time
import threading
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
import logging
from bot_kameleo import GoogleSearchBot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'seo-bot-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variables to track bot state
bot_instance = None
bot_thread = None
bot_status = {
    'is_running': False,
    'message': 'Bot ready to start',
    'found': 0,
    'total': 0,
    'completed': 0,
    'start_time': None,
    'current_proxy': None
}
bot_results = []
bot_logs = []

def make_json_serializable(obj):
    """Convert datetime objects to strings for JSON serialization"""
    if isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_serializable(item) for item in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    else:
        return obj

class WebSocketLogger(logging.Handler):
    """Custom logging handler to send logs to web interface"""
    
    def emit(self, record):
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
        socketio.emit('new_log', log_entry)
    
    def get_log_type(self, levelname):
        mapping = {
            'INFO': 'info',
            'WARNING': 'warning',
            'ERROR': 'error',
            'CRITICAL': 'error',
            'DEBUG': 'info'
        }
        return mapping.get(levelname, 'info')

# Add custom handler to bot logger
web_handler = WebSocketLogger()
bot_logger = logging.getLogger('bot_kameleo')
bot_logger.addHandler(web_handler)
bot_logger.setLevel(logging.INFO)

class EnhancedGoogleSearchBot(GoogleSearchBot):
    """Enhanced bot class with web interface integration"""
    
    def __init__(self, keyword, target_domain, proxy_list, max_pages=3):
        super().__init__(keyword, target_domain, proxy_list)
        self.max_pages = max_pages
        self.current_proxy_index = 0
        
    def run_with_web_updates(self):
        """Run bot with real-time web updates"""
        global bot_status, bot_results
        
        try:
            bot_status['is_running'] = True
            bot_status['message'] = 'Bot starting...'
            bot_status['total'] = len(self.proxy_list)
            bot_status['completed'] = 0
            bot_status['found'] = 0
            bot_status['start_time'] = datetime.now().isoformat()
            
            socketio.emit('status_update', make_json_serializable(bot_status))
            
            logger.info(f"Starting SEO bot with {len(self.proxy_list)} proxies")
            logger.info(f"Searching for '{self.keyword}' on domain '{self.target_domain}'")
            
            successful_runs = 0
            
            for i, proxy in enumerate(self.proxy_list, 1):
                if not bot_status['is_running']:  # Check if stopped
                    break
                    
                self.current_proxy_index = i
                bot_status['current_proxy'] = proxy
                bot_status['message'] = f'Processing proxy {i}/{len(self.proxy_list)}'
                socketio.emit('status_update', make_json_serializable(bot_status))
                
                logger.info(f"--- Processing proxy {i}/{len(self.proxy_list)} ---")
                
                result = self.run_single_proxy_with_tracking(proxy, i)
                
                if result['success']:
                    successful_runs += 1
                    bot_status['found'] += 1
                    logger.info(f"✓ Proxy {proxy} completed successfully")
                else:
                    logger.error(f"✗ Proxy {proxy} failed")
                
                # Add result to results list
                bot_results.insert(0, result)
                socketio.emit('new_result', make_json_serializable(result))
                
                bot_status['completed'] += 1
                socketio.emit('status_update', make_json_serializable(bot_status))
                
                # Random delay between proxies
                if i < len(self.proxy_list) and bot_status['is_running']:
                    delay = 3  # Reduced delay for demo
                    logger.info(f"Waiting {delay} seconds before next proxy...")
                    time.sleep(delay)
            
            # Final status
            bot_status['is_running'] = False
            bot_status['message'] = f'Bot finished! Found domain in {bot_status["found"]}/{bot_status["total"]} sessions'
            socketio.emit('status_update', make_json_serializable(bot_status))
            
            logger.info("=" * 50)
            logger.info("FINAL RESULTS:")
            logger.info(f"Total proxies tested: {len(self.proxy_list)}")
            logger.info(f"Successful runs: {successful_runs}")
            logger.info(f"Failed runs: {len(self.proxy_list) - successful_runs}")
            logger.info("=" * 50)
            
        except Exception as e:
            logger.error(f"Bot execution error: {str(e)}")
            bot_status['is_running'] = False
            bot_status['message'] = f'Bot error: {str(e)}'
            socketio.emit('status_update', make_json_serializable(bot_status))
    
    def run_single_proxy_with_tracking(self, proxy, proxy_number):
        """Run single proxy with result tracking"""
        start_time = datetime.now()
        
        result = {
            'id': int(time.time() * 1000) + proxy_number,
            'status': 'not found',
            'keyword': self.keyword,
            'proxy': proxy.split(':')[0] + ':' + proxy.split(':')[1] if ':' in proxy else proxy,
            'page': 1,
            'position': None,
            'time': start_time.strftime('%H:%M:%S'),
            'success': False
        }
        
        try:
            # Check proxy
            proxy_works, proxy_ip = self.check_proxy(proxy)
            if not proxy_works:
                logger.error(f"Proxy {proxy} is not working, skipping...")
                return result
            
            # Setup browser
            if not self.setup_browser(proxy):
                logger.error("Failed to setup browser")
                return result
            
            # Verify proxy is being used
            if not self.verify_proxy_ip():
                logger.error("Proxy verification failed - using real IP!")
                self.close_browser()
                return result
            
            # Search Google
            if not self.search_google():
                logger.error("Google search failed")
                self.close_browser()
                return result
            
            # Find and visit target with page tracking
            found, page, position = self.find_and_visit_target_with_tracking()
            
            if found:
                result['status'] = 'found'
                result['page'] = page
                result['position'] = position
                result['success'] = True
                logger.info(f"✓ Found domain on page {page}, position {position}")
            else:
                logger.warning(f"Domain not found in search results")
            
            self.close_browser()
            return result
            
        except Exception as e:
            logger.error(f"Error in single proxy run: {str(e)}")
            self.close_browser()
            return result
    
    def find_and_visit_target_with_tracking(self):
        """Find target domain with page and position tracking"""
        try:
            logger.info(f"Looking for domain: {self.target_domain}")
            
            for page in range(1, self.max_pages + 1):
                if page > 1:
                    # Navigate to next page
                    try:
                        next_button = self.driver.find_element(By.ID, "pnnext")
                        next_button.click()
                        time.sleep(3)
                        logger.info(f"Navigated to page {page}")
                    except:
                        logger.warning(f"Could not navigate to page {page}")
                        break
                
                # Get search results on current page
                search_results = self.driver.find_elements(By.CSS_SELECTOR, "h3")
                
                for position, result in enumerate(search_results, 1):
                    try:
                        parent_link = result.find_element(By.XPATH, "..")
                        if parent_link.tag_name == 'a':
                            href = parent_link.get_attribute('href')
                            if href and self.target_domain in href:
                                logger.info(f"Found target domain on page {page}, position {position}: {href}")
                                
                                # Click and visit
                                time.sleep(2)
                                parent_link.click()
                                time.sleep(3)
                                
                                # Perform realistic interaction
                                self.realistic_website_interaction()
                                
                                return True, page, position
                                
                    except Exception as e:
                        continue
                
                logger.info(f"Domain not found on page {page}")
            
            return False, self.max_pages, None
            
        except Exception as e:
            logger.error(f"Error finding/visiting target: {str(e)}")
            return False, 1, None

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
    global bot_instance, bot_thread, bot_status
    
    if bot_status['is_running']:
        return jsonify({'error': 'Bot is already running'}), 400
    
    try:
        data = request.json
        keyword = data.get('keyword', '').strip()
        domain = data.get('domain', '').strip()
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
        bot_instance = EnhancedGoogleSearchBot(keyword, domain, proxy_list, max_pages)
        
        # Start bot in separate thread
        bot_thread = threading.Thread(target=bot_instance.run_with_web_updates)
        bot_thread.daemon = True
        bot_thread.start()
        
        return jsonify({'message': 'Bot started successfully'})
        
    except Exception as e:
        logger.error(f"Error starting bot: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stop', methods=['POST'])
def stop_bot():
    """Stop the running bot"""
    global bot_status
    
    if not bot_status['is_running']:
        return jsonify({'error': 'Bot is not running'}), 400
    
    bot_status['is_running'] = False
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