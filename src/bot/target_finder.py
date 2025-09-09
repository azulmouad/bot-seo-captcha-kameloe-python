#!/usr/bin/env python3
"""
Target Finder - Handles finding and visiting target domains with enhanced interactions
"""

import time
import random
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from src.utils.bot_status import bot_status
from src.utils.sound_notifier import SoundNotifier

logger = logging.getLogger(__name__)

class TargetFinder:
    """Handles finding and visiting target domains"""
    
    @staticmethod
    def find_and_visit_target_with_tracking(bot_instance):
        """Find target domain with page and position tracking and enhanced interactions"""
        try:
            logger.info(f"Looking for domain: {bot_instance.target_domain}")
            
            cumulative_position = 0  # Track total position across all pages
            page_results_count = []  # Track results count per page
            
            for page in range(1, bot_instance.max_pages + 1):
                # Wait while paused before processing each page
                while bot_status['is_paused'] and bot_status['is_running']:
                    time.sleep(1)
                
                if not bot_status['is_running']:
                    return False, page, None
                
                logger.info(f"🔍 Searching on page {page}")
                
                if page > 1:
                    # Navigate to next page
                    try:
                        next_button = bot_instance.driver.find_element(By.ID, "pnnext")
                        
                        # Scroll to next button and hover before clicking
                        bot_instance.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
                        time.sleep(1)
                        
                        # Hover over next button
                        actions = ActionChains(bot_instance.driver)
                        actions.move_to_element(next_button).pause(0.5).perform()
                        time.sleep(1)
                        
                        next_button.click()
                        
                        # Wait for page to load
                        time.sleep(3)
                        logger.info(f"✓ Navigated to page {page}")
                        
                        # Wait 15 seconds and perform interactions on each new page
                        logger.info(f"⏰ Waiting 15 seconds on page {page}...")
                        
                        # Sleep in small increments to allow pause/resume during wait
                        for _ in range(15):
                            if not bot_status['is_running']:
                                return False, page, None
                            # Wait while paused
                            while bot_status['is_paused'] and bot_status['is_running']:
                                time.sleep(0.5)
                            if bot_status['is_running']:
                                time.sleep(1)
                        
                        # Perform interactions on this page
                        logger.info(f"🎭 Performing interactions on page {page}...")
                        bot_instance.perform_google_page_interactions()
                        
                    except Exception as e:
                        logger.warning(f"Could not navigate to page {page}: {str(e)}")
                        break
                
                # Get search results on current page
                search_results = bot_instance.driver.find_elements(By.CSS_SELECTOR, "h3")
                current_page_results = len(search_results)
                page_results_count.append(current_page_results)
                
                logger.info(f"📊 Page {page} has {current_page_results} search results")
                
                for position, result in enumerate(search_results, 1):
                    try:
                        parent_link = result.find_element(By.XPATH, "..")
                        if parent_link.tag_name == 'a':
                            href = parent_link.get_attribute('href')
                            if href and bot_instance.target_domain in href:
                                # Calculate cumulative position across all pages
                                global_position = cumulative_position + position
                                
                                logger.info(f"🎯 Found target domain on page {page}, local position {position}, GLOBAL position {global_position}: {href}")
                                logger.info(f"📈 Position calculation: {' + '.join(map(str, page_results_count[:-1]))} + {position} = {global_position}")
                                
                                # 🔊 PLAY SUCCESS NOTIFICATION SOUND
                                SoundNotifier.play_target_found_notification()
                                
                                # ENHANCED INTERACTION: Hover over target before clicking
                                logger.info("🖱️ Hovering over target link...")
                                
                                # Scroll element into view
                                bot_instance.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", parent_link)
                                time.sleep(2)
                                
                                # Hover over the target link for a realistic duration
                                actions = ActionChains(bot_instance.driver)
                                actions.move_to_element(parent_link).perform()
                                time.sleep(random.uniform(2, 4))  # Hover for 2-4 seconds
                                
                                # Additional hover behavior - move slightly and hover again
                                actions.move_to_element_with_offset(parent_link, 5, 5).perform()
                                time.sleep(random.uniform(1, 2))
                                
                                logger.info("✨ Completed hovering over target link")
                                
                                # Now click the target
                                try:
                                    # Method 1: ActionChains click with pause
                                    actions.move_to_element(parent_link).pause(1).click().perform()
                                    
                                    logger.info("✓ Successfully clicked target link using ActionChains")
                                    time.sleep(3)
                                    
                                except Exception as e1:
                                    logger.warning(f"ActionChains click failed: {str(e1)}")
                                    try:
                                        # Method 2: JavaScript click
                                        bot_instance.driver.execute_script("arguments[0].click();", parent_link)
                                        logger.info("✓ Successfully clicked target link using JavaScript")
                                        time.sleep(3)
                                        
                                    except Exception as e2:
                                        logger.warning(f"JavaScript click failed: {str(e2)}")
                                        try:
                                            # Method 3: Direct navigation
                                            logger.info(f"Direct navigation to: {href}")
                                            bot_instance.driver.get(href)
                                            time.sleep(3)
                                            
                                        except Exception as e3:
                                            logger.error(f"All click methods failed: {str(e3)}")
                                            return True, page, global_position  # Return global position
                                
                                # Check if we successfully navigated to target domain
                                current_url = bot_instance.driver.current_url
                                if bot_instance.target_domain in current_url:
                                    logger.info(f"✓ Successfully navigated to target website: {current_url}")
                                    
                                    # Perform realistic interaction
                                    logger.info("🎭 Starting realistic website interaction (60 seconds)")
                                    from src.bot.website_interactor import WebsiteInteractor
                                    WebsiteInteractor.realistic_website_interaction(bot_instance)
                                    
                                    logger.info("✅ Successfully visited and interacted with target website")
                                    return True, page, global_position  # Return global position
                                else:
                                    logger.warning(f"Navigation may have failed. Current URL: {current_url}")
                                    return True, page, global_position  # Return global position
                                
                    except Exception as e:
                        continue
                
                # Add current page results to cumulative count for next page calculation
                cumulative_position += current_page_results
                logger.info(f"📊 Cumulative results after page {page}: {cumulative_position}")
                logger.info(f"Domain not found on page {page}")
            
            return False, bot_instance.max_pages, None
            
        except Exception as e:
            logger.error(f"Error finding/visiting target: {str(e)}")
            return False, 1, None