#!/usr/bin/env python3
"""
Website Interactor - Handles realistic human-like interactions on target websites
"""

import time
import random
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from src.utils.bot_status import bot_status

logger = logging.getLogger(__name__)

class WebsiteInteractor:
    """Handles realistic website interactions"""
    
    @staticmethod
    def realistic_website_interaction(bot_instance):
        """Perform realistic human-like interactions for 1 minute"""
        try:
            start_time = time.time()
            total_duration = 60  # 1 minute
            
            logger.info("🎭 Starting realistic website interaction (60 seconds)")
            
            # Wait for page to fully load with pause check
            for _ in range(3):
                if not bot_status['is_running']:
                    return
                while bot_status['is_paused'] and bot_status['is_running']:
                    time.sleep(0.5)
                if bot_status['is_running']:
                    time.sleep(1)
            
            # Check if we're actually on the target website
            current_url = bot_instance.driver.current_url
            if bot_instance.target_domain not in current_url:
                logger.warning(f"Not on target domain. Current URL: {current_url}")
                # Still perform some interaction for realism
                total_duration = 30  # Reduce time if not on target
            
            # Phase 1: Initial exploration (0-15 seconds)
            logger.info("Phase 1: Initial page exploration...")
            
            # Check pause before each action
            while bot_status['is_paused'] and bot_status['is_running']:
                time.sleep(0.5)
            if not bot_status['is_running']:
                return
                
            WebsiteInteractor.smooth_scroll_down(bot_instance, 600)
            
            # Pause-aware sleep
            for _ in range(2):
                if not bot_status['is_running']:
                    return
                while bot_status['is_paused'] and bot_status['is_running']:
                    time.sleep(0.5)
                if bot_status['is_running']:
                    time.sleep(1)
            
            while bot_status['is_paused'] and bot_status['is_running']:
                time.sleep(0.5)
            if not bot_status['is_running']:
                return
                
            WebsiteInteractor.hover_random_elements(bot_instance, 2)
            
            # Continue with other phases...
            WebsiteInteractor._phase_2_navigation(bot_instance, start_time)
            WebsiteInteractor._phase_3_content(bot_instance, start_time)
            WebsiteInteractor._phase_4_final(bot_instance, start_time, total_duration)
            
            # Fill remaining time with gentle scrolling
            WebsiteInteractor._final_scrolling_loop(bot_instance, start_time, total_duration)
            
            total_time = time.time() - start_time
            logger.info(f"✅ Completed realistic interaction session ({total_time:.1f} seconds)")
            
        except Exception as e:
            logger.error(f"Error during realistic website interaction: {str(e)}")
            # Fallback to simple behavior
            logger.info("Falling back to simple scrolling...")
            try:
                bot_instance.human_like_scroll()
                time.sleep(30)  # At least spend some time on the site
            except:
                pass
    
    @staticmethod
    def _phase_2_navigation(bot_instance, start_time):
        """Phase 2: Header navigation exploration (15-35 seconds)"""
        elapsed = time.time() - start_time
        if elapsed < 35:
            while bot_status['is_paused'] and bot_status['is_running']:
                time.sleep(0.5)
            if not bot_status['is_running']:
                return
                
            logger.info("Phase 2: Exploring navigation...")
            WebsiteInteractor.click_header_navigation(bot_instance)
    
    @staticmethod
    def _phase_3_content(bot_instance, start_time):
        """Phase 3: Content exploration (35-50 seconds)"""
        elapsed = time.time() - start_time
        if elapsed < 50:
            while bot_status['is_paused'] and bot_status['is_running']:
                time.sleep(0.5)
            if not bot_status['is_running']:
                return
                
            logger.info("Phase 3: Content exploration...")
            
            # Scroll through content
            WebsiteInteractor.smooth_scroll_down(bot_instance, 800)
            
            # Pause-aware sleep and interactions
            for _ in range(2):
                if not bot_status['is_running']:
                    return
                while bot_status['is_paused'] and bot_status['is_running']:
                    time.sleep(0.5)
                if bot_status['is_running']:
                    time.sleep(1)
    
    @staticmethod
    def _phase_4_final(bot_instance, start_time, total_duration):
        """Phase 4: Final exploration (50-60 seconds)"""
        elapsed = time.time() - start_time
        remaining_time = total_duration - elapsed
        
        if remaining_time > 5:
            while bot_status['is_paused'] and bot_status['is_running']:
                time.sleep(0.5)
            if not bot_status['is_running']:
                return
                
            logger.info("Phase 4: Final exploration...")
            # Add final exploration logic here
    
    @staticmethod
    def _final_scrolling_loop(bot_instance, start_time, total_duration):
        """Fill remaining time with gentle scrolling"""
        while time.time() - start_time < total_duration and bot_status['is_running']:
            # Check for pause before each action
            while bot_status['is_paused'] and bot_status['is_running']:
                time.sleep(0.5)
            if not bot_status['is_running']:
                break
                
            remaining = total_duration - (time.time() - start_time)
            if remaining > 2:
                if random.choice([True, False]):
                    WebsiteInteractor.smooth_scroll_down(bot_instance, random.randint(100, 300))
                else:
                    WebsiteInteractor.smooth_scroll_up(bot_instance, random.randint(100, 200))
                
                # Pause-aware sleep
                if not bot_status['is_running']:
                    break
                while bot_status['is_paused'] and bot_status['is_running']:
                    time.sleep(0.5)
                if bot_status['is_running']:
                    time.sleep(1)
            else:
                # Final sleep with pause check
                sleep_time = remaining
                while sleep_time > 0 and bot_status['is_running']:
                    while bot_status['is_paused'] and bot_status['is_running']:
                        time.sleep(0.5)
                    if bot_status['is_running']:
                        sleep_chunk = min(0.5, sleep_time)
                        time.sleep(sleep_chunk)
                        sleep_time -= sleep_chunk
                    else:
                        break
                break
    
    @staticmethod
    def smooth_scroll_down(bot_instance, pixels=None):
        """Perform smooth scrolling down"""
        try:
            if pixels is None:
                pixels = random.randint(300, 800)
            
            # Smooth scroll in small increments
            scroll_steps = random.randint(8, 15)
            step_size = pixels // scroll_steps
            
            for i in range(scroll_steps):
                bot_instance.driver.execute_script(f"window.scrollBy(0, {step_size});")
                time.sleep(random.uniform(0.05, 0.15))
            
            logger.info(f"Smooth scrolled down {pixels} pixels")
            
        except Exception as e:
            logger.error(f"Error during smooth scroll down: {str(e)}")
    
    @staticmethod
    def smooth_scroll_up(bot_instance, pixels=None):
        """Perform smooth scrolling up"""
        try:
            if pixels is None:
                pixels = random.randint(200, 600)
            
            # Smooth scroll in small increments
            scroll_steps = random.randint(8, 15)
            step_size = pixels // scroll_steps
            
            for i in range(scroll_steps):
                bot_instance.driver.execute_script(f"window.scrollBy(0, -{step_size});")
                time.sleep(random.uniform(0.05, 0.15))
            
            logger.info(f"Smooth scrolled up {pixels} pixels")
            
        except Exception as e:
            logger.error(f"Error during smooth scroll up: {str(e)}")
    
    @staticmethod
    def hover_random_elements(bot_instance, duration=2):
        """Hover over random elements on the page"""
        try:
            # Common selectors for hoverable elements
            hover_selectors = [
                'a', 'button', 'h1', 'h2', 'h3', 'img', 
                '.menu', '.nav', '.header', '.link', 
                '[role="button"]', '[role="link"]'
            ]
            
            actions = ActionChains(bot_instance.driver)
            hovered_count = 0
            
            for selector in hover_selectors:
                try:
                    elements = bot_instance.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements and hovered_count < 3:  # Limit to 3 hovers
                        # Select a random visible element
                        visible_elements = [el for el in elements[:10] if el.is_displayed()]
                        if visible_elements:
                            element = random.choice(visible_elements)
                            
                            # Scroll element into view
                            bot_instance.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                            time.sleep(0.5)
                            
                            # Hover over element
                            actions.move_to_element(element).perform()
                            time.sleep(1)
                            hovered_count += 1
                            
                            logger.info(f"Hovered over {selector} element")
                            
                except Exception:
                    continue
            
            if hovered_count > 0:
                logger.info(f"Hovered over {hovered_count} elements")
            
        except Exception as e:
            logger.error(f"Error during hovering: {str(e)}")
    
    @staticmethod
    def click_header_navigation(bot_instance):
        """Click on header navigation elements and explore pages"""
        try:
            # Common selectors for header navigation
            nav_selectors = [
                'header a', 'nav a', '.header a', '.navigation a',
                '.menu a', '.navbar a', '.top-menu a', '.main-menu a',
                'ul.menu a', '.nav-item a', '.menu-item a'
            ]
            
            clicked_links = []
            original_url = bot_instance.driver.current_url
            
            for selector in nav_selectors:
                try:
                    nav_links = bot_instance.driver.find_elements(By.CSS_SELECTOR, selector)
                    if nav_links:
                        # Filter for visible links that aren't external
                        valid_links = []
                        for link in nav_links[:8]:  # Check first 8 links
                            try:
                                if (link.is_displayed() and 
                                    link.get_attribute('href') and
                                    not any(ext in link.get_attribute('href').lower() 
                                           for ext in ['mailto:', 'tel:', 'javascript:', '#']) and
                                    bot_instance.target_domain in link.get_attribute('href')):
                                    valid_links.append(link)
                            except:
                                continue
                        
                        if valid_links and len(clicked_links) < 2:  # Limit to 2 navigation clicks
                            link = random.choice(valid_links)
                            link_text = link.text.strip()[:30] or "Navigation Link"
                            
                            try:
                                # Scroll to link and click
                                bot_instance.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", link)
                                time.sleep(1)
                                
                                # Human-like click
                                actions = ActionChains(bot_instance.driver)
                                actions.move_to_element(link).pause(0.5).click().perform()
                                
                                logger.info(f"Clicked navigation link: {link_text}")
                                clicked_links.append(link_text)
                                
                                # Wait for page to load
                                time.sleep(3)
                                
                                # Check if we're on a new page
                                new_url = bot_instance.driver.current_url
                                if new_url != original_url:
                                    logger.info(f"Navigated to new page: {new_url}")
                                    
                                    # Explore the new page briefly
                                    WebsiteInteractor.explore_page_briefly(bot_instance)
                                    
                                    # Go back to original page
                                    bot_instance.driver.back()
                                    time.sleep(2)
                                    logger.info("Returned to previous page")
                                
                                break  # Exit selector loop after successful click
                                
                            except Exception as e:
                                logger.warning(f"Failed to click navigation link: {str(e)}")
                                continue
                        
                except Exception:
                    continue
            
            if clicked_links:
                logger.info(f"Successfully explored {len(clicked_links)} navigation pages")
            else:
                logger.info("No suitable navigation links found")
                
        except Exception as e:
            logger.error(f"Error during header navigation: {str(e)}")
    
    @staticmethod
    def explore_page_briefly(bot_instance):
        """Briefly explore a page with scrolling and hovering"""
        try:
            # Quick scroll down
            WebsiteInteractor.smooth_scroll_down(bot_instance, 400)
            time.sleep(1)
            
            # Hover over an element
            WebsiteInteractor.hover_random_elements(bot_instance, 1)
            
            # Quick scroll up
            WebsiteInteractor.smooth_scroll_up(bot_instance, 200)
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Error during brief page exploration: {str(e)}")