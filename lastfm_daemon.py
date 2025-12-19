#!/usr/bin/env python3
"""
Last.fm Daemon for Pi Badge
Runs continuously, caches album art, and serves HTML display
"""

import requests
import json
import os
import sys
import time
import hashlib
from PIL import Image
from pathlib import Path
from io import BytesIO
import threading
import signal
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse
from datetime import datetime, timezone
import pytz

# Theme configuration - customize colors and fonts here
THEMES = {
    'default': {
        'background': '#1a1a1a',
        'title_color': '#00ff00',      # Green
        'track_color': 'white',
        'artist_color': '#ff6b6b',     # Red
        'album_color': '#74c0fc',      # Blue
        'timestamp_color': '#666666'   # Gray
    },
    'dark': {
        'background': '#000000',
        'title_color': '#00ff88',      # Bright green
        'track_color': '#ffffff',
        'artist_color': '#ff4444',     # Bright red
        'album_color': '#4488ff',      # Bright blue
        'timestamp_color': '#888888'
    },
    'vintage': {
        'background': '#2d1b1b',
        'title_color': '#ffd700',      # Gold
        'track_color': '#f5f5dc',      # Beige
        'artist_color': '#ff6347',     # Tomato
        'album_color': '#87ceeb',      # Sky blue
        'timestamp_color': '#a9a9a9'
    },
    'stats': {
        'background': '#0a0a0a',
        'title_color': '#00ff88',      # Bright green
        'track_color': '#ffffff',      # White
        'artist_color': '#ff6b6b',     # Red
        'album_color': '#74c0fc',      # Blue
        'timestamp_color': '#666666'   # Gray
    }
}

class LastFmHTTPHandler(SimpleHTTPRequestHandler):
    """Custom HTTP handler for serving Last.fm display"""
    
    def __init__(self, *args, daemon=None, **kwargs):
        self.daemon = daemon
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/' or self.path == '/index.html':
            self.serve_main_page()
        elif self.path == '/api/current':
            self.serve_current_data()
        elif self.path.startswith('/cache/'):
            self.serve_cached_image()
        else:
            self.send_error(404, "Not Found")
    
    def serve_main_page(self):
        """Serve the main HTML page"""
        html = self.daemon.generate_html()
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.send_header('Content-length', len(html.encode()))
        self.end_headers()
        self.wfile.write(html.encode())
    
    def serve_current_data(self):
        """Serve current track data as JSON"""
        data = self.daemon.get_current_data()
        json_data = json.dumps(data)
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Content-length', len(json_data.encode()))
        self.end_headers()
        self.wfile.write(json_data.encode())
    
    def serve_cached_image(self):
        """Serve cached album art images"""
        try:
            # Extract filename from path
            filename = self.path[7:]  # Remove '/cache/'
            filepath = self.daemon.cache_dir / filename
            
            if filepath.exists() and filepath.suffix.lower() in ['.png', '.jpg', '.jpeg']:
                with open(filepath, 'rb') as f:
                    content = f.read()
                
                self.send_response(200)
                if filepath.suffix.lower() == '.png':
                    self.send_header('Content-type', 'image/png')
                else:
                    self.send_header('Content-type', 'image/jpeg')
                self.send_header('Content-length', len(content))
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_error(404, "Image not found")
        except Exception as e:
            print(f"Error serving image: {e}")
            self.send_error(500, "Internal Server Error")

