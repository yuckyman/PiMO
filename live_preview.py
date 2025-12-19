#!/usr/bin/env python3
"""
Live Preview with Image Viewer
Automatically opens generated images in system viewer
"""

import os
import sys
import time
import subprocess
import platform
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

# Import the daemon class
from lastfm_daemon import LastFmDaemon, load_environment, THEMES

def open_image_viewer(image_path):
    """Open image in system's default viewer"""
    try:
        if platform.system() == "Darwin":  # macOS
            subprocess.run(["open", image_path])
        elif platform.system() == "Windows":
            subprocess.run(["start", image_path], shell=True)
        else:  # Linux
            subprocess.run(["xdg-open", image_path])
        return True
    except Exception as e:
        print(f"❌ Could not open image viewer: {e}")
        return False

def live_preview():
    """Live preview with automatic image viewer"""
    print("🖼️  LIVE PREVIEW MODE")
    print("=" * 40)
    
    # Load environment
    if not load_environment():
        print("❌ Environment not configured. Please set up .env file first.")
        return
    
    # Get credentials from environment
    api_key = os.getenv('LASTFM_API_KEY')
    username = os.getenv('LASTFM_USERNAME')
    
    if not api_key or not username:
        print("❌ Missing environment variables: LASTFM_API_KEY and LASTFM_USERNAME")
        return
    
    # Initialize daemon
    daemon = LastFmDaemon(
        api_key=api_key,
        username=username,
        update_interval=30,
        upscale=2,
        theme='default'
    )
    
    # Get current track
    track_info = daemon.get_recent_tracks(limit=1)
    if not track_info:
        print("❌ No tracks found")
        return
    album_art = daemon.download_album_art(track_info)
    
    print(f"🎵 Current track: {track_info.get('name', 'Unknown')}")
    print(f"👤 Artist: {track_info.get('artist', {}).get('#text', 'Unknown')}")
    print(f"💿 Album: {track_info.get('album', {}).get('#text', 'Unknown')}")
    
    # Create initial display
    print("\n📸 Creating initial display...")
    create_live_display(track_info, album_art)
    
    # Open in image viewer
    if open_image_viewer('current_display.png'):
        print("🖼️  Image opened in viewer!")
        print("💡 Close the image viewer to continue tweaking")
    
    # Interactive tweaking
    print("\n🔧 LIVE TWEAKING:")
    print("Commands: u<scale> t<theme> a<ratio> s<spacing> r(refresh) q(quit)")
    
    while True:
        try:
            cmd = input("\n🎛️  Command: ").strip().lower()
            
            if cmd.startswith('u'):
                try:
                    upscale = int(cmd[1:])
                    if 1 <= upscale <= 4:
                        print(f"✅ Creating {upscale}x display...")
                        create_live_display(track_info, album_art, upscale=upscale)
                        open_image_viewer('current_display.png')
                    else:
                        print("❌ Upscale must be 1-4")
                except:
                    print("❌ Invalid upscale value")
                    
            elif cmd.startswith('t'):
                theme = cmd[1:]
                if theme in THEMES:
                    print(f"✅ Creating {theme} theme...")
                    create_live_display(track_info, album_art, theme=theme)
                    open_image_viewer('current_display.png')
                else:
                    print(f"❌ Theme must be one of: {list(THEMES.keys())}")
                    
            elif cmd.startswith('a'):
                try:
                    ratio = float(cmd[1:])
                    if 0.3 <= ratio <= 0.7:
                        print(f"✅ Creating display with {ratio} album ratio...")
                        create_live_display(track_info, album_art, album_ratio=ratio)
                        open_image_viewer('current_display.png')
                    else:
                        print("❌ Ratio must be 0.3-0.7")
                except:
                    print("❌ Invalid ratio value")
                    
            elif cmd.startswith('s'):
                try:
                    spacing = int(cmd[1:])
                    if 15 <= spacing <= 35:
                        print(f"✅ Creating display with {spacing} spacing...")
                        create_live_display(track_info, album_art, line_spacing=spacing)
                        open_image_viewer('current_display.png')
                    else:
                        print("❌ Spacing must be 15-35")
                except:
                    print("❌ Invalid spacing value")
                    
            elif cmd == 'r':
                print("🔄 Refreshing display...")
                create_live_display(track_info, album_art)
                open_image_viewer('current_display.png')
                
            elif cmd == 'q':
                print("👋 Goodbye!")
                break
                
            else:
                print("❓ Unknown command. Use: u<scale> t<theme> a<ratio> s<spacing> r q")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def create_live_display(track_info, album_art=None, **kwargs):
    """Create display with live preview parameters"""
    # Default parameters
    params = {
        'upscale': 2,
        'theme': 'default',
        'album_ratio': 0.45,
        'line_spacing': 25
    }
    params.update(kwargs)
    
    # Base resolution
    base_width, base_height = 320, 240
    width = base_width * params['upscale']
    height = base_height * params['upscale']
    
    # Create image
    img = Image.new('RGB', (width, height), color=THEMES[params['theme']]['background'])
    draw = ImageDraw.Draw(img)
    
    # Scale fonts
    try:
        title_font = ImageFont.truetype(THEMES[params['theme']]['fonts']['title'], 20 * params['upscale'])
        subtitle_font = ImageFont.truetype(THEMES[params['theme']]['fonts']['subtitle'], 16 * params['upscale'])
        small_font = ImageFont.truetype(THEMES[params['theme']]['fonts']['small'], 12 * params['upscale'])
    except:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # Custom container layout
    album_container_width = int(width * params['album_ratio'])
    text_container_width = width - album_container_width - (30 * params['upscale'])
    text_x = 10 * params['upscale'] + album_container_width + (10 * params['upscale'])
    text_y = 30 * params['upscale']
    
    if album_art:
        # Album art container
        album_size = min(album_container_width - (20 * params['upscale']), height - (20 * params['upscale']))
        album_art_resized = album_art.resize((album_size, album_size), Image.Resampling.LANCZOS)
        album_center_x = 10 * params['upscale'] + (album_container_width - album_size) // 2
        album_center_y = (height - album_size) // 2
        img.paste(album_art_resized, (album_center_x, album_center_y))
    
    # Text rendering
    title = "NOW PLAYING"
    bbox = draw.textbbox((0, 0), title, title_font)
    title_width = bbox[2] - bbox[0]
    title_x = text_x + text_container_width - title_width
    draw.text((title_x, text_y), title, fill=THEMES[params['theme']]['title_color'], font=title_font)
    
    # Track info
    track_name = track_info.get('name', 'Unknown Track')
    artist_name = track_info.get('artist', {}).get('#text', 'Unknown Artist')
    album_name = track_info.get('album', {}).get('#text', 'Unknown Album')
    
    track_y = text_y + (50 * params['upscale'])
    
    # Use daemon's wrap_text method
    daemon = LastFmDaemon(api_key="dummy", username="dummy")  # Just for wrap_text
    track_lines = daemon.wrap_text(track_name, subtitle_font, text_container_width - (10 * params['upscale']))
    for i, line in enumerate(track_lines):
        bbox = draw.textbbox((0, 0), line, subtitle_font)
        line_width = bbox[2] - bbox[0]
        line_x = text_x + text_container_width - line_width
        line_y = track_y + (i * params['line_spacing'] * params['upscale'])
        draw.text((line_x, line_y), line, fill=THEMES[params['theme']]['track_color'], font=subtitle_font)
    
    # Save the display
    img.save('current_display.png')
    print(f"📸 Saved: {width}x{height} ({os.path.getsize('current_display.png')} bytes)")

if __name__ == "__main__":
    live_preview() 