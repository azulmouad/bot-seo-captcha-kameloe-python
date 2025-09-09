#!/usr/bin/env python3
"""
Bot Runner - Handles bot execution with web updates and pause/resume functionality
"""

import time
import logging
from datetime import datetime
from src.utils.bot_status import bot_status
from src.utils.helpers import make_json_serializable
from src.utils.cookie_manager import CookieManager

logger = logging.getLogger(__name__)

class BotRunner:
    """Handles bot execution with real-time web updates"""
    
    def __init__(self, bot_instance, socketio):
        self.bot = bot_instance
        self.socketio = socketio
        
        # Initialize cookie manager for bot runner
        self.cookie_manager = CookieManager()
        logger.info("Bot runner initialized with cookie management support")
    
    def run_with_web_updates(self):
        """Run bot with real-time web updates"""
        try:
            bot_status['is_running'] = True
            bot_status['is_paused'] = False
            bot_status['message'] = 'Bot starting...'
            bot_status['total'] = len(self.bot.proxy_list)
            bot_status['completed'] = 0
            bot_status['found'] = 0
            bot_status['start_time'] = datetime.now().isoformat()
            
            self.socketio.emit('status_update', make_json_serializable(bot_status))
            
            logger.info(f"Starting SEO bot with {len(self.bot.proxy_list)} proxies")
            logger.info(f"Searching for '{self.bot.keyword}' on domain '{self.bot.target_domain}'")
            logger.info(f"Using Google domain: {self.bot.google_domain}")
            logger.info(f"Device profile: {self.bot.device_profile.title()}")
            
            successful_runs = 0
            
            for i, proxy in enumerate(self.bot.proxy_list, 1):
                if not bot_status['is_running']:  # Check if stopped
                    break
                
                # Wait while paused
                while bot_status['is_paused'] and bot_status['is_running']:
                    time.sleep(1)  # Check every second
                
                if not bot_status['is_running']:  # Check again after pause
                    break
                    
                self.bot.current_proxy_index = i
                bot_status['current_proxy'] = proxy
                bot_status['message'] = f'Processing proxy {i}/{len(self.bot.proxy_list)}'
                self.socketio.emit('status_update', make_json_serializable(bot_status))
                
                logger.info(f"--- Processing proxy {i}/{len(self.bot.proxy_list)} ---")
                
                result = self.run_single_proxy_with_tracking(proxy, i)
                
                if result['success']:
                    successful_runs += 1
                    bot_status['found'] += 1
                    logger.info(f"✓ Proxy {proxy} completed successfully")
                else:
                    logger.error(f"✗ Proxy {proxy} failed")
                
                # Add result to results list
                from src.utils.bot_status import bot_results
                bot_results.insert(0, result)
                self.socketio.emit('new_result', make_json_serializable(result))
                
                bot_status['completed'] += 1
                self.socketio.emit('status_update', make_json_serializable(bot_status))
                
                # Random delay between proxies
                if i < len(self.bot.proxy_list) and bot_status['is_running']:
                    delay = 3  # Reduced delay for demo
                    logger.info(f"Waiting {delay} seconds before next proxy...")
                    
                    # Sleep in small increments to allow pause/resume during delay
                    for _ in range(delay):
                        if not bot_status['is_running']:
                            break
                        # Wait while paused
                        while bot_status['is_paused'] and bot_status['is_running']:
                            time.sleep(0.5)
                        if bot_status['is_running']:
                            time.sleep(1)
            
            # Final status
            bot_status['is_running'] = False
            bot_status['message'] = f'Bot finished! Found domain in {bot_status["found"]}/{bot_status["total"]} sessions'
            self.socketio.emit('status_update', make_json_serializable(bot_status))
            
            logger.info("=" * 50)
            logger.info("FINAL RESULTS:")
            logger.info(f"Total proxies tested: {len(self.bot.proxy_list)}")
            logger.info(f"Successful runs: {successful_runs}")
            logger.info(f"Failed runs: {len(self.bot.proxy_list) - successful_runs}")
            logger.info("=" * 50)
            
        except Exception as e:
            logger.error(f"Bot execution error: {str(e)}")
            bot_status['is_running'] = False
            bot_status['message'] = f'Bot error: {str(e)}'
            self.socketio.emit('status_update', make_json_serializable(bot_status))
    
    def run_single_proxy_with_tracking(self, proxy, proxy_number):
        """Run single proxy with result tracking"""
        start_time = datetime.now()
        
        result = {
            'id': int(time.time() * 1000) + proxy_number,
            'status': 'not found',
            'keyword': self.bot.keyword,
            'proxy': proxy.split(':')[0] + ':' + proxy.split(':')[1] if ':' in proxy else proxy,
            'page': 1,
            'position': None,
            'time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'success': False
        }
        
        try:
            # Wait while paused before starting proxy processing
            while bot_status['is_paused'] and bot_status['is_running']:
                time.sleep(1)
            
            if not bot_status['is_running']:
                return result
            
            # Check proxy
            proxy_works, proxy_ip = self.bot.check_proxy(proxy)
            if not proxy_works:
                logger.error(f"Proxy {proxy} is not working, skipping...")
                return result
            
            # Wait while paused before browser setup
            while bot_status['is_paused'] and bot_status['is_running']:
                time.sleep(1)
            
            if not bot_status['is_running']:
                return result
            
            # Setup browser
            if not self.bot.setup_browser(proxy):
                logger.error("Failed to setup browser")
                return result
            
            # Wait while paused before proxy verification
            while bot_status['is_paused'] and bot_status['is_running']:
                time.sleep(1)
            
            if not bot_status['is_running']:
                self.bot.close_browser()
                return result
            
            # Verify proxy is being used
            if not self.bot.verify_proxy_ip():
                logger.error("Proxy verification failed - using real IP!")
                self.bot.close_browser()
                return result
            
            # Wait while paused before Google search
            while bot_status['is_paused'] and bot_status['is_running']:
                time.sleep(1)
            
            if not bot_status['is_running']:
                self.bot.close_browser()
                return result
            
            # Search Google with enhanced interactions
            if not self.bot.search_google():
                logger.error("Google search failed")
                self.bot.close_browser()
                return result
            
            # Wait while paused before target search
            while bot_status['is_paused'] and bot_status['is_running']:
                time.sleep(1)
            
            if not bot_status['is_running']:
                self.bot.close_browser()
                return result
            
            # Find and visit target with page tracking
            found, page, position = self.bot.find_and_visit_target_with_tracking()
            
            if found:
                result['status'] = 'found'
                result['page'] = page
                result['position'] = position
                result['success'] = True
                logger.info(f"✓ Found domain on page {page}, position {position}")
            else:
                logger.warning(f"Domain not found in search results")
            
            # Cookies will be automatically saved in close_browser() method
            
            self.bot.close_browser()
            return result
            
        except Exception as e:
            logger.error(f"Error in single proxy run: {str(e)}")
            self.bot.close_browser()
            return result
    
    def get_cookie_summary(self):
        """Get summary of saved cookies across all proxies"""
        try:
            proxies_with_cookies = self.cookie_manager.get_all_proxies_with_cookies()
            return {
                'total_proxies_with_cookies': len(proxies_with_cookies),
                'proxies': proxies_with_cookies
            }
        except Exception as e:
            logger.error(f"Failed to get cookie summary: {str(e)}")
            return {'total_proxies_with_cookies': 0, 'proxies': []}
    
    def clear_all_saved_cookies(self):
        """Clear all saved cookies from database"""
        try:
            logger.info("🗑️ Clearing all saved cookies...")
            success = self.cookie_manager.clear_all_cookies()
            if success:
                logger.info("✓ All cookies cleared successfully")
            return success
        except Exception as e:
            logger.error(f"Failed to clear all cookies: {str(e)}")
            return False
    
    def get_proxy_cookie_info(self, proxy_id):
        """Get cookie information for specific proxy"""
        try:
            has_cookies = self.cookie_manager.has_cookies(proxy_id)
            if has_cookies:
                cookies = self.cookie_manager.load_cookies(proxy_id)
                return {
                    'has_cookies': True,
                    'count': len(cookies) if cookies else 0,
                    'proxy_id': proxy_id
                }
            else:
                return {
                    'has_cookies': False,
                    'count': 0,
                    'proxy_id': proxy_id
                }
        except Exception as e:
            logger.error(f"Failed to get proxy cookie info: {str(e)}")
            return {'has_cookies': False, 'count': 0, 'proxy_id': proxy_id}