#!/usr/bin/env python3
"""
Example script demonstrating 2captcha integration with the bot
"""

import sys
import os
import time

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from captcha_solver import CaptchaSolver

def test_recaptcha_v2():
    """Test reCAPTCHA v2 solving"""
    print("Testing reCAPTCHA v2 solving...")
    
    # Setup Chrome driver
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=options)
    captcha_solver = CaptchaSolver()
    
    try:
        # Go to reCAPTCHA demo page
        driver.get('https://2captcha.com/demo/recaptcha-v2')
        time.sleep(3)
        
        # Solve the captcha
        result = captcha_solver.detect_and_solve_captcha(driver)
        
        if result:
            print("✓ reCAPTCHA v2 solved successfully!")
            time.sleep(5)  # Wait to see the result
        else:
            print("✗ Failed to solve reCAPTCHA v2")
            
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        driver.quit()

def test_recaptcha_v3():
    """Test reCAPTCHA v3 solving"""
    print("Testing reCAPTCHA v3 solving...")
    
    # Setup Chrome driver
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=options)
    captcha_solver = CaptchaSolver()
    
    try:
        # Go to reCAPTCHA v3 demo page
        driver.get('https://2captcha.com/demo/recaptcha-v3')
        time.sleep(3)
        
        # Solve the captcha
        result = captcha_solver.detect_and_solve_captcha(driver)
        
        if result:
            print("✓ reCAPTCHA v3 solved successfully!")
            time.sleep(5)  # Wait to see the result
        else:
            print("✗ Failed to solve reCAPTCHA v3")
            
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        driver.quit()

def test_hcaptcha():
    """Test hCaptcha solving"""
    print("Testing hCaptcha solving...")
    
    # Setup Chrome driver
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=options)
    captcha_solver = CaptchaSolver()
    
    try:
        # Go to hCaptcha demo page
        driver.get('https://2captcha.com/demo/hcaptcha')
        time.sleep(3)
        
        # Solve the captcha
        result = captcha_solver.detect_and_solve_captcha(driver)
        
        if result:
            print("✓ hCaptcha solved successfully!")
            time.sleep(5)  # Wait to see the result
        else:
            print("✗ Failed to solve hCaptcha")
            
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        driver.quit()

def main():
    """Main function to run captcha tests"""
    print("2captcha Integration Test")
    print("=" * 30)
    
    # API key is now hardcoded in captcha_solver.py
    print("✓ API key configured: 56d4457439...")
    print()
    
    # Test different captcha types
    try:
        test_recaptcha_v2()
        print()
        
        test_recaptcha_v3()
        print()
        
        test_hcaptcha()
        print()
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Test failed: {str(e)}")

if __name__ == "__main__":
    main()