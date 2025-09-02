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
                                try:
                                    time.sleep(2)
                                    parent_link.click()
                                    time.sleep(3)
                                    
                                    # Perform realistic interaction
                                    logger.info("🎭 Starting realistic website interaction (60 seconds)")
                                    self.realistic_website_interaction()
                                    
                                    logger.info("✅ Successfully visited and interacted with target website")
                                    return True, page, position
                                except Exception as e:
                                    logger.error(f"Error clicking/visiting target: {str(e)}")
                                    return True, page, position  # Still count as found even if click failed
                                
                    except Exception as e:
                        continue
                
                logger.info(f"Domain not found on page {page}")
            
            return False, self.max_pages, None
            
        except Exception as e:
            logger.error(f"Error finding/visiting target: {str(e)}")
            return False, 1, None
    
    def search_google(self):
        """Search Google with the keyword - Enhanced version with better captcha handling"""
        try:
            logger.info("Opening Google.com...")
            self.driver.get('https://www.google.com')
            
            # Wait 5 seconds as requested
            logger.info("Waiting 5 seconds...")
            time.sleep(5)
            
            # Check for captcha or /sorry page
            if not self.handle_google_captcha():
                logger.error("Failed to handle Google captcha")
                return False
            
            # Find search box
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.common.keys import Keys
            
            search_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            
            logger.info(f"Typing keyword: {self.keyword}")
            self.human_like_typing(search_box, self.keyword)
            
            # Random delay before pressing enter
            time.sleep(random.uniform(1, 2))
            search_box.send_keys(Keys.RETURN)
            
            # Check for captcha after search submission
            if not self.handle_google_captcha():
                logger.error("Failed to handle captcha after search submission")
                return False
            
            # Wait for results to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "search"))
            )
            
            logger.info("Search results loaded")
            
            # Human-like scrolling on search results
            self.human_like_scroll()
            
            return True
            
        except Exception as e:
            logger.error(f"Error during Google search: {str(e)}")
            return False
    
    def realistic_website_interaction(self):
        """Perform realistic human-like interactions for 1 minute"""
        try:
            start_time = time.time()
            total_duration = 60  # 1 minute
            
            logger.info("🎭 Starting realistic website interaction (60 seconds)")
            
            # Phase 1: Initial exploration (0-15 seconds)
            logger.info("Phase 1: Initial page exploration...")
            self.smooth_scroll_down(600)
            time.sleep(2)
            
            self.hover_random_elements(2)
            time.sleep(1)
            
            self.smooth_scroll_up(300)
            time.sleep(2)
            
            # Phase 2: Header navigation exploration (15-35 seconds)
            elapsed = time.time() - start_time
            if elapsed < 35:
                logger.info("Phase 2: Exploring navigation...")
                self.click_header_navigation()
            
            # Phase 3: Content exploration (35-50 seconds)
            elapsed = time.time() - start_time
            if elapsed < 50:
                logger.info("Phase 3: Content exploration...")
                
                # Scroll through content
                self.smooth_scroll_down(800)
                time.sleep(2)
                
                self.hover_random_elements(3)
                time.sleep(1)
                
                # Read-like behavior (pause at different sections)
                for i in range(3):
                    self.smooth_scroll_down(200)
                    time.sleep(1.5)  # Reading pause
                
                self.smooth_scroll_up(400)
                time.sleep(1)
            
            # Phase 4: Final exploration (50-60 seconds)
            elapsed = time.time() - start_time
            remaining_time = total_duration - elapsed
            
            if remaining_time > 5:
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
                        link = random.choice(valid_internal_links)
                        link_text = link.text.strip()[:30] or "Internal Link"
                        
                        # Scroll to and click link
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", link)
                        time.sleep(1)
                        
                        from selenium.webdriver.common.action_chains import ActionChains
                        actions = ActionChains(self.driver)
                        actions.move_to_element(link).pause(0.5).click().perform()
                        
                        logger.info(f"Clicked internal link: {link_text}")
                        
                        # Brief exploration of new page
                        time.sleep(2)
                        self.smooth_scroll_down(400)
                        time.sleep(1)
                        
                except Exception as e:
                    logger.warning(f"Could not explore internal links: {str(e)}")
            
            # Fill remaining time with gentle scrolling
            while time.time() - start_time < total_duration:
                remaining = total_duration - (time.time() - start_time)
                if remaining > 2:
                    if random.choice([True, False]):
                        self.smooth_scroll_down(random.randint(100, 300))
                    else:
                        self.smooth_scroll_up(random.randint(100, 200))
                    time.sleep(1)
                else:
                    time.sleep(remaining)
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
            
            from selenium.webdriver.common.action_chains import ActionChains
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
                                from selenium.webdriver.common.action_chains import ActionChains
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
    
    def handle_google_captcha(self, max_attempts=3):
        """Handle Google captcha including /sorry pages"""
        try:
            current_url = self.driver.current_url
            
            # Check if we're on a captcha/sorry page
            if '/sorry' in current_url or 'captcha' in current_url.lower():
                logger.info(f"Detected Google captcha page: {current_url}")
                
                for attempt in range(max_attempts):
                    logger.info(f"Captcha solving attempt {attempt + 1}/{max_attempts}")
                    
                    # Wait a bit for page to fully load
                    time.sleep(3)
                    
                    # Check for reCAPTCHA elements
                    if self.solve_google_recaptcha():
                        logger.info("✓ Successfully solved Google captcha")
                        
                        # Wait for redirect or page change
                        time.sleep(5)
                        
                        # Check if we're still on captcha page
                        new_url = self.driver.current_url
                        if '/sorry' not in new_url and 'captcha' not in new_url.lower():
                            logger.info("✓ Successfully passed Google captcha verification")
                            return True
                        else:
                            logger.warning(f"Still on captcha page after solving (attempt {attempt + 1})")
                    else:
                        logger.warning(f"Failed to solve captcha (attempt {attempt + 1})")
                    
                    # Wait before retry
                    if attempt < max_attempts - 1:
                        time.sleep(10)
                
                logger.error("Failed to solve Google captcha after all attempts")
                return False
            
            # No captcha detected
            logger.info("No Google captcha detected")
            return True
            
        except Exception as e:
            logger.error(f"Error handling Google captcha: {str(e)}")
            return False
    
    def solve_google_recaptcha(self):
        """Solve Google reCAPTCHA using 2captcha service"""
        try:
            # Detect sitekey
            sitekey = self.detect_recaptcha_sitekey()
            if not sitekey:
                logger.error("Could not detect reCAPTCHA sitekey")
                return False
            
            current_url = self.driver.current_url
            logger.info(f"Solving reCAPTCHA with sitekey: {sitekey}")
            logger.info(f"URL: {current_url}")
            
            # Use 2captcha to solve
            try:
                result = self.captcha_solver.recaptcha(
                    sitekey=sitekey,
                    url=current_url,
                    timeout=120
                )
                
                if result and 'code' in result:
                    solution_token = result['code']
                    logger.info(f"✓ Received captcha solution: {solution_token[:50]}...")
                    
                    # Inject solution and submit
                    return self.inject_and_submit_captcha_solution(solution_token)
                else:
                    logger.error("No valid solution received from 2captcha")
                    return False
                    
            except Exception as e:
                logger.error(f"2captcha service error: {str(e)}")
                return False
                
        except Exception as e:
            logger.error(f"Error solving reCAPTCHA: {str(e)}")
            return False
    
    def detect_recaptcha_sitekey(self):
        """Detect reCAPTCHA sitekey from the page"""
        try:
            # Method 1: Look for data-sitekey attribute
            sitekey_selectors = [
                '[data-sitekey]',
                '.g-recaptcha[data-sitekey]',
                'div[data-sitekey]'
            ]
            
            for selector in sitekey_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        sitekey = element.get_attribute('data-sitekey')
                        if sitekey:
                            logger.info(f"Found sitekey via {selector}: {sitekey}")
                            return sitekey
                except:
                    continue
            
            # Method 2: Extract from iframe src
            try:
                iframes = self.driver.find_elements(By.CSS_SELECTOR, 'iframe[src*="recaptcha"]')
                for iframe in iframes:
                    src = iframe.get_attribute('src')
                    if 'sitekey=' in src:
                        sitekey = src.split('sitekey=')[1].split('&')[0]
                        logger.info(f"Found sitekey from iframe: {sitekey}")
                        return sitekey
            except:
                pass
            
            # Method 3: Search page source
            try:
                page_source = self.driver.page_source
                import re
                patterns = [
                    r'data-sitekey=["\']([^"\']+)["\']',
                    r'"sitekey":\s*["\']([^"\']+)["\']',
                    r'sitekey:\s*["\']([^"\']+)["\']'
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, page_source)
                    if matches:
                        sitekey = matches[0]
                        logger.info(f"Found sitekey from source: {sitekey}")
                        return sitekey
            except:
                pass
            
            logger.error("Could not detect reCAPTCHA sitekey")
            return None
            
        except Exception as e:
            logger.error(f"Error detecting sitekey: {str(e)}")
            return None
    
    def inject_and_submit_captcha_solution(self, solution_token):
        """Inject captcha solution and submit the form"""
        try:
            logger.info("Injecting captcha solution...")
            
            # Method 1: Fill g-recaptcha-response textarea
            script1 = f"""
                var textareas = document.querySelectorAll('textarea[name="g-recaptcha-response"]');
                for (var i = 0; i < textareas.length; i++) {{
                    textareas[i].value = '{solution_token}';
                    textareas[i].style.display = 'block';
                }}
                console.log('Filled ' + textareas.length + ' recaptcha response fields');
            """
            self.driver.execute_script(script1)
            
            # Method 2: Try to trigger callback
            script2 = f"""
                if (typeof grecaptcha !== 'undefined') {{
                    try {{
                        var callback = window.recaptchaCallback || window.onRecaptchaSuccess;
                        if (callback && typeof callback === 'function') {{
                            callback('{solution_token}');
                            console.log('Triggered recaptcha callback');
                        }}
                    }} catch(e) {{
                        console.log('Callback error:', e);
                    }}
                }}
            """
            self.driver.execute_script(script2)
            
            # Wait for solution to be processed
            time.sleep(2)
            
            # Try to find and click submit button
            submit_selectors = [
                'input[type="submit"]',
                'button[type="submit"]',
                '#submit',
                '.submit',
                'button:contains("Submit")',
                'input[value*="Submit"]'
            ]
            
            for selector in submit_selectors:
                try:
                    submit_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if submit_button.is_displayed() and submit_button.is_enabled():
                        logger.info(f"Clicking submit button: {selector}")
                        submit_button.click()
                        time.sleep(3)
                        return True
                except:
                    continue
            
            # If no submit button found, try pressing Enter on the form
            try:
                from selenium.webdriver.common.keys import Keys
                body = self.driver.find_element(By.TAG_NAME, 'body')
                body.send_keys(Keys.RETURN)
                logger.info("Pressed Enter to submit form")
                time.sleep(3)
                return True
            except:
                pass
            
            logger.warning("Could not find submit button, solution may still be valid")
            return True
            
        except Exception as e:
            logger.error(f"Error injecting captcha solution: {str(e)}")
            return False

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