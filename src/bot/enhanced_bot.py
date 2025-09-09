#!/usr/bin/env python3
"""
Enhanced Google Search Bot with web interface integration
"""

import time
import random
import logging
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from bot_kameleo import GoogleSearchBot
from src.bot.target_finder import TargetFinder

logger = logging.getLogger(__name__)

class EnhancedGoogleSearchBot(GoogleSearchBot):
    """Enhanced bot class with web interface integration"""
    
    def __init__(self, keyword, target_domain, proxy_list, max_pages=3, google_domain="google.com.tr", device_profile="desktop"):
        super().__init__(keyword, target_domain, proxy_list, device_profile)
        self.max_pages = max_pages
        self.current_proxy_index = 0
        self.google_domain = google_domain
    
    def search_google(self):
        """Enhanced Google search with interaction"""
        try:
            google_url = f"https://www.{self.google_domain}"
            logger.info(f"Navigating to Google search: {google_url}")
            self.driver.get(google_url)
            
            # Wait 15 seconds as requested
            logger.info("⏰ Waiting 15 seconds after opening Google search...")
            
            # Sleep in small increments to allow pause/resume during wait
            from src.utils.bot_status import bot_status
            for _ in range(15):
                if not bot_status['is_running']:
                    return False
                # Wait while paused
                while bot_status['is_paused'] and bot_status['is_running']:
                    time.sleep(0.5)
                if bot_status['is_running']:
                    time.sleep(1)
            
            # Perform scrolling interactions
            logger.info("🎭 Performing initial Google page interactions...")
            self.perform_google_page_interactions()
            
            # Find search box and perform search
            search_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            
            # Clear any existing text and type keyword
            search_box.clear()
            logger.info(f"Typing keyword: {self.keyword}")
            
            # Type with human-like delays
            for char in self.keyword:
                search_box.send_keys(char)
                time.sleep(random.uniform(0.1, 0.3))
            
            time.sleep(1)
            search_box.send_keys(Keys.RETURN)
            
            # Wait for search results
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "search"))
            )
            
            logger.info("✓ Google search completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Google search failed: {str(e)}")
            return False
    
    def perform_google_page_interactions(self):
        """Perform realistic interactions on any Google search page"""
        try:
            logger.info("🎭 Starting Google page interactions...")
            
            # Random initial wait
            time.sleep(random.uniform(1, 3))
            
            # Scroll down gradually
            logger.info("📜 Scrolling down on Google page...")
            for i in range(3):
                scroll_amount = random.randint(200, 400)
                self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                time.sleep(random.uniform(0.5, 1.5))
            
            # Wait and observe
            time.sleep(random.uniform(2, 4))
            
            # Scroll up a bit
            logger.info("📜 Scrolling up on Google page...")
            for i in range(2):
                scroll_amount = random.randint(150, 300)
                self.driver.execute_script(f"window.scrollBy(0, -{scroll_amount});")
                time.sleep(random.uniform(0.5, 1.5))
            
            # Hover over some elements randomly
            self.hover_google_elements()
            
            logger.info("✅ Completed Google page interactions")
            
        except Exception as e:
            logger.error(f"Error during Google page interactions: {str(e)}")
    
    def hover_google_elements(self):
        """Hover over random elements on Google search page"""
        try:
            # Common Google search elements to hover over
            hover_selectors = [
                'h3', 'a', '.g', '.tF2Cxc', '.yuRUbf', 
                '.VwiC3b', '.LC20lb', '.kno-ecr-pt'
            ]
            
            actions = ActionChains(self.driver)
            hovered_count = 0
            
            for selector in hover_selectors:
                if hovered_count >= 3:  # Limit to 3 hovers
                    break
                    
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    visible_elements = [el for el in elements[:5] if el.is_displayed()]
                    
                    if visible_elements:
                        element = random.choice(visible_elements)
                        
                        # Scroll element into view
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                        time.sleep(0.5)
                        
                        # Hover over element
                        actions.move_to_element(element).perform()
                        time.sleep(random.uniform(1, 2))
                        hovered_count += 1
                        
                        logger.info(f"🖱️ Hovered over Google element: {selector}")
                        
                except Exception:
                    continue
            
        except Exception as e:
            logger.error(f"Error hovering Google elements: {str(e)}") 
   
    def find_and_visit_target_with_tracking(self):
        """Find target domain with page and position tracking"""
        return TargetFinder.find_and_visit_target_with_tracking(self)