class LastFmDaemon:
    def __init__(self, api_key, username, cache_dir="cache", update_interval=30, theme='default', port=8080):
        self.api_key = api_key
        self.username = username
        self.base_url = "http://ws.audioscrobbler.com/2.0/"
        self.cache_dir = Path(cache_dir)
        self.update_interval = update_interval
        self.theme = THEMES.get(theme, THEMES['default'])
        self.port = port
        self.running = True
        self.last_track_hash = None
        self.current_track = None
        self.current_stats = None
        self.server = None
        self.server_thread = None
        
        # Create cache directory
        self.cache_dir.mkdir(exist_ok=True)
        
        # Signal handling for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
        self.running = False
        if self.server:
            self.server.shutdown()
    
    def get_track_hash(self, track_info):
        """Generate a hash for track info to detect changes"""
        track_data = f"{track_info.get('name', '')}{track_info.get('artist', {}).get('#text', '')}{track_info.get('album', {}).get('#text', '')}"
        return hashlib.md5(track_data.encode()).hexdigest()
    
    def get_cache_path(self, track_hash, suffix=""):
        """Get cache file path for a track"""
        return self.cache_dir / f"track_{track_hash}{suffix}.png"
    
    def is_cached(self, track_hash, suffix=""):
        """Check if track is cached"""
        cache_path = self.get_cache_path(track_hash, suffix)
        return cache_path.exists()
    
    def get_recent_tracks(self, limit=1):
        """Fetch recent tracks from Last.fm API"""
        params = {
            'method': 'user.getrecenttracks',
            'user': self.username,
            'api_key': self.api_key,
            'format': 'json',
            'limit': limit
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'recenttracks' in data and 'track' in data['recenttracks']:
                tracks = data['recenttracks']['track']
                if tracks:
                    return tracks[0]  # Return most recent track
            return None
            
        except requests.RequestException as e:
            print(f"❌ Error fetching from Last.fm: {e}")
            return None
    
    def generate_html(self):
        """Generate HTML page for current track"""
        theme = self.theme
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pi Badge - Last.fm Display</title>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            background-color: {theme['background']};
            color: {theme['track_color']};
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }}
        
        .container {{
            display: flex;
            gap: 20px;
            align-items: flex-start;
            flex: 1;
        }}
        
        .album-art {{
            flex-shrink: 0;
            width: 240px;
            height: 240px;
        }}
        
        .album-art img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        }}
        
        .track-info {{
            flex: 1;
            text-align: right;
            padding-left: 20px;
        }}
        
        .title {{
            color: {theme['title_color']};
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 20px;
            text-transform: uppercase;
            letter-spacing: 2px;
        }}
        
        .track-name {{
            color: {theme['track_color']};
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 10px;
            word-wrap: break-word;
        }}
        
        .artist-name {{
            color: {theme['artist_color']};
            font-size: 18px;
            font-weight: 500;
            margin-bottom: 8px;
            word-wrap: break-word;
        }}
        
        .album-name {{
            color: {theme['album_color']};
            font-size: 14px;
            margin-bottom: 30px;
            word-wrap: break-word;
        }}
        
        .stats {{
            border-top: 1px solid {theme['timestamp_color']};
            padding-top: 20px;
            font-size: 12px;
        }}
        
        .stat-line {{
            margin-bottom: 8px;
        }}
        
        .status {{
            color: {theme['title_color']};
            font-weight: bold;
        }}
        
        .play-count {{
            color: {theme['track_color']};
        }}
        
        .time {{
            color: {theme['artist_color']};
        }}
        
        .total {{
            color: {theme['album_color']};
        }}
        
        .timestamp {{
            position: fixed;
            bottom: 10px;
            right: 10px;
            color: {theme['timestamp_color']};
            font-size: 12px;
        }}
        
        .no-album-art .container {{
            flex-direction: column;
            align-items: flex-end;
        }}
        
        .no-album-art .track-info {{
            padding-left: 0;
            width: 100%;
        }}
        
        @media (max-width: 768px) {{
            .container {{
                flex-direction: column;
                align-items: center;
            }}
            
            .track-info {{
                text-align: center;
                padding-left: 0;
            }}
            
            .album-art {{
                width: 200px;
                height: 200px;
            }}
        }}
    </style>
