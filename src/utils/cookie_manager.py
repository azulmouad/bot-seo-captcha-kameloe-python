#!/usr/bin/env python3
"""
Cookie Management System for Kameleo Profiles
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
from kameleo.local_api_client.models import CookieRequest

logger = logging.getLogger(__name__)

class CookieManager:
    """Manages cookies for Kameleo profiles using SQLite database"""
    
    def __init__(self, db_path="cookies.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the SQLite database for cookies"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create cookies table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cookies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    proxy_id TEXT UNIQUE NOT NULL,
                    cookies_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info(f"Cookie database initialized: {self.db_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize cookie database: {str(e)}")
            raise
    
    def save_cookies(self, proxy_id: str, cookies: List[Dict]) -> bool:
        """Save cookies for a specific proxy"""
        try:
            if not cookies:
                logger.info(f"No cookies to save for proxy: {proxy_id}")
                return True
            
            logger.info(f"💾 Attempting to save {len(cookies)} cookies for proxy: {proxy_id}")
            
            # Convert cookies to JSON string
            cookies_json = json.dumps(cookies, indent=2)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insert or update cookies for this proxy
            cursor.execute('''
                INSERT OR REPLACE INTO cookies (proxy_id, cookies_data, updated_at)
                VALUES (?, ?, ?)
            ''', (proxy_id, cookies_json, datetime.now().isoformat()))
            
            conn.commit()
            
            # Verify the save worked
            cursor.execute('SELECT COUNT(*) FROM cookies WHERE proxy_id = ?', (proxy_id,))
            count = cursor.fetchone()[0]
            
            conn.close()
            
            if count > 0:
                logger.info(f"✅ Successfully saved {len(cookies)} cookies for proxy: {proxy_id}")
                return True
            else:
                logger.error(f"❌ Failed to verify cookie save for proxy: {proxy_id}")
                return False
            
        except Exception as e:
            logger.error(f"❌ Failed to save cookies for proxy {proxy_id}: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def load_cookies(self, proxy_id: str) -> Optional[List[Dict]]:
        """Load cookies for a specific proxy"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT cookies_data FROM cookies WHERE proxy_id = ?
            ''', (proxy_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                cookies = json.loads(result[0])
                
                # Filter out expired cookies
                valid_cookies = []
                current_time = datetime.now().timestamp()
                
                for cookie in cookies:
                    expiration = cookie.get('expiration_date')
                    if expiration is None or expiration > current_time:
                        valid_cookies.append(cookie)
                    else:
                        logger.debug(f"Filtered expired cookie: {cookie.get('name', 'unknown')}")
                
                if len(valid_cookies) != len(cookies):
                    logger.info(f"Filtered {len(cookies) - len(valid_cookies)} expired cookies")
                    # Update database with valid cookies only
                    if valid_cookies:
                        self.save_cookies(proxy_id, valid_cookies)
                    else:
                        self.delete_cookies(proxy_id)
                
                if valid_cookies:
                    logger.info(f"✓ Loaded {len(valid_cookies)} valid cookies for proxy: {proxy_id}")
                    return valid_cookies
                else:
                    logger.info(f"No valid cookies found for proxy: {proxy_id}")
                    return None
            else:
                logger.info(f"No saved cookies found for proxy: {proxy_id}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to load cookies for proxy {proxy_id}: {str(e)}")
            return None
    
    def has_cookies(self, proxy_id: str) -> bool:
        """Check if cookies exist for a specific proxy"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT COUNT(*) FROM cookies WHERE proxy_id = ?
            ''', (proxy_id,))
            
            count = cursor.fetchone()[0]
            conn.close()
            
            return count > 0
            
        except Exception as e:
            logger.error(f"Failed to check cookies for proxy {proxy_id}: {str(e)}")
            return False
    
    def delete_cookies(self, proxy_id: str) -> bool:
        """Delete cookies for a specific proxy"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM cookies WHERE proxy_id = ?
            ''', (proxy_id,))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✓ Deleted cookies for proxy: {proxy_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete cookies for proxy {proxy_id}: {str(e)}")
            return False
    
    def get_all_proxies_with_cookies(self) -> List[str]:
        """Get list of all proxy IDs that have saved cookies"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT proxy_id FROM cookies ORDER BY updated_at DESC')
            results = cursor.fetchall()
            conn.close()
            
            return [row[0] for row in results]
            
        except Exception as e:
            logger.error(f"Failed to get proxies with cookies: {str(e)}")
            return []
    
    def clear_all_cookies(self) -> bool:
        """Clear all saved cookies"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM cookies')
            conn.commit()
            conn.close()
            
            logger.info("✓ Cleared all saved cookies")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear all cookies: {str(e)}")
            return False
    
    def convert_kameleo_cookies_to_dict(self, kameleo_cookies) -> List[Dict]:
        """Convert Kameleo cookie objects to dictionary format for storage"""
        cookies_list = []
        
        try:
            for cookie in kameleo_cookies:
                cookie_dict = {
                    'domain': cookie.domain,
                    'name': cookie.name,
                    'path': cookie.path,
                    'value': cookie.value,
                    'host_only': cookie.host_only,
                    'http_only': cookie.http_only,
                    'secure': cookie.secure,
                    'same_site': cookie.same_site,
                    'expiration_date': cookie.expiration_date
                }
                cookies_list.append(cookie_dict)
            
            return cookies_list
            
        except Exception as e:
            logger.error(f"Failed to convert Kameleo cookies: {str(e)}")
            return []
    
    def convert_dict_to_kameleo_cookies(self, cookies_dict: List[Dict]) -> List[CookieRequest]:
        """Convert dictionary format cookies to Kameleo CookieRequest objects"""
        kameleo_cookies = []
        
        try:
            for cookie_dict in cookies_dict:
                cookie_request = CookieRequest(
                    domain=cookie_dict.get('domain'),
                    name=cookie_dict.get('name'),
                    path=cookie_dict.get('path'),
                    value=cookie_dict.get('value'),
                    host_only=cookie_dict.get('host_only'),
                    http_only=cookie_dict.get('http_only'),
                    secure=cookie_dict.get('secure'),
                    same_site=cookie_dict.get('same_site'),
                    expiration_date=cookie_dict.get('expiration_date')
                )
                kameleo_cookies.append(cookie_request)
            
            return kameleo_cookies
            
        except Exception as e:
            logger.error(f"Failed to convert dict to Kameleo cookies: {str(e)}")
            return []
    
    def cleanup_expired_cookies(self) -> int:
        """Clean up expired cookies across all proxies and return count of cleaned proxies"""
        try:
            proxies_with_cookies = self.get_all_proxies_with_cookies()
            cleaned_count = 0
            
            for proxy_id in proxies_with_cookies:
                # Loading cookies will automatically filter and update expired ones
                cookies = self.load_cookies(proxy_id)
                if cookies is None:  # All cookies were expired and removed
                    cleaned_count += 1
            
            if cleaned_count > 0:
                logger.info(f"✓ Cleaned expired cookies from {cleaned_count} proxies")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired cookies: {str(e)}")
            return 0
    
    def get_cookie_stats(self) -> Dict:
        """Get comprehensive cookie statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get total proxies with cookies
            cursor.execute('SELECT COUNT(*) FROM cookies')
            total_proxies = cursor.fetchone()[0]
            
            # Get total cookie count across all proxies
            cursor.execute('SELECT cookies_data FROM cookies')
            results = cursor.fetchall()
            
            total_cookies = 0
            for result in results:
                cookies = json.loads(result[0])
                total_cookies += len(cookies)
            
            conn.close()
            
            return {
                'total_proxies_with_cookies': total_proxies,
                'total_cookies': total_cookies,
                'average_cookies_per_proxy': round(total_cookies / total_proxies, 2) if total_proxies > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get cookie stats: {str(e)}")
            return {
                'total_proxies_with_cookies': 0,
                'total_cookies': 0,
                'average_cookies_per_proxy': 0
            }