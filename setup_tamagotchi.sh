#!/bin/bash

echo "🎵 Setting up Last.fm Tamagotchi..."

# Update system
echo "📦 Updating system packages..."
sudo apt update

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
sudo apt install -y python3-pip python3-tk python3-pil python3-pil.imagetk

# Install Python packages
echo "📚 Installing required Python packages..."
pip3 install requests python-dotenv

# Make scripts executable
echo "🔧 Making scripts executable..."
chmod +x lastfm_tamagotchi.py
chmod +x display_image.py

# Create images directory
echo "📁 Creating directories..."
mkdir -p images

# Create .env file template
echo "⚙️ Creating environment file template..."
cat > .env.template << EOF
# Last.fm API Configuration
# Get your API key from: https://www.last.fm/api/account/create
LASTFM_API_KEY=your_api_key_here
LASTFM_USERNAME=your_username_here

# Discord Integration (Optional)
# Create a webhook at: https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks
DISCORD_WEBHOOK_URL=your_webhook_url_here
DISCORD_BOT_TOKEN=your_bot_token_here
DISCORD_CHANNEL_ID=your_channel_id_here
EOF

# Create autostart script
echo "🚀 Creating autostart script..."
cat > start_tamagotchi.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source .env
python3 lastfm_tamagotchi.py
EOF

chmod +x start_tamagotchi.sh

# Create systemd service for auto-start
echo "🔧 Creating systemd service..."
sudo tee /etc/systemd/system/tamagotchi.service > /dev/null << EOF
[Unit]
Description=Last.fm Tamagotchi
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=$(pwd)
Environment=PATH=/usr/bin:/usr/local/bin
ExecStart=/usr/bin/python3 $(pwd)/lastfm_tamagotchi.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable the service
echo "🔧 Enabling tamagotchi service..."
sudo systemctl enable tamagotchi.service

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env.template and rename to .env"
echo "2. Add your Last.fm API key and username"
echo "3. (Optional) Add Discord webhook for notifications"
echo "4. Run: python3 lastfm_tamagotchi.py"
echo "5. Or start the service: sudo systemctl start tamagotchi"
echo ""
echo "🎵 Your Last.fm Tamagotchi is ready to feed on music!"