#!/usr/bin/env python3
"""
Test Sound Notification System
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.sound_notifier import SoundNotifier
import time
import os

def test_sound_notifications():
    """Test different sound notifications"""
    print("🔊 Testing Sound Notification System")
    print("=" * 40)
    
    # Check if notification file exists
    notification_path = SoundNotifier.get_notification_file_path()
    print(f"\n📁 Notification file path: {notification_path}")
    print(f"📁 File exists: {'✅ Yes' if os.path.exists(notification_path) else '❌ No'}")
    
    print("\n1. Testing custom notification.mp3...")
    if SoundNotifier.play_custom_notification():
        print("   ✅ Custom notification played successfully!")
    else:
        print("   ❌ Custom notification failed")
    time.sleep(3)
    
    print("\n2. Testing target found notification (with fallbacks)...")
    SoundNotifier.play_target_found_notification()
    time.sleep(3)
    
    print("\n3. Testing completion beep...")
    SoundNotifier.play_notification_beep()
    time.sleep(2)
    
    print("\n4. Testing system success sound...")
    SoundNotifier.play_success_sound()
    time.sleep(2)
    
    print("\n✅ Sound test completed!")
    print("If you heard sounds, the notification system is working!")
    print(f"Custom notification file: {notification_path}")

if __name__ == "__main__":
    test_sound_notifications()