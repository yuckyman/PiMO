# Quick Start Guide

## 🚀 Get Your Pi Badge Running in 5 Minutes

### Step 1: Flash Your SD Card
1. Download [Raspberry Pi OS Lite](https://www.raspberrypi.com/software/)
2. Flash it to your micro SD card using Raspberry Pi Imager
3. Before ejecting, create these files in the boot partition:
   - `ssh` (empty file)
   - `wpa_supplicant.conf` (if using WiFi)

### Step 2: Boot Your Pi
1. Insert SD card into Pi Zero 2 W
2. Connect power and wait for boot
3. Connect via SSH: `ssh pi@raspberrypi.local`

### Step 3: Copy Files
```bash
# Clone or copy the piBadge files to your Pi
git clone <your-repo> piBadge
cd piBadge
```

### Step 4: Run Setup
```bash
chmod +x setup.sh
./setup.sh
```

### Step 5: Test It!
```bash
# Test the display
python3 test_display.py

# Or display your own image
python3 display_image.py your_image.jpg
```

## 🎯 What You Should See
- A fullscreen image display
- Press ESC to exit
- The setup script creates a sample badge image

## 🔧 Troubleshooting
- **No display?** Check HDMI connection and power
- **Script not found?** Make sure you're in the right directory
- **Permission denied?** Run `chmod +x *.py`

## 📱 Next Steps
- Add your own images
- Set up auto-start on boot
- Customize the display script

That's it! Your Pi Badge should be displaying images in no time! 🎉 