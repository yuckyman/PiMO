#!/usr/bin/env python3
"""
Simple image display script for Raspberry Pi Zero 2 W
Displays an image in fullscreen mode
"""

import tkinter as tk
from PIL import Image, ImageTk
import os
import sys
import time

class ImageDisplay:
    def __init__(self, image_path):
        self.root = tk.Tk()
        self.root.title("Pi Badge Image Display")
        
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Set window to fullscreen
        self.root.geometry(f"{screen_width}x{screen_height}+0+0")
        self.root.attributes('-fullscreen', True)
        
        # Load and resize image
        self.load_image(image_path, screen_width, screen_height)
        
        # Bind escape key to exit
        self.root.bind('<Escape>', lambda e: self.root.quit())
        
    def load_image(self, image_path, screen_width, screen_height):
        """Load and resize image to fit screen"""
        try:
            # Open image
            image = Image.open(image_path)
            
            # Calculate aspect ratio
            img_width, img_height = image.size
            aspect_ratio = img_width / img_height
            screen_ratio = screen_width / screen_height
            
            # Resize image to fit screen while maintaining aspect ratio
            if aspect_ratio > screen_ratio:
                # Image is wider than screen
                new_width = screen_width
                new_height = int(screen_width / aspect_ratio)
            else:
                # Image is taller than screen
                new_height = screen_height
                new_width = int(screen_height * aspect_ratio)
            
            # Resize image
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(image)
            
            # Create label and center it
            label = tk.Label(self.root, image=photo)
            label.image = photo  # Keep a reference
            label.place(relx=0.5, rely=0.5, anchor='center')
            
        except Exception as e:
            print(f"Error loading image: {e}")
            # Create error message
            error_label = tk.Label(self.root, text=f"Error loading image: {e}", 
                                 font=('Arial', 20), fg='red')
            error_label.place(relx=0.5, rely=0.5, anchor='center')
    
    def run(self):
        """Start the display"""
        self.root.mainloop()

def main():
    # Default image path
    default_image = "badge_image.jpg"
    
    # Get image path from command line or use default
    image_path = sys.argv[1] if len(sys.argv) > 1 else default_image
    
    # Check if image exists
    if not os.path.exists(image_path):
        print(f"Image file '{image_path}' not found!")
        print("Please provide a valid image path as argument.")
        print("Example: python display_image.py my_image.jpg")
        return
    
    print(f"Displaying image: {image_path}")
    print("Press ESC to exit")
    
    # Create and run display
    display = ImageDisplay(image_path)
    display.run()

if __name__ == "__main__":
    main() 