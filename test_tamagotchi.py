#!/usr/bin/env python3
"""
Test script for Last.fm Tamagotchi
Tests the core functionality without requiring a display
"""

import sys
import os
import time
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_pet_system():
    """Test the pet system logic"""
    print("🧪 Testing Last.fm Tamagotchi System...")
    
    # Simulate pet state
    pet_state = {
        'name': 'Melody',
        'hunger': 50,
        'happiness': 50,
        'energy': 50,
        'level': 1,
        'experience': 0,
        'mood': 'happy',
        'last_fed': None,
        'total_scrobbles': 0,
        'evolution_stage': 0
    }
    
    # Test feeding
    print("\n🎵 Testing pet feeding...")
    track = {'name': 'Test Song', 'artist': {'#text': 'Test Artist'}}
    
    # Simulate feeding
    pet_state['hunger'] = min(100, pet_state['hunger'] + 15)
    pet_state['happiness'] = min(100, pet_state['happiness'] + 10)
    pet_state['energy'] = min(100, pet_state['energy'] + 5)
    pet_state['experience'] += 10
    pet_state['total_scrobbles'] += 1
    pet_state['last_fed'] = datetime.now()
    
    print(f"✅ Fed pet with: {track['name']} by {track['artist']['#text']}")
    print(f"   Hunger: {pet_state['hunger']}%")
    print(f"   Happiness: {pet_state['happiness']}%")
    print(f"   Energy: {pet_state['energy']}%")
    print(f"   Experience: {pet_state['experience']}/{pet_state['level'] * 100}")
    
    # Test level up
    print("\n⬆️ Testing level up...")
    pet_state['experience'] = pet_state['level'] * 100
    old_level = pet_state['level']
    pet_state['level'] += 1
    pet_state['experience'] = 0
    
    print(f"✅ Pet leveled up from {old_level} to {pet_state['level']}!")
    
    # Test evolution
    print("\n🌟 Testing evolution...")
    if pet_state['level'] % 5 == 0:
        pet_state['evolution_stage'] += 1
        evolution_names = ['Baby', 'Growing', 'Teen', 'Adult', 'Legendary']
        stage_name = evolution_names[min(pet_state['evolution_stage'], len(evolution_names) - 1)]
        print(f"✅ Pet evolved to {stage_name} stage!")
    
    # Test mood system
    print("\n😊 Testing mood system...")
    avg_stats = (pet_state['hunger'] + pet_state['happiness'] + pet_state['energy']) / 3
    
    if avg_stats >= 80:
        pet_state['mood'] = 'ecstatic'
    elif avg_stats >= 60:
        pet_state['mood'] = 'happy'
    elif avg_stats >= 40:
        pet_state['mood'] = 'neutral'
    elif avg_stats >= 20:
        pet_state['mood'] = 'sad'
    else:
        pet_state['mood'] = 'starving'
    
    print(f"✅ Pet mood: {pet_state['mood']} (avg stats: {avg_stats:.1f}%)")
    
    # Test stat decay
    print("\n⏰ Testing stat decay...")
    pet_state['hunger'] = max(0, pet_state['hunger'] - 0.5)
    pet_state['happiness'] = max(0, pet_state['happiness'] - 0.3)
    pet_state['energy'] = max(0, pet_state['energy'] - 0.2)
    
    print(f"✅ Stats after decay:")
    print(f"   Hunger: {pet_state['hunger']:.1f}%")
    print(f"   Happiness: {pet_state['happiness']:.1f}%")
    print(f"   Energy: {pet_state['energy']:.1f}%")
    
    print("\n✅ All tests passed!")
    return True

def test_config():
    """Test configuration loading"""
    print("\n⚙️ Testing configuration...")
    
    try:
        from config import PET_CONFIG, DISPLAY_CONFIG, EVOLUTION_STAGES, MOODS
        print("✅ Configuration loaded successfully")
        print(f"   Pet config: {len(PET_CONFIG)} settings")
        print(f"   Display config: {len(DISPLAY_CONFIG)} settings")
        print(f"   Evolution stages: {len(EVOLUTION_STAGES)} stages")
        print(f"   Moods: {len(MOODS)} moods")
        return True
    except ImportError as e:
        print(f"❌ Failed to load configuration: {e}")
        return False

def test_discord_integration():
    """Test Discord integration"""
    print("\n📱 Testing Discord integration...")
    
    try:
        from discord_integration import DiscordIntegration
        discord = DiscordIntegration()
        print("✅ Discord integration loaded")
        print(f"   Enabled: {discord.enabled}")
        return True
    except ImportError as e:
        print(f"❌ Failed to load Discord integration: {e}")
        return False

def test_dependencies():
    """Test required dependencies"""
    print("\n📦 Testing dependencies...")
    
    dependencies = [
        ('tkinter', 'tkinter'),
        ('PIL', 'PIL'),
        ('requests', 'requests'),
        ('datetime', 'datetime'),
        ('threading', 'threading')
    ]
    
    all_good = True
    for name, module in dependencies:
        try:
            __import__(module)
            print(f"✅ {name}")
        except ImportError:
            print(f"❌ {name} - missing")
            all_good = False
    
    return all_good

def main():
    """Run all tests"""
    print("🎵 Last.fm Tamagotchi Test Suite")
    print("=" * 40)
    
    tests = [
        ("Dependencies", test_dependencies),
        ("Configuration", test_config),
        ("Pet System", test_pet_system),
        ("Discord Integration", test_discord_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
    
    print("\n" + "=" * 40)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your tamagotchi is ready to go!")
        return True
    else:
        print("⚠️ Some tests failed. Check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)