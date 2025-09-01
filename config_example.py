#!/usr/bin/env python3
"""
Configuration example for 2captcha integration
Copy this file to config.py and update with your settings
"""

import os

# 2captcha Configuration
CAPTCHA_CONFIG = {
    # Your 2captcha API key - get it from https://2captcha.com/
    'api_key': os.getenv('APIKEY_2CAPTCHA', 'YOUR_API_KEY_HERE'),
    
    # Default timeout for captcha solving (seconds)
    'timeout': 120,
    
    # reCAPTCHA v3 settings
    'recaptcha_v3': {
        'action': 'verify',
        'min_score': 0.3
    },
    
    # Enable/disable captcha solving
    'enabled': True,
    
    # Auto-detect captcha types
    'auto_detect': True
}

# Bot Configuration
BOT_CONFIG = {
    # Default search keyword
    'keyword': 'python tutorials',
    
    # Default target domain
    'target_domain': 'example.com',
    
    # Proxy list (format: ip:port or ip:port:username:password)
    'proxy_list': [
        '123.456.789.10:8080',
        '98.765.432.10:3128:username:password',
        '111.222.333.44:8080'
    ],
    
    # Human-like behavior settings
    'human_behavior': {
        'scroll_delay': (0.5, 1.5),  # Random delay between scrolls
        'typing_delay': (0.05, 0.2),  # Random delay between keystrokes
        'click_delay': (1, 3),  # Random delay before clicking
        'page_stay_time': 20  # Time to stay on target page
    }
}

# Kameleo Configuration (for Kameleo version)
KAMELEO_CONFIG = {
    # Kameleo port (default: 5050)
    'port': os.getenv('KAMELEO_PORT', '5050'),
    
    # Browser fingerprint preferences
    'fingerprint': {
        'device_type': 'desktop',
        'browser_product': 'chrome',
        'browser_version': '>134',
        'languages': ['en-US', 'en-GB', 'de-DE', 'fr-FR', 'es-ES']
    }
}

# Logging Configuration
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(levelname)s - %(message)s',
    'file': 'bot_activity.log'
}

def validate_config():
    """Validate configuration settings"""
    errors = []
    
    # Check 2captcha API key
    if CAPTCHA_CONFIG['api_key'] == 'YOUR_API_KEY_HERE':
        errors.append("2captcha API key not configured")
    
    # Check proxy list
    if not BOT_CONFIG['proxy_list']:
        errors.append("No proxies configured")
    
    # Check required fields
    if not BOT_CONFIG['keyword']:
        errors.append("Search keyword not configured")
    
    if not BOT_CONFIG['target_domain']:
        errors.append("Target domain not configured")
    
    return errors

def print_config_status():
    """Print current configuration status"""
    print("Configuration Status:")
    print("=" * 30)
    
    # 2captcha status
    api_key = CAPTCHA_CONFIG['api_key']
    if api_key != 'YOUR_API_KEY_HERE':
        print(f"✓ 2captcha API key: {api_key[:10]}...")
    else:
        print("✗ 2captcha API key: Not configured")
    
    # Bot settings
    print(f"✓ Search keyword: {BOT_CONFIG['keyword']}")
    print(f"✓ Target domain: {BOT_CONFIG['target_domain']}")
    print(f"✓ Proxy count: {len(BOT_CONFIG['proxy_list'])}")
    
    # Kameleo settings
    print(f"✓ Kameleo port: {KAMELEO_CONFIG['port']}")
    
    # Validation
    errors = validate_config()
    if errors:
        print("\nConfiguration Errors:")
        for error in errors:
            print(f"✗ {error}")
    else:
        print("\n✓ Configuration is valid!")

if __name__ == "__main__":
    print_config_status()