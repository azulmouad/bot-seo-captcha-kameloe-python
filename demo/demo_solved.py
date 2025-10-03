"""
Simple Google Search Bot with Kameleo + 2captcha
Handles Google's special data-s parameter for /sorry pages
"""

import time
import random
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from kameleo.local_api_client import KameleoLocalApiClient
from kameleo.local_api_client.models import CreateProfileRequest, ProxyChoice, Server
from twocaptcha import TwoCaptcha

class SimpleCaptchaBot:
    def __init__(self, keyword, target_domain, proxy_string, api_key):
        self.keyword = keyword
        self.target_domain = target_domain
        self.proxy_string = proxy_string
        self.api_key = api_key
        
        # Parse proxy: ip:port:username:password
        parts = proxy_string.split(':')
        self.proxy_ip = parts[0]
        self.proxy_port = int(parts[1])
        self.proxy_user = parts[2] if len(parts) > 2 else None
        self.proxy_pass = parts[3] if len(parts) > 3 else None
        
        # Initialize 2captcha
        self.captcha_solver = TwoCaptcha(
            apiKey=api_key,
            defaultTimeout=120,
            recaptchaTimeout=600,
            pollingInterval=10
        )
        
        self.driver = None
        self.kameleo_client = None
        self.profile = None
    
    def is_captcha_page(self):
        """Check if current page has captcha"""
        try:
            url = self.driver.current_url
            
            # Check URL
            if '/sorry' in url or 'captcha' in url.lower():
                print(f"CAPTCHA DETECTED: {url}")
                return True
            
            # Check page content
            page_text = self.driver.page_source.lower()
            captcha_words = ['recaptcha', 'captcha', 'unusual traffic', 
                           'verify you', 'not a robot', 'security check']
            
            for word in captcha_words:
                if word in page_text:
                    print(f"CAPTCHA DETECTED: Found '{word}'")
                    return True
            
            return False
        except:
            return False
    
    def get_data_s_parameter(self):
        """Extract data-s parameter from Google /sorry page"""
        try:
            # Method 1: From page source
            page_source = self.driver.page_source
            
            # Look for data-s in various formats
            patterns = [
                r'data-s="([^"]+)"',
                r'"data-s":"([^"]+)"',
                r'data-s=\'([^\']+)\'',
                r'data-s\s*=\s*["\']([^"\']+)["\']',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, page_source)
                if match:
                    data_s = match.group(1)
                    print(f"Found data-s: {data_s}")
                    return data_s
            
            # Method 2: From URL parameter (sometimes it's there)
            url = self.driver.current_url
            if 'q=' in url:
                # Extract q parameter which contains data-s info
                match = re.search(r'q=([^&]+)', url)
                if match:
                    data_s = match.group(1)
                    print(f"Found data-s in URL: {data_s}")
                    return data_s
            
            # Method 3: Execute JavaScript to get it
            try:
                data_s = self.driver.execute_script("""
                    var dataS = document.querySelector('[data-s]');
                    if (dataS) return dataS.getAttribute('data-s');
                    
                    var scripts = document.getElementsByTagName('script');
                    for (var i = 0; i < scripts.length; i++) {
                        var text = scripts[i].textContent;
                        var match = text.match(/data-s["\s:=]+["']?([^"',\\s]+)["']?/);
                        if (match) return match[1];
                    }
                    return null;
                """)
                
                if data_s:
                    print(f"Found data-s via JS: {data_s}")
                    return data_s
            except:
                pass
            
            print("WARNING: Could not find data-s parameter")
            return None
            
        except Exception as e:
            print(f"Error getting data-s: {e}")
            return None
    
    def get_sitekey(self):
        """Extract reCAPTCHA sitekey"""
        try:
            # Method 1: data-sitekey attribute
            elements = self.driver.find_elements(By.CSS_SELECTOR, '[data-sitekey]')
            for el in elements:
                sitekey = el.get_attribute('data-sitekey')
                if sitekey and len(sitekey) > 20:
                    return sitekey
            
            # Method 2: iframe src
            iframes = self.driver.find_elements(By.CSS_SELECTOR, 'iframe[src*="recaptcha"]')
            for iframe in iframes:
                src = iframe.get_attribute('src')
                if 'k=' in src:
                    return src.split('k=')[1].split('&')[0]
            
            # Method 3: page source
            page = self.driver.page_source
            match = re.search(r'data-sitekey=["\']([^"\']+)["\']', page)
            if match:
                return match.group(1)
            
            return None
        except Exception as e:
            print(f"Error getting sitekey: {e}")
            return None
    
    def solve_captcha(self):
        """Solve captcha using 2captcha with data-s parameter via raw API"""
        try:
            print("\n" + "="*50)
            print("SOLVING CAPTCHA")
            print("="*50)
            
            url = self.driver.current_url
            
            # Check if this is Google /sorry page
            is_google_sorry = '/sorry' in url and 'google.com' in url
            
            # Get sitekey
            print("Getting sitekey...")
            sitekey = self.get_sitekey()
            if not sitekey:
                print("ERROR: No sitekey found")
                return False
            
            print(f"Sitekey: {sitekey}")
            
            # Get data-s parameter if it's Google /sorry page
            data_s = None
            if is_google_sorry:
                print("This is Google /sorry page, getting data-s parameter...")
                data_s = self.get_data_s_parameter()
                
                if data_s:
                    print(f"Using data-s: {data_s[:50]}...")
                else:
                    print("WARNING: No data-s found, solving may fail")
            
            # Solve with 2captcha using raw API
            print("Submitting to 2captcha (please wait)...")
            
            try:
                import requests
                
                # Submit captcha
                submit_url = "https://2captcha.com/in.php"
                params = {
                    'key': self.api_key,
                    'method': 'userrecaptcha',
                    'googlekey': sitekey,
                    'pageurl': url,
                    'json': 1
                }
                
                # Add data-s if available
                if data_s:
                    params['data-s'] = data_s
                
                response = requests.post(submit_url, data=params, timeout=30)
                result = response.json()
                
                if result.get('status') != 1:
                    print(f"ERROR: Submission failed - {result}")
                    return False
                
                captcha_id = result.get('request')
                print(f"Captcha submitted, ID: {captcha_id}")
                print("Waiting for solution (this takes 30-120 seconds)...")
                
                # Poll for result
                result_url = "https://2captcha.com/res.php"
                max_wait = 180  # 3 minutes max
                start_time = time.time()
                
                while time.time() - start_time < max_wait:
                    time.sleep(10)  # Check every 10 seconds
                    
                    result_params = {
                        'key': self.api_key,
                        'action': 'get',
                        'id': captcha_id,
                        'json': 1
                    }
                    
                    result_response = requests.get(result_url, params=result_params, timeout=30)
                    result_data = result_response.json()
                    
                    if result_data.get('status') == 1:
                        solution = result_data.get('request')
                        elapsed = time.time() - start_time
                        print(f"Solution received in {elapsed:.1f}s! Length: {len(solution)}")
                        break
                    elif result_data.get('request') == 'CAPCHA_NOT_READY':
                        elapsed = time.time() - start_time
                        print(f"Still solving... ({elapsed:.0f}s elapsed)")
                        continue
                    else:
                        print(f"ERROR: {result_data}")
                        return False
                else:
                    print("ERROR: Timeout waiting for solution")
                    return False
                
            except Exception as e:
                print(f"ERROR: 2captcha failed - {e}")
                return False
            
            # Inject solution
            print("Injecting solution...")
            self.driver.execute_script(f"""
                var textareas = document.querySelectorAll('textarea[name="g-recaptcha-response"]');
                for (var i = 0; i < textareas.length; i++) {{
                    textareas[i].value = '{solution}';
                }}
                var main = document.getElementById('g-recaptcha-response');
                if (main) main.value = '{solution}';
            """)
            
            time.sleep(1)
            
            # Submit
            print("Submitting form...")
            try:
                # Try submit button
                buttons = self.driver.find_elements(By.CSS_SELECTOR, 'button[type="submit"]')
                if buttons and buttons[0].is_displayed():
                    buttons[0].click()
                else:
                    # Submit form directly
                    self.driver.execute_script("""
                        var forms = document.querySelectorAll('form');
                        if (forms.length > 0) forms[0].submit();
                    """)
            except:
                pass
            
            # Wait for verification
            print("Waiting for verification...")
            time.sleep(10)
            
            # Check if solved
            if not self.is_captcha_page():
                print("SUCCESS: Captcha solved!")
                print("="*50 + "\n")
                return True
            else:
                # Sometimes takes longer
                print("Still verifying, waiting more...")
                time.sleep(10)
                
                if not self.is_captcha_page():
                    print("SUCCESS: Captcha solved!")
                    print("="*50 + "\n")
                    return True
                else:
                    print("WARNING: Still on captcha page")
                    return False
                
        except Exception as e:
            print(f"ERROR solving captcha: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def setup_browser(self):
        """Setup Kameleo browser with proxy"""
        try:
            print("Setting up Kameleo...")
            
            # Connect to Kameleo
            self.kameleo_client = KameleoLocalApiClient(
                endpoint='http://localhost:5050'
            )
            
            # Get fingerprint
            fingerprints = self.kameleo_client.fingerprint.search_fingerprints(
                device_type='desktop',
                browser_product='chrome'
            )
            
            if not fingerprints:
                print("ERROR: No fingerprints found")
                return False
            
            # Setup proxy
            proxy_config = ProxyChoice(
                value='http',
                extra=Server(
                    host=self.proxy_ip,
                    port=self.proxy_port,
                    id=self.proxy_user,
                    secret=self.proxy_pass
                )
            )
            
            # Create profile
            profile_request = CreateProfileRequest(
                fingerprint_id=fingerprints[0].id,
                name=f'Bot - {self.proxy_ip}',
                proxy=proxy_config
            )
            
            self.profile = self.kameleo_client.profile.create_profile(profile_request)
            print(f"Profile created: {self.profile.id}")
            
            # Start profile
            self.kameleo_client.profile.start_profile(self.profile.id)
            
            # Connect browser
            options = webdriver.ChromeOptions()
            options.add_experimental_option('kameleo:profileId', self.profile.id)
            
            self.driver = webdriver.Remote(
                command_executor='http://localhost:5050/webdriver',
                options=options
            )
            
            print("Browser ready!")
            return True
            
        except Exception as e:
            print(f"ERROR setting up browser: {e}")
            return False
    
    def search_google(self):
        """Search Google and handle captchas"""
        try:
            print(f"\nSearching Google for: {self.keyword}")
            
            # Open Google
            self.driver.get('https://www.google.com')
            time.sleep(3)
            
            # Check for captcha
            if self.is_captcha_page():
                print("Captcha on homepage")
                if not self.solve_captcha():
                    return False
            
            # Accept cookies
            try:
                cookie_btn = self.driver.find_element(By.CSS_SELECTOR, 'button[id="L2AGLb"]')
                cookie_btn.click()
                time.sleep(1)
            except:
                pass
            
            # Find search box
            search_box = self.driver.find_element(By.CSS_SELECTOR, 'textarea[name="q"]')
            
            # Type keyword
            for char in self.keyword:
                search_box.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
            
            time.sleep(1)
            search_box.send_keys(Keys.RETURN)
            
            print("Waiting for results...")
            time.sleep(5)
            
            # Check for captcha after search
            if self.is_captcha_page():
                print("Captcha after search")
                if not self.solve_captcha():
                    return False
            
            # Verify results
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "search"))
                )
                print("Results loaded!")
                return True
            except:
                print("ERROR: No results found")
                return False
                
        except Exception as e:
            print(f"ERROR searching: {e}")
            return False
    
    def find_target(self):
        """Find and click target domain"""
        try:
            print(f"\nLooking for: {self.target_domain}")
            
            max_pages = 10
            for page in range(1, max_pages + 1):
                print(f"\nPage {page}/{max_pages}")
                
                # Check for captcha
                if self.is_captcha_page():
                    print("Captcha on results page")
                    if not self.solve_captcha():
                        break
                
                # Search for target
                results = self.driver.find_elements(By.CSS_SELECTOR, "h3")
                
                for result in results:
                    try:
                        parent = result.find_element(By.XPATH, "..")
                        if parent.tag_name == 'a':
                            href = parent.get_attribute('href')
                            if href and self.target_domain in href:
                                print(f"FOUND on page {page}!")
                                print(f"URL: {href}")
                                
                                # Click
                                parent.click()
                                time.sleep(3)
                                
                                # Check for captcha on target site
                                if self.is_captcha_page():
                                    print("Captcha on target site")
                                    self.solve_captcha()
                                
                                print(f"\nVisiting {self.target_domain}...")
                                time.sleep(10)
                                
                                return True
                    except:
                        continue
                
                # Go to next page
                if page < max_pages:
                    print("Not found, going to next page...")
                    
                    import urllib.parse
                    keyword_encoded = urllib.parse.quote_plus(self.keyword)
                    next_url = f"https://www.google.com/search?q={keyword_encoded}&start={page*10}"
                    self.driver.get(next_url)
                    time.sleep(5)
                    
                    # Check for captcha after navigation
                    if self.is_captcha_page():
                        print("Captcha after navigation")
                        if not self.solve_captcha():
                            break
            
            print(f"\nTarget not found in {max_pages} pages")
            return False
            
        except Exception as e:
            print(f"ERROR finding target: {e}")
            return False
    
    def cleanup(self):
        """Close browser and delete profile"""
        try:
            if self.driver:
                self.driver.quit()
            
            if self.kameleo_client and self.profile:
                self.kameleo_client.profile.stop_profile(self.profile.id)
                self.kameleo_client.profile.delete_profile(self.profile.id)
                print("Cleanup done")
        except:
            pass
    
    def run(self):
        """Run the bot"""
        try:
            print("\n" + "="*50)
            print("STARTING BOT")
            print("="*50)
            print(f"Keyword: {self.keyword}")
            print(f"Target: {self.target_domain}")
            print(f"Proxy: {self.proxy_ip}:{self.proxy_port}")
            print("="*50 + "\n")
            
            # Setup
            if not self.setup_browser():
                return False
            
            # Search
            if not self.search_google():
                return False
            
            # Find target
            if not self.find_target():
                return False
            
            print("\n" + "="*50)
            print("BOT COMPLETED SUCCESSFULLY!")
            print("="*50)
            return True
            
        except Exception as e:
            print(f"\nERROR: {e}")
            return False
        finally:
            self.cleanup()


# USAGE
if __name__ == "__main__":
    print("Simple Google Bot with Auto Captcha Solving")
    print("="*50)
    
    keyword = input("Enter keyword: ").strip()
    target = input("Enter target domain (e.g., example.com): ").strip()
    proxy = input("Enter proxy (ip:port:user:pass): ").strip()
    api_key = input("Enter 2captcha API key: ").strip()
    
    if not all([keyword, target, proxy, api_key]):
        print("ERROR: All fields required!")
    else:
        bot = SimpleCaptchaBot(keyword, target, proxy, api_key)
        bot.run()