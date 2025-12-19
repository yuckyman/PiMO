# Pi Badge - Last.fm Music Display

A clean, idempotent system that displays your current music on a Raspberry Pi badge with album art.

## Features

- 🎵 **Real-time music display** - Shows your current Last.fm track
- 🖼️ **Album art integration** - Downloads and displays album artwork
- 💾 **Smart caching** - Only downloads new tracks, caches everything
- 🔄 **Idempotent operation** - Safe to run repeatedly
- ⏰ **Configurable updates** - Set your own update interval
- 🚫 **No tkinter issues** - Works on all platforms including macOS

## Quick Start

### 1. Set up your Last.fm credentials
Create a `.env` file with your Last.fm API credentials:
```bash
export LASTFM_API_KEY='your_api_key_here'
export LASTFM_USERNAME='your_username_here'
```

Get your API key from: https://www.last.fm/api/account/create

### 2. Run the daemon
```bash
# Start with default 30-second updates
uv run lastfm_daemon.py

# Or with custom update interval (10 seconds)
uv run lastfm_daemon.py 10
```

### 3. Display on Pi Badge
```bash
# Check current display
uv run display_current.py

# Display on Pi Badge
python3 display_image.py current_display.png
```

## How it Works

### Daemon Mode (`lastfm_daemon.py`)
- Runs continuously in the background
- Checks Last.fm API every 30 seconds (configurable)
- Downloads album art and creates display images
- Caches everything to avoid re-downloading
- Creates `current_display.png` symlink for easy access
- Only updates when track changes (idempotent)

### Caching System
- **Cache directory**: `cache/`
- **Album art**: `track_[hash]_art.png` (240x240 base)
- **Full display**: `track_[hash]_full.png` (240x320 base, configurable upscaling)
- **Current symlink**: `current_display.png` → latest display

### Display Options
- **Album art only**: 240x240 PNG format (base size)
- **Full display**: 240x320 base resolution with configurable upscaling
- **Upscaling options**: 1x (240x320), 2x (480x640), 3x (720x960), 4x (960x1280)
- **Text fallback**: When no album art available

## Files

- `lastfm_daemon.py` - Main daemon script
- `display_current.py` - Show current display info
- `display_image.py` - Original Pi Badge display script
- `cache/` - Album art and display cache
- `.env` - Your Last.fm credentials
- `current_display.png` - Symlink to current display

## Pi Deployment

### 1. Copy files to Pi
```bash
scp -r . pi@raspberrypi.local:~/pibadge/
```

### 2. Set up on Pi
```bash
ssh pi@raspberrypi.local
cd pibadge
pip3 install requests pillow
```

### 3. Run daemon
```bash
# Start daemon
python3 lastfm_daemon.py &

# Display current image
python3 display_image.py current_display.png
```

### 4. Auto-start on boot (optional)
Add to `/etc/rc.local`:
```bash
cd /home/pi/pibadge && python3 lastfm_daemon.py &
```

## Configuration

### Environment Variables
- `LASTFM_API_KEY` - Your Last.fm API key
- `LASTFM_USERNAME` - Your Last.fm username

### Command Line Options
- Update interval (seconds): `uv run lastfm_daemon.py 60`
- Upscale factor (1-4x): `uv run lastfm_daemon.py 30 2` (30s updates, 2x upscaling)
- Base resolution: 240x320 pixels
- Supported upscaling: 1x (240x320), 2x (480x640), 3x (720x960), 4x (960x1280)

### Cache Management
- Cache is automatically managed
- Old tracks are kept for reuse
- Cache directory: `cache/`

## Troubleshooting

### No display shows
- Check if daemon is running: `ps aux | grep lastfm_daemon`
- Check current display: `uv run display_current.py`
- Verify credentials in `.env` file

### API errors
- Verify your API key and username
- Check internet connection
- Last.fm API has generous limits (5,000 requests/day)

### Cache issues
- Delete `cache/` directory to clear cache
- Restart daemon: `pkill -f lastfm_daemon`

## Development

### Testing locally
```bash
# Start daemon with short interval
uv run lastfm_daemon.py 10

# Check current display
uv run display_current.py
```

### Customization
- Modify `create_album_display()` in `lastfm_daemon.py` for layout changes
- Adjust colors, fonts, and positioning
- Add more track information as needed

## License

This project is open source. Feel free to modify and distribute!

---

🎵 Your Pi Badge will now show your music taste to the world! 🎸 