#!/usr/bin/env python3
"""
Debug Cookie Database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.cookie_manager import CookieManager
import sqlite3

def debug_cookie_database():
    """Debug the cookie database"""
    print("🔍 Debugging Cookie Database")
    print("=" * 40)
    
    # Check if database exists
    db_path = "cookies.db"
    if os.path.exists(db_path):
        print(f"✓ Database exists: {db_path}")
        
        # Check database contents
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get all records
            cursor.execute("SELECT proxy_id, created_at, updated_at FROM cookies")
            records = cursor.fetchall()
            
            print(f"📊 Database contains {len(records)} records:")
            for record in records:
                proxy_id, created, updated = record
                print(f"   - {proxy_id} (created: {created}, updated: {updated})")
            
            # Get detailed cookie data for each proxy
            for record in records:
                proxy_id = record[0]
                cursor.execute("SELECT cookies_data FROM cookies WHERE proxy_id = ?", (proxy_id,))
                result = cursor.fetchone()
                if result:
                    import json
                    cookies = json.loads(result[0])
                    print(f"   📋 {proxy_id} has {len(cookies)} cookies:")
                    for cookie in cookies[:3]:  # Show first 3
                        print(f"      - {cookie.get('name', 'unknown')} ({cookie.get('domain', 'unknown')})")
                    if len(cookies) > 3:
                        print(f"      ... and {len(cookies) - 3} more")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Error reading database: {str(e)}")
    else:
        print(f"❌ Database does not exist: {db_path}")
    
    print("\n🧪 Testing Cookie Manager")
    print("-" * 30)
    
    # Test cookie manager
    cookie_manager = CookieManager()
    
    # Get all proxies with cookies
    proxies = cookie_manager.get_all_proxies_with_cookies()
    print(f"📋 Proxies with cookies: {len(proxies)}")
    for proxy in proxies:
        print(f"   - {proxy}")
    
    # Get stats
    stats = cookie_manager.get_cookie_stats()
    print(f"📊 Cookie Statistics:")
    print(f"   - Total proxies: {stats['total_proxies_with_cookies']}")
    print(f"   - Total cookies: {stats['total_cookies']}")
    print(f"   - Average per proxy: {stats['average_cookies_per_proxy']}")
    
    print("\n" + "=" * 40)

if __name__ == "__main__":
    debug_cookie_database()