#!/usr/bin/env python3
"""
Simple test script to verify 2captcha integration works
"""

import sys
import os
from captcha_solver import CaptchaSolver
from twocaptcha import TwoCaptcha

def test_api_key():
    """Test if the API key is working"""
    print("🔑 Testing 2captcha API key...")
    
    try:
        # Test with direct TwoCaptcha client
        solver = TwoCaptcha('56d4457439d8eb46c1831d271166f13b')
        balance = solver.balance()
        print(f"✅ API key is valid! Balance: ${balance}")
        return True
    except Exception as e:
        print(f"❌ API key test failed: {str(e)}")
        return False

def test_captcha_solver():
    """Test the captcha solver class"""
    print("\n🧪 Testing CaptchaSolver class...")
    
    try:
        solver = CaptchaSolver()
        if solver.solver:
            print("✅ CaptchaSolver initialized successfully")
            
            # Test balance check
            try:
                balance = solver.solver.balance()
                print(f"✅ Balance check successful: ${balance}")
                return True
            except Exception as e:
                print(f"⚠️  Balance check failed: {str(e)}")
                return False
        else:
            print("❌ CaptchaSolver failed to initialize")
            return False
    except Exception as e:
        print(f"❌ CaptchaSolver test failed: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🚀 2captcha Integration Test")
    print("=" * 30)
    
    success_count = 0
    total_tests = 2
    
    # Test API key directly
    if test_api_key():
        success_count += 1
    
    # Test captcha solver class
    if test_captcha_solver():
        success_count += 1
    
    print(f"\n📊 Test Results: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("🎉 All tests passed! Captcha solving is ready to use.")
        print("\n💡 You can now run:")
        print("   python bot.py")
        print("   python bot_kameleo.py")
    else:
        print("❌ Some tests failed. Check your 2captcha account:")
        print("   - Make sure you have sufficient balance")
        print("   - Verify the API key is correct")
        print("   - Check your internet connection")

if __name__ == "__main__":
    main()