#!/usr/bin/env python3
"""
Sound Notification System for SEO Bot
"""

import logging
import platform
import subprocess
import os

logger = logging.getLogger(__name__)

class SoundNotifier:
    """Cross-platform sound notification system"""
    
    @staticmethod
    def get_notification_file_path():
        """Get the path to the notification.mp3 file"""
        # Get the project root directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        notification_path = os.path.join(project_root, "assets", "notification.mp3")
        return notification_path
    
    @staticmethod
    def play_custom_notification():
        """Play the custom notification.mp3 file"""
        try:
            notification_path = SoundNotifier.get_notification_file_path()
            
            if not os.path.exists(notification_path):
                logger.warning(f"Notification file not found: {notification_path}")
                return False
            
            system = platform.system().lower()
            
            if system == "darwin":  # macOS
                # Use afplay for MP3 files on macOS
                result = subprocess.run(["afplay", notification_path], 
                                      check=False, capture_output=True, timeout=5)
                if result.returncode == 0:
                    logger.info("🔊 Played custom notification.mp3 (macOS)")
                    return True
                
            elif system == "windows":  # Windows
                # Use Windows Media Player or built-in sound
                try:
                    import winsound
                    winsound.PlaySound(notification_path, winsound.SND_FILENAME)
                    logger.info("🔊 Played custom notification.mp3 (Windows)")
                    return True
                except:
                    # Fallback to system command
                    result = subprocess.run(["powershell", "-c", f"(New-Object Media.SoundPlayer '{notification_path}').PlaySync()"], 
                                          check=False, capture_output=True, timeout=5)
                    if result.returncode == 0:
                        logger.info("🔊 Played custom notification.mp3 (Windows PowerShell)")
                        return True
                
            elif system == "linux":  # Linux
                # Try different Linux audio players
                players = [
                    ["paplay", notification_path],  # PulseAudio
                    ["aplay", notification_path],   # ALSA
                    ["mpg123", notification_path],  # mpg123
                    ["ffplay", "-nodisp", "-autoexit", notification_path],  # ffmpeg
                    ["cvlc", "--play-and-exit", notification_path]  # VLC
                ]
                
                for player_cmd in players:
                    try:
                        result = subprocess.run(player_cmd, check=False, capture_output=True, timeout=5)
                        if result.returncode == 0:
                            logger.info(f"🔊 Played custom notification.mp3 (Linux - {player_cmd[0]})")
                            return True
                    except:
                        continue
            
            return False
            
        except Exception as e:
            logger.debug(f"Custom notification failed: {str(e)}")
            return False
    
    @staticmethod
    def play_success_sound():
        """Play success notification sound when target is found"""
        try:
            system = platform.system().lower()
            
            if system == "darwin":  # macOS
                # Use built-in macOS sound
                subprocess.run(["afplay", "/System/Library/Sounds/Glass.aiff"], 
                             check=False, capture_output=True)
                logger.info("🔊 Played success sound (macOS)")
                
            elif system == "windows":  # Windows
                # Use built-in Windows sound
                import winsound
                winsound.MessageBeep(winsound.MB_OK)
                logger.info("🔊 Played success sound (Windows)")
                
            elif system == "linux":  # Linux
                # Try different Linux sound methods
                try:
                    # Try paplay (PulseAudio)
                    subprocess.run(["paplay", "/usr/share/sounds/alsa/Front_Left.wav"], 
                                 check=False, capture_output=True, timeout=2)
                    logger.info("🔊 Played success sound (Linux - paplay)")
                except:
                    try:
                        # Try aplay (ALSA)
                        subprocess.run(["aplay", "/usr/share/sounds/alsa/Front_Left.wav"], 
                                     check=False, capture_output=True, timeout=2)
                        logger.info("🔊 Played success sound (Linux - aplay)")
                    except:
                        try:
                            # Try system beep
                            subprocess.run(["beep"], check=False, capture_output=True, timeout=1)
                            logger.info("🔊 Played system beep (Linux)")
                        except:
                            logger.info("🔊 Sound notification attempted (Linux - no audio system found)")
            else:
                logger.info("🔊 Sound notification not supported on this platform")
                
        except Exception as e:
            logger.debug(f"Sound notification failed: {str(e)}")
    
    @staticmethod
    def play_notification_beep():
        """Play a simple beep notification"""
        try:
            system = platform.system().lower()
            
            if system == "darwin":  # macOS
                # Use system beep
                subprocess.run(["osascript", "-e", "beep"], 
                             check=False, capture_output=True)
                logger.info("🔊 Played notification beep (macOS)")
                
            elif system == "windows":  # Windows
                import winsound
                winsound.Beep(800, 300)  # 800Hz for 300ms
                logger.info("🔊 Played notification beep (Windows)")
                
            elif system == "linux":  # Linux
                try:
                    subprocess.run(["beep", "-f", "800", "-l", "300"], 
                                 check=False, capture_output=True, timeout=1)
                    logger.info("🔊 Played notification beep (Linux)")
                except:
                    # Fallback to print bell character
                    print("\a", end="", flush=True)
                    logger.info("🔊 Played terminal bell (Linux)")
            else:
                print("\a", end="", flush=True)  # Terminal bell
                logger.info("🔊 Played terminal bell")
                
        except Exception as e:
            logger.debug(f"Beep notification failed: {str(e)}")
    
    @staticmethod
    def play_target_found_notification():
        """Play notification when target domain is found"""
        try:
            logger.info("🎉 TARGET FOUND! Playing notification sound...")
            
            # Try custom notification.mp3 first
            if SoundNotifier.play_custom_notification():
                return
            
            # Fallback to system sounds
            try:
                SoundNotifier.play_success_sound()
            except:
                SoundNotifier.play_notification_beep()
                
        except Exception as e:
            logger.debug(f"Target found notification failed: {str(e)}")
            # Ultimate fallback - terminal bell
            try:
                print("\a\a\a", end="", flush=True)  # Triple beep
                logger.info("🔊 Played terminal bell notification")
            except:
                pass