</head>
<body class="{'no-album-art' if not self.get_album_art_url() else ''}">
    <div class="container">
        {self.get_album_art_html()}
        <div class="track-info">
            <div class="title">NOW PLAYING</div>
            <div class="track-name" id="track-name">{self.current_track.get('name', 'Unknown Track') if self.current_track else 'No track playing'}</div>
            <div class="artist-name" id="artist-name">{self.current_track.get('artist', {}).get('#text', 'Unknown Artist') if self.current_track else ''}</div>
            <div class="album-name" id="album-name">{self.current_track.get('album', {}).get('#text', 'Unknown Album') if self.current_track else ''}</div>
            
            <div class="stats" id="stats">
                {self.get_stats_html()}
            </div>
        </div>
    </div>
    
    <div class="timestamp" id="timestamp">{datetime.now(pytz.timezone('America/New_York')).strftime('%H:%M:%S')}</div>
    
    <script>
        // Auto-refresh data every 10 seconds
        setInterval(function() {{
            fetch('/api/current')
                .then(response => response.json())
                .then(data => {{
                    if (data.track) {{
                        document.getElementById('track-name').textContent = data.track.name || 'Unknown Track';
                        document.getElementById('artist-name').textContent = data.track.artist || 'Unknown Artist';
                        document.getElementById('album-name').textContent = data.track.album || 'Unknown Album';
                        
                        // Update album art if available
                        const albumArt = document.querySelector('.album-art img');
                        if (data.album_art_url && albumArt) {{
                            albumArt.src = data.album_art_url + '?t=' + new Date().getTime();
                        }}
                        
                        // Update stats
                        document.getElementById('stats').innerHTML = data.stats_html;
                    }}
                    
                    // Update timestamp
                    document.getElementById('timestamp').textContent = data.timestamp;
                }})
                .catch(error => console.error('Error fetching data:', error));
        }}, 10000);
    </script>
