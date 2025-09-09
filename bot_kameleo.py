import requests
import time
import random
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, WebDriverException
from kameleo.local_api_client import KameleoLocalApiClient
from kameleo.local_api_client.models import CreateProfileRequest, ProxyChoice, Server
from twocaptcha import TwoCaptcha
import os
from src.utils.cookie_manager import CookieManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot_activity.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GoogleSearchBot:
    def __init__(self, keyword, target_domain, proxy_list, device_profile="desktop", use_cookies=False):
        self.keyword = keyword
        self.target_domain = target_domain
        self.proxy_list = proxy_list
        self.device_profile = device_profile
        self.use_cookies = use_cookies
        self.current_proxy = None
        self.current_proxy_id = None
        self.driver = None
        self.kameleo_client = None
        self.current_profile = None
        self.kameleo_port = os.getenv('KAMELEO_PORT', '5050')
        self.available_fingerprints = []  # Cache fingerprints
        self.used_fingerprints = []  # Track used fingerprints
        
        # Initialize cookie manager
        self.cookie_manager = CookieManager()
        
        # Initialize 2captcha solver
        self.captcha_api_key = "56d4457439d8eb46c1831d271166f13b"
        self.captcha_solver = TwoCaptcha(self.captcha_api_key)
        logger.info(f"2captcha solver initialized with API key: {self.captcha_api_key[:10]}...")
        logger.info(f"Cookie management: {'Enabled' if use_cookies else 'Disabled'}")
        
    def init_kameleo_client(self):
        """Initialize Kameleo client and load fingerprints"""
        try:
            self.kameleo_client = KameleoLocalApiClient(
                endpoint=f'http://localhost:{self.kameleo_port}'
            )
            logger.info(f"Kameleo client initialized on port {self.kameleo_port}")
            
            # Load available fingerprints once
            self.load_fingerprints()
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Kameleo client: {str(e)}")
            logger.error("Make sure Kameleo.CLI is running on the specified port")
            return False
    
    def load_fingerprints(self):
        """Load and cache available fingerprints with variety"""
        try:
            if self.device_profile == "mobile":
                logger.info("Attempting to load Mobile Safari fingerprints...")
                
                # Try to load mobile fingerprints
                fingerprint_sets = []
                
                try:
                    # iOS Safari fingerprints
                    fp_mobile = self.kameleo_client.fingerprint.search_fingerprints(
                        device_type='mobile',
                        os_family='ios',
                        browser_product='safari'
                    )
                    fingerprint_sets.extend(fp_mobile)
                    
                    # Different iOS versions for variety
                    fp_ios_versions = self.kameleo_client.fingerprint.search_fingerprints(
                        device_type='mobile',
                        os_family='ios',
                        browser_product='safari'
                    )
                    fingerprint_sets.extend(fp_ios_versions[:10])  # Add first 10
                    
                    if not fingerprint_sets:
                        raise Exception("No mobile fingerprints available")
                        
                except Exception as e:
                    logger.warning(f"Mobile fingerprints not available: {str(e)}")
                    logger.info("Falling back to desktop fingerprints...")
                    self.device_profile = "desktop"  # Fallback to desktop
                
            else:
                logger.info("Loading available Desktop Chrome fingerprints...")
                
                # Load desktop fingerprints
                fingerprint_sets = []
                
                # Recent Chrome versions
                fp1 = self.kameleo_client.fingerprint.search_fingerprints(
                    device_type='desktop',
                    browser_product='chrome',
                    browser_version='>134'
                )
                fingerprint_sets.extend(fp1)
                
                # Different languages for variety
                languages = ['en-US', 'en-GB', 'de-DE', 'fr-FR', 'es-ES']
                for lang in languages[:2]:  # Use first 2 languages
                    try:
                        fp_lang = self.kameleo_client.fingerprint.search_fingerprints(
                            device_type='desktop',
                            browser_product='chrome',
                            browser_version='>134',
                            language=lang
                        )
                        fingerprint_sets.extend(fp_lang[:5])  # Add first 5 from each language
                    except:
                        continue
            
            # Remove duplicates by fingerprint ID
            seen_ids = set()
            self.available_fingerprints = []
            for fp in fingerprint_sets:
                if fp.id not in seen_ids:
                    self.available_fingerprints.append(fp)
                    seen_ids.add(fp.id)
            
            if not self.available_fingerprints:
                logger.error("No Chrome fingerprints found")
                return False
            
            # Shuffle fingerprints for better variety
            random.shuffle(self.available_fingerprints)
            logger.info(f"Loaded {len(self.available_fingerprints)} unique Chrome fingerprints")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load fingerprints: {str(e)}")
            return False
    
    def parse_proxy(self, proxy_string):
        """Parse proxy string to extract IP, port, username, password"""
        try:
            parts = proxy_string.split(':')
            if len(parts) == 4:
                # Format: ip:port:username:password
                ip, port, username, password = parts
                return ip, int(port), username, password
            elif len(parts) == 2:
                # Format: ip:port (no auth)
                ip, port = parts
                return ip, int(port), None, None
            else:
                raise ValueError(f"Invalid proxy format: {proxy_string}")
        except Exception as e:
            logger.error(f"Failed to parse proxy {proxy_string}: {str(e)}")
            return None, None, None, None
    
    def get_proxy_id(self, proxy_string):
        """Generate a unique ID for the proxy"""
        # Use the proxy string as ID (without password for security)
        parts = proxy_string.split(':')
        if len(parts) >= 2:
            return f"{parts[0]}:{parts[1]}"
        return proxy_string
    
    def save_profile_cookies(self):
        """Save cookies from current Kameleo profile"""
        if not self.use_cookies or not self.kameleo_client or not self.current_profile or not self.current_proxy_id:
            return False
        
        try:
            logger.info(f"💾 Saving cookies from current profile for proxy {self.current_proxy_id}...")
            
            # Get cookies from Kameleo profile
            cookie_list = self.kameleo_client.cookie.list_cookies(self.current_profile.id)
            
            if not cookie_list:
                logger.info("No cookies found in profile to save")
                return True
            
            # Convert Kameleo cookies to dictionary format
            cookies_dict = self.cookie_manager.convert_kameleo_cookies_to_dict(cookie_list)
            
            # Filter out empty or invalid cookies
            valid_cookies = []
            for cookie in cookies_dict:
                if cookie.get('name') and cookie.get('value') and cookie.get('domain'):
                    valid_cookies.append(cookie)
            
            if not valid_cookies:
                logger.info("No valid cookies to save")
                return True
            
            # Save cookies to database
            success = self.cookie_manager.save_cookies(self.current_proxy_id, valid_cookies)
            
            if success:
                logger.info(f"✅ Saved {len(valid_cookies)} cookies for proxy {self.current_proxy_id}")
                # Log some cookie details for debugging
                for cookie in valid_cookies[:3]:  # Show first 3 cookies
                    logger.info(f"   - {cookie['name']} ({cookie['domain']})")
                if len(valid_cookies) > 3:
                    logger.info(f"   ... and {len(valid_cookies) - 3} more cookies")
            else:
                logger.error(f"Failed to save cookies for proxy {self.current_proxy_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error saving profile cookies: {str(e)}")
            return False
    
    def save_cookies_if_enabled(self, context=""):
        """Helper method to save cookies with context logging"""
        if self.use_cookies:
            logger.info(f"💾 Saving cookies {context}...")
            return self.save_profile_cookies()
        return True
    
    def merge_cookies(self, existing_cookies, new_cookies):
        """Merge existing cookies with new ones, building realistic browsing history"""
        try:
            # Create a dictionary for fast lookup: (name, domain) -> cookie
            merged_dict = {}
            
            # Add existing cookies first
            for cookie in existing_cookies:
                key = (cookie.get('name'), cookie.get('domain'))
                merged_dict[key] = cookie
            
            # Add/update with new cookies (overwrites existing ones with same name+domain)
            new_count = 0
            updated_count = 0
            
            for cookie in new_cookies:
                key = (cookie.get('name'), cookie.get('domain'))
                if key in merged_dict:
                    # Update existing cookie
                    merged_dict[key] = cookie
                    updated_count += 1
                else:
                    # Add new cookie
                    merged_dict[key] = cookie
                    new_count += 1
            
            # Convert back to list
            merged_cookies = list(merged_dict.values())
            
            logger.info(f"🔄 Cookie merge details:")
            logger.info(f"   Kept existing: {len(existing_cookies) - updated_count}")
            logger.info(f"   Updated existing: {updated_count}")
            logger.info(f"   Added new: {new_count}")
            logger.info(f"   Total result: {len(merged_cookies)}")
            
            return merged_cookies
            
        except Exception as e:
            logger.error(f"Error merging cookies: {str(e)}")
            # Fallback: return new cookies only
            return new_cookies
    
    def debug_cookie_status(self):
        """Debug method to check current cookie status"""
        if not self.use_cookies:
            logger.info("🔍 Cookie management is DISABLED")
            return
        
        logger.info("🔍 Cookie Debug Status:")
        logger.info(f"   - Use cookies: {self.use_cookies}")
        logger.info(f"   - Current proxy ID: {self.current_proxy_id}")
        logger.info(f"   - Profile exists: {self.current_profile is not None}")
        logger.info(f"   - Kameleo client: {self.kameleo_client is not None}")
        
        if self.current_proxy_id:
            has_saved = self.cookie_manager.has_cookies(self.current_proxy_id)
            logger.info(f"   - Has saved cookies: {has_saved}")
            
            if has_saved:
                saved_cookies = self.cookie_manager.load_cookies(self.current_proxy_id)
                logger.info(f"   - Saved cookie count: {len(saved_cookies) if saved_cookies else 0}")
        
        if self.current_profile and self.kameleo_client:
            try:
                current_cookies = self.kameleo_client.cookie.list_cookies(self.current_profile.id)
                logger.info(f"   - Current profile cookies: {len(current_cookies) if current_cookies else 0}")
            except Exception as e:
                logger.info(f"   - Error getting current cookies: {str(e)}")
    
    def load_profile_cookies_properly(self):
        """Load saved cookies into Kameleo profile using proper sequence"""
        if not self.use_cookies or not self.kameleo_client or not self.current_profile or not self.current_proxy_id:
            return False
        
        try:
            # Check if cookies exist for this proxy
            if not self.cookie_manager.has_cookies(self.current_proxy_id):
                logger.info(f"ℹ️ No saved cookies for proxy {self.current_proxy_id} - keeping profile running")
                return True  # Not an error, just no cookies to load
            
            # Load cookies from database
            cookies_dict = self.cookie_manager.load_cookies(self.current_proxy_id)
            
            if not cookies_dict:
                logger.info("ℹ️ No cookies loaded from database - keeping profile running")
                return True
            
            # Convert dictionary cookies to Kameleo format
            kameleo_cookies = self.cookie_manager.convert_dict_to_kameleo_cookies(cookies_dict)
            
            if not kameleo_cookies:
                logger.warning("⚠️ Failed to convert cookies to Kameleo format - keeping profile running")
                return True  # Don't fail, just continue without cookies
            
            # PROPER SEQUENCE: Stop profile, add cookies (caller will restart)
            try:
                logger.info(f"📂 Stopping profile to add {len(kameleo_cookies)} cookies...")
                
                # Stop the profile (puts it in terminated state)
                self.kameleo_client.profile.stop_profile(self.current_profile.id)
                logger.info("✓ Profile stopped for cookie loading")
                
                # Add cookies to the stopped profile
                self.kameleo_client.cookie.add_cookies(self.current_profile.id, kameleo_cookies)
                logger.info(f"✅ Added {len(kameleo_cookies)} saved cookies to stopped profile")
                
                return True
                
            except Exception as e:
                logger.error(f"❌ Failed to add cookies to profile: {str(e)}")
                # Try to restart the profile if we stopped it
                try:
                    self.kameleo_client.profile.start_profile(self.current_profile.id)
                    logger.info("✓ Profile restarted after cookie loading error")
                except:
                    pass
                return False
            
        except Exception as e:
            logger.error(f"❌ Error loading profile cookies: {str(e)}")
            return False
    
    def load_profile_cookies(self):
        """Load saved cookies into current Kameleo profile (legacy method for compatibility)"""
        return self.load_profile_cookies_properly()
    
    def check_proxy(self, proxy):
        """Check if proxy is working and get IP address"""
        try:
            logger.info(f"Testing proxy: {proxy}")
            
            # Parse proxy
            ip, port, username, password = self.parse_proxy(proxy)
            if not ip or not port:
                return False, None
            
            # Build proxy URL
            if username and password:
                proxy_url = f'http://{username}:{password}@{ip}:{port}'
                proxy_display = f'{ip}:{port} (with auth)'
            else:
                proxy_url = f'http://{ip}:{port}'
                proxy_display = f'{ip}:{port}'
            
            proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            
            logger.info(f"Testing proxy: {proxy_display}")
            
            # Test proxy with a simple request
            response = requests.get('http://httpbin.org/ip', 
                                  proxies=proxies, 
                                  timeout=15)
            
            if response.status_code == 200:
                proxy_ip = response.json().get('origin')
                logger.info(f"✓ Proxy {proxy_display} is working. IP: {proxy_ip}")
                return True, proxy_ip
            else:
                logger.warning(f"Proxy {proxy_display} returned status code: {response.status_code}")
                return False, None
                
        except Exception as e:
            logger.error(f"Proxy {proxy} failed: {str(e)}")
            return False, None
    
    def get_unique_fingerprint(self):
        """Get a unique fingerprint that hasn't been used yet"""
        try:
            if not self.available_fingerprints:
                logger.error("No fingerprints available")
                return None
            
            # Find unused fingerprints
            unused_fingerprints = [fp for fp in self.available_fingerprints 
                                 if fp.id not in self.used_fingerprints]
            
            # If all fingerprints have been used, reset and start over
            if not unused_fingerprints:
                logger.info("All fingerprints used, resetting for variety")
                self.used_fingerprints = []
                unused_fingerprints = self.available_fingerprints
            
            # Select a random unused fingerprint
            selected_fingerprint = random.choice(unused_fingerprints)
            self.used_fingerprints.append(selected_fingerprint.id)
            
            logger.info(f"Selected unique fingerprint: {selected_fingerprint.id} "
                       f"({len(self.used_fingerprints)}/{len(self.available_fingerprints)} used)")
            
            return selected_fingerprint
            
        except Exception as e:
            logger.error(f"Failed to get unique fingerprint: {str(e)}")
            return None
    
    def create_kameleo_profile(self, proxy):
        """Create a Kameleo profile with proxy configuration and unique fingerprint"""
        try:
            logger.info(f"Creating Kameleo profile with proxy: {proxy}")
            
            # Parse proxy
            ip, port, username, password = self.parse_proxy(proxy)
            if not ip or not port:
                return None
            
            # Get a unique fingerprint for this profile
            selected_fingerprint = self.get_unique_fingerprint()
            if not selected_fingerprint:
                logger.error("Failed to get unique fingerprint")
                return None
            
            # Create profile request with proxy
            proxy_config = None
            if username and password:
                # Authenticated proxy
                proxy_config = ProxyChoice(
                    value='http',  # or 'socks5' depending on your proxy type
                    extra=Server(
                        host=ip,
                        port=port,
                        id=username,
                        secret=password
                    )
                )
                logger.info(f"Using authenticated proxy: {ip}:{port}")
            else:
                # Simple proxy without auth
                proxy_config = ProxyChoice(
                    value='http',
                    extra=Server(
                        host=ip,
                        port=port
                    )
                )
                logger.info(f"Using simple proxy: {ip}:{port}")
            
            create_profile_request = CreateProfileRequest(
                fingerprint_id=selected_fingerprint.id,
                name=f'SEO Bot Profile - {ip}:{port}',
                proxy=proxy_config
            )
            
            # Create the profile
            profile = self.kameleo_client.profile.create_profile(create_profile_request)
            logger.info(f"✓ Kameleo profile created: {profile.id} for proxy {ip}:{port}")
            
            return profile
            
        except Exception as e:
            logger.error(f"Failed to create Kameleo profile: {str(e)}")
            return None
    
    def get_my_ip(self):
        """Get current public IP address without proxy"""
        try:
            response = requests.get('http://httpbin.org/ip', timeout=10)
            return response.json().get('origin')
        except Exception as e:
            logger.error(f"Failed to get real IP: {str(e)}")
            return None
    
    def setup_browser(self, proxy):
        """Setup Chrome browser with Kameleo and proxy"""
        try:
            logger.info(f"Setting up Kameleo browser with proxy: {proxy}")
            
            # Store current proxy info
            self.current_proxy = proxy
            self.current_proxy_id = self.get_proxy_id(proxy)
            
            # STEP 1: Check for existing cookies BEFORE creating profile
            if self.use_cookies:
                logger.info(f"🔍 Checking for existing cookies for proxy: {self.current_proxy_id}")
                has_cookies = self.cookie_manager.has_cookies(self.current_proxy_id)
                if has_cookies:
                    saved_cookies = self.cookie_manager.load_cookies(self.current_proxy_id)
                    logger.info(f"✅ Found {len(saved_cookies) if saved_cookies else 0} saved cookies for this proxy")
                else:
                    logger.info(f"ℹ️ No saved cookies found for proxy: {self.current_proxy_id}")
            
            # Initialize Kameleo client if not done
            if not self.kameleo_client:
                if not self.init_kameleo_client():
                    return False
            
            # Create Kameleo profile with proxy
            self.current_profile = self.create_kameleo_profile(proxy)
            if not self.current_profile:
                return False
            
            # Start profile first (required for cookie operations)
            if self.device_profile == "mobile":
                # Start mobile profile with touch emulation disabled
                self.kameleo_client.profile.start_profile(self.current_profile.id, {
                    'additionalOptions': [
                        {
                            'key': 'disableTouchEmulation',
                            'value': True,
                        },
                    ],
                })
                logger.info("✓ Mobile profile started with touch emulation disabled")
            else:
                # Start desktop profile normally
                self.kameleo_client.profile.start_profile(self.current_profile.id)
                logger.info("✓ Desktop profile started")
            
            # STEP 2: Load saved cookies (profile must be started first, then stopped, then restarted)
            if self.use_cookies:
                logger.info("📂 Loading saved cookies into Kameleo profile...")
                try:
                    success = self.load_profile_cookies_properly()
                    logger.info(f"📂 Cookie loading result: {'✅ Success' if success else '❌ Failed'}")
                    
                    # Only restart if cookies were actually loaded
                    if success and self.cookie_manager.has_cookies(self.current_proxy_id):
                        logger.info("🔄 Restarting profile with loaded cookies...")
                        if self.device_profile == "mobile":
                            self.kameleo_client.profile.start_profile(self.current_profile.id, {
                                'additionalOptions': [
                                    {
                                        'key': 'disableTouchEmulation',
                                        'value': True,
                                    },
                                ],
                            })
                            logger.info("✓ Mobile profile restarted after loading cookies")
                        else:
                            self.kameleo_client.profile.start_profile(self.current_profile.id)
                            logger.info("✓ Desktop profile restarted after loading cookies")
                    else:
                        logger.info("ℹ️ No cookies to load, profile remains running")
                        
                except Exception as e:
                    logger.error(f"📂 Error loading cookies: {str(e)}")
                    logger.info("⚠️ Continuing with profile in current state")
            
            # Setup browser options for Kameleo
            if self.device_profile == "mobile":
                # Use Safari options for mobile
                from selenium.webdriver.safari.options import Options as SafariOptions
                options = SafariOptions()
            else:
                # Use Chrome options for desktop
                options = webdriver.ChromeOptions()
            
            options.add_experimental_option('kameleo:profileId', self.current_profile.id)
            
            # Connect to Kameleo WebDriver
            self.driver = webdriver.Remote(
                command_executor=f'http://localhost:{self.kameleo_port}/webdriver',
                options=options
            )
            
            # Set appropriate screen resolution
            if self.device_profile == "mobile":
                # Mobile resolutions (iPhone/iPad)
                mobile_resolutions = [(375, 667), (414, 896), (390, 844), (428, 926)]
                width, height = random.choice(mobile_resolutions)
            else:
                # Desktop resolutions
                resolutions = [(1920, 1080), (1366, 768), (1440, 900), (1536, 864)]
                width, height = random.choice(resolutions)
            
            self.driver.set_window_size(width, height)
            
            logger.info("Kameleo browser setup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup Kameleo browser: {str(e)}")
            return False
    
    def verify_proxy_ip(self):
        """Verify that the browser is using the proxy IP"""
        try:
            logger.info("Verifying proxy IP...")
            
            # Try multiple IP check services
            ip_services = [
                'http://httpbin.org/ip',
                'http://icanhazip.com/',
                'https://api.ipify.org?format=json'
            ]
            
            for service in ip_services:
                try:
                    self.driver.get(service)
                    time.sleep(3)
                    
                    page_source = self.driver.page_source
                    current_ip = None
                    
                    # Extract IP from different service formats
                    if 'httpbin.org' in service:
                        import re
                        ip_match = re.search(r'"origin":\s*"([^"]+)"', page_source)
                        if ip_match:
                            current_ip = ip_match.group(1).split(',')[0].strip()
                    elif 'icanhazip.com' in service:
                        # Extract IP from plain text response
                        import re
                        ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', page_source)
                        if ip_match:
                            current_ip = ip_match.group(1)
                    elif 'ipify.org' in service:
                        import re
                        ip_match = re.search(r'"ip":\s*"([^"]+)"', page_source)
                        if ip_match:
                            current_ip = ip_match.group(1)
                    
                    if current_ip:
                        logger.info(f"Browser IP (via {service}): {current_ip}")
                        
                        # Get real IP for comparison
                        my_real_ip = self.get_my_ip()
                        logger.info(f"Real IP: {my_real_ip}")
                        
                        if current_ip != my_real_ip and current_ip != "127.0.0.1":
                            logger.info("✓ Proxy is working correctly - IP is masked")
                            return True
                        else:
                            logger.error("✗ Proxy is not working - using real IP")
                            return False
                    
                except Exception as e:
                    logger.warning(f"Failed to check IP via {service}: {str(e)}")
                    continue
            
            logger.error("Could not verify proxy IP from any service")
            return False
                
        except Exception as e:
            logger.error(f"Failed to verify proxy IP: {str(e)}")
            return False
    
    def human_like_scroll(self):
        """Perform human-like scrolling"""
        try:
            # Random scroll patterns
            scroll_patterns = [
                # Scroll down slowly
                lambda: self.driver.execute_script("window.scrollBy(0, Math.random() * 300 + 200);"),
                # Scroll up
                lambda: self.driver.execute_script("window.scrollBy(0, -(Math.random() * 200 + 100));"),
                # Small scroll
                lambda: self.driver.execute_script("window.scrollBy(0, Math.random() * 100 + 50);")
            ]
            
            # Perform 3-5 random scrolls
            num_scrolls = random.randint(3, 5)
            for i in range(num_scrolls):
                scroll_action = random.choice(scroll_patterns)
                scroll_action()
                time.sleep(random.uniform(0.5, 1.5))
                
            logger.info(f"Performed {num_scrolls} human-like scroll actions")
            
        except Exception as e:
            logger.error(f"Error during scrolling: {str(e)}")
    
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
                            time.sleep(random.uniform(0.3, 0.7))
                            
                            # Hover over element
                            actions.move_to_element(element).perform()
                            time.sleep(random.uniform(0.5, 1.5))
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
                                time.sleep(random.uniform(0.5, 1.0))
                                
                                # Human-like click
                                actions = ActionChains(self.driver)
                                actions.move_to_element(link).pause(random.uniform(0.2, 0.5)).click().perform()
                                
                                logger.info(f"Clicked navigation link: {link_text}")
                                clicked_links.append(link_text)
                                
                                # Wait for page to load
                                time.sleep(random.uniform(2, 4))
                                
                                # Check if we're on a new page
                                new_url = self.driver.current_url
                                if new_url != original_url:
                                    logger.info(f"Navigated to new page: {new_url}")
                                    
                                    # Explore the new page briefly
                                    self.explore_page_briefly()
                                    
                                    # Go back to original page
                                    self.driver.back()
                                    time.sleep(random.uniform(1, 2))
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
            time.sleep(random.uniform(1, 2))
            
            # Hover over an element
            self.hover_random_elements(1)
            
            # Quick scroll up
            self.smooth_scroll_up(200)
            time.sleep(random.uniform(0.5, 1))
            
        except Exception as e:
            logger.error(f"Error during brief page exploration: {str(e)}")
    
    def realistic_website_interaction(self):
        """Perform realistic human-like interactions for 1 minute"""
        try:
            start_time = time.time()
            total_duration = 60  # 1 minute
            
            logger.info("🎭 Starting realistic website interaction (60 seconds)")
            
            # Phase 1: Initial exploration (0-15 seconds)
            logger.info("Phase 1: Initial page exploration...")
            self.smooth_scroll_down(600)
            time.sleep(random.uniform(2, 3))
            
            self.hover_random_elements(2)
            time.sleep(random.uniform(1, 2))
            
            self.smooth_scroll_up(300)
            time.sleep(random.uniform(1, 2))
            
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
                time.sleep(random.uniform(2, 3))
                
                self.hover_random_elements(3)
                time.sleep(random.uniform(1, 2))
                
                # Read-like behavior (pause at different sections)
                for i in range(3):
                    self.smooth_scroll_down(200)
                    time.sleep(random.uniform(1.5, 2.5))  # Reading pause
                
                self.smooth_scroll_up(400)
                time.sleep(random.uniform(1, 2))
            
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
                        time.sleep(random.uniform(0.5, 1))
                        
                        actions = ActionChains(self.driver)
                        actions.move_to_element(link).pause(random.uniform(0.3, 0.7)).click().perform()
                        
                        logger.info(f"Clicked internal link: {link_text}")
                        
                        # Brief exploration of new page
                        time.sleep(random.uniform(2, 3))
                        self.smooth_scroll_down(400)
                        time.sleep(random.uniform(1, 2))
                        
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
                    time.sleep(random.uniform(0.8, 1.5))
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
    
    def human_like_typing(self, element, text):
        """Type text in a human-like manner"""
        try:
            for char in text:
                element.send_keys(char)
                time.sleep(random.uniform(0.05, 0.2))  # Random delay between keystrokes
                
        except Exception as e:
            logger.error(f"Error during typing: {str(e)}")
    
    def detect_recaptcha_sitekey(self):
        """Detect reCAPTCHA sitekey from the page"""
        try:
            # Method 1: Look for data-sitekey in iframe or div
            sitekey_selectors = [
                '[data-sitekey]',
                'iframe[src*="recaptcha"][src*="sitekey"]',
                '.g-recaptcha[data-sitekey]'
            ]
            
            for selector in sitekey_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    sitekey = element.get_attribute('data-sitekey')
                    if sitekey:
                        logger.info(f"Found sitekey via {selector}: {sitekey}")
                        return sitekey
                except:
                    continue
            
            # Method 2: Extract from iframe src
            try:
                iframe = self.driver.find_element(By.CSS_SELECTOR, 'iframe[src*="recaptcha"]')
                src = iframe.get_attribute('src')
                if 'sitekey=' in src:
                    sitekey = src.split('sitekey=')[1].split('&')[0]
                    logger.info(f"Found sitekey from iframe src: {sitekey}")
                    return sitekey
            except:
                pass
            
            # Method 3: Check page source for common patterns
            page_source = self.driver.page_source
            import re
            sitekey_pattern = r'data-sitekey["\']?\s*=\s*["\']([^"\']+)["\']'
            match = re.search(sitekey_pattern, page_source)
            if match:
                sitekey = match.group(1)
                logger.info(f"Found sitekey from page source: {sitekey}")
                return sitekey
            
            logger.warning("Could not detect reCAPTCHA sitekey")
            return None
            
        except Exception as e:
            logger.error(f"Error detecting sitekey: {str(e)}")
            return None
    
    def inject_captcha_solution(self, solution_token):
        """Inject the captcha solution into the page"""
        try:
            logger.info("Injecting captcha solution into page...")
            
            # Method 1: Set g-recaptcha-response textarea
            script = f"""
                var textarea = document.getElementById('g-recaptcha-response');
                if (textarea) {{
                    textarea.value = '{solution_token}';
                    textarea.style.display = 'block';
                    console.log('Set g-recaptcha-response value');
                }}
            """
            self.driver.execute_script(script)
            
            # Method 2: Try to find and fill any hidden recaptcha response fields
            script2 = f"""
                var textareas = document.querySelectorAll('textarea[name="g-recaptcha-response"]');
                for (var i = 0; i < textareas.length; i++) {{
                    textareas[i].value = '{solution_token}';
                    textareas[i].style.display = 'block';
                }}
                console.log('Filled ' + textareas.length + ' recaptcha response textareas');
            """
            self.driver.execute_script(script2)
            
            # Method 3: Trigger callback if it exists
            script3 = f"""
                if (window.grecaptcha && window.grecaptcha.execute) {{
                    try {{
                        // Try to trigger callback
                        var callback = window.recaptchaCallback || window.onRecaptchaSuccess;
                        if (callback && typeof callback === 'function') {{
                            callback('{solution_token}');
                            console.log('Triggered recaptcha callback');
                        }}
                    }} catch(e) {{
                        console.log('Error triggering callback:', e);
                    }}
                }}
            """
            self.driver.execute_script(script3)
            
            # Wait a moment for the solution to be processed
            time.sleep(2)
            
            # Verify the solution was injected
            response_value = self.driver.execute_script(
                "return document.getElementById('g-recaptcha-response') ? document.getElementById('g-recaptcha-response').value : null;"
            )
            
            if response_value and len(response_value) > 100:
                logger.info("✓ Captcha solution successfully injected")
                return True
            else:
                logger.warning("⚠️  Solution injection may have failed")
                return False
                
        except Exception as e:
            logger.error(f"Error injecting captcha solution: {str(e)}")
            return False
    
    def wait_for_recaptcha_and_solve(self, timeout=180):
        """Wait for reCAPTCHA to appear and solve it automatically"""
        try:
            current_url = self.driver.current_url
            logger.info(f"Checking for reCAPTCHA on current page: {current_url}")
            
            # Check if we're on a Google /sorry page (captcha page)
            if '/sorry' in current_url or 'captcha' in current_url.lower():
                logger.info(f"✓ Detected Google captcha page: {current_url}")
                return self.solve_google_sorry_captcha()
            
            # Check if reCAPTCHA is present on regular pages
            recaptcha_present = False
            try:
                # Look for reCAPTCHA iframe
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'iframe[src*="recaptcha"]'))
                )
                recaptcha_present = True
                logger.info("✓ reCAPTCHA iframe detected")
            except TimeoutException:
                # Also check for other reCAPTCHA indicators
                if ('recaptcha' in self.driver.page_source.lower() or 
                    self.driver.find_elements(By.CSS_SELECTOR, '[data-sitekey]')):
                    recaptcha_present = True
                    logger.info("✓ reCAPTCHA elements detected")
                else:
                    logger.info("No reCAPTCHA detected on current page")
                    return True  # No captcha to solve
            
            if not recaptcha_present:
                return True
            
            # Solve regular reCAPTCHA
            return self.solve_regular_recaptcha()
                
        except Exception as e:
            logger.error(f"Error in captcha solving: {str(e)}")
            return False
    
    def solve_google_sorry_captcha(self):
        """Solve Google /sorry page captcha"""
        try:
            logger.info("Solving Google /sorry page captcha...")
            
            # Wait for reCAPTCHA iframe to be present
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'iframe[src*="recaptcha"]'))
            )
            logger.info("✓ reCAPTCHA iframe detected on /sorry page")
            
            # Detect sitekey
            sitekey = self.detect_recaptcha_sitekey()
            if not sitekey:
                logger.error("Cannot solve captcha without sitekey")
                return False
            
            current_url = self.driver.current_url
            logger.info(f"Solving reCAPTCHA for URL: {current_url}")
            logger.info(f"Using sitekey: {sitekey}")
            
            # Solve captcha using 2captcha
            logger.info("Submitting captcha to 2captcha service...")
            logger.info("This may take 30-120 seconds...")
            
            start_time = time.time()
            
            try:
                result = self.captcha_solver.recaptcha(
                    sitekey=sitekey,
                    url=current_url
                )
                
                solve_time = time.time() - start_time
                logger.info(f"✓ Captcha solved in {solve_time:.1f} seconds!")
                logger.info(f"Solution token: {result['code'][:50]}...")
                
                # Inject the solution and submit
                success = self.inject_captcha_solution(result['code'])
                
                if success:
                    # Wait for page to redirect after successful captcha
                    time.sleep(5)
                    
                    # Check if we're still on /sorry page
                    new_url = self.driver.current_url
                    if '/sorry' not in new_url and 'captcha' not in new_url.lower():
                        logger.info("✓ Successfully passed Google captcha verification")
                        return True
                    else:
                        logger.warning("Still on captcha page after solving")
                        return False
                else:
                    return False
                
            except Exception as e:
                solve_time = time.time() - start_time
                error_msg = str(e).lower()
                if 'cannot recognize' in error_msg or 'google-search-recaptcha' in error_msg:
                    logger.warning("Google search captcha not supported by 2captcha service")
                    logger.info("Trying alternative approach...")
                    # Try refreshing the page as fallback
                    self.driver.refresh()
                    time.sleep(5)
                    new_url = self.driver.current_url
                    if '/sorry' not in new_url:
                        logger.info("✓ Page refresh bypassed captcha")
                        return True
                    return False
                else:
                    logger.error(f"✗ Failed to solve captcha after {solve_time:.1f} seconds: {str(e)}")
                    return False
                
        except Exception as e:
            logger.error(f"Error solving Google /sorry captcha: {str(e)}")
            return False
    
    def solve_regular_recaptcha(self):
        """Solve regular reCAPTCHA (not Google /sorry page)"""
        try:
            # Detect sitekey
            sitekey = self.detect_recaptcha_sitekey()
            if not sitekey:
                logger.error("Cannot solve captcha without sitekey")
                return False
            
            # Get current page URL
            current_url = self.driver.current_url
            logger.info(f"Solving reCAPTCHA for URL: {current_url}")
            logger.info(f"Using sitekey: {sitekey}")
            
            # Solve captcha using 2captcha
            logger.info("Submitting captcha to 2captcha service...")
            logger.info("This may take 30-120 seconds...")
            
            start_time = time.time()
            
            try:
                result = self.captcha_solver.recaptcha(
                    sitekey=sitekey,
                    url=current_url
                )
                
                solve_time = time.time() - start_time
                logger.info(f"✓ Captcha solved in {solve_time:.1f} seconds!")
                logger.info(f"Solution token: {result['code'][:50]}...")
                
                # Inject the solution into the page
                return self.inject_captcha_solution(result['code'])
                
            except Exception as e:
                solve_time = time.time() - start_time
                logger.error(f"✗ Failed to solve captcha after {solve_time:.1f} seconds: {str(e)}")
                return False
                
        except Exception as e:
            logger.error(f"Error solving regular reCAPTCHA: {str(e)}")
            return False
    
    def search_google(self):
        """Search Google with the keyword"""
        try:
            logger.info("Opening Google.com...")
            self.driver.get('https://www.google.com')
            
            # Wait 5 seconds as requested
            logger.info("Waiting 5 seconds...")
            time.sleep(5)
            
            # Check for and solve any captcha that might appear
            if not self.wait_for_recaptcha_and_solve():
                logger.error("Failed to solve captcha on Google homepage")
                return False
            
            # Find search box
            search_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            
            logger.info(f"Typing keyword: {self.keyword}")
            self.human_like_typing(search_box, self.keyword)
            
            # Random delay before pressing enter
            time.sleep(random.uniform(1, 2))
            search_box.send_keys(Keys.RETURN)
            
            # Check for captcha after search submission
            if not self.wait_for_recaptcha_and_solve():
                logger.error("Failed to solve captcha after search submission")
                return False
            
            # Wait for results to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "search"))
            )
            
            logger.info("Search results loaded")
            
            # Human-like scrolling on search results
            self.human_like_scroll()
            
            # Note: Cookies will be saved at the end of the session
            
            return True
            
        except Exception as e:
            logger.error(f"Error during Google search: {str(e)}")
            return False
    
    def find_and_visit_target(self):
        """Find target domain in search results and visit it - searches up to 20 pages"""
        try:
            logger.info(f"Looking for domain: {self.target_domain}")
            
            max_pages = 20
            current_page = 1
            
            while current_page <= max_pages:
                logger.info(f"Searching page {current_page} of {max_pages} for target domain...")
                
                # Wait for search results to load
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.ID, "search"))
                    )
                except:
                    logger.error(f"Search results not loaded on page {current_page}")
                    break
                
                # Get all search result links on current page
                search_results = self.driver.find_elements(By.CSS_SELECTOR, "h3")
                
                target_found = False
                for result in search_results:
                    try:
                        parent_link = result.find_element(By.XPATH, "..")
                        if parent_link.tag_name == 'a':
                            href = parent_link.get_attribute('href')
                            if href and self.target_domain in href:
                                logger.info(f"✓ Found target domain on page {current_page}: {href}")
                                
                                # Random delay before clicking
                                time.sleep(random.uniform(1, 3))
                                
                                # Human-like click
                                actions = ActionChains(self.driver)
                                actions.move_to_element(parent_link).click().perform()
                                
                                target_found = True
                                break
                                
                    except Exception as e:
                        continue
                
                if target_found:
                    logger.info("Successfully clicked on target website")
                    
                    # Wait for page to load
                    time.sleep(3)
                    
                    # Check for and solve any captcha on target website
                    if not self.wait_for_recaptcha_and_solve():
                        logger.warning("Failed to solve captcha on target website, continuing anyway...")
                    
                    # Perform realistic human-like interactions for 1 minute
                    logger.info("Starting 1-minute realistic interaction session on target website...")
                    self.realistic_website_interaction()
                    
                    # Note: Cookies will be saved when profile closes
                    
                    return True
                
                # Target not found on current page, try to go to next page
                if current_page < max_pages:
                    logger.info(f"Target not found on page {current_page}, trying next page...")
                    
                    # Method 1: Try to construct the next page URL manually to maintain search query
                    try:
                        current_url = self.driver.current_url
                        logger.info(f"Current URL: {current_url}")
                        
                        # Check if current URL contains our keyword
                        if self.keyword.replace(' ', '+') not in current_url and self.keyword.replace(' ', '%20') not in current_url:
                            logger.warning("Current URL doesn't contain our keyword, reconstructing search...")
                            # Reconstruct the search URL with our keyword
                            import urllib.parse
                            encoded_keyword = urllib.parse.quote_plus(self.keyword)
                            start_param = current_page * 10  # Google shows 10 results per page
                            next_url = f"https://www.google.com/search?q={encoded_keyword}&start={start_param}"
                            logger.info(f"Navigating to: {next_url}")
                            self.driver.get(next_url)
                            next_clicked = True
                        else:
                            # Try clicking next button first
                            next_clicked = False
                            
                            # Try different selectors for next page button
                            next_selectors = [
                                'a[aria-label="Next page"]',
                                'a#pnnext',
                                'a[id="pnnext"]',
                                'td.b a[href*="start="]',
                                'a[href*="start="]'
                            ]
                            
                            for selector in next_selectors:
                                try:
                                    next_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                                    if next_button and next_button.is_enabled():
                                        next_url = next_button.get_attribute('href')
                                        # Verify the next URL contains our keyword
                                        if (self.keyword.replace(' ', '+') in next_url or 
                                            self.keyword.replace(' ', '%20') in next_url or
                                            'q=' in next_url):
                                            
                                            # Scroll to next button
                                            self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                                            time.sleep(1)
                                            
                                            # Human-like click on next button
                                            actions = ActionChains(self.driver)
                                            actions.move_to_element(next_button).click().perform()
                                            
                                            logger.info(f"Clicked next page button, moving to page {current_page + 1}")
                                            next_clicked = True
                                            break
                                        else:
                                            logger.warning(f"Next button URL doesn't contain our keyword: {next_url}")
                                except:
                                    continue
                            
                            if not next_clicked:
                                # Try alternative method - look for page numbers
                                try:
                                    page_links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="start="]')
                                    for link in page_links:
                                        link_text = link.text.strip()
                                        if link_text.isdigit() and int(link_text) == current_page + 1:
                                            link_url = link.get_attribute('href')
                                            # Verify the link contains our keyword
                                            if (self.keyword.replace(' ', '+') in link_url or 
                                                self.keyword.replace(' ', '%20') in link_url):
                                                
                                                # Scroll to page link
                                                self.driver.execute_script("arguments[0].scrollIntoView(true);", link)
                                                time.sleep(1)
                                                
                                                # Click page number
                                                actions = ActionChains(self.driver)
                                                actions.move_to_element(link).click().perform()
                                                
                                                logger.info(f"Clicked page {current_page + 1} link")
                                                next_clicked = True
                                                break
                                except:
                                    pass
                            
                            # If still no success, construct URL manually
                            if not next_clicked:
                                logger.info("Manual navigation: constructing next page URL...")
                                import urllib.parse
                                encoded_keyword = urllib.parse.quote_plus(self.keyword)
                                start_param = current_page * 10
                                next_url = f"https://www.google.com/search?q={encoded_keyword}&start={start_param}"
                                logger.info(f"Navigating to: {next_url}")
                                self.driver.get(next_url)
                                next_clicked = True
                        
                    except Exception as e:
                        logger.error(f"Error navigating to next page: {str(e)}")
                        next_clicked = False
                    
                    if not next_clicked:
                        logger.warning(f"Could not navigate to next page from page {current_page}")
                        break
                    
                    # Wait for next page to load
                    time.sleep(random.uniform(3, 5))
                    
                    # Verify we're still searching for the right keyword
                    try:
                        current_url = self.driver.current_url
                        if (self.keyword.replace(' ', '+') not in current_url and 
                            self.keyword.replace(' ', '%20') not in current_url):
                            logger.warning(f"Page {current_page + 1} URL doesn't contain our keyword!")
                            logger.warning(f"Expected keyword: {self.keyword}")
                            logger.warning(f"Current URL: {current_url}")
                    except:
                        pass
                    
                    # Check for captcha on new page
                    if not self.wait_for_recaptcha_and_solve():
                        logger.warning("Failed to solve captcha on search results page, continuing anyway...")
                    
                    # Human-like scrolling on new page
                    self.human_like_scroll()
                    
                    current_page += 1
                else:
                    break
            
            logger.warning(f"Target domain '{self.target_domain}' not found in {max_pages} pages of search results")
            return False
                
        except Exception as e:
            logger.error(f"Error finding/visiting target: {str(e)}")
            return False
    
    def close_browser(self):
        """Close the browser and clean up Kameleo profile"""
        try:
            # Close browser first
            if self.driver:
                self.driver.quit()
                logger.info("Browser closed")
            
            # CRITICAL: Save cookies BEFORE deleting profile
            if self.use_cookies and self.kameleo_client and self.current_profile and self.current_proxy_id:
                logger.info(f"💾 FINAL COOKIE SAVE before closing profile for proxy: {self.current_proxy_id}")
                try:
                    # Stop the profile first (required to access cookies)
                    self.kameleo_client.profile.stop_profile(self.current_profile.id)
                    logger.info(f"Kameleo profile {self.current_profile.id} stopped")
                    
                    # Now get all cookies from the stopped profile
                    cookie_list = self.kameleo_client.cookie.list_cookies(self.current_profile.id)
                    logger.info(f"📊 Found {len(cookie_list) if cookie_list else 0} cookies in profile to save")
                    
                    if cookie_list and len(cookie_list) > 0:
                        logger.info(f"🍪 PRINTING ALL COOKIES FOUND BEFORE SAVING:")
                        logger.info("=" * 60)
                        
                        # Convert and print all cookies
                        cookies_dict = self.cookie_manager.convert_kameleo_cookies_to_dict(cookie_list)
                        
                        # for i, cookie in enumerate(cookies_dict, 1):
                        #     logger.info(f"Cookie #{i}:")
                        #     logger.info(f"  Name: {cookie.get('name', 'N/A')}")
                        #     logger.info(f"  Domain: {cookie.get('domain', 'N/A')}")
                        #     logger.info(f"  Path: {cookie.get('path', 'N/A')}")
                        #     logger.info(f"  Value: {cookie.get('value', 'N/A')[:50]}{'...' if len(str(cookie.get('value', ''))) > 50 else ''}")
                        #     logger.info(f"  Secure: {cookie.get('secure', 'N/A')}")
                        #     logger.info(f"  HttpOnly: {cookie.get('http_only', 'N/A')}")
                        #     logger.info(f"  SameSite: {cookie.get('same_site', 'N/A')}")
                        #     logger.info(f"  Expires: {cookie.get('expiration_date', 'Session')}")
                        #     logger.info("-" * 40)
                        
                        # logger.info("=" * 60)
                        
                        # Filter valid cookies
                        valid_cookies = []
                        invalid_cookies = []
                        
                        for cookie in cookies_dict:
                            if cookie.get('name') and cookie.get('value') and cookie.get('domain'):
                                valid_cookies.append(cookie)
                            else:
                                invalid_cookies.append(cookie)
                                logger.warning(f"⚠️ Invalid cookie: {cookie.get('name', 'NO_NAME')} - missing required fields")
                        
                        logger.info(f"📊 Cookie Summary:")
                        logger.info(f"   Total found: {len(cookies_dict)}")
                        logger.info(f"   Valid: {len(valid_cookies)}")
                        logger.info(f"   Invalid: {len(invalid_cookies)}")
                        
                        if valid_cookies:
                            # MERGE COOKIES: Load existing + add new ones for realistic browsing history
                            logger.info(f"🔄 Merging {len(valid_cookies)} new cookies with existing ones...")
                            
                            # Load existing cookies from database
                            existing_cookies = self.cookie_manager.load_cookies(self.current_proxy_id) or []
                            logger.info(f"📂 Found {len(existing_cookies)} existing cookies in database")
                            
                            # Merge cookies: new cookies override existing ones with same name+domain
                            merged_cookies = self.merge_cookies(existing_cookies, valid_cookies)
                            
                            logger.info(f"🔄 Cookie merge result:")
                            logger.info(f"   Existing: {len(existing_cookies)}")
                            logger.info(f"   New: {len(valid_cookies)}")
                            logger.info(f"   Merged total: {len(merged_cookies)}")
                            
                            # Save merged cookies
                            success = self.cookie_manager.save_cookies(self.current_proxy_id, merged_cookies)
                            if success:
                                logger.info(f"✅ SUCCESSFULLY SAVED {len(merged_cookies)} merged cookies for proxy {self.current_proxy_id}")
                                
                                # Show cookie breakdown by domain
                                domain_counts = {}
                                for cookie in merged_cookies:
                                    domain = cookie.get('domain', 'unknown')
                                    domain_counts[domain] = domain_counts.get(domain, 0) + 1
                                
                                logger.info("📋 Cookies by domain:")
                                for domain, count in sorted(domain_counts.items()):
                                    logger.info(f"   ✓ {domain}: {count} cookies")
                            else:
                                logger.error(f"❌ FAILED to save merged cookies for proxy {self.current_proxy_id}")
                        else:
                            logger.info("ℹ️ No valid cookies to save")
                    else:
                        logger.info("ℹ️ No cookies found in profile to save")
                        
                    # Delete the profile after saving cookies
                    self.kameleo_client.profile.delete_profile(self.current_profile.id)
                    logger.info(f"Kameleo profile {self.current_profile.id} deleted")
                        
                except Exception as e:
                    logger.error(f"❌ CRITICAL ERROR saving cookies: {str(e)}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    
                    # Still try to delete the profile even if cookie saving failed
                    try:
                        if self.current_profile:
                            self.kameleo_client.profile.delete_profile(self.current_profile.id)
                            logger.info(f"Kameleo profile {self.current_profile.id} deleted (after error)")
                    except Exception as delete_error:
                        logger.warning(f"Failed to delete profile after cookie error: {str(delete_error)}")
                
                self.current_profile = None
                self.current_proxy = None
                self.current_proxy_id = None
            
            # Handle case where cookies are disabled but we still need to clean up profile
            elif self.kameleo_client and self.current_profile:
                try:
                    # Stop and delete profile
                    self.kameleo_client.profile.stop_profile(self.current_profile.id)
                    logger.info(f"Kameleo profile {self.current_profile.id} stopped")
                    
                    self.kameleo_client.profile.delete_profile(self.current_profile.id)
                    logger.info(f"Kameleo profile {self.current_profile.id} deleted")
                    
                except Exception as e:
                    logger.warning(f"Failed to stop/delete Kameleo profile: {str(e)}")
                
                self.current_profile = None
                self.current_proxy = None
                self.current_proxy_id = None
                    
        except Exception as e:
            logger.error(f"Error closing browser: {str(e)}")
    
    def run_single_proxy(self, proxy):
        """Run the complete process with a single proxy"""
        try:
            logger.info(f"\n{'='*50}")
            logger.info(f"Starting process with proxy: {proxy}")
            logger.info(f"{'='*50}")
            
            # Check proxy
            proxy_works, proxy_ip = self.check_proxy(proxy)
            if not proxy_works:
                logger.error(f"Proxy {proxy} is not working, skipping...")
                return False
            
            # Setup browser (creates profile)
            if not self.setup_browser(proxy):
                logger.error("Failed to setup browser")
                # Clean up profile if it was created but browser setup failed
                self.close_browser()
                return False
            
            # Verify proxy is being used
            if not self.verify_proxy_ip():
                logger.error("Proxy verification failed - using real IP!")
                self.close_browser()
                return False
            
            # Search Google
            if not self.search_google():
                logger.error("Google search failed")
                self.close_browser()
                return False
            
            # Find and visit target
            if not self.find_and_visit_target():
                logger.error("Failed to find/visit target domain")
                # Cookies will be saved in close_browser() method
                self.close_browser()
                return False
            
            # Cookies will be saved in close_browser() method
            
            logger.info("✓ Process completed successfully!")
            self.close_browser()
            return True
            
        except Exception as e:
            logger.error(f"Error in single proxy run: {str(e)}")
            # Cookies will be saved in close_browser() method
            self.close_browser()
            return False
    
    def run(self):
        """Run the bot with all proxies"""
        logger.info(f"Starting Google Search Bot")
        logger.info(f"Keyword: {self.keyword}")
        logger.info(f"Target Domain: {self.target_domain}")
        logger.info(f"Total Proxies: {len(self.proxy_list)}")
        
        successful_runs = 0
        
        for i, proxy in enumerate(self.proxy_list, 1):
            logger.info(f"\n--- Processing proxy {i}/{len(self.proxy_list)} ---")
            
            if self.run_single_proxy(proxy):
                successful_runs += 1
                logger.info(f"✓ Proxy {proxy} completed successfully")
            else:
                logger.error(f"✗ Proxy {proxy} failed")
            
            # Random delay between proxy switches
            if i < len(self.proxy_list):
                delay = random.uniform(5, 15)
                logger.info(f"Waiting {delay:.1f} seconds before next proxy...")
                time.sleep(delay)
        
        logger.info(f"\n{'='*50}")
        logger.info(f"FINAL RESULTS:")
        logger.info(f"Total proxies tested: {len(self.proxy_list)}")
        logger.info(f"Successful runs: {successful_runs}")
        logger.info(f"Failed runs: {len(self.proxy_list) - successful_runs}")
        logger.info(f"{'='*50}")

def main():
    """Main function to run the bot"""
    print("Google Search Bot with Proxy Rotation")
    print("=" * 40)
    
    # Get user input
    keyword = input("Enter search keyword: ").strip()
    target_domain = input("Enter target domain (e.g., example.com): ").strip()
    
    print("\nEnter proxy list (format: ip:port, one per line, press Enter twice when done):")
    proxy_list = []
    while True:
        proxy = input().strip()
        if not proxy:
            break
        proxy_list.append(proxy)
    
    if not keyword or not target_domain or not proxy_list:
        print("Error: Please provide keyword, domain, and at least one proxy")
        return
    
    print(f"\nConfiguration:")
    print(f"Keyword: {keyword}")
    print(f"Target Domain: {target_domain}")
    print(f"Proxies: {len(proxy_list)}")
    
    confirm = input("\nStart the bot? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Bot cancelled")
        return
    
    # Create and run bot
    bot = GoogleSearchBot(keyword, target_domain, proxy_list)
    bot.run()

if __name__ == "__main__":
    main()

# Example usage:
"""
Required packages (install with pip):
pip install selenium kameleo.local-api-client requests

Prerequisites:
1. Install Kameleo.CLI and make sure it's running on port 5050 (default)
2. Set KAMELEO_PORT environment variable if using different port

Example proxy list format:
123.456.789.10:8080
98.765.432.10:3128:username:password
111.222.333.44:8080

Example run:
keyword: "python tutorials"
domain: "realpython.com"
proxy list: 
123.456.789.10:8080
98.765.432.10:3128:myuser:mypass

The bot will:
1. Test each proxy
2. Create Kameleo profile with proxy
3. Verify IP masking with real browser fingerprinting protection
4. Search Google with human-like behavior
5. Find and click target domain
6. Stay on target site for 20 seconds
7. Clean up Kameleo profile and move to next proxy

Kameleo provides superior anti-detection compared to undetected-chromedriver:
- Real browser fingerprints
- Canvas fingerprint protection
- WebGL fingerprint protection
- Audio fingerprint protection
- Font fingerprint protection
- And much more...
"""