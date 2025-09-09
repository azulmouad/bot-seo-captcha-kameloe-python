#!/usr/bin/env python3
"""
Flask web application to serve the SEO Bot Dashboard and handle bot execution
"""

import os
import json
import time
import threading
import random
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
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
    
    def __init__(self, keyword, target_domain, proxy_list, max_pages=3, google_domain="google.com.tr", device_profile="desktop"):
        super().__init__(keyword, target_domain, proxy_list, device_profile)
        self.max_pages = max_pages
        self.current_proxy_index = 0
        self.google_domain = google_domain
    
    def search_google(self):
        """Enhanced Google search with interaction"""
        try:
            google_url = f"https://www.{self.google_domain}"
            logger.info(f"Navigating to Google search: {google_url}")
            self.driver.get(google_url)
            
            # Wait 15 seconds as requested
            logger.info("⏰ Waiting 15 seconds after opening Google search...")
            
            # Sleep in small increments to allow pause/resume during wait
            for _ in range(15):
                if not bot_status['is_running']:
                    return False
                # Wait while paused
                while bot_status['is_paused'] and bot_status['is_running']:
                    time.sleep(0.5)
                if bot_status['is_running']:
                    time.sleep(1)
            
            # Perform scrolling interactions
            logger.info("🎭 Performing initial Google page interactions...")
            self.perform_google_page_interactions()
            
            # Find search box and perform search
            search_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            
            # Clear any existing text and type keyword
            search_box.clear()
            logger.info(f"Typing keyword: {self.keyword}")
            
            # Type with human-like delays
            for char in self.keyword:
                search_box.send_keys(char)
                time.sleep(random.uniform(0.1, 0.3))
            
            time.sleep(1)
            search_box.send_keys(Keys.RETURN)
            
            # Wait for search results
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "search"))
            )
            
            logger.info("✓ Google search completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Google search failed: {str(e)}")
            return False
    
    def perform_google_page_interactions(self):
        """Perform realistic interactions on any Google search page"""
        try:
            logger.info("🎭 Starting Google page interactions...")
            
            # Random initial wait
            time.sleep(random.uniform(1, 3))
            
            # Scroll down gradually
            logger.info("📜 Scrolling down on Google page...")
            for i in range(3):
                scroll_amount = random.randint(200, 400)
                self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                time.sleep(random.uniform(0.5, 1.5))
            
            # Wait and observe
            time.sleep(random.uniform(2, 4))
            
            # Scroll up a bit
            logger.info("📜 Scrolling up on Google page...")
            for i in range(2):
                scroll_amount = random.randint(150, 300)
                self.driver.execute_script(f"window.scrollBy(0, -{scroll_amount});")
                time.sleep(random.uniform(0.5, 1.5))
            
            # Hover over some elements randomly
            self.hover_google_elements()
            
            logger.info("✅ Completed Google page interactions")
            
        except Exception as e:
            logger.error(f"Error during Google page interactions: {str(e)}")
    
    def hover_google_elements(self):
        """Hover over random elements on Google search page"""
        try:
            # Common Google search elements to hover over
            hover_selectors = [
                'h3', 'a', '.g', '.tF2Cxc', '.yuRUbf', 
                '.VwiC3b', '.LC20lb', '.kno-ecr-pt'
            ]
            
            actions = ActionChains(self.driver)
            hovered_count = 0
            
            for selector in hover_selectors:
                if hovered_count >= 3:  # Limit to 3 hovers
                    break
                    
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    visible_elements = [el for el in elements[:5] if el.is_displayed()]
                    
                    if visible_elements:
                        element = random.choice(visible_elements)
                        
                        # Scroll element into view
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                        time.sleep(0.5)
                        
                        # Hover over element
                        actions.move_to_element(element).perform()
                        time.sleep(random.uniform(1, 2))
                        hovered_count += 1
                        
                        logger.info(f"🖱️ Hovered over Google element: {selector}")
                        
                except Exception:
                    continue
            
        except Exception as e:
            logger.error(f"Error hovering Google elements: {str(e)}")
        
    def run_with_web_updates(self):
        """Run bot with real-time web updates"""
        global bot_status, bot_results
        
        try:
            bot_status['is_running'] = True
            bot_status['is_paused'] = False
            bot_status['message'] = 'Bot starting...'
            bot_status['total'] = len(self.proxy_list)
            bot_status['completed'] = 0
            bot_status['found'] = 0
            bot_status['start_time'] = datetime.now().isoformat()
            
            socketio.emit('status_update', make_json_serializable(bot_status))
            
            logger.info(f"Starting SEO bot with {len(self.proxy_list)} proxies")
            logger.info(f"Searching for '{self.keyword}' on domain '{self.target_domain}'")
            logger.info(f"Using Google domain: {self.google_domain}")
            logger.info(f"Device profile: {self.device_profile.title()}")
            
            successful_runs = 0
            
            for i, proxy in enumerate(self.proxy_list, 1):
                if not bot_status['is_running']:  # Check if stopped
                    break
                
                # Wait while paused
                while bot_status['is_paused'] and bot_status['is_running']:
                    time.sleep(1)  # Check every second
                
                if not bot_status['is_running']:  # Check again after pause
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
            proxy_works, proxy_ip = self.check_proxy(proxy)
            if not proxy_works:
                logger.error(f"Proxy {proxy} is not working, skipping...")
                return result
            
            # Wait while paused before browser setup
            while bot_status['is_paused'] and bot_status['is_running']:
                time.sleep(1)
            
            if not bot_status['is_running']:
                return result
            
            # Setup browser
            if not self.setup_browser(proxy):
                logger.error("Failed to setup browser")
                return result
            
            # Wait while paused before proxy verification
            while bot_status['is_paused'] and bot_status['is_running']:
                time.sleep(1)
            
            if not bot_status['is_running']:
                self.close_browser()
                return result
            
            # Verify proxy is being used
            if not self.verify_proxy_ip():
                logger.error("Proxy verification failed - using real IP!")
                self.close_browser()
                return result
            
            # Wait while paused before Google search
            while bot_status['is_paused'] and bot_status['is_running']:
                time.sleep(1)
            
            if not bot_status['is_running']:
                self.close_browser()
                return result
            
            # Search Google with enhanced interactions
            if not self.search_google():
                logger.error("Google search failed")
                self.close_browser()
                return result
            
            # Wait while paused before target search
            while bot_status['is_paused'] and bot_status['is_running']:
                time.sleep(1)
            
            if not bot_status['is_running']:
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
        """Find target domain with page and position tracking and enhanced interactions"""
        try:
            logger.info(f"Looking for domain: {self.target_domain}")
            
            cumulative_position = 0  # Track total position across all pages
            page_results_count = []  # Track results count per page
            
            for page in range(1, self.max_pages + 1):
                # Wait while paused before processing each page
                while bot_status['is_paused'] and bot_status['is_running']:
                    time.sleep(1)
                
                if not bot_status['is_running']:
                    return False, page, None
                
                logger.info(f"🔍 Searching on page {page}")
                
                if page > 1:
                    # Navigate to next page
                    try:
                        next_button = self.driver.find_element(By.ID, "pnnext")
                        
                        # Scroll to next button and hover before clicking
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
                        time.sleep(1)
                        
                        # Hover over next button
                        actions = ActionChains(self.driver)
                        actions.move_to_element(next_button).pause(0.5).perform()
                        time.sleep(1)
                        
                        next_button.click()
                        
                        # Wait for page to load
                        time.sleep(3)
                        logger.info(f"✓ Navigated to page {page}")
                        
                        # Wait 15 seconds and perform interactions on each new page
                        logger.info(f"⏰ Waiting 15 seconds on page {page}...")
                        
                        # Sleep in small increments to allow pause/resume during wait
                        for _ in range(15):
                            if not bot_status['is_running']:
                                return False, page, None
                            # Wait while paused
                            while bot_status['is_paused'] and bot_status['is_running']:
                                time.sleep(0.5)
                            if bot_status['is_running']:
                                time.sleep(1)
                        
                        # Perform interactions on this page
                        logger.info(f"🎭 Performing interactions on page {page}...")
                        self.perform_google_page_interactions()
                        
                    except Exception as e:
                        logger.warning(f"Could not navigate to page {page}: {str(e)}")
                        break
                
                # Get search results on current page
                search_results = self.driver.find_elements(By.CSS_SELECTOR, "h3")
                current_page_results = len(search_results)
                page_results_count.append(current_page_results)
                
                logger.info(f"📊 Page {page} has {current_page_results} search results")
                
                for position, result in enumerate(search_results, 1):
                    try:
                        parent_link = result.find_element(By.XPATH, "..")
                        if parent_link.tag_name == 'a':
                            href = parent_link.get_attribute('href')
                            if href and self.target_domain in href:
                                # Calculate cumulative position across all pages
                                global_position = cumulative_position + position
                                
                                logger.info(f"🎯 Found target domain on page {page}, local position {position}, GLOBAL position {global_position}: {href}")
                                logger.info(f"📈 Position calculation: {' + '.join(map(str, page_results_count[:-1]))} + {position} = {global_position}")
                                
                                # ENHANCED INTERACTION: Hover over target before clicking
                                logger.info("🖱️ Hovering over target link...")
                                
                                # Scroll element into view
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", parent_link)
                                time.sleep(2)
                                
                                # Hover over the target link for a realistic duration
                                actions = ActionChains(self.driver)
                                actions.move_to_element(parent_link).perform()
                                time.sleep(random.uniform(2, 4))  # Hover for 2-4 seconds
                                
                                # Additional hover behavior - move slightly and hover again
                                actions.move_to_element_with_offset(parent_link, 5, 5).perform()
                                time.sleep(random.uniform(1, 2))
                                
                                logger.info("✨ Completed hovering over target link")
                                
                                # Now click the target
                                try:
                                    # Method 1: ActionChains click with pause
                                    actions.move_to_element(parent_link).pause(1).click().perform()
                                    
                                    logger.info("✓ Successfully clicked target link using ActionChains")
                                    time.sleep(3)
                                    
                                except Exception as e1:
                                    logger.warning(f"ActionChains click failed: {str(e1)}")
                                    try:
                                        # Method 2: JavaScript click
                                        self.driver.execute_script("arguments[0].click();", parent_link)
                                        logger.info("✓ Successfully clicked target link using JavaScript")
                                        time.sleep(3)
                                        
                                    except Exception as e2:
                                        logger.warning(f"JavaScript click failed: {str(e2)}")
                                        try:
                                            # Method 3: Direct navigation
                                            logger.info(f"Direct navigation to: {href}")
                                            self.driver.get(href)
                                            time.sleep(3)
                                            
                                        except Exception as e3:
                                            logger.error(f"All click methods failed: {str(e3)}")
                                            return True, page, global_position  # Return global position
                                
                                # Check if we successfully navigated to target domain
                                current_url = self.driver.current_url
                                if self.target_domain in current_url:
                                    logger.info(f"✓ Successfully navigated to target website: {current_url}")
                                    
                                    # Perform realistic interaction
                                    logger.info("🎭 Starting realistic website interaction (60 seconds)")
                                    self.realistic_website_interaction()
                                    
                                    logger.info("✅ Successfully visited and interacted with target website")
                                    return True, page, global_position  # Return global position
                                else:
                                    logger.warning(f"Navigation may have failed. Current URL: {current_url}")
                                    return True, page, global_position  # Return global position
                                
                    except Exception as e:
                        continue
                
                # Add current page results to cumulative count for next page calculation
                cumulative_position += current_page_results
                logger.info(f"📊 Cumulative results after page {page}: {cumulative_position}")
                logger.info(f"Domain not found on page {page}")
            
            return False, self.max_pages, None
            
        except Exception as e:
            logger.error(f"Error finding/visiting target: {str(e)}")
            return False, 1, None
    
    def realistic_website_interaction(self):
        """Perform realistic human-like interactions for 1 minute"""
        try:
            start_time = time.time()
            total_duration = 60  # 1 minute
            
            logger.info("🎭 Starting realistic website interaction (60 seconds)")
            
            # Wait for page to fully load with pause check
            for _ in range(3):
                if not bot_status['is_running']:
                    return
                while bot_status['is_paused'] and bot_status['is_running']:
                    time.sleep(0.5)
                if bot_status['is_running']:
                    time.sleep(1)
            
            # Check if we're actually on the target website
            current_url = self.driver.current_url
            if self.target_domain not in current_url:
                logger.warning(f"Not on target domain. Current URL: {current_url}")
                # Still perform some interaction for realism
                total_duration = 30  # Reduce time if not on target
            
            # Phase 1: Initial exploration (0-15 seconds)
            logger.info("Phase 1: Initial page exploration...")
            
            # Check pause before each action
            while bot_status['is_paused'] and bot_status['is_running']:
                time.sleep(0.5)
            if not bot_status['is_running']:
                return
                
            self.smooth_scroll_down(600)
            
            # Pause-aware sleep
            for _ in range(2):
                if not bot_status['is_running']:
                    return
                while bot_status['is_paused'] and bot_status['is_running']:
                    time.sleep(0.5)
                if bot_status['is_running']:
                    time.sleep(1)
            
            while bot_status['is_paused'] and bot_status['is_running']:
                time.sleep(0.5)
            if not bot_status['is_running']:
                return
                
            self.hover_random_elements(2)
            
            # Pause-aware sleep
            for _ in range(1):
                if not bot_status['is_running']:
                    return
                while bot_status['is_paused'] and bot_status['is_running']:
                    time.sleep(0.5)
                if bot_status['is_running']:
                    time.sleep(1)
            
            while bot_status['is_paused'] and bot_status['is_running']:
                time.sleep(0.5)
            if not bot_status['is_running']:
                return
                
            self.smooth_scroll_up(300)
            
            # Pause-aware sleep
            for _ in range(2):
                if not bot_status['is_running']:
                    return
                while bot_status['is_paused'] and bot_status['is_running']:
                    time.sleep(0.5)
                if bot_status['is_running']:
                    time.sleep(1)
            
            # Phase 2: Header navigation exploration (15-35 seconds)
            elapsed = time.time() - start_time
            if elapsed < 35:
                while bot_status['is_paused'] and bot_status['is_running']:
                    time.sleep(0.5)
                if not bot_status['is_running']:
                    return
                    
                logger.info("Phase 2: Exploring navigation...")
                self.click_header_navigation()
            
            # Phase 3: Content exploration (35-50 seconds)
            elapsed = time.time() - start_time
            if elapsed < 50:
                while bot_status['is_paused'] and bot_status['is_running']:
                    time.sleep(0.5)
                if not bot_status['is_running']:
                    return
                    
                logger.info("Phase 3: Content exploration...")
                
                # Scroll through content
                self.smooth_scroll_down(800)
                
                # Pause-aware sleep
                for _ in range(2):
                    if not bot_status['is_running']:
                        return
                    while bot_status['is_paused'] and bot_status['is_running']:
                        time.sleep(0.5)
                    if bot_status['is_running']:
                        time.sleep(1)
                
                while bot_status['is_paused'] and bot_status['is_running']:
                    time.sleep(0.5)
                if not bot_status['is_running']:
                    return
                    
                self.hover_random_elements(3)
                
                # Pause-aware sleep
                for _ in range(1):
                    if not bot_status['is_running']:
                        return
                    while bot_status['is_paused'] and bot_status['is_running']:
                        time.sleep(0.5)
                    if bot_status['is_running']:
                        time.sleep(1)
                
                # Read-like behavior (pause at different sections)
                for i in range(3):
                    while bot_status['is_paused'] and bot_status['is_running']:
                        time.sleep(0.5)
                    if not bot_status['is_running']:
                        return
                        
                    self.smooth_scroll_down(200)
                    
                    # Pause-aware reading pause
                    for _ in range(int(1.5)):
                        if not bot_status['is_running']:
                            return
                        while bot_status['is_paused'] and bot_status['is_running']:
                            time.sleep(0.5)
                        if bot_status['is_running']:
                            time.sleep(1)
                
                while bot_status['is_paused'] and bot_status['is_running']:
                    time.sleep(0.5)
                if not bot_status['is_running']:
                    return
                    
                self.smooth_scroll_up(400)
                
                # Pause-aware sleep
                for _ in range(1):
                    if not bot_status['is_running']:
                        return
                    while bot_status['is_paused'] and bot_status['is_running']:
                        time.sleep(0.5)
                    if bot_status['is_running']:
                        time.sleep(1)
            
            # Phase 4: Final exploration (50-60 seconds)
            elapsed = time.time() - start_time
            remaining_time = total_duration - elapsed
            
            if remaining_time > 5:
                while bot_status['is_paused'] and bot_status['is_running']:
                    time.sleep(0.5)
                if not bot_status['is_running']:
                    return
                    
                logger.info("Phase 4: Final exploration...")
                
                # Try to find and click another internal link
                try:
                    internal_links = self.driver.find_elements(By.CSS_SELECTOR, 'a')
                    valid_internal_links = []
                    
                    for link in internal_links[:15]:
                        try:
                            href = link.get_attribute('href')
                            if (href and link.is_displayed() and 
                                self.target_domain in href and
                                not any(ext in href.lower() for ext in ['mailto:', 'tel:', '#'])):
                                valid_internal_links.append(link)
                        except:
                            continue
                    
                    if valid_internal_links:
                        while bot_status['is_paused'] and bot_status['is_running']:
                            time.sleep(0.5)
                        if not bot_status['is_running']:
                            return
                            
                        link = random.choice(valid_internal_links)
                        link_text = link.text.strip()[:30] or "Internal Link"
                        
                        # Scroll to and click link
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", link)
                        
                        # Pause-aware sleep
                        for _ in range(1):
                            if not bot_status['is_running']:
                                return
                            while bot_status['is_paused'] and bot_status['is_running']:
                                time.sleep(0.5)
                            if bot_status['is_running']:
                                time.sleep(1)
                        
                        actions = ActionChains(self.driver)
                        actions.move_to_element(link).pause(0.5).click().perform()
                        
                        logger.info(f"Clicked internal link: {link_text}")
                        
                        # Brief exploration of new page with pause checks
                        for _ in range(2):
                            if not bot_status['is_running']:
                                return
                            while bot_status['is_paused'] and bot_status['is_running']:
                                time.sleep(0.5)
                            if bot_status['is_running']:
                                time.sleep(1)
                        
                        while bot_status['is_paused'] and bot_status['is_running']:
                            time.sleep(0.5)
                        if not bot_status['is_running']:
                            return
                            
                        self.smooth_scroll_down(400)
                        
                        # Pause-aware sleep
                        for _ in range(1):
                            if not bot_status['is_running']:
                                return
                            while bot_status['is_paused'] and bot_status['is_running']:
                                time.sleep(0.5)
                            if bot_status['is_running']:
                                time.sleep(1)
                        
                except Exception as e:
                    logger.warning(f"Could not explore internal links: {str(e)}")
            
            # Fill remaining time with gentle scrolling
            while time.time() - start_time < total_duration and bot_status['is_running']:
                # Check for pause before each action
                while bot_status['is_paused'] and bot_status['is_running']:
                    time.sleep(0.5)
                if not bot_status['is_running']:
                    break
                    
                remaining = total_duration - (time.time() - start_time)
                if remaining > 2:
                    if random.choice([True, False]):
                        self.smooth_scroll_down(random.randint(100, 300))
                    else:
                        self.smooth_scroll_up(random.randint(100, 200))
                    
                    # Pause-aware sleep
                    if not bot_status['is_running']:
                        break
                    while bot_status['is_paused'] and bot_status['is_running']:
                        time.sleep(0.5)
                    if bot_status['is_running']:
                        time.sleep(1)
                else:
                    # Final sleep with pause check
                    sleep_time = remaining
                    while sleep_time > 0 and bot_status['is_running']:
                        while bot_status['is_paused'] and bot_status['is_running']:
                            time.sleep(0.5)
                        if bot_status['is_running']:
                            sleep_chunk = min(0.5, sleep_time)
                            time.sleep(sleep_chunk)
                            sleep_time -= sleep_chunk
                        else:
                            break
                    break
            
            total_time = time.time() - start_time
            logger.info(f"✅ Completed realistic interaction session ({total_time:.1f} seconds)")
            
        except Exception as e:
            logger.error(f"Error during realistic website interaction: {str(e)}")
            # Fallback to simple behavior
            logger.info("Falling back to simple scrolling...")
            self.human_like_scroll()
            time.sleep(30)  # At least spend some time on the site
    
    def smooth_scroll_down(self, pixels=None):
        """Perform smooth scrolling down"""
        try:
            if pixels is None:
                pixels = random.randint(300, 800)
            
            # Smooth scroll in small increments
            scroll_steps = random.randint(8, 15)
            step_size = pixels // scroll_steps
            
            for i in range(scroll_steps):
                self.driver.execute_script(f"window.scrollBy(0, {step_size});")
                time.sleep(random.uniform(0.05, 0.15))
            
            logger.info(f"Smooth scrolled down {pixels} pixels")
            
        except Exception as e:
            logger.error(f"Error during smooth scroll down: {str(e)}")
    
    def smooth_scroll_up(self, pixels=None):
        """Perform smooth scrolling up"""
        try:
            if pixels is None:
                pixels = random.randint(200, 600)
            
            # Smooth scroll in small increments
            scroll_steps = random.randint(8, 15)
            step_size = pixels // scroll_steps
            
            for i in range(scroll_steps):
                self.driver.execute_script(f"window.scrollBy(0, -{step_size});")
                time.sleep(random.uniform(0.05, 0.15))
            
            logger.info(f"Smooth scrolled up {pixels} pixels")
            
        except Exception as e:
            logger.error(f"Error during smooth scroll up: {str(e)}")
    
    def hover_random_elements(self, duration=2):
        """Hover over random elements on the page"""
        try:
            # Common selectors for hoverable elements
            hover_selectors = [
                'a', 'button', 'h1', 'h2', 'h3', 'img', 
                '.menu', '.nav', '.header', '.link', 
                '[role="button"]', '[role="link"]'
            ]
            
            actions = ActionChains(self.driver)
            hovered_count = 0
            
            for selector in hover_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements and hovered_count < 3:  # Limit to 3 hovers
                        # Select a random visible element
                        visible_elements = [el for el in elements[:10] if el.is_displayed()]
                        if visible_elements:
                            element = random.choice(visible_elements)
                            
                            # Scroll element into view
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                            time.sleep(0.5)
                            
                            # Hover over element
                            actions.move_to_element(element).perform()
                            time.sleep(1)
                            hovered_count += 1
                            
                            logger.info(f"Hovered over {selector} element")
                            
                except Exception:
                    continue
            
            if hovered_count > 0:
                logger.info(f"Hovered over {hovered_count} elements")
            
        except Exception as e:
            logger.error(f"Error during hovering: {str(e)}")
    
    def click_header_navigation(self):
        """Click on header navigation elements and explore pages"""
        try:
            # Common selectors for header navigation
            nav_selectors = [
                'header a', 'nav a', '.header a', '.navigation a',
                '.menu a', '.navbar a', '.top-menu a', '.main-menu a',
                'ul.menu a', '.nav-item a', '.menu-item a'
            ]
            
            clicked_links = []
            original_url = self.driver.current_url
            
            for selector in nav_selectors:
                try:
                    nav_links = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if nav_links:
                        # Filter for visible links that aren't external
                        valid_links = []
                        for link in nav_links[:8]:  # Check first 8 links
                            try:
                                if (link.is_displayed() and 
                                    link.get_attribute('href') and
                                    not any(ext in link.get_attribute('href').lower() 
                                           for ext in ['mailto:', 'tel:', 'javascript:', '#']) and
                                    self.target_domain in link.get_attribute('href')):
                                    valid_links.append(link)
                            except:
                                continue
                        
                        if valid_links and len(clicked_links) < 2:  # Limit to 2 navigation clicks
                            link = random.choice(valid_links)
                            link_text = link.text.strip()[:30] or "Navigation Link"
                            
                            try:
                                # Scroll to link and click
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", link)
                                time.sleep(1)
                                
                                # Human-like click
                                actions = ActionChains(self.driver)
                                actions.move_to_element(link).pause(0.5).click().perform()
                                
                                logger.info(f"Clicked navigation link: {link_text}")
                                clicked_links.append(link_text)
                                
                                # Wait for page to load
                                time.sleep(3)
                                
                                # Check if we're on a new page
                                new_url = self.driver.current_url
                                if new_url != original_url:
                                    logger.info(f"Navigated to new page: {new_url}")
                                    
                                    # Explore the new page briefly
                                    self.explore_page_briefly()
                                    
                                    # Go back to original page
                                    self.driver.back()
                                    time.sleep(2)
                                    logger.info("Returned to previous page")
                                
                                break  # Exit selector loop after successful click
                                
                            except Exception as e:
                                logger.warning(f"Failed to click navigation link: {str(e)}")
                                continue
                        
                except Exception:
                    continue
            
            if clicked_links:
                logger.info(f"Successfully explored {len(clicked_links)} navigation pages")
            else:
                logger.info("No suitable navigation links found")
                
        except Exception as e:
            logger.error(f"Error during header navigation: {str(e)}")
    
    def explore_page_briefly(self):
        """Briefly explore a page with scrolling and hovering"""
        try:
            # Quick scroll down
            self.smooth_scroll_down(400)
            time.sleep(1)
            
            # Hover over an element
            self.hover_random_elements(1)
            
            # Quick scroll up
            self.smooth_scroll_up(200)
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Error during brief page exploration: {str(e)}")


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
    global bot_status
    
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
    global bot_status
    
    if not bot_status['is_running']:
        return jsonify({'error': 'Bot is not running'}), 400
    
    if not bot_status['is_paused']:
        return jsonify({'error': 'Bot is not paused'}), 400
    
    bot_status['is_paused'] = False
    bot_status['message'] = 'Bot resumed - Continuing automated operation'
    
    socketio.emit('status_update', make_json_serializable(bot_status))
    logger.info("Bot resumed by user - Continuing automated operation")
    
    return jsonify({'message': 'Bot resumed successfully'})

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