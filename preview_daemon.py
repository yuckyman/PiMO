#!/usr/bin/env python3
"""
Interactive Last.fm Display Preview
Shows the display in real-time and allows live parameter tweaking
"""

import os
import sys
import time
import signal
import threading
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

# Import the daemon class
from lastfm_daemon import LastFmDaemon, load_environment, THEMES

class InteractivePreview:
    def __init__(self):
        self.running = True
        self.current_params = {
            'upscale': 2,
            'theme': 'default',
            'album_container_ratio': 0.45,
            'text_margin': 10,
            'line_spacing': 25
        }
        self.daemon = None
        self.setup_daemon()
        
    def setup_daemon(self):
        """Initialize the Last.fm daemon"""
        if not load_environment():
            print("❌ Environment not configured. Please set up .env file first.")
            return False
        
        # Get credentials from environment
        api_key = os.getenv('LASTFM_API_KEY')
        username = os.getenv('LASTFM_USERNAME')
        
        if not api_key or not username:
            print("❌ Missing environment variables: LASTFM_API_KEY and LASTFM_USERNAME")
            return False
            
        self.daemon = LastFmDaemon(
            api_key=api_key,
            username=username,
            update_interval=30,
            upscale=self.current_params['upscale'],
            theme=self.current_params['theme']
        )
        return True
        
    def show_help(self):
        """Display interactive commands"""
        print("\n🎛️  INTERACTIVE CONTROLS:")
        print("  u <number>     - Set upscale (1-4)")
        print("  t <theme>      - Change theme (default/dark/stats)")
        print("  a <ratio>      - Album container ratio (0.3-0.7)")
        print("  m <margin>     - Text margin (5-20)")
        print("  s <spacing>    - Line spacing (15-35)")
        print("  r              - Refresh current track")
        print("  h              - Show this help")
        print("  q              - Quit")
        print("  ?              - Show current parameters")
        
    def show_params(self):
        """Display current parameters"""
        print(f"\n📊 CURRENT PARAMETERS:")
        print(f"  Upscale: {self.current_params['upscale']}x")
        print(f"  Theme: {self.current_params['theme']}")
        print(f"  Album ratio: {self.current_params['album_container_ratio']}")
        print(f"  Text margin: {self.current_params['text_margin']}")
        print(f"  Line spacing: {self.current_params['line_spacing']}")
        
    def update_display(self):
        """Force update the current display"""
        if not self.daemon:
            return
            
        try:
            # Get recent track
            track_info = self.daemon.get_recent_tracks(limit=1)
            if track_info:
                print(f"\n🔄 Refreshing display for: {track_info.get('name', 'Unknown')}")
                
                # Download album art
                album_art = self.daemon.download_album_art(track_info)
                
                # Create display with current parameters
                self.create_custom_display(track_info, album_art)
                
                # Show file info
                if os.path.exists('current_display.png'):
                    img = Image.open('current_display.png')
                    print(f"📸 Display updated: {img.size[0]}x{img.size[1]}")
                    
        except Exception as e:
            print(f"❌ Error updating display: {e}")
    
    def create_custom_display(self, track_info, album_art=None):
        """Create display with custom parameters"""
        # Base resolution
        base_width, base_height = 320, 240
        width = base_width * self.current_params['upscale']
        height = base_height * self.current_params['upscale']
        
        # Create image
        img = Image.new('RGB', (width, height), color=THEMES[self.current_params['theme']]['background'])
        draw = ImageDraw.Draw(img)
        
        # Scale fonts
        try:
            title_font = ImageFont.truetype(THEMES[self.current_params['theme']]['fonts']['title'], 20 * self.current_params['upscale'])
            subtitle_font = ImageFont.truetype(THEMES[self.current_params['theme']]['fonts']['subtitle'], 16 * self.current_params['upscale'])
            small_font = ImageFont.truetype(THEMES[self.current_params['theme']]['fonts']['small'], 12 * self.current_params['upscale'])
        except:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Custom container layout
        album_container_width = int(width * self.current_params['album_container_ratio'])
        text_container_width = width - album_container_width - (30 * self.current_params['upscale'])
        text_x = 10 * self.current_params['upscale'] + album_container_width + (10 * self.current_params['upscale'])
        text_y = 30 * self.current_params['upscale']
        
        if album_art:
            # Album art container
            album_size = min(album_container_width - (20 * self.current_params['upscale']), height - (20 * self.current_params['upscale']))
            album_art_resized = album_art.resize((album_size, album_size), Image.Resampling.LANCZOS)
            album_center_x = 10 * self.current_params['upscale'] + (album_container_width - album_size) // 2
            album_center_y = (height - album_size) // 2
            img.paste(album_art_resized, (album_center_x, album_center_y))
        
        # Text rendering with custom parameters
        title = "NOW PLAYING"
        bbox = draw.textbbox((0, 0), title, title_font)
        title_width = bbox[2] - bbox[0]
        title_x = text_x + text_container_width - title_width
        draw.text((title_x, text_y), title, fill=THEMES[self.current_params['theme']]['title_color'], font=title_font)
        
        # Track info with custom spacing
        track_name = track_info.get('name', 'Unknown Track')
        artist_name = track_info.get('artist', {}).get('#text', 'Unknown Artist')
        album_name = track_info.get('album', {}).get('#text', 'Unknown Album')
        
        track_y = text_y + (50 * self.current_params['upscale'])
        track_lines = self.daemon.wrap_text(track_name, subtitle_font, text_container_width - (self.current_params['text_margin'] * self.current_params['upscale']))
        for i, line in enumerate(track_lines):
            bbox = draw.textbbox((0, 0), line, subtitle_font)
            line_width = bbox[2] - bbox[0]
            line_x = text_x + text_container_width - line_width
            line_y = track_y + (i * self.current_params['line_spacing'] * self.current_params['upscale'])
            draw.text((line_x, line_y), line, fill=THEMES[self.current_params['theme']]['track_color'], font=subtitle_font)
        
        # Save the custom display
        img.save('current_display.png')
        
    def handle_input(self):
        """Handle interactive input"""
        while self.running:
            try:
                cmd = input("\n🎛️  Command: ").strip().lower()
                
                if cmd.startswith('u '):
                    try:
                        upscale = int(cmd.split()[1])
                        if 1 <= upscale <= 4:
                            self.current_params['upscale'] = upscale
                            print(f"✅ Upscale set to {upscale}x")
                            self.update_display()
                        else:
                            print("❌ Upscale must be 1-4")
                    except:
                        print("❌ Invalid upscale value")
                        
                elif cmd.startswith('t '):
                    theme = cmd.split()[1]
                    if theme in THEMES:
                        self.current_params['theme'] = theme
                        print(f"✅ Theme set to {theme}")
                        self.update_display()
                    else:
                        print(f"❌ Theme must be one of: {list(THEMES.keys())}")
                        
                elif cmd.startswith('a '):
                    try:
                        ratio = float(cmd.split()[1])
                        if 0.3 <= ratio <= 0.7:
                            self.current_params['album_container_ratio'] = ratio
                            print(f"✅ Album ratio set to {ratio}")
                            self.update_display()
                        else:
                            print("❌ Ratio must be 0.3-0.7")
                    except:
                        print("❌ Invalid ratio value")
                        
                elif cmd.startswith('m '):
                    try:
                        margin = int(cmd.split()[1])
                        if 5 <= margin <= 20:
                            self.current_params['text_margin'] = margin
                            print(f"✅ Text margin set to {margin}")
                            self.update_display()
                        else:
                            print("❌ Margin must be 5-20")
                    except:
                        print("❌ Invalid margin value")
                        
                elif cmd.startswith('s '):
                    try:
                        spacing = int(cmd.split()[1])
                        if 15 <= spacing <= 35:
                            self.current_params['line_spacing'] = spacing
                            print(f"✅ Line spacing set to {spacing}")
                            self.update_display()
                        else:
                            print("❌ Spacing must be 15-35")
                    except:
                        print("❌ Invalid spacing value")
                        
                elif cmd == 'r':
                    self.update_display()
                    
                elif cmd == 'h':
                    self.show_help()
                    
                elif cmd == '?':
                    self.show_params()
                    
                elif cmd == 'q':
                    print("👋 Goodbye!")
                    self.running = False
                    break
                    
                else:
                    print("❓ Unknown command. Type 'h' for help.")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                self.running = False
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def run(self):
        """Start interactive preview"""
        if not self.setup_daemon():
            return
            
        print("🎵 Interactive Last.fm Display Preview")
        print("=" * 50)
        self.show_help()
        self.show_params()
        
        # Initial display
        self.update_display()
        
        # Start input handling
        self.handle_input()

def main():
    preview = InteractivePreview()
    preview.run()

if __name__ == "__main__":
    main() 