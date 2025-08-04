# Pi Badge Image Display

A simple Python script to display images in fullscreen on a Raspberry Pi Zero 2 W.

## Features

- Fullscreen image display
- Automatic image resizing to fit screen
- Maintains aspect ratio
- ESC key to exit
- Support for common image formats (JPG, PNG, GIF, etc.)

## Setup Instructions

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
├── display_image.py    # Main display script
├── setup.sh           # Setup script
├── requirements.txt    # Python dependencies
├── README.md          # This file
└── badge_image.jpg    # Sample image (created by setup)
```

## Customization

You can modify the script to:
- Add slideshow functionality
- Include text overlays
- Add transition effects
- Implement remote control via network

## License

This project is open source. Feel free to modify and distribute! 