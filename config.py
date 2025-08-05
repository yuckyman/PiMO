"""
Configuration settings for Last.fm Tamagotchi
"""

import os

# Last.fm API Configuration
LASTFM_API_KEY = os.getenv('LASTFM_API_KEY')
LASTFM_USERNAME = os.getenv('LASTFM_USERNAME')

# Pet Configuration
PET_CONFIG = {
    'default_name': 'Melody',
    'max_stats': 100,
    'min_stats': 0,
    'hunger_decay_rate': 0.5,  # per minute
    'happiness_decay_rate': 0.3,  # per minute
    'energy_decay_rate': 0.2,  # per minute
    'feed_hunger_bonus': 15,
    'feed_happiness_bonus': 10,
    'feed_energy_bonus': 5,
    'feed_experience_bonus': 10,
    'level_up_experience_multiplier': 100,
    'evolution_levels': [5, 10, 15, 20, 25],  # Levels when pet evolves
}

# Display Configuration
DISPLAY_CONFIG = {
    'update_interval': 1000,  # milliseconds
    'scrobble_check_interval': 30,  # seconds
    'background_color': 'black',
    'text_color': 'white',
    'font_family': 'Arial',
    'title_font_size': 16,
    'body_font_size': 12,
}

# Evolution Stages
EVOLUTION_STAGES = [
    {
        'name': 'Baby Melody',
        'color': '#FFB6C1',
        'features': []
    },
    {
        'name': 'Growing Melody',
        'color': '#FF69B4',
        'features': ['wings']
    },
    {
        'name': 'Teen Melody',
        'color': '#FF1493',
        'features': ['wings', 'glow']
    },
    {
        'name': 'Adult Melody',
        'color': '#8A2BE2',
        'features': ['wings', 'glow', 'crown']
    },
    {
        'name': 'Legendary Melody',
        'color': '#FFD700',
        'features': ['wings', 'glow', 'crown', 'aura']
    }
]

# Mood Configuration
MOODS = {
    'ecstatic': {
        'min_stats': 80,
        'brightness': 1.3,
        'description': 'Overjoyed with music!'
    },
    'happy': {
        'min_stats': 60,
        'brightness': 1.1,
        'description': 'Feeling great!'
    },
    'neutral': {
        'min_stats': 40,
        'brightness': 1.0,
        'description': 'Doing okay.'
    },
    'sad': {
        'min_stats': 20,
        'brightness': 0.8,
        'description': 'Needs more music...'
    },
    'starving': {
        'min_stats': 0,
        'brightness': 0.6,
        'description': 'Desperately needs music!'
    }
}

# Discord Integration (for future use)
DISCORD_CONFIG = {
    'enabled': False,
    'webhook_url': os.getenv('DISCORD_WEBHOOK_URL'),
    'bot_token': os.getenv('DISCORD_BOT_TOKEN'),
    'channel_id': os.getenv('DISCORD_CHANNEL_ID'),
}

# File paths
PATHS = {
    'state_file': 'tamagotchi_state.json',
    'log_file': 'tamagotchi.log',
    'images_dir': 'images/',
}