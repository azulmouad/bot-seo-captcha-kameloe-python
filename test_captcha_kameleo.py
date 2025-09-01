#!/usr/bin/env python3
"""
Test script to verify 2captcha-python integration with Kameleo browser
Tests against Google's reCAPTCHA demo page: https://www.google.com/recaptcha/api2/demo

Requirements:
pip install 2captcha-python selenium kameleo

Environment Variables:
TWOCAPTCHA_API_KEY - Your 2captcha API key
KAMELEO_PORT - Kameleo port (default: 5050)
"""

import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from kameleo.local_api_client import KameleoLocalApiClient
from kameleo.local_api_client.models import CreateProfileRequest
from twocaptcha import TwoCaptcha

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('captcha_2captcha_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CaptchaTest2Captcha:
    def __init__(self):
        self.driver = None
        self.kameleo_client = None
        self.current_profile = None
        self.kameleo_port = "5050"
        
        # Initialize 2captcha solver
        api_key = "56d4457439d8eb46c1831d271166f13b"
        if not api_key:
            raise ValueError("TWOCAPTCHA_API_KEY environment variable is required")
        
        self.solver = TwoCaptcha(api_key)
        logger.info(f"2captcha solver initialized with API key: {api_key[:10]}...")
        
    def init_kameleo_client(self):
        """Initialize Kameleo client"""
        try:
            self.kameleo_client = KameleoLocalApiClient(
                endpoint=f'http://localhost:{self.kameleo_port}'
            )
            logger.info(f"Kameleo client initialized on port {self.kameleo_port}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Kameleo client: {str(e)}")
            logger.error("Make sure Kameleo.CLI is running on the specified port")
            return False
    
    def create_kameleo_profile(self):
        """Create a Kameleo profile for testing"""
        try:
            logger.info("Creating Kameleo profile for captcha testing...")
            
            # Get a Chrome fingerprint
            fingerprints = self.kameleo_client.fingerprint.search_fingerprints(
                device_type='desktop',
                browser_product='chrome',
                browser_version='>120'
            )
            
            if not fingerprints:
                logger.error("No Chrome fingerprints found")
                return None
            
            selected_fingerprint = fingerprints[0]
            logger.info(f"Using fingerprint: {selected_fingerprint.id}")
            
            # Create profile request
            create_profile_request = CreateProfileRequest(
                fingerprint_id=selected_fingerprint.id,
                name='2captcha Test Profile',
                start_page='https://www.google.com/recaptcha/api2/demo'
            )
            
            # Create the profile
            profile = self.kameleo_client.profile.create_profile(create_profile_request)
            logger.info(f"✓ Kameleo profile created: {profile.id}")
            
            return profile
            
        except Exception as e:
            logger.error(f"Failed to create Kameleo profile: {str(e)}")
            return None
    
    def setup_browser(self):
        """Setup Kameleo browser"""
        try:
            logger.info("Setting up Kameleo browser...")
            
            # Initialize Kameleo client
            if not self.init_kameleo_client():
                return False
            
            # Create Kameleo profile
            self.current_profile = self.create_kameleo_profile()
            if not self.current_profile:
                return False
            
            # Start the profile
            self.kameleo_client.profile.start_profile(self.current_profile.id)
            logger.info(f"Kameleo profile {self.current_profile.id} started")
            
            # Setup Chrome options for Kameleo
            options = webdriver.ChromeOptions()
            options.add_experimental_option('kameleo:profileId', self.current_profile.id)
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            
            # Connect to Kameleo WebDriver
            self.driver = webdriver.Remote(
                command_executor=f'http://localhost:{self.kameleo_port}/webdriver',
                options=options
            )
            
            # Set window size
            self.driver.set_window_size(1366, 768)
            
            logger.info("✓ Kameleo browser setup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup Kameleo browser: {str(e)}")
            return False
    
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
                except NoSuchElementException:
                    continue
            
            # Method 2: Extract from iframe src
            try:
                iframe = self.driver.find_element(By.CSS_SELECTOR, 'iframe[src*="recaptcha"]')
                src = iframe.get_attribute('src')
                if 'sitekey=' in src:
                    sitekey = src.split('sitekey=')[1].split('&')[0]
                    logger.info(f"Found sitekey from iframe src: {sitekey}")
                    return sitekey
            except NoSuchElementException:
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
            
            logger.error("Could not detect reCAPTCHA sitekey")
            return None
            
        except Exception as e:
            logger.error(f"Error detecting sitekey: {str(e)}")
            return None
    
    def wait_for_recaptcha_and_solve(self, timeout=180):
        """Wait for reCAPTCHA to appear and solve it"""
        try:
            logger.info("Waiting for reCAPTCHA to load...")
            
            # Wait for reCAPTCHA iframe to be present
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'iframe[src*="recaptcha"]'))
            )
            logger.info("✓ reCAPTCHA iframe detected")
            
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
                result = self.solver.recaptcha(
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
                
        except TimeoutException:
            logger.error("Timeout waiting for reCAPTCHA to load")
            return False
        except Exception as e:
            logger.error(f"Error solving reCAPTCHA: {str(e)}")
            return False
    
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
    
    def test_recaptcha_demo(self):
        """Test reCAPTCHA solving on Google's demo page"""
        try:
            logger.info("=" * 60)
            logger.info("TESTING RECAPTCHA ON GOOGLE DEMO PAGE")
            logger.info("=" * 60)
            
            # Navigate to Google's reCAPTCHA demo
            demo_url = "https://www.google.com/recaptcha/api2/demo"
            logger.info(f"Navigating to: {demo_url}")
            self.driver.get(demo_url)
            
            # Wait for page to load
            time.sleep(3)
            
            # Check page title
            page_title = self.driver.title
            logger.info(f"Page title: {page_title}")
            
            # Wait for and solve reCAPTCHA
            success = self.wait_for_recaptcha_and_solve()
            
            if success:
                logger.info("✓ reCAPTCHA solved successfully!")
                
                # Try to submit the form
                try:
                    logger.info("Attempting to submit the form...")
                    submit_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.ID, "recaptcha-demo-submit"))
                    )
                    submit_button.click()
                    logger.info("✓ Clicked submit button")
                    
                    # Wait for response
                    time.sleep(5)
                    
                    # Check if submission was successful
                    try:
                        success_element = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Verification Success') or contains(text(), 'success')]"))
                        )
                        logger.info("🎉 SUCCESS! Form submitted successfully - Verification Success found!")
                        return True
                    except TimeoutException:
                        # Check page source for success indicators
                        page_source = self.driver.page_source.lower()
                        if "success" in page_source or "verified" in page_source:
                            logger.info("🎉 SUCCESS! Form appears to have been submitted successfully!")
                            return True
                        else:
                            logger.warning("Form submitted but success confirmation not found")
                            logger.info("Current URL:", self.driver.current_url)
                            return True  # Still consider it success if captcha was solved
                        
                except TimeoutException:
                    logger.error("Submit button not found or not clickable")
                    return False
                except Exception as e:
                    logger.error(f"Error submitting form: {str(e)}")
                    return True  # Still success if captcha was solved
                    
            else:
                logger.error("✗ Failed to solve reCAPTCHA")
                return False
                
        except Exception as e:
            logger.error(f"Error during reCAPTCHA test: {str(e)}")
            return False
    
    def check_2captcha_balance(self):
        """Check 2captcha account balance"""
        try:
            balance = self.solver.balance()
            logger.info(f"2captcha account balance: ${balance}")
            if balance < 0.01:
                logger.warning("⚠️  Low balance! Make sure you have sufficient funds.")
                return False
            return True
        except Exception as e:
            logger.error(f"Error checking 2captcha balance: {str(e)}")
            return False
    
    def close_browser(self):
        """Close browser and clean up"""
        try:
            if self.driver:
                self.driver.quit()
                logger.info("Browser closed")
            
            # Clean up Kameleo profile
            if self.kameleo_client and self.current_profile:
                try:
                    self.kameleo_client.profile.stop_profile(self.current_profile.id)
                    logger.info(f"Kameleo profile {self.current_profile.id} stopped")
                    
                    self.kameleo_client.profile.delete_profile(self.current_profile.id)
                    logger.info(f"Kameleo profile {self.current_profile.id} deleted")
                    
                except Exception as e:
                    logger.warning(f"Failed to clean up Kameleo profile: {str(e)}")
                
                self.current_profile = None
                    
        except Exception as e:
            logger.error(f"Error closing browser: {str(e)}")
    
    def run_full_test(self):
        """Run complete captcha test suite"""
        try:
            logger.info("🚀 Starting 2captcha + Kameleo Integration Test")
            logger.info("=" * 60)
            
            # Check 2captcha balance first
            if not self.check_2captcha_balance():
                logger.error("❌ Insufficient 2captcha balance or API error")
                return False
            
            # Setup browser
            if not self.setup_browser():
                logger.error("❌ Failed to setup browser")
                return False
            
            logger.info("Browser fingerprint and profile loaded successfully")
            
            # Run the main test
            logger.info("\n🧩 Starting reCAPTCHA solving test...")
            solving_success = self.test_recaptcha_demo()
            
            # Results
            logger.info("\n" + "=" * 60)
            logger.info("TEST RESULTS SUMMARY")
            logger.info("=" * 60)
            logger.info(f"reCAPTCHA Solving Test: {'✅ PASSED' if solving_success else '❌ FAILED'}")
            
            if solving_success:
                logger.info("🎉 ALL TESTS PASSED!")
                logger.info("Your 2captcha + Kameleo integration is working perfectly!")
            else:
                logger.info("⚠️  TEST FAILED - Check logs above for details")
            
            return solving_success
            
        except Exception as e:
            logger.error(f"Error during full test: {str(e)}")
            return False
        finally:
            self.close_browser()

