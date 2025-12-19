#!/usr/bin/env python3
"""
Pi Badge LCD Display - Last.fm Now Playing
Simple, self-contained script that queries Last.fm and displays on ILI9341 LCD
"""

import os
import sys
import time
import hashlib
import requests
import threading
import json
from pathlib import Path
from io import BytesIO
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from datetime import datetime

# LCD and image libraries
from PIL import Image, ImageDraw, ImageFont

# Try to import LCD libraries (only available on Pi)
try:
    from luma.core.interface.serial import spi
    from luma.lcd.device import ili9341
    LCD_AVAILABLE = True
except ImportError:
    LCD_AVAILABLE = False

# Try to import GPIO for backlight PWM
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    try:
        from gpiozero import PWMOutputDevice
        GPIOZERO_AVAILABLE = True
        GPIO_AVAILABLE = False
    except ImportError:
        GPIO_AVAILABLE = False
        GPIOZERO_AVAILABLE = False

# Display dimensions (hardware is 320x240, rotation makes it portrait)
# For rendering, we use portrait dimensions (240x320)
RENDER_WIDTH = 240
RENDER_HEIGHT = 320
# Hardware dimensions (used for device initialization)
HW_WIDTH = 320
HW_HEIGHT = 240

# Master font size - all text uses this size
MASTER_FONT_SIZE = 26

# Theme colors
THEME = {
    'background': '#1a1a1a',
    'title': '#00ff00',  # Green for "now playing..."
    'text_offwhite': '#e0e0e0',  # Off-white for song, album, artist, timestamp
}

def load_env():
    """Load environment variables from .env file"""
    env_file = Path('.env')
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    if line.startswith('export '):
                        line = line[7:]
                    key, value = line.split('=', 1)
                    os.environ[key] = value.strip("'\"")

