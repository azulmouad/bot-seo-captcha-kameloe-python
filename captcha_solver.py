import os
import time
import logging
from twocaptcha import TwoCaptcha
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger(__name__)

class CaptchaSolver:
    def __init__(self, api_key=None):
        """Initialize 2captcha solver with API key"""
        self.api_key = api_key or '56d4457439d8eb46c1831d271166f13b'
        self.solver = TwoCaptcha(self.api_key)
        logger.info("2captcha solver initialized with API key")
    
    def solve_recaptcha_v2(self, driver, sitekey=None, timeout=120):
        """Solve reCAPTCHA v2 challenge"""
        if not self.solver:
            logger.error("2captcha solver not initialized. Check API key.")
            return False
        
        try:
            current_url = driver.current_url
            logger.info(f"Attempting to solve reCAPTCHA v2 on {current_url}")
            
            # Auto-detect sitekey if not provided
            if not sitekey:
                sitekey = self.detect_recaptcha_sitekey(driver)
                if not sitekey:
                    logger.error("Could not detect reCAPTCHA sitekey")
                    return False
            
            logger.info(f"Using sitekey: {sitekey}")
            
            # Solve captcha using 2captcha service
            logger.info("Sending reCAPTCHA to 2captcha service...")
            result = self.solver.recaptcha(
                sitekey=sitekey,
                url=current_url,
                timeout=timeout
            )
            
            if result and 'code' in result:
                captcha_response = result['code']
                logger.info("✓ reCAPTCHA solved successfully")
                
                # Inject the solution into the page
                return self.inject_recaptcha_solution(driver, captcha_response)
            else:
                logger.error("Failed to solve reCAPTCHA")
                return False
                
        except Exception as e:
            logger.error(f"Error solving reCAPTCHA: {str(e)}")
            return False
    
    def solve_recaptcha_v3(self, driver, sitekey=None, action='verify', min_score=0.3, timeout=120):
        """Solve reCAPTCHA v3 challenge"""
        if not self.solver:
            logger.error("2captcha solver not initialized. Check API key.")
            return False
        
        try:
            current_url = driver.current_url
            logger.info(f"Attempting to solve reCAPTCHA v3 on {current_url}")
            
            # Auto-detect sitekey if not provided
            if not sitekey:
                sitekey = self.detect_recaptcha_sitekey(driver)
                if not sitekey:
                    logger.error("Could not detect reCAPTCHA v3 sitekey")
                    return False
            
            logger.info(f"Using sitekey: {sitekey}, action: {action}, min_score: {min_score}")
            
            # Solve captcha using 2captcha service
            logger.info("Sending reCAPTCHA v3 to 2captcha service...")
            result = self.solver.recaptcha(
                sitekey=sitekey,
                url=current_url,
                version='v3',
                action=action,
                min_score=min_score,
                timeout=timeout
            )
            
            if result and 'code' in result:
                captcha_response = result['code']
                logger.info("✓ reCAPTCHA v3 solved successfully")
                
                # For v3, we typically need to inject the token and trigger form submission
                return self.inject_recaptcha_v3_solution(driver, captcha_response)
            else:
                logger.error("Failed to solve reCAPTCHA v3")
                return False
                
        except Exception as e:
            logger.error(f"Error solving reCAPTCHA v3: {str(e)}")
            return False
    
    def solve_hcaptcha(self, driver, sitekey=None, timeout=120):
        """Solve hCaptcha challenge"""
        if not self.solver:
            logger.error("2captcha solver not initialized. Check API key.")
            return False
        
        try:
            current_url = driver.current_url
            logger.info(f"Attempting to solve hCaptcha on {current_url}")
            
            # Auto-detect sitekey if not provided
            if not sitekey:
                sitekey = self.detect_hcaptcha_sitekey(driver)
                if not sitekey:
                    logger.error("Could not detect hCaptcha sitekey")
                    return False
            
            logger.info(f"Using sitekey: {sitekey}")
            
            # Solve captcha using 2captcha service
            logger.info("Sending hCaptcha to 2captcha service...")
            result = self.solver.hcaptcha(
                sitekey=sitekey,
                url=current_url,
                timeout=timeout
            )
            
            if result and 'code' in result:
                captcha_response = result['code']
                logger.info("✓ hCaptcha solved successfully")
                
                # Inject the solution into the page
                return self.inject_hcaptcha_solution(driver, captcha_response)
            else:
                logger.error("Failed to solve hCaptcha")
                return False
                
        except Exception as e:
            logger.error(f"Error solving hCaptcha: {str(e)}")
            return False
    
    def detect_recaptcha_sitekey(self, driver):
        """Auto-detect reCAPTCHA sitekey from page"""
        try:
            # Common selectors for reCAPTCHA sitekey
            selectors = [
                '[data-sitekey]',
                '.g-recaptcha[data-sitekey]',
                'div[data-sitekey]',
                'iframe[src*="recaptcha"]'
            ]
            
            for selector in selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        sitekey = element.get_attribute('data-sitekey')
                        if sitekey:
                            logger.info(f"Detected reCAPTCHA sitekey: {sitekey}")
                            return sitekey
                except:
                    continue
            
            # Try to find sitekey in page source
            page_source = driver.page_source
            import re
            
            # Look for sitekey in various formats
            patterns = [
                r'data-sitekey=["\']([^"\']+)["\']',
                r'"sitekey":\s*["\']([^"\']+)["\']',
                r'sitekey:\s*["\']([^"\']+)["\']'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, page_source)
                if matches:
                    sitekey = matches[0]
                    logger.info(f"Detected reCAPTCHA sitekey from source: {sitekey}")
                    return sitekey
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting reCAPTCHA sitekey: {str(e)}")
            return None
    
    def detect_hcaptcha_sitekey(self, driver):
        """Auto-detect hCaptcha sitekey from page"""
        try:
            # Common selectors for hCaptcha sitekey
            selectors = [
                '[data-sitekey]',
                '.h-captcha[data-sitekey]',
                'div[data-sitekey]'
            ]
            
            for selector in selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        sitekey = element.get_attribute('data-sitekey')
                        if sitekey and 'hcaptcha' in driver.page_source.lower():
                            logger.info(f"Detected hCaptcha sitekey: {sitekey}")
                            return sitekey
                except:
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting hCaptcha sitekey: {str(e)}")
            return None
    
    def inject_recaptcha_solution(self, driver, captcha_response):
        """Inject reCAPTCHA v2 solution into the page"""
        try:
            # Find the reCAPTCHA response textarea
            response_element = driver.find_element(By.NAME, 'g-recaptcha-response')
            
            # Make the textarea visible and inject the solution
            driver.execute_script("""
                var element = arguments[0];
                element.style.display = 'block';
                element.style.visibility = 'visible';
                element.value = arguments[1];
            """, response_element, captcha_response)
            
            # Trigger the callback if it exists
            driver.execute_script("""
                if (typeof grecaptcha !== 'undefined') {
                    var widgets = grecaptcha.getResponse();
                    if (widgets) {
                        grecaptcha.execute();
                    }
                }
            """)
            
            logger.info("reCAPTCHA solution injected successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error injecting reCAPTCHA solution: {str(e)}")
            return False
    
    def inject_recaptcha_v3_solution(self, driver, captcha_response):
        """Inject reCAPTCHA v3 solution into the page"""
        try:
            # For v3, we typically need to set the token and trigger form submission
            driver.execute_script(f"""
                if (typeof grecaptcha !== 'undefined') {{
                    window.captchaToken = '{captcha_response}';
                    
                    // Try to find and fill hidden token fields
                    var tokenFields = document.querySelectorAll('input[name*="token"], input[name*="captcha"]');
                    for (var i = 0; i < tokenFields.length; i++) {{
                        tokenFields[i].value = '{captcha_response}';
                    }}
                    
                    // Trigger any callback functions
                    if (window.onCaptchaSuccess) {{
                        window.onCaptchaSuccess('{captcha_response}');
                    }}
                }}
            """)
            
            logger.info("reCAPTCHA v3 solution injected successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error injecting reCAPTCHA v3 solution: {str(e)}")
            return False
    
    def inject_hcaptcha_solution(self, driver, captcha_response):
        """Inject hCaptcha solution into the page"""
        try:
            # Find the hCaptcha response textarea
            response_element = driver.find_element(By.NAME, 'h-captcha-response')
            
            # Make the textarea visible and inject the solution
            driver.execute_script("""
                var element = arguments[0];
                element.style.display = 'block';
                element.style.visibility = 'visible';
                element.value = arguments[1];
            """, response_element, captcha_response)
            
            # Trigger the callback if it exists
            driver.execute_script("""
                if (typeof hcaptcha !== 'undefined') {
                    var widgets = hcaptcha.getResponse();
                    if (widgets) {
                        hcaptcha.execute();
                    }
                }
            """)
            
            logger.info("hCaptcha solution injected successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error injecting hCaptcha solution: {str(e)}")
            return False
    
    def detect_and_solve_captcha(self, driver, timeout=120):
        """Auto-detect and solve any captcha on the current page"""
        try:
            logger.info("Scanning page for captcha challenges...")
            
            # Check for reCAPTCHA v2
            if self.is_recaptcha_v2_present(driver):
                logger.info("reCAPTCHA v2 detected")
                return self.solve_recaptcha_v2(driver, timeout=timeout)
            
            # Check for reCAPTCHA v3
            elif self.is_recaptcha_v3_present(driver):
                logger.info("reCAPTCHA v3 detected")
                return self.solve_recaptcha_v3(driver, timeout=timeout)
            
            # Check for hCaptcha
            elif self.is_hcaptcha_present(driver):
                logger.info("hCaptcha detected")
                return self.solve_hcaptcha(driver, timeout=timeout)
            
            else:
                logger.info("No captcha detected on current page")
                return True  # No captcha to solve
                
        except Exception as e:
            logger.error(f"Error in auto-detect captcha: {str(e)}")
            return False
    
    def is_recaptcha_v2_present(self, driver):
        """Check if reCAPTCHA v2 is present on the page"""
        try:
            # Look for reCAPTCHA v2 elements
            selectors = [
                '.g-recaptcha',
                'div[data-sitekey]',
                'iframe[src*="recaptcha/api2"]'
            ]
            
            for selector in selectors:
                if driver.find_elements(By.CSS_SELECTOR, selector):
                    return True
            
            return 'recaptcha/api2' in driver.page_source
            
        except:
            return False
    
    def is_recaptcha_v3_present(self, driver):
        """Check if reCAPTCHA v3 is present on the page"""
        try:
            return 'recaptcha/api.js' in driver.page_source or 'grecaptcha.execute' in driver.page_source
        except:
            return False
    
    def is_hcaptcha_present(self, driver):
        """Check if hCaptcha is present on the page"""
        try:
            # Look for hCaptcha elements
            selectors = [
                '.h-captcha',
                'div[data-sitekey]'
            ]
            
            for selector in selectors:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements and 'hcaptcha' in driver.page_source.lower():
                    return True
            
            return 'hcaptcha.com' in driver.page_source
            
        except:
            return False
    
    def wait_for_captcha_and_solve(self, driver, max_wait=30, solve_timeout=120):
        """Wait for captcha to appear and solve it automatically"""
        try:
            logger.info(f"Waiting up to {max_wait} seconds for captcha to appear...")
            
            start_time = time.time()
            while time.time() - start_time < max_wait:
                if (self.is_recaptcha_v2_present(driver) or 
                    self.is_recaptcha_v3_present(driver) or 
                    self.is_hcaptcha_present(driver)):
                    
                    logger.info("Captcha detected, attempting to solve...")
                    return self.detect_and_solve_captcha(driver, timeout=solve_timeout)
                
                time.sleep(1)
            
            logger.info("No captcha appeared within the wait time")
            return True  # No captcha to solve
            
        except Exception as e:
            logger.error(f"Error waiting for captcha: {str(e)}")
            return False