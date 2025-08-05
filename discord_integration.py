"""
Discord Integration for Last.fm Tamagotchi
Connects to Discord to share pet updates and achievements
"""

import requests
import json
import os
from datetime import datetime
from config import DISCORD_CONFIG

class DiscordIntegration:
    def __init__(self):
        self.webhook_url = DISCORD_CONFIG['webhook_url']
        self.bot_token = DISCORD_CONFIG['bot_token']
        self.channel_id = DISCORD_CONFIG['channel_id']
        self.enabled = DISCORD_CONFIG['enabled'] and self.webhook_url
        
    def send_webhook(self, content, embeds=None):
        """Send a webhook message to Discord"""
        if not self.enabled:
            return False
            
        try:
            payload = {
                'content': content,
                'username': 'Melody Tamagotchi',
                'avatar_url': 'https://i.imgur.com/example.png'  # Add a cute pet avatar
            }
            
            if embeds:
                payload['embeds'] = embeds
                
            response = requests.post(self.webhook_url, json=payload)
            return response.status_code == 204
            
        except Exception as e:
            print(f"Discord webhook error: {e}")
            return False
    
    def pet_fed(self, track_info, pet_state):
        """Notify Discord when pet is fed"""
        if not self.enabled:
            return
            
        track_name = track_info.get('name', 'Unknown Track')
        artist_name = track_info.get('artist', {}).get('#text', 'Unknown Artist')
        
        embed = {
            'title': '🎵 Melody was fed!',
            'description': f'**{track_name}** by **{artist_name}**',
            'color': 0xFF69B4,
            'fields': [
                {
                    'name': 'Pet Stats',
                    'value': f"Hunger: {pet_state['hunger']}% | Happiness: {pet_state['happiness']}% | Energy: {pet_state['energy']}%",
                    'inline': True
                },
                {
                    'name': 'Total Scrobbles',
                    'value': str(pet_state['total_scrobbles']),
                    'inline': True
                }
            ],
            'timestamp': datetime.now().isoformat()
        }
        
        self.send_webhook(f"🎵 {pet_state['name']} enjoyed listening to **{track_name}**!", [embed])
    
    def pet_level_up(self, pet_state):
        """Notify Discord when pet levels up"""
        if not self.enabled:
            return
            
        embed = {
            'title': '🎉 Level Up!',
            'description': f"{pet_state['name']} reached level {pet_state['level']}!",
            'color': 0xFFD700,
            'fields': [
                {
                    'name': 'New Level',
                    'value': str(pet_state['level']),
                    'inline': True
                },
                {
                    'name': 'Experience',
                    'value': f"{pet_state['experience']}/{pet_state['level'] * 100}",
                    'inline': True
                }
            ],
            'timestamp': datetime.now().isoformat()
        }
        
        self.send_webhook(f"🎉 **{pet_state['name']}** reached level **{pet_state['level']}**!", [embed])
    
    def pet_evolved(self, pet_state, evolution_stage):
        """Notify Discord when pet evolves"""
        if not self.enabled:
            return
            
        evolution_names = ['Baby', 'Growing', 'Teen', 'Adult', 'Legendary']
        stage_name = evolution_names[min(evolution_stage, len(evolution_names) - 1)]
        
        embed = {
            'title': '🌟 Evolution!',
            'description': f"{pet_state['name']} evolved into a {stage_name} Melody!",
            'color': 0x8A2BE2,
            'fields': [
                {
                    'name': 'Evolution Stage',
                    'value': stage_name,
                    'inline': True
                },
                {
                    'name': 'Level',
                    'value': str(pet_state['level']),
                    'inline': True
                }
            ],
            'timestamp': datetime.now().isoformat()
        }
        
        self.send_webhook(f"🌟 **{pet_state['name']}** evolved into a **{stage_name} Melody**!", [embed])
    
    def pet_mood_change(self, pet_state, old_mood, new_mood):
        """Notify Discord when pet's mood changes significantly"""
        if not self.enabled:
            return
            
        # Only notify for significant mood changes
        mood_importance = {
            'ecstatic': 5,
            'happy': 4,
            'neutral': 3,
            'sad': 2,
            'starving': 1
        }
        
        old_importance = mood_importance.get(old_mood, 3)
        new_importance = mood_importance.get(new_mood, 3)
        
        # Only notify if mood changed by 2+ levels
        if abs(new_importance - old_importance) >= 2:
            mood_emojis = {
                'ecstatic': '😍',
                'happy': '😊',
                'neutral': '😐',
                'sad': '😢',
                'starving': '😵'
            }
            
            embed = {
                'title': f'{mood_emojis.get(new_mood, "😊")} Mood Change',
                'description': f"{pet_state['name']} is now feeling {new_mood}!",
                'color': 0x4ECDC4 if new_importance > old_importance else 0xFF6B6B,
                'fields': [
                    {
                        'name': 'Current Mood',
                        'value': new_mood.title(),
                        'inline': True
                    },
                    {
                        'name': 'Stats',
                        'value': f"Hunger: {pet_state['hunger']}% | Happiness: {pet_state['happiness']}%",
                        'inline': True
                    }
                ],
                'timestamp': datetime.now().isoformat()
            }
            
            self.send_webhook(f"{mood_emojis.get(new_mood, '😊')} **{pet_state['name']}** is feeling {new_mood}!", [embed])
    
    def daily_summary(self, pet_state, scrobbles_today):
        """Send daily summary to Discord"""
        if not self.enabled:
            return
            
        embed = {
            'title': '📊 Daily Summary',
            'description': f"Here's how {pet_state['name']} did today!",
            'color': 0x45B7D1,
            'fields': [
                {
                    'name': 'Scrobbles Today',
                    'value': str(scrobbles_today),
                    'inline': True
                },
                {
                    'name': 'Current Level',
                    'value': f"{pet_state['level']} ({pet_state['experience']}/{pet_state['level'] * 100} XP)",
                    'inline': True
                },
                {
                    'name': 'Current Mood',
                    'value': pet_state['mood'].title(),
                    'inline': True
                },
                {
                    'name': 'Stats',
                    'value': f"Hunger: {pet_state['hunger']}% | Happiness: {pet_state['happiness']}% | Energy: {pet_state['energy']}%",
                    'inline': False
                }
            ],
            'timestamp': datetime.now().isoformat()
        }
        
        self.send_webhook(f"📊 **{pet_state['name']}**'s daily summary!", [embed])
    
    def achievement_unlocked(self, achievement_name, description):
        """Notify Discord when an achievement is unlocked"""
        if not self.enabled:
            return
            
        embed = {
            'title': '🏆 Achievement Unlocked!',
            'description': f"**{achievement_name}**\n{description}",
            'color': 0xFFD700,
            'timestamp': datetime.now().isoformat()
        }
        
        self.send_webhook(f"🏆 Achievement unlocked: **{achievement_name}**!", [embed])

# Example usage:
if __name__ == "__main__":
    # Test Discord integration
    discord = DiscordIntegration()
    
    if discord.enabled:
        print("Discord integration enabled!")
        discord.send_webhook("🎵 Melody Tamagotchi is now online!")
    else:
        print("Discord integration disabled. Set DISCORD_WEBHOOK_URL to enable.")