</body>
</html>"""
        return html
    
    def get_album_art_url(self):
        """Get URL for current album art"""
        if self.current_track:
            track_hash = self.get_track_hash(self.current_track)
            art_path = self.get_cache_path(track_hash, "_art")
            if art_path.exists():
                return f"/cache/{art_path.name}"
        return None
    
    def get_album_art_html(self):
        """Generate HTML for album art display"""
        album_art_url = self.get_album_art_url()
        if album_art_url:
            return f'<div class="album-art"><img src="{album_art_url}" alt="Album Art"></div>'
        return ''
    
    def get_stats_html(self):
        """Generate HTML for stats section"""
        if not self.current_stats:
            return '<div class="stat-line status">No stats available</div>'
        
        stats_html = f"""
        <div class="stat-line status">{self.current_stats.get('status', 'Unknown')}</div>
        <div class="stat-line play-count">Top Artist: {self.current_stats.get('top_artist', 'Unknown')} ({self.current_stats.get('top_artist_plays', '0')} plays)</div>
        <div class="stat-line time">Today: {self.current_stats.get('today_plays', 'Unknown')} plays</div>
        <div class="stat-line total">Total: {self.current_stats.get('total_scrobbles', 'Unknown')} scrobbles</div>
        """
        return stats_html
    
    def get_current_data(self):
        """Get current track data as JSON"""
        # Use New York timezone
        ny_tz = pytz.timezone('America/New_York')
        current_time = datetime.now(ny_tz)
        
        data = {
            'timestamp': current_time.strftime('%H:%M:%S'),
            'album_art_url': self.get_album_art_url(),
            'track': None,
            'stats_html': self.get_stats_html()
        }
        
        if self.current_track:
            data['track'] = {
                'name': self.current_track.get('name', 'Unknown Track'),
                'artist': self.current_track.get('artist', {}).get('#text', 'Unknown Artist'),
                'album': self.current_track.get('album', {}).get('#text', 'Unknown Album')
            }
        
        return data

    def get_track_stats(self, track_info):
        """Get additional stats for a track"""
        stats = {}
        
        # Get play count if available
        play_count = track_info.get('playcount', '0')
        stats['play_count'] = play_count
        
        # Get scrobble time
        if '@attr' in track_info and 'nowplaying' in track_info['@attr']:
            stats['status'] = 'Now Playing'
            stats['scrobble_time'] = 'Live'
        else:
            stats['status'] = 'Last Played'
            # Try to get scrobble time
            date = track_info.get('date', {})
            if date and '#text' in date:
                stats['scrobble_time'] = date['#text']
            else:
                stats['scrobble_time'] = 'Unknown'
        
        # Get top artist of the week
        try:
            weekly_params = {
                'method': 'user.getweeklyartistchart',
                'user': self.username,
                'api_key': self.api_key,
                'format': 'json',
                'limit': 1
            }
            weekly_response = requests.get(self.base_url, params=weekly_params)
            weekly_response.raise_for_status()
            weekly_data = weekly_response.json()
            
            if 'weeklyartistchart' in weekly_data and 'artist' in weekly_data['weeklyartistchart']:
                artists = weekly_data['weeklyartistchart']['artist']
                if artists:
                    top_artist = artists[0]
                    stats['top_artist'] = top_artist.get('name', 'Unknown')
                    stats['top_artist_plays'] = top_artist.get('playcount', '0')
        except:
            stats['top_artist'] = 'Unknown'
            stats['top_artist_plays'] = '0'
        
        # Get total plays today
        try:
            # Get recent tracks to count today's plays
            recent_params = {
                'method': 'user.getrecenttracks',
                'user': self.username,
                'api_key': self.api_key,
                'format': 'json',
                'limit': 200  # Get more tracks to count today's plays
            }
            recent_response = requests.get(self.base_url, params=recent_params)
            recent_response.raise_for_status()
            recent_data = recent_response.json()
            
            if 'recenttracks' in recent_data and 'track' in recent_data['recenttracks']:
                tracks = recent_data['recenttracks']['track']
                today_plays = 0
                today = datetime.now(pytz.timezone('America/New_York')).date()
                
                for track in tracks:
                    if '@attr' in track and 'nowplaying' in track['@attr']:
                        continue  # Skip currently playing
                    
                    date = track.get('date', {})
                    if date and '#text' in date:
                        try:
                            # Parse the date from Last.fm format
                            track_date = datetime.strptime(date['#text'], '%d %b %Y, %H:%M')
                            track_date = pytz.timezone('America/New_York').localize(track_date)
                            if track_date.date() == today:
                                today_plays += 1
                        except:
                            continue
                
                stats['today_plays'] = str(today_plays)
        except:
            stats['today_plays'] = 'Unknown'
        
        # Get user's total scrobbles
        try:
            user_params = {
                'method': 'user.getinfo',
                'user': self.username,
                'api_key': self.api_key,
                'format': 'json'
            }
            user_response = requests.get(self.base_url, params=user_params)
            user_response.raise_for_status()
            user_data = user_response.json()
            
            if 'user' in user_data:
                stats['total_scrobbles'] = user_data['user'].get('playcount', '0')
        except:
            stats['total_scrobbles'] = 'Unknown'
        
        return stats
    
    def download_album_art(self, track_info, size='large'):
        """Download album art from Last.fm"""
        try:
            # Get album art URL from track info
            images = track_info.get('image', [])
            album_art_url = None
            
            for img in images:
                if img.get('size') == size:
                    album_art_url = img.get('#text')
                    break
            
            if not album_art_url:
                # Try medium size if large not available
                for img in images:
                    if img.get('size') == 'medium':
                        album_art_url = img.get('#text')
                        break
            
            if album_art_url:
                print(f"📥 Downloading album art: {album_art_url}")
                response = requests.get(album_art_url)
                response.raise_for_status()
                
                # Open and resize to 240x240 (base size for small displays)
                img = Image.open(BytesIO(response.content))
                img = img.convert('RGB')  # Ensure RGB format
                img = img.resize((240, 240), Image.Resampling.LANCZOS)
                return img
            else:
                print("⚠️  No album art URL found")
                return None
                
        except Exception as e:
            print(f"❌ Error downloading album art: {e}")
            return None
    
    def save_album_art(self, track_info, album_art):
        """Save album art to cache for web serving"""
        if album_art:
            track_hash = self.get_track_hash(track_info)
            album_art_path = self.get_cache_path(track_hash, "_art")
            
            # Resize to standard size for web display
            album_art = album_art.resize((240, 240), Image.Resampling.LANCZOS)
            album_art.save(album_art_path, 'PNG')
            print(f"💾 Cached album art: {album_art_path}")
            return album_art_path
        return None
    
    def process_track(self, track_info):
        """Process a track - download art and update current data"""
        track_hash = self.get_track_hash(track_info)
        
        # Check if we already have album art cached
        if self.is_cached(track_hash, "_art"):
            print(f"✅ Album art already cached for: {track_info.get('name', 'Unknown')}")
        else:
            print(f"🔄 Processing new track: {track_info.get('name', 'Unknown')} by {track_info.get('artist', {}).get('#text', 'Unknown')}")
            
            # Download and save album art
            album_art = self.download_album_art(track_info)
            if album_art:
                self.save_album_art(track_info, album_art)
        
        # Update current track and stats
        self.current_track = track_info
        self.current_stats = self.get_track_stats(track_info)
        
        return True
    
    def update_display(self):
        """Update the current track data"""
        track = self.get_recent_tracks()
        
        if track:
            track_hash = self.get_track_hash(track)
            
            # Only update if track has changed
            if track_hash != self.last_track_hash:
                self.process_track(track)
                self.last_track_hash = track_hash
                
                print(f"🎵 Now playing: {track.get('name', 'Unknown')} by {track.get('artist', {}).get('#text', 'Unknown')}")
                print(f"🌐 Web display: http://localhost:{self.port}")
            else:
                print(f"⏰ No change in track ({time.strftime('%H:%M:%S')})")
        else:
            print("❌ No recent tracks found")
            self.current_track = None
            self.current_stats = None
    
    def start_web_server(self):
        """Start the web server in a separate thread"""
        def create_handler(*args, **kwargs):
            return LastFmHTTPHandler(*args, daemon=self, **kwargs)
        
        self.server = HTTPServer(('0.0.0.0', self.port), create_handler)
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        print(f"🌐 Web server started on http://localhost:{self.port}")
    
    def run(self):
        """Main daemon loop with web server"""
        print(f"🎵 Starting Last.fm daemon for user: {self.username}")
        print(f"⏰ Update interval: {self.update_interval} seconds")
        print(f"🎨 Theme: {list(THEMES.keys())[list(THEMES.values()).index(self.theme)]}")
        print(f"💾 Cache directory: {self.cache_dir}")
        print(f"🌐 Port: {self.port}")
        print("🛑 Press Ctrl+C to stop")
        print()
        
        # Start web server
        try:
            self.start_web_server()
        except Exception as e:
            print(f"❌ Failed to start web server: {e}")
            return
        
        while self.running:
            try:
                self.update_display()
                
                if self.running:
                    print(f"⏳ Waiting {self.update_interval} seconds...")
                    time.sleep(self.update_interval)
                    
            except KeyboardInterrupt:
                print("\n🛑 Interrupted by user")
                break
            except Exception as e:
                print(f"❌ Error in main loop: {e}")
                time.sleep(10)  # Wait before retrying
        
        # Shutdown web server
        if self.server:
            print("🛑 Stopping web server...")
            self.server.shutdown()
        
        print("👋 Daemon stopped")

def load_environment():
    """Load environment variables from .env file"""
    env_file = Path('.env')
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    if line.startswith('export '):
                        # Handle export format
                        key_value = line[7:]  # Remove 'export '
                        if '=' in key_value:
                            key, value = key_value.split('=', 1)
                            value = value.strip("'\"")
                            os.environ[key] = value
                    else:
                        # Handle direct key=value format
                        key, value = line.split('=', 1)
                        value = value.strip("'\"")
                        os.environ[key] = value
        return True
    return False

def main():
    # Load environment variables
    if not load_environment():
        print("❌ No .env file found. Please create one with your Last.fm credentials:")
        print("export LASTFM_API_KEY='your_api_key'")
        print("export LASTFM_USERNAME='your_username'")
        return
    
    # Get credentials from environment
    api_key = os.getenv('LASTFM_API_KEY')
    username = os.getenv('LASTFM_USERNAME')
    
    if not api_key or not username:
        print("❌ Missing environment variables:")
        print("  LASTFM_API_KEY and LASTFM_USERNAME must be set")
        return
    
    # Get command line arguments or use defaults
    update_interval = 30  # seconds
    theme = 'default'
    port = 8080
    
    if len(sys.argv) > 1:
        try:
            update_interval = int(sys.argv[1])
        except ValueError:
            print("❌ Invalid update interval. Using default 30 seconds.")
    
    if len(sys.argv) > 2:
        theme = sys.argv[2]
        if theme not in THEMES:
            print(f"❌ Unknown theme '{theme}'. Available themes: {list(THEMES.keys())}")
            print("Using default theme.")
            theme = 'default'
    
    if len(sys.argv) > 3:
        try:
            port = int(sys.argv[3])
        except ValueError:
            print("❌ Invalid port number. Using default 8080.")
    
    # Create and run daemon
    daemon = LastFmDaemon(api_key, username, update_interval=update_interval, theme=theme, port=port)
    daemon.run()

if __name__ == "__main__":
    main() 