#!/bin/bash

set -e

PROJECT_DIR="/home/cate/cate-PA"
AUDIO_INBOX="/home/cate/audio_inbox"
SERVICE_NAME="pa-audio"
REPO_URL="https://github.com/roydenlyr/cate-PA.git"

echo "========================================="
echo "PA Audio System - Setup"
echo "========================================="

# ---- System Packages ----
echo "[1/6] Installing system packages..."
sudo apt update -qq
sudo apt install samba git -y -qq

# ---- Auto-detect headphone audio card ----
echo "[2/6] Configuring audio card..."
CARD_NUM=$(aplay -l 2>/dev/null | grep -i headphones | head -1 | sed 's/card \([0-9]\+\):.*/\1/')

if [ -z "$CARD_NUM" ]; then
    echo "WARNING: Could not detect headphone audio card. Defaulting to card 0."
    CARD_NUM=0
fi

echo "Detected headphone card: $CARD_NUM"
sudo bash -c "cat > /etc/asound.conf << EOF
defaults.pcm.card $CARD_NUM
defaults.ctl.card $CARD_NUM
EOF"

# ---- Audio inbox folder ----
echo "[3/6] Setting up audio inbox folder..."
mkdir -p "$AUDIO_INBOX"
sudo chmod 777 "$AUDIO_INBOX"

# ---- Samba config (only add if not already configured) ----
echo "[4/6] Configuring Samba..."
if ! grep -q "\[audio_inbox\]" /etc/samba/smb.conf; then
    sudo bash -c "cat >> /etc/samba/smb.conf << EOF

[audio_inbox]
    path = $AUDIO_INBOX
    browseable = yes
    writable = yes
    guest ok = yes
    create mask = 0777
EOF"
    echo "Samba share added"
else
    echo "Samba share already configured, skipping."
fi

# Add map to guest if not present
if ! grep -q "map to guest" /etc/samba/smb.conf; then
    sudo sed -i '/\[global\]/a\\    map to guest = bad user' /etc/samba/smb.conf
    echo "Added guest mapping."
fi

sudo systemctl restart smbd
sudo systemctl enable smbd

# ---- Clone project repo ----
echo "[5/6] Setting up project repository..."
if [ -d "$PROJECT_DIR" ]; then
    echo "Project directory already exists. Pulling latest changes..."
    cd "$PROJECT_DIR"
    git pull
else
    echo "Cloning project repository..."
    cd "$(dirname "$PROJECT_DIR")"
    git clone "$REPO_URL" "$(basename "$PROJECT_DIR")"
fi

# ---- Systemd service (only add if not already present) ----
echo "[6/6] Setting up auto-start service..."
sudo bash -c "cat > /etc/systemd/system/${SERVICE_NAME}.service << EOF

[Unit]
Description=PA Audio Server
After=network.target sound.target

[Service]
Type=simple
User=cate
WorkingDirectory=${PROJECT_DIR}/src
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF"

sudo systemctl daemon-reload
sudo systemctl enable "${SERVICE_NAME}.service"

# ---- Test audio ----
echo ""
echo "Testing audio output on card $CARD_NUM..."
if aplay -l | grep -qi headphones; then
    speaker-test -c 1 -t sine -l 1 -p 1 2>/dev/null && echo "Audio test passed." || echo "Audio test failed. Check connections."
else
    echo "Skipping audio test - no headphones device found."
fi

# ---- Summary ----
echo ""
echo "========================================="
echo "Setup complete!"
echo "========================================="
echo "Audio card:    $CARD_NUM"
echo "Project:       $PROJECT_DIR"
echo "Audio inbox:   $AUDIO_INBOX"
echo "Samba share:   \\\\$(hostname -I | awk '{print $1}')\\audio_inbox"
echo "Service:       $SERVICE_NAME"
echo ""
echo "Remaining manual steps:"
echo "  1. Set Samba password:  sudo smbpasswd -a cate"
echo "  2. Update config.py with correct STATION_ID and peer IPs"
echo "  3. Start service:       sudo systemctl start $SERVICE_NAME"
echo "     Or reboot:           sudo reboot"
echo "========================================="
