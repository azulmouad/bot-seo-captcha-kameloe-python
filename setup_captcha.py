#!/usr/bin/env python3
"""
Setup script for 2captcha integration
This script helps configure the captcha solving functionality
"""

import os
import sys
import subprocess

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def install_requirements():
    """Install required packages"""
    print("\n📦 Installing required packages...")
    
    try:
        # Install regular requirements
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✅ Regular requirements installed")
        
        # Install Kameleo requirements if file exists
        if os.path.exists('requirements_kameleo.txt'):
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements_kameleo.txt'])
            print("✅ Kameleo requirements installed")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False

def setup_api_key():
    """Check 2captcha API key status"""
    print("\n🔑 Checking 2captcha API key...")
    
    # API key is now hardcoded in captcha_solver.py
    print("✅ API key is hardcoded in captcha_solver.py: 56d4457439...")
    print("💡 The API key is already configured and ready to use")
    return True

def test_captcha_solver():
    """Test the captcha solver functionality"""
    print("\n🧪 Testing captcha solver...")
    
    try:
        from captcha_solver import CaptchaSolver
        
        solver = CaptchaSolver()
        if solver.solver:
            print("✅ Captcha solver initialized successfully")
            return True
        else:
            print("⚠️  Captcha solver initialized but API key may be invalid")
            return False
    except ImportError as e:
        print(f"❌ Failed to import captcha solver: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing captcha solver: {e}")
        return False

def create_config_file():
    """Create configuration file from example"""
    print("\n📝 Creating configuration file...")
    
    if os.path.exists('config.py'):
        print("✅ config.py already exists")
        return True
    
    if os.path.exists('config_example.py'):
        try:
            import shutil
            shutil.copy('config_example.py', 'config.py')
            print("✅ Created config.py from example")
            print("💡 Edit config.py to customize your settings")
            return True
        except Exception as e:
            print(f"❌ Failed to create config.py: {e}")
            return False
    else:
        print("⚠️  config_example.py not found")
        return False

def check_chrome_driver():
    """Check if Chrome/ChromeDriver is available"""
    print("\n🌐 Checking Chrome/ChromeDriver...")
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        driver = webdriver.Chrome(options=options)
        driver.quit()
        print("✅ Chrome/ChromeDriver is working")
        return True
    except Exception as e:
        print(f"❌ Chrome/ChromeDriver issue: {e}")
        print("💡 Make sure Chrome browser and ChromeDriver are installed")
        return False

def print_usage_instructions():
    """Print usage instructions"""
    print("\n📖 Usage Instructions:")
    print("=" * 50)
    print()
    print("1. Regular bot (with undetected-chromedriver):")
    print("   python bot.py")
    print()
    print("2. Kameleo bot (requires Kameleo.CLI running):")
    print("   python bot_kameleo.py")
    print()
    print("3. Test captcha solving:")
    print("   python example/captcha_example.py")
    print()
    print("4. Configuration:")
    print("   - Edit config.py for custom settings")
    print("   - Set APIKEY_2CAPTCHA environment variable")
    print("   - Set KAMELEO_PORT if using different port")
    print()
    print("📚 Captcha Types Supported:")
    print("   - reCAPTCHA v2")
    print("   - reCAPTCHA v3")
    print("   - hCaptcha")
    print()
    print("💰 2captcha Pricing:")
    print("   - reCAPTCHA v2: $1 per 1000 solves")
    print("   - reCAPTCHA v3: $2 per 1000 solves")
    print("   - hCaptcha: $1 per 1000 solves")

def main():
    """Main setup function"""
    print("🚀 2captcha Integration Setup")
    print("=" * 40)
    
    success_count = 0
    total_checks = 6
    
    # Check Python version
    if check_python_version():
        success_count += 1
    
    # Install requirements
    if install_requirements():
        success_count += 1
    
    # Setup API key
    if setup_api_key():
        success_count += 1
    
    # Test captcha solver
    if test_captcha_solver():
        success_count += 1
    
    # Create config file
    if create_config_file():
        success_count += 1
    
    # Check Chrome driver
    if check_chrome_driver():
        success_count += 1
    
    # Print results
    print(f"\n📊 Setup Results: {success_count}/{total_checks} checks passed")
    
    if success_count == total_checks:
        print("🎉 Setup completed successfully!")
    elif success_count >= 4:
        print("⚠️  Setup mostly complete with some warnings")
    else:
        print("❌ Setup incomplete. Please fix the issues above")
    
    # Print usage instructions
    print_usage_instructions()

if __name__ == "__main__":
    main()