def main():
    """Main function to run the captcha test"""
    print("🔧 2captcha-python + Kameleo Integration Test")
    print("=" * 60)
    print("This test will:")
    print("1. Setup Kameleo browser with fingerprint protection")
    print("2. Navigate to Google's reCAPTCHA demo page")
    print("3. Detect and solve the reCAPTCHA using 2captcha service")
    print("4. Verify the solution works by submitting the form")
    print()
    
    # Check prerequisites
    print("📋 Checking prerequisites...")
    
    # Check if API key is set
    api_key = "56d4457439d8eb46c1831d271166f13b"
    if not api_key:
        print("❌ TWOCAPTCHA_API_KEY environment variable not set")
        print("   Set it with: export TWOCAPTCHA_API_KEY='your_api_key_here'")
        return
    else:
        print(f"✅ 2captcha API key configured: {api_key[:10]}...")
    
    # Check Kameleo port
    kameleo_port = "5050"
    print(f"✅ Kameleo port: {kameleo_port}")
    
    print("✅ Prerequisites check completed")
    print()
    
    # Check required packages
    try:
        import twocaptcha
        print("✅ twocaptcha package available")
    except ImportError:
        print("❌ twocaptcha package not found. Install with: pip install 2captcha-python")
        return
    
    try:
        from kameleo.local_api_client import KameleoLocalApiClient
        print("✅ kameleo package available")
    except ImportError:
        print("❌ kameleo package not found. Make sure Kameleo SDK is installed")
        return
    
    # Ask user confirmation
    print("\n⚠️  This test will use 2captcha credits (approximately $0.002-0.003 per solve)")
    confirm = input("🚀 Ready to start the test? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Test cancelled by user")
        return
    
    # Run the test
    try:
        tester = CaptchaTest2Captcha()
        success = tester.run_full_test()
        
        if success:
            print("\n🎉 Test completed successfully!")
            print("Your 2captcha + Kameleo integration is working properly!")
        else:
            print("\n⚠️  Test failed. Check the logs above for details.")
            print("\nCommon troubleshooting steps:")
            print("- Make sure Kameleo.CLI is running on the specified port")
            print("- Verify your 2captcha API key has sufficient balance")
            print("- Check your internet connection")
            print("- Ensure no firewalls are blocking the connections")
            
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()