# 🎵 Last.fm Tamagotchi

A digital pet that feeds on your music scrobbles! Your Raspberry Pi badge now displays a cute tamagotchi that grows, evolves, and gets happy when you listen to music.

## 🌟 Features

- **Music-Fed Pet**: Your digital pet "Melody" gets fed every time you scrobble a track
- **Evolution System**: Pet evolves through 5 stages as it levels up
- **Mood System**: Pet's mood changes based on how well-fed it is
- **Real-time Stats**: Live display of hunger, happiness, and energy
- **Discord Integration**: Share pet updates with your Discord server
- **Fullscreen Display**: Beautiful fullscreen interface on your Pi badge
- **Auto-start**: Runs automatically when your Pi boots

## 🎮 How It Works

1. **Feed Your Pet**: Every time you listen to music and it gets scrobbled to Last.fm, your pet gets fed
2. **Watch It Grow**: Pet gains experience and levels up from listening to music
3. **Evolution**: Every 5 levels, your pet evolves into a new form
4. **Mood Changes**: Pet's mood reflects its current stats (hunger, happiness, energy)
5. **Discord Updates**: Get notified on Discord when your pet levels up, evolves, or achieves milestones

## 🚀 Quick Start

### 1. Get Last.fm API Key

1. Go to [Last.fm API](https://www.last.fm/api/account/create)
2. Create an account and get your API key
3. Note your Last.fm username

### 2. Set Up Your Pi

```bash
# Clone or copy files to your Pi
git clone <your-repo> piBadge
cd piBadge

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

## 🎯 Pet Features

### Evolution Stages
1. **Baby Melody** (Level 1-4): Pink, basic form
2. **Growing Melody** (Level 5-9): Pink with wings
3. **Teen Melody** (Level 10-14): Hot pink with wings and glow
4. **Adult Melody** (Level 15-19): Purple with wings, glow, and crown
5. **Legendary Melody** (Level 20+): Gold with all features and aura

### Mood System
- **Ecstatic** (80%+ stats): Overjoyed with music!
- **Happy** (60%+ stats): Feeling great!
- **Neutral** (40%+ stats): Doing okay
- **Sad** (20%+ stats): Needs more music...
- **Starving** (0%+ stats): Desperately needs music!

### Stats
- **Hunger**: Decreases over time, fed by scrobbles
- **Happiness**: Affected by feeding frequency
- **Energy**: Sustained by regular music listening

## 🔧 Discord Integration

### Setup Discord Webhook

1. Go to your Discord server settings
2. Create a webhook in the channel you want notifications
3. Copy the webhook URL
4. Add to your `.env` file:

```
DISCORD_WEBHOOK_URL=your_webhook_url_here
```

### Discord Notifications

- **Pet Fed**: When your pet eats a new scrobble
- **Level Up**: When pet reaches a new level
- **Evolution**: When pet evolves to a new stage
- **Mood Changes**: Significant mood changes
- **Daily Summary**: Daily stats and achievements

## 🎨 Customization

### Pet Name
Edit `config.py` to change the default pet name:
```python
PET_CONFIG = {
    'default_name': 'Your Pet Name',
    # ... other settings
}
```

### Evolution Stages
Customize evolution stages in `config.py`:
```python
EVOLUTION_STAGES = [
    {
        'name': 'Your Custom Stage',
        'color': '#FFB6C1',
        'features': ['wings', 'glow']
    },
    # ... more stages
]
```

### Stats Decay Rates
Adjust how quickly stats decrease:
```python
PET_CONFIG = {
    'hunger_decay_rate': 0.5,  # per minute
    'happiness_decay_rate': 0.3,
    'energy_decay_rate': 0.2,
}
```

## 📊 Monitoring

### Check Pet Status
```bash
# View service status
sudo systemctl status tamagotchi

# View logs
sudo journalctl -u tamagotchi -f
```

### Manual Control
```bash
# Start service
sudo systemctl start tamagotchi

# Stop service
sudo systemctl stop tamagotchi

# Restart service
sudo systemctl restart tamagotchi
```

## 🐛 Troubleshooting

### Pet Not Feeding
- Check your Last.fm API key and username
- Verify you have recent scrobbles
- Check internet connection

### Display Issues
- Ensure you have a display connected
- Check if running in GUI environment
- Try running `python3 test_display.py` first

### Discord Notifications Not Working
- Verify webhook URL is correct
- Check Discord server permissions
- Ensure webhook is in the right channel

## 🎵 Integration with Discord Buddy

This tamagotchi can integrate with your Discord buddy repository:

1. **Shared Notifications**: Both systems can post to the same Discord channel
2. **Music Stats**: Discord buddy can show music stats alongside pet updates
3. **Achievement System**: Unlock achievements for both systems
4. **Social Features**: Share pet status with Discord buddies

### Example Integration
```python
# In your Discord buddy bot
from discord_integration import DiscordIntegration

discord = DiscordIntegration()
discord.pet_fed(track_info, pet_state)
```

## 📁 File Structure

```
piBadge/
├── lastfm_tamagotchi.py    # Main tamagotchi application
├── config.py               # Configuration settings
├── discord_integration.py  # Discord notification system
├── setup_tamagotchi.sh    # Setup script
├── display_image.py        # Original image display
├── requirements.txt        # Python dependencies
├── .env.template          # Environment template
├── start_tamagotchi.sh    # Autostart script
└── README_TAMAGOTCHI.md   # This file
```

## 🤝 Contributing

Want to add features to your tamagotchi?

- **New Pet Types**: Add different pet species
- **Achievement System**: Create music-based achievements
- **Social Features**: Pet interactions with other users
- **Music Analysis**: Pet preferences based on genres
- **Visual Effects**: More animations and effects

## 📄 License

This project is open source. Feel free to modify and share your tamagotchi!

---

**🎵 Happy listening and pet feeding!** 🐾