def get_current_track(api_key, username, retries=3):
    """Fetch current/recent track from Last.fm with retry logic"""
    url = "http://ws.audioscrobbler.com/2.0/"
    params = {
        'method': 'user.getrecenttracks',
        'user': username,
        'api_key': api_key,
        'format': 'json',
        'limit': 1
    }
    
    # Retry with exponential backoff: 1s, 2s, 4s
    for attempt in range(retries):
        try:
            # Reduced timeout for faster failure detection on hotspot
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            tracks = data.get('recenttracks', {}).get('track', [])
            if tracks:
                track = tracks[0]
                # Try to get image URLs in order of preference
                images = track.get('image', [])
                image_url = None
                # Try sizes in order: extralarge, large, medium, small
                for size in ['extralarge', 'large', 'medium', 'small']:
                    for img in images:
                        if img.get('size') == size and img.get('#text'):
                            image_url = img['#text']
                            break
                    if image_url:
                        break
                
                return {
                    'name': track.get('name', 'Unknown'),
                    'artist': track.get('artist', {}).get('#text', 'Unknown'),
                    'album': track.get('album', {}).get('#text', ''),
                    'image_url': image_url,
                    'now_playing': '@attr' in track and 'nowplaying' in track.get('@attr', {})
                }
        except requests.exceptions.Timeout:
            if attempt < retries - 1:
                wait_time = 2 ** attempt  # 1s, 2s, 4s
                print(f"⏳ Timeout, retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"❌ Last.fm timeout after {retries} attempts")
        except requests.exceptions.ConnectionError:
            if attempt < retries - 1:
                wait_time = 2 ** attempt
                print(f"📡 Connection error, retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"❌ Last.fm connection failed after {retries} attempts")
        except Exception as e:
            print(f"❌ Last.fm error: {e}")
            break  # Don't retry on other errors
    
    return None

def download_album_art(url, cache_dir="cache"):
    """Download album art with caching - tries multiple sizes if needed"""
    if not url:
        return None
    
    # Skip placeholder images (Last.fm uses these when no art is available)
    if '2a96cbd8b46e442fc41c2b86b821562f' in url or '4128a6eb29f94943c9d206c08e625904' in url:
        return None
    
    # Cache by URL hash
    cache_path = Path(cache_dir)
    cache_path.mkdir(exist_ok=True)
    
    url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
    cached_file = cache_path / f"{url_hash}.png"
    
    if cached_file.exists():
        try:
            img = Image.open(cached_file)
            # Convert to RGB safely
            if img.mode != 'RGB':
                img = img.convert('RGB')
            return img
        except Exception as e:
            # Corrupted cache, delete it
            try:
                cached_file.unlink()
            except:
                pass
    
    # Try the provided URL first
    try:
        response = requests.get(url, timeout=5, allow_redirects=True)
        if response.status_code == 200 and len(response.content) > 1000:  # Skip tiny/placeholder images
            img = Image.open(BytesIO(response.content))
            # Convert to RGB safely
            if img.mode != 'RGB':
                img = img.convert('RGB')
            # Validate dimensions
            if img.size[0] > 0 and img.size[1] > 0:
                img.save(cached_file, 'PNG')
                return img
    except Exception:
        pass
    
    # If that failed, try alternative sizes by modifying the URL
    # Last.fm URLs typically have size codes like: /174s/, /300x300/, etc.
    # Try common alternatives
    alternatives = []
    
    # Replace size codes in URL
    if '/174s/' in url:
        alternatives = [
            url.replace('/174s/', '/300x300/'),
            url.replace('/174s/', '/64s/'),
            url.replace('/174s/', '/126s/'),
        ]
    elif '/300x300/' in url:
        alternatives = [
            url.replace('/300x300/', '/174s/'),
            url.replace('/300x300/', '/64s/'),
        ]
    
    for alt_url in alternatives:
        try:
            response = requests.get(alt_url, timeout=5, allow_redirects=True)
            if response.status_code == 200 and len(response.content) > 1000:
                img = Image.open(BytesIO(response.content))
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                if img.size[0] > 0 and img.size[1] > 0:
                    img.save(cached_file, 'PNG')
                    return img
        except Exception:
            continue
    
    # All attempts failed
    return None

def save_track_cache(track, cache_dir="cache"):
    """Save track data to cache with timestamp"""
    cache_path = Path(cache_dir)
    cache_path.mkdir(exist_ok=True)
    
    cache_file = cache_path / "last_track.json"
    cache_data = {
        'track': track,
        'timestamp': time.time(),
        'cached_at': datetime.now().isoformat()
    }
    
    try:
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f, indent=2)
    except Exception as e:
        print(f"⚠️  Failed to save track cache: {e}")

def load_track_cache(cache_dir="cache", max_age_seconds=300):
    """Load cached track data if available and not stale"""
    cache_file = Path(cache_dir) / "last_track.json"
    
    if not cache_file.exists():
        return None
    
    try:
        with open(cache_file, 'r') as f:
            cache_data = json.load(f)
        
        # Check if cache is stale
        cache_age = time.time() - cache_data.get('timestamp', 0)
        if cache_age > max_age_seconds:
            return None
        
        return cache_data.get('track')
    except Exception as e:
        print(f"⚠️  Failed to load track cache: {e}")
        return None

def load_font(size):
    """Load custom font if available, otherwise fall back to system fonts"""
    custom_font_path = Path("Jacquard12-Regular.ttf")
    
    try:
        if custom_font_path.exists() and custom_font_path.stat().st_size > 0:
            # Load font without testing (testing can cause segfaults with bad fonts)
            return ImageFont.truetype(str(custom_font_path), size)
    except Exception as e:
        # Silently fall back to system fonts
        pass
    
    # Try system fonts
    try:
        if size >= 14:
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
        else:
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    except Exception:
        # Final fallback to default font
        return ImageFont.load_default()

def render_display(track, album_art=None, offline=False):
    """Render track info to a PIL Image - stacked vertical layout"""
    # Validate inputs
    if not track:
        track = {'name': 'Unknown', 'artist': 'Unknown', 'album': ''}
    
    # Ensure track has required fields
    track = {
        'name': str(track.get('name', 'Unknown')),
        'artist': str(track.get('artist', 'Unknown')),
        'album': str(track.get('album', '')),
        'now_playing': bool(track.get('now_playing', False))
    }
    
    # Validate dimensions
    if RENDER_WIDTH <= 0 or RENDER_HEIGHT <= 0:
        raise ValueError(f"Invalid render dimensions: {RENDER_WIDTH}x{RENDER_HEIGHT}")
    
    try:
        img = Image.new('RGB', (RENDER_WIDTH, RENDER_HEIGHT), THEME['background'])
        draw = ImageDraw.Draw(img)
    except Exception as e:
        raise ValueError(f"Failed to create image: {e}")
    
    # Use master font size
    master_font = load_font(MASTER_FONT_SIZE)
    
    # Helper function to render crisp text without antialiasing
    def draw_crisp_text(x, y, text, font, fill_color):
        """Render text at 2x resolution, then scale down with nearest neighbor for crisp pixels"""
        scale = 2
        # Get text bounding box at original size
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        
        if text_w <= 0 or text_h <= 0:
            return
        
        # Add extra padding to ensure full text is captured (especially for descenders)
        padding_x = 6
        padding_y_top = 4
        padding_y_bottom = 8  # Extra space for descenders
        temp_w = int(text_w * scale) + (padding_x * 2)
        temp_h = int(text_h * scale) + padding_y_top + padding_y_bottom
        temp_img = Image.new('RGB', (temp_w, temp_h), THEME['background'])
        temp_draw = ImageDraw.Draw(temp_img)
        
        # Load font at 2x size
        font_size = MASTER_FONT_SIZE * scale
        scaled_font = load_font(font_size)
        
        # Draw text at 2x resolution with padding offset
        temp_draw.text((padding_x, padding_y_top), text, fill=fill_color, font=scaled_font)
        
        # Scale down with nearest neighbor (no antialiasing)
        final_w = int(text_w)
        final_h = int(text_h)
        scaled = temp_img.resize((final_w, final_h), Image.Resampling.NEAREST)
        
        # Paste onto main image
        paste_x = int(x)
        paste_y = int(y)
        # Make sure we don't go out of bounds
        if paste_x + final_w <= RENDER_WIDTH and paste_y + final_h <= RENDER_HEIGHT:
            img.paste(scaled, (paste_x, paste_y))
    
    # Album art section: square 1:1 aspect ratio (240x240)
    art_size = RENDER_WIDTH  # 240px square
    art_y_end = art_size
    
    if album_art:
        # Resize to square (1:1 aspect ratio)
        art = album_art.resize((art_size, art_size), Image.Resampling.LANCZOS)
        img.paste(art, (0, 0))  # Top-left corner
    else:
        # No album art - draw placeholder square
        draw.rectangle((0, 0, art_size, art_size), fill='#0a0a0a')
        draw_crisp_text(art_size//2 - 40, art_size//2 - 10, "🎵", master_font, '#333333')
    
    # Text section: three rows below art
    text_y_start = art_y_end + 3
    text_height = RENDER_HEIGHT - text_y_start
    
    # Padding and container setup
    padding = 6
    container_width = (RENDER_WIDTH - (padding * 3)) // 2  # Half width for left/right columns
    left_x = padding
    right_x = padding * 2 + container_width
    full_width = RENDER_WIDTH - (padding * 2)  # Full width for title row
    
    # Helper function to find optimal font size that fits text
    def find_fitting_font(text, max_width, start_size=17, min_size=10):
        """Find the largest font size that fits text within max_width"""
        for size in range(start_size, min_size - 1, -1):
            try:
                test_font = load_font(size)
                bbox = draw.textbbox((0, 0), text, font=test_font)
                if bbox[2] - bbox[0] <= max_width:
                    return test_font, size
            except:
                continue
        # Fallback to minimum size
        return load_font(min_size), min_size
    
    y = text_y_start
    
    # ROW 1: "now playing..." (left) and artist (right)
    status = "now playing..."
    if offline:
        status = "📡 offline - " + status
    draw_crisp_text(left_x, y, status, master_font, THEME['title'])
    
    # Artist - right-aligned, auto-sized, off-white
    artist = track['artist']
    artist_font, _ = find_fitting_font(artist, container_width, start_size=MASTER_FONT_SIZE, min_size=20)
    bbox = draw.textbbox((0, 0), artist, font=artist_font)
    artist_x = right_x + container_width - (bbox[2] - bbox[0])  # Right-align
    draw_crisp_text(artist_x, y, artist, artist_font, THEME['text_offwhite'])
    
    # ROW 2: Song title (full width, left-aligned, off-white, scrolling if too long)
    y += 28
    track_name = track['name']
    
    # Check if text fits
    bbox = draw.textbbox((0, 0), track_name, font=master_font)
    text_width = bbox[2] - bbox[0]
    
    if text_width <= full_width:
        # Text fits, just display it
        draw_crisp_text(left_x, y, track_name, master_font, THEME['text_offwhite'])
    else:
        # Text is too long, implement scrolling animation
        # Calculate scroll position based on time
        scroll_cycle_time = 8.0  # Total cycle time: 2s pause + scroll right + scroll back
        pause_time = 2.0  # Initial pause
        scroll_speed = 30.0  # pixels per second
        
        current_time = time.time()
        cycle_position = (current_time % scroll_cycle_time)
        
        if cycle_position < pause_time:
            # Pause at start (show beginning)
            scroll_x = left_x
        elif cycle_position < pause_time + ((text_width - full_width) / scroll_speed):
            # Scroll right
            elapsed = cycle_position - pause_time
            scroll_x = left_x - (elapsed * scroll_speed)
        else:
            # Scroll back to start
            elapsed = cycle_position - (pause_time + ((text_width - full_width) / scroll_speed))
            scroll_x = left_x - ((text_width - full_width) - (elapsed * scroll_speed))
        
        # Clamp scroll position
        max_scroll = text_width - full_width
        scroll_x = max(left_x - max_scroll, min(left_x, scroll_x))
        
        # Create a temporary image for the full text to clip from (at 2x for crisp rendering)
        scale = 2
        temp_w = int((text_width + 20) * scale)
        temp_h = int(30 * scale)
        temp_img = Image.new('RGB', (temp_w, temp_h), THEME['background'])
        temp_draw = ImageDraw.Draw(temp_img)
        scaled_font = load_font(MASTER_FONT_SIZE * scale)
        temp_draw.text((10 * scale, 0), track_name, fill=THEME['text_offwhite'], font=scaled_font)
        
        # Crop and paste the visible portion (scale down with nearest neighbor)
        crop_x = max(0, int((left_x - scroll_x + 10) * scale))
        crop_width = min(int(full_width * scale), int((text_width - (left_x - scroll_x + 10) + 10) * scale))
        if crop_width > 0:
            cropped = temp_img.crop((crop_x, 0, crop_x + crop_width, temp_h))
            # Scale down with nearest neighbor for crisp pixels
            final_cropped = cropped.resize((crop_width // scale, temp_h // scale), Image.Resampling.NEAREST)
            img.paste(final_cropped, (left_x, y))
    
    y += 24  # Move down for next row
    
    # ROW 3: Album (left) and timestamp (right), both off-white
    y += 4
    album = track.get('album', '')
    if album:
        album_font, _ = find_fitting_font(album, container_width, start_size=MASTER_FONT_SIZE, min_size=20)
        draw_crisp_text(left_x, y, album, album_font, THEME['text_offwhite'])
    
    # Timestamp - right-aligned, off-white
    timestamp = time.strftime("%H:%M")
    bbox = draw.textbbox((0, 0), timestamp, font=master_font)
    timestamp_x = right_x + container_width - (bbox[2] - bbox[0])  # Right-align
    draw_crisp_text(timestamp_x, y, timestamp, master_font, THEME['text_offwhite'])
    
    return img

def render_waiting():
    """Render a waiting screen"""
    img = Image.new('RGB', (RENDER_WIDTH, RENDER_HEIGHT), THEME['background'])
    draw = ImageDraw.Draw(img)
    
    font = load_font(MASTER_FONT_SIZE)
    
    # Helper function for crisp text
    def draw_crisp_text(x, y, text, font, fill_color):
        scale = 2
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        if text_w <= 0 or text_h <= 0:
            return
        padding_x = 6
        padding_y_top = 4
        padding_y_bottom = 8
        temp_w = int(text_w * scale) + (padding_x * 2)
        temp_h = int(text_h * scale) + padding_y_top + padding_y_bottom
        temp_img = Image.new('RGB', (temp_w, temp_h), THEME['background'])
        temp_draw = ImageDraw.Draw(temp_img)
        scaled_font = load_font(MASTER_FONT_SIZE * scale)
        temp_draw.text((padding_x, padding_y_top), text, fill=fill_color, font=scaled_font)
        final_w = int(text_w)
        final_h = int(text_h)
        scaled = temp_img.resize((final_w, final_h), Image.Resampling.NEAREST)
        paste_x = int(x)
        paste_y = int(y)
        if paste_x + final_w <= RENDER_WIDTH and paste_y + final_h <= RENDER_HEIGHT:
            img.paste(scaled, (paste_x, paste_y))
    
    # Center text for portrait mode
    text1 = "🎵 Connecting..."
    text2 = "Waiting for Last.fm"
    bbox1 = draw.textbbox((0, 0), text1, font=font)
    bbox2 = draw.textbbox((0, 0), text2, font=font)
    x1 = (RENDER_WIDTH - (bbox1[2] - bbox1[0])) // 2
    x2 = (RENDER_WIDTH - (bbox2[2] - bbox2[0])) // 2
    
    draw_crisp_text(x1, RENDER_HEIGHT // 2 - 20, text1, font, THEME['title'])
    draw_crisp_text(x2, RENDER_HEIGHT // 2 + 10, text2, font, '#666666')
    
    return img

def render_error(message):
    """Render an error screen"""
    img = Image.new('RGB', (RENDER_WIDTH, RENDER_HEIGHT), '#1a0000')
    draw = ImageDraw.Draw(img)
    
    font = load_font(MASTER_FONT_SIZE)
    
    # Helper function for crisp text
    def draw_crisp_text(x, y, text, font, fill_color):
        scale = 2
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        if text_w <= 0 or text_h <= 0:
            return
        padding_x = 6
        padding_y_top = 4
        padding_y_bottom = 8
        temp_w = int(text_w * scale) + (padding_x * 2)
        temp_h = int(text_h * scale) + padding_y_top + padding_y_bottom
        temp_img = Image.new('RGB', (temp_w, temp_h), '#1a0000')
        temp_draw = ImageDraw.Draw(temp_img)
        scaled_font = load_font(MASTER_FONT_SIZE * scale)
        temp_draw.text((padding_x, padding_y_top), text, fill=fill_color, font=scaled_font)
        final_w = int(text_w)
        final_h = int(text_h)
        scaled = temp_img.resize((final_w, final_h), Image.Resampling.NEAREST)
        paste_x = int(x)
        paste_y = int(y)
        if paste_x + final_w <= RENDER_WIDTH and paste_y + final_h <= RENDER_HEIGHT:
            img.paste(scaled, (paste_x, paste_y))
    
    # Center error title
    error_text = "❌ Error"
    bbox = draw.textbbox((0, 0), error_text, font=font)
    x = (RENDER_WIDTH - (bbox[2] - bbox[0])) // 2
    draw_crisp_text(x, RENDER_HEIGHT // 2 - 40, error_text, font, '#ff4444')
    
    # Wrap error message (centered)
    words = message.split()
    line = ""
    y = RENDER_HEIGHT // 2 - 10
    for word in words:
        test = f"{line} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] < RENDER_WIDTH - 40:
            line = test
        else:
            if line:
                bbox = draw.textbbox((0, 0), line, font=font)
                x = (RENDER_WIDTH - (bbox[2] - bbox[0])) // 2
                draw_crisp_text(x, y, line, font, '#888888')
                y += 16
            line = word
    if line:
        bbox = draw.textbbox((0, 0), line, font=font)
        x = (RENDER_WIDTH - (bbox[2] - bbox[0])) // 2
        draw_crisp_text(x, y, line, font, '#888888')
    
    return img

class Display:
    """LCD display wrapper (supports both real LCD and preview mode)"""
    
    def __init__(self, preview=False, brightness=100):
        self.preview = preview
        self.device = None
        self.backlight_pwm = None
        self.brightness = max(0, min(100, brightness))  # Clamp 0-100
        
        if not preview and LCD_AVAILABLE:
            serial = spi(
                port=0,
                device=0,
                gpio_DC=24,
                gpio_RST=25,
                bus_speed_hz=32000000
            )
            self.device = ili9341(serial, width=HW_WIDTH, height=HW_HEIGHT, rotate=1)
            print("✅ LCD initialized")
            
            # Initialize backlight PWM on GPIO 18
            self.init_backlight()
        elif not preview:
            print("⚠️  LCD not available, running in preview mode")
            self.preview = True
    
    def init_backlight(self):
        """Initialize PWM backlight on GPIO 18"""
        BACKLIGHT_PIN = 18
        PWM_FREQ = 1000  # 1kHz PWM frequency
        
        try:
            if GPIO_AVAILABLE:
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(BACKLIGHT_PIN, GPIO.OUT)
                self.backlight_pwm = GPIO.PWM(BACKLIGHT_PIN, PWM_FREQ)
                self.backlight_pwm.start(0)
                self.set_brightness(self.brightness)
                print(f"💡 Backlight initialized (GPIO {BACKLIGHT_PIN})")
            elif GPIOZERO_AVAILABLE:
                self.backlight_pwm = PWMOutputDevice(BACKLIGHT_PIN, frequency=PWM_FREQ)
                self.set_brightness(self.brightness)
                print(f"💡 Backlight initialized (GPIO {BACKLIGHT_PIN})")
        except Exception as e:
            print(f"⚠️  Backlight initialization failed: {e}")
            self.backlight_pwm = None
    
    def set_brightness(self, brightness):
        """Set backlight brightness (0-100)"""
        self.brightness = max(0, min(100, brightness))
        
        if self.backlight_pwm is None:
            return
        
        try:
            if GPIO_AVAILABLE:
                # RPi.GPIO uses 0-100 for duty cycle
                self.backlight_pwm.ChangeDutyCycle(self.brightness)
            elif GPIOZERO_AVAILABLE:
                # gpiozero uses 0.0-1.0 for duty cycle
                self.backlight_pwm.value = self.brightness / 100.0
        except Exception as e:
            print(f"⚠️  Brightness adjustment failed: {e}")
    
    def get_brightness(self):
        """Get current brightness (0-100)"""
        return self.brightness
    
    def show(self, img):
        """Display an image"""
        global current_display_img, current_display_bytes
        
        # Save for web server
        current_display_img = img
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        current_display_bytes = img_bytes.getvalue()
        
        if self.device:
            self.device.display(img)
        
        if self.preview:
            # Save preview image
            img.save('preview.png')
            print(f"📸 Preview saved: preview.png")
    
    def clear(self):
        """Clear the display and turn off backlight"""
        img = Image.new('RGB', (RENDER_WIDTH, RENDER_HEIGHT), 'black')
        if self.device:
            self.device.display(img)
        
        # Turn off backlight
        if self.backlight_pwm:
            try:
                if GPIO_AVAILABLE:
                    self.backlight_pwm.ChangeDutyCycle(0)
                elif GPIOZERO_AVAILABLE:
                    self.backlight_pwm.value = 0.0
            except:
                pass
    
    def __del__(self):
        """Cleanup on deletion"""
        if self.backlight_pwm:
            try:
                if GPIO_AVAILABLE:
                    self.backlight_pwm.stop()
                    GPIO.cleanup()
                elif GPIOZERO_AVAILABLE:
                    self.backlight_pwm.close()
            except:
                pass

# Global state for web server
current_display_img = None
current_track_info = None
current_display_bytes = None

class DisplayHandler(BaseHTTPRequestHandler):
    """HTTP handler for web preview"""
    
    def do_GET(self):
        global current_display_bytes, current_track_info
        
        if self.path == '/' or self.path == '/index.html':
            self.serve_html()
        elif self.path == '/display.png':
            self.serve_image()
        elif self.path == '/api/track':
            self.serve_track_json()
        else:
            self.send_error(404)
    
    def serve_html(self):
        """Serve HTML preview page"""
        global current_track_info
        
        track = current_track_info or {}
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pi Badge Display</title>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            background: #0a0a0a;
            color: #fff;
            font-family: monospace;
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        h1 {{
            color: #00ff00;
            margin-bottom: 10px;
        }}
        .display {{
            border: 2px solid #333;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0,255,0,0.2);
            margin: 20px 0;
        }}
        .info {{
            margin-top: 20px;
            text-align: center;
            color: #888;
        }}
        .track {{
            color: #fff;
            font-size: 18px;
            margin: 5px 0;
        }}
        .artist {{
            color: #ff6b6b;
            font-size: 14px;
        }}
        .album {{
            color: #74c0fc;
            font-size: 12px;
        }}
        .status {{
            color: #00ff00;
            font-size: 12px;
            margin-top: 10px;
        }}
    </style>
    <script>
        function refreshDisplay() {{
            const img = document.getElementById('display');
            const timestamp = new Date().getTime();
            img.src = '/display.png?t=' + timestamp;
            
            fetch('/api/track')
                .then(r => r.json())
                .then(data => {{
                    if (data.track) {{
                        document.getElementById('track').textContent = data.track.name || 'Unknown';
                        document.getElementById('artist').textContent = data.track.artist || 'Unknown';
                        document.getElementById('album').textContent = data.track.album || '';
                        document.getElementById('status').textContent = data.track.now_playing ? '▶ NOW PLAYING' : '♫ LAST PLAYED';
                    }}
                }});
        }}
        
        // Auto-refresh every 5 seconds
        setInterval(refreshDisplay, 5000);
        refreshDisplay();
    </script>
</head>
<body>
    <h1>🎵 Pi Badge Display</h1>
    <div class="display">
        <img id="display" src="/display.png" alt="Display" style="display: block; image-rendering: pixelated; image-rendering: crisp-edges;">
    </div>
    <div class="info">
        <div id="status" class="status">Loading...</div>
        <div id="track" class="track">-</div>
        <div id="artist" class="artist">-</div>
        <div id="album" class="album">-</div>
    </div>
</body>
</html>"""
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def serve_image(self):
        """Serve current display image"""
        global current_display_bytes
        
        if current_display_bytes:
            self.send_response(200)
            self.send_header('Content-type', 'image/png')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(current_display_bytes)
        else:
            self.send_error(404, "No display image available")
    
    def serve_track_json(self):
        """Serve current track info as JSON"""
        global current_track_info
        
        import json
        data = current_track_info or {}
        json_data = json.dumps(data)
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json_data.encode())
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass

def start_web_server(port=8080):
    """Start web server in background thread"""
    def run_server():
        server = HTTPServer(('0.0.0.0', port), DisplayHandler)
        print(f"🌐 Web preview: http://localhost:{port}")
        print(f"📱 Network: http://[your-ip]:{port}")
        server.serve_forever()
    
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    return thread

def main():
    load_env()
    
    api_key = os.getenv('LASTFM_API_KEY')
    username = os.getenv('LASTFM_USERNAME')
    
    if not api_key or not username:
        print("❌ Missing credentials!")
        print("Create a .env file with:")
        print("  LASTFM_API_KEY='your_key'")
        print("  LASTFM_USERNAME='your_username'")
        sys.exit(1)
    
    # Parse args
    interval = 30
    preview = False
    browser = False
    port = 8080
    brightness = 100  # Default brightness (0-100)
    
    i = 0
    while i < len(sys.argv[1:]):
        arg = sys.argv[1:][i]
        if arg.isdigit():
            interval = int(arg)
        elif arg in ['--preview', '-p']:
            preview = True
        elif arg in ['--browser', '-b']:
            browser = True
            # Check for port number next
            if i + 1 < len(sys.argv[1:]) and sys.argv[1:][i + 1].isdigit():
                port = int(sys.argv[1:][i + 1])
                i += 1
        elif arg in ['--brightness', '--bright', '-br']:
            # Check for brightness value next
            if i + 1 < len(sys.argv[1:]):
                try:
                    brightness = int(sys.argv[1:][i + 1])
                    brightness = max(0, min(100, brightness))  # Clamp 0-100
                    i += 1
                except ValueError:
                    print(f"⚠️  Invalid brightness value, using default 100")
        elif arg in ['--help', '-h']:
            print("Usage: python display_image.py [interval] [options]")
            print("  interval: Update interval in seconds (default: 30)")
            print("  --preview, -p: Save images to preview.png instead of LCD")
            print("  --browser, -b [port]: Start web server (default port: 8080)")
            print("  --brightness, --bright, -br [0-100]: Set backlight brightness (default: 100)")
            print("\nExamples:")
            print("  python display_image.py 10 --browser")
            print("  python display_image.py --browser 9000")
            print("  python display_image.py --brightness 50")
            print("  python display_image.py --brightness 75 --browser")
            sys.exit(0)
        i += 1
    
    print(f"🎵 Pi Badge Display")
    print(f"   User: {username}")
    print(f"   Interval: {interval}s")
    print(f"   Mode: {'Preview' if preview else 'LCD'}")
    if not preview:
        print(f"   Brightness: {brightness}%")
    if browser:
        print(f"   Browser: http://localhost:{port}")
    print("🛑 Press Ctrl+C to stop")
    print()
    
    # Start web server if requested
    if browser:
        start_web_server(port)
    
    display = Display(preview=preview, brightness=brightness)
    last_track_hash = None
    
    # Show waiting screen
    waiting_img = render_waiting()
    display.show(waiting_img)
    
    try:
        while True:
            offline = False
            track = get_current_track(api_key, username)
            
            if track:
                # Successfully fetched from API - save to cache
                save_track_cache(track)
                
                # Check if track changed
                track_hash = hashlib.md5(f"{track['name']}{track['artist']}".encode()).hexdigest()
                
                if track_hash != last_track_hash:
                    global current_track_info
                    print(f"🎵 {track['name']} - {track['artist']}")
                    
                    # Download album art
                    album_art = download_album_art(track.get('image_url'))
                    if album_art:
                        print("🖼️  Album art loaded")
                    else:
                        print("⚠️  No album art available")
                    
                    # Render and display
                    try:
                        img = render_display(track, album_art, offline=False)
                        if img and img.size[0] > 0 and img.size[1] > 0:
                            display.show(img)
                        else:
                            print("⚠️  Invalid image generated, skipping display")
                    except Exception as e:
                        print(f"❌ Render error: {e}")
                        import traceback
                        traceback.print_exc()
                    
                    # Update track info for web server
                    current_track_info = {
                        'track': {
                            'name': track['name'],
                            'artist': track['artist'],
                            'album': track.get('album', ''),
                            'now_playing': track.get('now_playing', False)
                        }
                    }
                    
                    last_track_hash = track_hash
                else:
                    print(f"⏰ No change ({time.strftime('%H:%M:%S')})")
            else:
                # API failed - try to load from cache
                cached_track = load_track_cache()
                if cached_track:
                    offline = True
                    track = cached_track
                    track_hash = hashlib.md5(f"{track['name']}{track['artist']}".encode()).hexdigest()
                    
                    if track_hash != last_track_hash:
                        print(f"📡 Offline - Using cached: {track['name']} - {track['artist']}")
                        
                        # Try to load cached album art
                        album_art = None
                        if track.get('image_url'):
                            album_art = download_album_art(track.get('image_url'))
                        
                        # Render with offline indicator
                        try:
                            img = render_display(track, album_art, offline=True)
                            if img and img.size[0] > 0 and img.size[1] > 0:
                                display.show(img)
                            else:
                                print("⚠️  Invalid image generated, skipping display")
                        except Exception as e:
                            print(f"❌ Render error: {e}")
                            import traceback
                            traceback.print_exc()
                        
                        # Update track info for web server
                        current_track_info = {
                            'track': {
                                'name': track['name'],
                                'artist': track['artist'],
                                'album': track.get('album', ''),
                                'now_playing': track.get('now_playing', False)
                            }
                        }
                        
                        last_track_hash = track_hash
                    else:
                        print(f"📡 Offline - No change ({time.strftime('%H:%M:%S')})")
                else:
                    print("❌ No track data and no cache available")
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n👋 Bye!")
        display.clear()

if __name__ == "__main__":
    main()
