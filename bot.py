import requests
import time
import random
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, WebDriverException
from fake_useragent import UserAgent
import undetected_chromedriver as uc
import zipfile
import os
import tempfile
import shutil

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
    def __init__(self, keyword, target_domain, proxy_list):
        self.keyword = keyword
        self.target_domain = target_domain
        self.proxy_list = proxy_list
        self.current_proxy = None
        self.driver = None
        self.ua = UserAgent()
        
    def parse_proxy(self, proxy_string):
        """Parse proxy string to extract IP, port, username, password"""
        try:
            parts = proxy_string.split(':')
            if len(parts) == 4:
                # Format: ip:port:username:password
                ip, port, username, password = parts
                return ip, port, username, password
            elif len(parts) == 2:
                # Format: ip:port (no auth)
                ip, port = parts
                return ip, port, None, None
            else:
                raise ValueError(f"Invalid proxy format: {proxy_string}")
        except Exception as e:
            logger.error(f"Failed to parse proxy {proxy_string}: {str(e)}")
            return None, None, None, None
    
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
    
    def create_proxy_auth_extension(self, proxy_host, proxy_port, proxy_user, proxy_pass):
        """Create Chrome extension for proxy authentication"""
        try:
            logger.info(f"Creating proxy auth extension for {proxy_host}:{proxy_port}")
            
            # Create extension manifest
            manifest_json = """{
    "version": "1.0.0",
    "manifest_version": 2,
    "name": "Proxy Auth",
    "permissions": [
        "proxy",
        "tabs",
        "unlimitedStorage",
        "storage",
        "<all_urls>",
        "webRequest",
        "webRequestBlocking"
    ],
    "background": {
        "scripts": ["background.js"]
    },
    "minimum_chrome_version": "22.0.0"
}"""
            
            background_js = f"""
var config = {{
    mode: "fixed_servers",
    rules: {{
        singleProxy: {{
            scheme: "http",
            host: "{proxy_host}",
            port: parseInt({proxy_port})
        }},
        bypassList: ["localhost"]
    }}
}};

chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{
    console.log("Proxy configured");
}});

function callbackFn(details) {{
    return {{
        authCredentials: {{
            username: "{proxy_user}",
            password: "{proxy_pass}"
        }}
    }};
}}

chrome.webRequest.onAuthRequired.addListener(
    callbackFn,
    {{urls: ["<all_urls>"]}},
    ['blocking']
);

console.log("Proxy authentication extension loaded");
"""
            
            # Create temporary directory for extension
            temp_dir = tempfile.mkdtemp()
            extension_dir = os.path.join(temp_dir, 'proxy_auth')
            os.makedirs(extension_dir, exist_ok=True)
            
            # Write files
            with open(os.path.join(extension_dir, 'manifest.json'), 'w') as f:
                f.write(manifest_json)
            
            with open(os.path.join(extension_dir, 'background.js'), 'w') as f:
                f.write(background_js)
            
            logger.info(f"Proxy auth extension created at: {extension_dir}")
            return extension_dir
            
        except Exception as e:
            logger.error(f"Failed to create proxy auth extension: {str(e)}")
            return None
        """Get current public IP address without proxy"""
        try:
            response = requests.get('http://httpbin.org/ip', timeout=10)
            return response.json().get('origin')
        except Exception as e:
            logger.error(f"Failed to get real IP: {str(e)}")
            return None
    
    def setup_browser(self, proxy):
        """Setup Chrome browser with proxy and anti-detection measures"""
        try:
            logger.info(f"Setting up browser with proxy: {proxy}")
            
            # Parse proxy
            ip, port, username, password = self.parse_proxy(proxy)
            if not ip or not port:
                return False
            
            # Create proxy auth extension if needed
            extension_dir = None
            if username and password:
                extension_dir = self.create_proxy_auth_extension(ip, port, username, password)
                if not extension_dir:
                    logger.error("Failed to create proxy auth extension")
                    return False
            
            # Chrome options - minimal for compatibility
            chrome_options = uc.ChromeOptions()
            
            # Add proxy auth extension
            if extension_dir:
                chrome_options.add_argument(f'--load-extension={extension_dir}')
                logger.info(f"Added proxy auth extension: {extension_dir}")
            else:
                # Simple proxy without auth
                chrome_options.add_argument(f'--proxy-server=http://{ip}:{port}')
            
            # Essential arguments only
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            
            # Random user agent
            user_agent = self.ua.random
            chrome_options.add_argument(f'--user-agent={user_agent}')
            logger.info(f"Using User-Agent: {user_agent}")
            
            # Initialize undetected chromedriver
            self.driver = uc.Chrome(options=chrome_options, version_main=None)
            
            # Store extension dir for cleanup
            self.extension_dir = extension_dir
            
            # Execute script to remove webdriver property
            try:
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            except:
                pass
            
            # Set random screen resolution
            resolutions = [(1920, 1080), (1366, 768), (1440, 900), (1536, 864)]
            width, height = random.choice(resolutions)
            self.driver.set_window_size(width, height)
            
            logger.info("Browser setup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup browser: {str(e)}")
            return False
    
    def verify_proxy_ip(self):
        """Verify that the browser is using the proxy IP"""
        try:
            logger.info("Verifying proxy IP...")
            self.driver.get('http://httpbin.org/ip')
            time.sleep(2)
            
            page_source = self.driver.page_source
            # Extract IP from the page
            import json
            import re
            
            # Look for IP in the page source
            ip_match = re.search(r'"origin":\s*"([^"]+)"', page_source)
            if ip_match:
                current_ip = ip_match.group(1)
                my_real_ip = self.get_my_ip()
                
                logger.info(f"Browser IP: {current_ip}")
                logger.info(f"Real IP: {my_real_ip}")
                
                if current_ip != my_real_ip:
                    logger.info("✓ Proxy is working correctly - IP is masked")
                    return True
                else:
                    logger.error("✗ Proxy is not working - using real IP")
                    return False
            else:
                logger.error("Could not extract IP from verification page")
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
    
    def human_like_typing(self, element, text):
        """Type text in a human-like manner"""
        try:
            for char in text:
                element.send_keys(char)
                time.sleep(random.uniform(0.05, 0.2))  # Random delay between keystrokes
                
        except Exception as e:
            logger.error(f"Error during typing: {str(e)}")
    
    def search_google(self):
        """Search Google with the keyword"""
        try:
            logger.info("Opening Google.com...")
            self.driver.get('https://www.google.com')
            
            # Wait 5 seconds as requested
            logger.info("Waiting 5 seconds...")
            time.sleep(5)
            
            # Find search box
            search_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            
            logger.info(f"Typing keyword: {self.keyword}")
            self.human_like_typing(search_box, self.keyword)
            
            # Random delay before pressing enter
            time.sleep(random.uniform(1, 2))
            search_box.send_keys(Keys.RETURN)
            
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
    
    def find_and_visit_target(self):
        """Find target domain in search results and visit it"""
        try:
            logger.info(f"Looking for domain: {self.target_domain}")
            
            # Get all search result links
            search_results = self.driver.find_elements(By.CSS_SELECTOR, "h3")
            
            target_found = False
            for result in search_results:
                try:
                    parent_link = result.find_element(By.XPATH, "..")
                    if parent_link.tag_name == 'a':
                        href = parent_link.get_attribute('href')
                        if href and self.target_domain in href:
                            logger.info(f"Found target domain in: {href}")
                            
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
                
                # Human-like scrolling on target website
                logger.info("Performing human-like scrolling on target website...")
                self.human_like_scroll()
                
                # Stay on page for 20 seconds
                logger.info("Staying on target website for 20 seconds...")
                time.sleep(20)
                
                return True
            else:
                logger.warning(f"Target domain '{self.target_domain}' not found in search results")
                return False
                
        except Exception as e:
            logger.error(f"Error finding/visiting target: {str(e)}")
            return False
    
    def close_browser(self):
        """Close the browser and clean up"""
        try:
            if self.driver:
                self.driver.quit()
                logger.info("Browser closed")
            
            # Clean up extension directory
            if hasattr(self, 'extension_dir') and self.extension_dir and os.path.exists(self.extension_dir):
                try:
                    shutil.rmtree(os.path.dirname(self.extension_dir))
                    logger.info("Cleaned up extension files")
                except:
                    pass
                    
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
            
            # Setup browser
            if not self.setup_browser(proxy):
                logger.error("Failed to setup browser")
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
                self.close_browser()
                return False
            
            logger.info("✓ Process completed successfully!")
            self.close_browser()
            return True
            
        except Exception as e:
            logger.error(f"Error in single proxy run: {str(e)}")
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
pip install selenium undetected-chromedriver fake-useragent requests

Example proxy list format:
123.456.789.10:8080
98.765.432.10:3128
111.222.333.44:8080

Example run:
keyword: "python tutorials"
domain: "realpython.com"
proxy list: 
123.456.789.10:8080
98.765.432.10:3128

The bot will:
1. Test each proxy
2. Verify IP masking
3. Open Google with fake user agent
4. Search for keyword
5. Scroll like human
6. Find and click target domain
7. Scroll on target site
8. Stay for 20 seconds
9. Move to next proxy
"""