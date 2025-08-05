# Pi Badge - Last.fm Tamagotchi

A Raspberry Pi Zero 2 W badge that displays a digital pet that feeds on your Last.fm scrobbles! Your music listening habits power a cute tamagotchi that grows, evolves, and gets happy when you listen to music.

## 🌟 Features

- **Last.fm Tamagotchi**: Digital pet that feeds on your music scrobbles
- **Evolution System**: Pet evolves through 5 stages as it levels up
- **Real-time Display**: Beautiful fullscreen interface showing pet stats
- **Discord Integration**: Share pet updates with your Discord server
- **Auto-start**: Runs automatically when your Pi boots
- **Original Image Display**: Still supports the original image display functionality

## Original Features

- Fullscreen image display
- Automatic image resizing to fit screen
- Maintains aspect ratio
- ESC key to exit
- Support for common image formats (JPG, PNG, GIF, etc.)

## 🎵 Quick Start - Tamagotchi Mode

### 1. Get Last.fm API Key
1. Go to [Last.fm API](https://www.last.fm/api/account/create)
2. Create an account and get your API key
3. Note your Last.fm username

### 2. Set Up Your Pi
```bash
# Run the tamagotchi setup
chmod +x setup_tamagotchi.sh
./setup_tamagotchi.sh
```

### 3. Configure Environment
```bash
# Copy the template
cp .env.template .env

# Edit with your details
nano .env
```

Add your Last.fm credentials:
```
LASTFM_API_KEY=your_api_key_here
LASTFM_USERNAME=your_username_here
```

### 4. Start Your Tamagotchi
```bash
# Run manually
python3 lastfm_tamagotchi.py

# Or start as a service
sudo systemctl start tamagotchi
```

## 🎮 Demo Mode

Want to test without Last.fm? Run the demo:
```bash
python3 demo_tamagotchi.py
```

## 📖 Original Setup Instructions

### 1. Prepare Your Micro SD Card

1. Download and flash Raspberry Pi OS Lite to your micro SD card
2. Enable SSH and configure WiFi (optional) by creating these files in the boot partition:
   - `ssh` (empty file)
   - `wpa_supplicant.conf` (if using WiFi)

### 2. Boot Your Pi Zero 2 W

1. Insert the micro SD card into your Pi Zero 2 W
2. Connect power and wait for it to boot
3. Connect via SSH or use a monitor/keyboard

### 3. Install Dependencies

Run the setup script:

```bash
chmod +x setup.sh
./setup.sh
```

Or install manually:

```bash
sudo apt update
sudo apt install -y python3-pip python3-tk python3-pil python3-pil.imagetk
pip3 install Pillow
chmod +x display_image.py
```

### 4. Add Your Images

Place your image files in the same directory as the script. Supported formats:
- JPG/JPEG
- PNG
- GIF
- BMP
- TIFF

## Usage

### Basic Usage

Display the default image (`badge_image.jpg`):
```bash
python3 display_image.py
```

### Custom Image

Display a specific image:
```bash
python3 display_image.py your_image.jpg
```

### Auto-start on Boot (Optional)

To make the display start automatically when the Pi boots:

1. Edit the autostart file:
```bash
sudo nano /etc/xdg/lxsession/LXDE-pi/autostart
```

2. Add this line:
```
@python3 /path/to/your/display_image.py
```

3. Replace `/path/to/your/` with the actual path to your script.

## Controls

- **ESC**: Exit the display
- **Ctrl+C**: Force quit (if running in terminal)

## Troubleshooting

### No Display Shows
- Check if your image file exists and is readable
- Ensure you have a display connected
- Try running with a test image first

### Image Doesn't Fit Screen
- The script automatically resizes images to fit the screen
- Images maintain their aspect ratio
- For best results, use images with 16:9 or 4:3 aspect ratios

### Performance Issues
- Use JPG format for large images
- Optimize image size (800x600 or 1920x1080 recommended)
- Close other applications to free up memory

## Hardware Requirements

- Raspberry Pi Zero 2 W
- Micro SD card (8GB+ recommended)
- Display (HDMI or composite)
- Power supply (5V, 2.5A recommended)

## File Structure

```
piBadge/
├── lastfm_tamagotchi.py    # Main tamagotchi application
├── demo_tamagotchi.py      # Demo version for testing
├── config.py               # Configuration settings
├── discord_integration.py  # Discord notification system
├── setup_tamagotchi.sh    # Tamagotchi setup script
├── display_image.py        # Original image display
├── setup.sh               # Original setup script
├── requirements.txt        # Python dependencies
├── test_tamagotchi.py     # Test suite
├── .env.template          # Environment template
├── README_TAMAGOTCHI.md   # Detailed tamagotchi docs
├── README.md              # This file
└── badge_image.jpg        # Sample image
```

## 🎨 Tamagotchi Customization

You can customize your tamagotchi by editing `config.py`:
- Change pet name and appearance
- Adjust evolution stages
- Modify stat decay rates
- Add new moods and features

## 📖 Original Customization

You can modify the original image display script to:
- Add slideshow functionality
- Include text overlays
- Add transition effects
- Implement remote control via network

## License

This project is open source. Feel free to modify and distribute! 