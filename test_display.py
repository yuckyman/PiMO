#!/usr/bin/env python3
"""
Test script to verify display functionality
Creates a test pattern and displays it
"""

from PIL import Image, ImageDraw, ImageFont
import tkinter as tk
from PIL import ImageTk
import sys

def create_test_pattern():
    """Create a test pattern image"""
    # Create a 800x600 test pattern
    img = Image.new('RGB', (800, 600), color='#1a1a1a')
    draw = ImageDraw.Draw(img)
    
    # Draw some test patterns
    colors = ['#ff0000', '#00ff00', '#0000ff', '#ffff00', '#ff00ff', '#00ffff']
    
    # Draw colored rectangles
    for i, color in enumerate(colors):
        x = (i % 3) * 266
        y = (i // 3) * 300
        draw.rectangle([x, y, x + 266, y + 300], fill=color, outline='white', width=2)
        
        # Add text
        try:
            font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 30)
        except:
            font = ImageFont.load_default()
        
        text = f"TEST {i+1}"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        text_x = x + (266 - text_width) // 2
        text_y = y + (300 - text_height) // 2
        
        draw.text((text_x, text_y), text, fill='white', font=font)
    
    # Add title
    try:
        title_font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 40)
    except:
        title_font = ImageFont.load_default()
    
    title = "DISPLAY TEST"
    bbox = draw.textbbox((0, 0), title, title_font)
    title_width = bbox[2] - bbox[0]
    title_x = (800 - title_width) // 2
    draw.text((title_x, 20), title, fill='white', font=title_font)
    
    return img

def test_display():
    """Test the display functionality"""
    print("Creating test pattern...")
    test_img = create_test_pattern()
    
    # Save test image
    test_img.save('test_pattern.jpg')
    print("Test pattern saved as 'test_pattern.jpg'")
    
    # Display the test pattern
    root = tk.Tk()
    root.title("Display Test")
    
    # Get screen dimensions
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    
    # Set window to fullscreen
    root.geometry(f"{screen_width}x{screen_height}+0+0")
    root.attributes('-fullscreen', True)
    
    # Resize test image to fit screen
    aspect_ratio = 800 / 600
    screen_ratio = screen_width / screen_height
    
    if aspect_ratio > screen_ratio:
        new_width = screen_width
        new_height = int(screen_width / aspect_ratio)
    else:
        new_height = screen_height
        new_width = int(screen_height * aspect_ratio)
    
    test_img = test_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    photo = ImageTk.PhotoImage(test_img)
    
    # Create label and center it
    label = tk.Label(root, image=photo)
    label.image = photo
    label.place(relx=0.5, rely=0.5, anchor='center')
    
    # Bind escape key
    root.bind('<Escape>', lambda e: root.quit())
    
    print("Display test running...")
    print("You should see a colored test pattern")
    print("Press ESC to exit")
    
    root.mainloop()
    print("Test complete!")

if __name__ == "__main__":
    test_display() 