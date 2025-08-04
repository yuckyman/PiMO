#!/bin/bash

echo "Setting up Pi Badge Image Display..."

# Update package list
echo "Updating package list..."
sudo apt update

# Install Python dependencies
echo "Installing Python dependencies..."
sudo apt install -y python3-pip python3-tk python3-pil python3-pil.imagetk

# Install Pillow via pip (for better image support)
echo "Installing Pillow..."
pip3 install Pillow

# Make the display script executable
echo "Making display script executable..."
chmod +x display_image.py

# Create a sample image if none exists
if [ ! -f "badge_image.jpg" ]; then
    echo "Creating a sample badge image..."
    # Create a simple colored rectangle as placeholder
    python3 -c "
from PIL import Image, ImageDraw, ImageFont
import os

# Create a 800x600 image with a gradient background
img = Image.new('RGB', (800, 600), color='#2E86AB')
draw = ImageDraw.Draw(img)

# Add some text
try:
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 60)
except:
    font = ImageFont.load_default()

text = 'PI BADGE'
bbox = draw.textbbox((0, 0), text, font=font)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]

x = (800 - text_width) // 2
y = (600 - text_height) // 2

draw.text((x, y), text, fill='white', font=font)

# Add subtitle
subtitle = 'Image Display Ready!'
try:
    subtitle_font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 30)
except:
    subtitle_font = ImageFont.load_default()

bbox = draw.textbbox((0, 0), subtitle, subtitle_font)
subtitle_width = bbox[2] - bbox[0]
subtitle_height = bbox[3] - bbox[1]

subtitle_x = (800 - subtitle_width) // 2
subtitle_y = y + text_height + 20

draw.text((subtitle_x, subtitle_y), subtitle, fill='#F7DC6F', font=subtitle_font)

img.save('badge_image.jpg')
print('Sample image created: badge_image.jpg')
"

fi

echo ""
echo "Setup complete! You can now run:"
echo "  python3 display_image.py"
echo "  or"
echo "  python3 display_image.py your_image.jpg"
echo ""
echo "Press ESC to exit the display" 