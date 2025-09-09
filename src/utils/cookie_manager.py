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
            conn.close()
            
            logger.info(f"✓ Saved {len(cookies)} cookies for proxy: {proxy_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save cookies for proxy {proxy_id}: {str(e)}")
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
                logger.info(f"✓ Loaded {len(cookies)} cookies for proxy: {proxy_id}")
                return cookies
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