#!/usr/bin/env python3
"""
Last.fm Tamagotchi - A digital pet that feeds on your music scrobbles!
"""

import tkinter as tk
from PIL import Image, ImageTk, ImageDraw, ImageFont
import requests
import json
import time
import threading
import os
from datetime import datetime, timedelta
import random

class LastFmTamagotchi:
    def __init__(self, api_key, username):
        self.api_key = api_key
        self.username = username
        self.pet_state = {
            'name': 'Melody',
            'hunger': 50,
            'happiness': 50,
            'energy': 50,
            'level': 1,
            'experience': 0,
            'mood': 'happy',
            'last_fed': None,
            'total_scrobbles': 0,
            'favorite_genres': [],
            'evolution_stage': 0
        }
        
        # Initialize display
        self.root = tk.Tk()
        self.root.title("Last.fm Tamagotchi")
        
        # Get screen dimensions
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        
        # Set window to fullscreen
        self.root.geometry(f"{self.screen_width}x{self.screen_height}+0+0")
        self.root.attributes('-fullscreen', True)
        
        # Bind escape key to exit
        self.root.bind('<Escape>', lambda e: self.root.quit())
        
        # Create canvas for drawing
        self.canvas = tk.Canvas(self.root, width=self.screen_width, height=self.screen_height, bg='black')
        self.canvas.pack()
        
        # Start background threads
        self.running = True
        self.scrobble_thread = threading.Thread(target=self.monitor_scrobbles, daemon=True)
        self.scrobble_thread.start()
        
        # Start animation loop
        self.animate()
    
    def get_recent_tracks(self):
        """Fetch recent tracks from Last.fm API"""
        try:
            url = "http://ws.audioscrobbler.com/2.0/"
            params = {
                'method': 'user.getrecenttracks',
                'user': self.username,
                'api_key': self.api_key,
                'format': 'json',
                'limit': 10
            }
            
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                return data.get('recenttracks', {}).get('track', [])
            else:
                print(f"API Error: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Error fetching tracks: {e}")
            return []
    
    def monitor_scrobbles(self):
        """Monitor for new scrobbles and feed the pet"""
        last_check = None
        
        while self.running:
            try:
                tracks = self.get_recent_tracks()
                if tracks:
                    latest_track = tracks[0]
                    
                    # Check if this is a new scrobble
                    if (last_check is None or 
                        latest_track.get('@attr', {}).get('nowplaying') != 'true'):
                        
                        # Feed the pet!
                        self.feed_pet(latest_track)
                        last_check = latest_track.get('date', {}).get('#text')
                
                # Update pet stats over time
                self.update_pet_stats()
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                print(f"Error in scrobble monitoring: {e}")
                time.sleep(60)
    
    def feed_pet(self, track):
        """Feed the pet with a new scrobble"""
        print(f"🎵 Feeding pet with: {track.get('name', 'Unknown')} by {track.get('artist', {}).get('#text', 'Unknown')}")
        
        # Increase stats based on the track
        self.pet_state['hunger'] = min(100, self.pet_state['hunger'] + 15)
        self.pet_state['happiness'] = min(100, self.pet_state['happiness'] + 10)
        self.pet_state['energy'] = min(100, self.pet_state['energy'] + 5)
        self.pet_state['experience'] += 10
        self.pet_state['total_scrobbles'] += 1
        self.pet_state['last_fed'] = datetime.now()
        
        # Check for level up
        if self.pet_state['experience'] >= self.pet_state['level'] * 100:
            self.level_up()
        
        # Update mood based on stats
        self.update_mood()
    
    def level_up(self):
        """Level up the pet"""
        self.pet_state['level'] += 1
        self.pet_state['experience'] = 0
        print(f"🎉 {self.pet_state['name']} reached level {self.pet_state['level']}!")
        
        # Check for evolution
        if self.pet_state['level'] % 5 == 0:
            self.evolve()
    
    def evolve(self):
        """Evolve the pet"""
        self.pet_state['evolution_stage'] += 1
        print(f"🌟 {self.pet_state['name']} is evolving!")
    
    def update_mood(self):
        """Update pet's mood based on stats"""
        avg_stats = (self.pet_state['hunger'] + self.pet_state['happiness'] + self.pet_state['energy']) / 3
        
        if avg_stats >= 80:
            self.pet_state['mood'] = 'ecstatic'
        elif avg_stats >= 60:
            self.pet_state['mood'] = 'happy'
        elif avg_stats >= 40:
            self.pet_state['mood'] = 'neutral'
        elif avg_stats >= 20:
            self.pet_state['mood'] = 'sad'
        else:
            self.pet_state['mood'] = 'starving'
    
    def update_pet_stats(self):
        """Gradually decrease stats over time"""
        # Decrease stats slowly
        self.pet_state['hunger'] = max(0, self.pet_state['hunger'] - 0.5)
        self.pet_state['happiness'] = max(0, self.pet_state['happiness'] - 0.3)
        self.pet_state['energy'] = max(0, self.pet_state['energy'] - 0.2)
        
        # Update mood
        self.update_mood()
    
    def draw_pet(self):
        """Draw the pet on the canvas"""
        self.canvas.delete("all")
        
        # Create a new image for the pet
        img_size = min(self.screen_width, self.screen_height) // 3
        img = Image.new('RGBA', (img_size, img_size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Draw pet based on evolution stage and mood
        self.draw_pet_sprite(draw, img_size)
        
        # Convert to PhotoImage
        photo = ImageTk.PhotoImage(img)
        
        # Display on canvas
        self.canvas.create_image(self.screen_width // 2, self.screen_height // 2 - 50, image=photo)
        self.canvas.image = photo  # Keep reference
        
        # Draw stats
        self.draw_stats()
        
        # Draw status text
        self.draw_status()
    
    def draw_pet_sprite(self, draw, size):
        """Draw the pet sprite based on evolution and mood"""
        center_x, center_y = size // 2, size // 2
        radius = size // 4
        
        # Base color based on evolution stage
        colors = ['#FFB6C1', '#FF69B4', '#FF1493', '#8A2BE2', '#FFD700']
        base_color = colors[min(self.pet_state['evolution_stage'], len(colors) - 1)]
        
        # Mood affects brightness
        mood_brightness = {
            'ecstatic': 1.3,
            'happy': 1.1,
            'neutral': 1.0,
            'sad': 0.8,
            'starving': 0.6
        }
        
        brightness = mood_brightness.get(self.pet_state['mood'], 1.0)
        
        # Draw body
        body_color = self.adjust_color(base_color, brightness)
        draw.ellipse([center_x - radius, center_y - radius, 
                     center_x + radius, center_y + radius], 
                    fill=body_color, outline='white', width=2)
        
        # Draw eyes
        eye_size = radius // 4
        eye_offset = radius // 3
        
        # Eye expression based on mood
        if self.pet_state['mood'] in ['ecstatic', 'happy']:
            # Happy eyes
            draw.ellipse([center_x - eye_offset - eye_size, center_y - eye_offset - eye_size,
                         center_x - eye_offset + eye_size, center_y - eye_offset + eye_size], 
                        fill='white')
            draw.ellipse([center_x + eye_offset - eye_size, center_y - eye_offset - eye_size,
                         center_x + eye_offset + eye_size, center_y - eye_offset + eye_size], 
                        fill='white')
        else:
            # Sad eyes
            draw.ellipse([center_x - eye_offset - eye_size, center_y - eye_offset - eye_size//2,
                         center_x - eye_offset + eye_size, center_y - eye_offset + eye_size//2], 
                        fill='white')
            draw.ellipse([center_x + eye_offset - eye_size, center_y - eye_offset - eye_size//2,
                         center_x + eye_offset + eye_size, center_y - eye_offset + eye_size//2], 
                        fill='white')
        
        # Draw mouth based on mood
        mouth_y = center_y + radius // 2
        if self.pet_state['mood'] in ['ecstatic', 'happy']:
            # Happy mouth
            draw.arc([center_x - radius//3, mouth_y - radius//3,
                     center_x + radius//3, mouth_y + radius//3], 
                    0, 180, fill='white', width=3)
        else:
            # Sad mouth
            draw.arc([center_x - radius//3, mouth_y - radius//3,
                     center_x + radius//3, mouth_y + radius//3], 
                    180, 360, fill='white', width=3)
        
        # Add evolution details
        if self.pet_state['evolution_stage'] > 0:
            # Add wings or other features
            wing_color = self.adjust_color('#87CEEB', brightness)
            draw.ellipse([center_x - radius*1.5, center_y - radius//2,
                         center_x - radius*0.8, center_y + radius//2], 
                        fill=wing_color, outline='white', width=1)
            draw.ellipse([center_x + radius*0.8, center_y - radius//2,
                         center_x + radius*1.5, center_y + radius//2], 
                        fill=wing_color, outline='white', width=1)
    
    def adjust_color(self, color, brightness):
        """Adjust color brightness"""
        # Simple brightness adjustment
        r = int(int(color[1:3], 16) * brightness)
        g = int(int(color[3:5], 16) * brightness)
        b = int(int(color[5:7], 16) * brightness)
        return f'#{min(255, r):02x}{min(255, g):02x}{min(255, b):02x}'
    
    def draw_stats(self):
        """Draw pet stats bars"""
        bar_width = self.screen_width // 3
        bar_height = 20
        start_x = (self.screen_width - bar_width) // 2
        start_y = self.screen_height // 2 + 100
        
        stats = [
            ('Hunger', self.pet_state['hunger'], '#FF6B6B'),
            ('Happiness', self.pet_state['happiness'], '#4ECDC4'),
            ('Energy', self.pet_state['energy'], '#45B7D1')
        ]
        
        for i, (name, value, color) in enumerate(stats):
            y = start_y + i * (bar_height + 10)
            
            # Draw label
            self.canvas.create_text(start_x - 10, y + bar_height//2, 
                                  text=name, fill='white', anchor='e', font=('Arial', 12))
            
            # Draw background bar
            self.canvas.create_rectangle(start_x, y, start_x + bar_width, y + bar_height,
                                       fill='#333333', outline='white')
            
            # Draw filled bar
            fill_width = int((value / 100) * bar_width)
            self.canvas.create_rectangle(start_x, y, start_x + fill_width, y + bar_height,
                                       fill=color, outline='white')
            
            # Draw percentage
            self.canvas.create_text(start_x + bar_width + 10, y + bar_height//2,
                                  text=f"{int(value)}%", fill='white', anchor='w', font=('Arial', 12))
    
    def draw_status(self):
        """Draw status information"""
        status_y = self.screen_height - 100
        
        # Pet name and level
        self.canvas.create_text(self.screen_width // 2, status_y,
                              text=f"{self.pet_state['name']} - Level {self.pet_state['level']}",
                              fill='white', font=('Arial', 16, 'bold'))
        
        # Mood
        mood_text = f"Mood: {self.pet_state['mood'].title()}"
        self.canvas.create_text(self.screen_width // 2, status_y + 25,
                              text=mood_text, fill='white', font=('Arial', 12))
        
        # Total scrobbles
        scrobble_text = f"Total Scrobbles: {self.pet_state['total_scrobbles']}"
        self.canvas.create_text(self.screen_width // 2, status_y + 45,
                              text=scrobble_text, fill='white', font=('Arial', 12))
        
        # Last fed
        if self.pet_state['last_fed']:
            time_diff = datetime.now() - self.pet_state['last_fed']
            if time_diff.total_seconds() < 60:
                last_fed_text = "Last fed: Just now!"
            else:
                minutes = int(time_diff.total_seconds() // 60)
                last_fed_text = f"Last fed: {minutes} minutes ago"
        else:
            last_fed_text = "Last fed: Never"
        
        self.canvas.create_text(self.screen_width // 2, status_y + 65,
                              text=last_fed_text, fill='white', font=('Arial', 12))
    
    def animate(self):
        """Animation loop"""
        self.draw_pet()
        self.root.after(1000, self.animate)  # Update every second
    
    def run(self):
        """Start the tamagotchi"""
        print(f"🎵 Starting Last.fm Tamagotchi for {self.username}")
        print("Press ESC to exit")
        self.root.mainloop()
        self.running = False

def main():
    # You'll need to get these from Last.fm
    API_KEY = os.getenv('LASTFM_API_KEY')
    USERNAME = os.getenv('LASTFM_USERNAME')
    
    if not API_KEY or not USERNAME:
        print("Please set LASTFM_API_KEY and LASTFM_USERNAME environment variables")
        print("Get your API key from: https://www.last.fm/api/account/create")
        return
    
    tamagotchi = LastFmTamagotchi(API_KEY, USERNAME)
    tamagotchi.run()

if __name__ == "__main__":
    main()