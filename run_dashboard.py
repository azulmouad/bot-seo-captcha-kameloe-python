#!/usr/bin/env python3
"""
Startup script for SEO Bot Dashboard
"""

import subprocess
import sys
import os
import time

def check_requirements():
    """Check if required packages are installed"""
    required_packages = [
        'flask',
        'flask_socketio',
        'selenium',
        'kameleo.local_api_client',
        'requests',
        'twocaptcha'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n📦 Install missing packages with:")
        print("   pip install -r requirements_web.txt")
        return False
    
    return True

def check_kameleo():
    """Check if Kameleo.CLI is running"""
    try:
        import requests
        response = requests.get('http://localhost:5050/api/v1/fingerprints', timeout=5)
        if response.status_code == 200:
            print("✅ Kameleo.CLI is running on port 5050")
            return True
        else:
            print("⚠️  Kameleo.CLI responded but with error")
            return False
    except Exception as e:
        print("❌ Kameleo.CLI is not running on port 5050")
        print("   Start Kameleo.CLI first:")
        print("   ./Kameleo.CLI email=your_email@example.com password=your_password")
        return False

def main():
    print("🚀 SEO Bot Dashboard Startup")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Python 3.7+ is required")
        return
    
    print(f"✅ Python {sys.version.split()[0]}")
    
    # Check requirements
    print("📦 Checking requirements...")
    if not check_requirements():
        return
    
    print("✅ All required packages installed")
    
    # Check Kameleo
    print("🔧 Checking Kameleo.CLI...")
    if not check_kameleo():
        print("\n⚠️  Warning: Kameleo.CLI is not running")
        print("   The dashboard will start but bot execution will fail")
        print("   Make sure to start Kameleo.CLI before running bots")
        
        choice = input("\n   Continue anyway? (y/n): ").strip().lower()
        if choice != 'y':
            return
    
    # Start the Flask app
    print("\n🌐 Starting SEO Bot Dashboard...")
    print("=" * 50)
    print("📊 Dashboard URL: http://localhost:8080")
    print("🔧 Make sure Kameleo.CLI is running on port 5050")
    print("💡 Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        # Import and run the Flask app
        from app import socketio, app
        socketio.run(app, host='0.0.0.0', port=8080, debug=False)
    except KeyboardInterrupt:
        print("\n\n👋 Dashboard stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting dashboard: {e}")

if __name__ == "__main__":
    main()