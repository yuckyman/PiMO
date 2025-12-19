#!/usr/bin/env python3
"""
Display current Last.fm web interface
Simple script to show information about the web-based display
"""

import requests
import json
import sys
from pathlib import Path

def check_web_display(port=8080):
    """Check if web display is running and show current track"""
    try:
        # Check if server is running
        response = requests.get(f"http://localhost:{port}/api/current", timeout=5)
        response.raise_for_status()
        
        data = response.json()
        
        print(f"🌐 Web display is running on http://localhost:{port}")
        print()
        
        if data.get('track'):
            track = data['track']
            print(f"🎵 Currently playing:")
            print(f"   Track: {track['name']}")
            print(f"   Artist: {track['artist']}")
            print(f"   Album: {track['album']}")
            print(f"   Album art: {'Available' if data.get('album_art_url') else 'Not available'}")
        else:
            print("🔇 No track currently playing")
        
        print(f"⏰ Last updated: {data.get('timestamp', 'Unknown')}")
        
        # Check cache directory
        cache_dir = Path("cache")
        if cache_dir.exists():
            art_files = list(cache_dir.glob("*_art.png"))
            print(f"💾 Cached album art: {len(art_files)} files")
        
    except requests.ConnectionError:
        print(f"❌ Web display is not running on port {port}")
        print("Run the daemon first: uv run lastfm_daemon.py")
        return False
    except requests.RequestException as e:
        print(f"❌ Error connecting to web display: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    return True

def main():
    port = 8080
    
    # Check for custom port
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("❌ Invalid port number. Using default 8080.")
    
    if check_web_display(port):
        print()
        print("🎯 To view the display:")
        print(f"  Open your browser: http://localhost:{port}")
        print()
        print("📱 For mobile viewing:")
        print(f"  Find your local IP and use: http://[your-ip]:{port}")
        print()
        print("🔄 The display auto-refreshes every 10 seconds")
        print()
        print("💡 For Raspberry Pi deployment:")
        print("  # Run on Pi")
        print("  uv run lastfm_daemon.py")
        print("  # Access from any device on network")
        print("  http://[pi-ip-address]:8080")

if __name__ == "__main__":
    main() 