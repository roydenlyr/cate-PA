#!/bin/bash

set -e

PROJECT_DIR="/home/cate/cate-PA"
SERVICE_NAME="pa-audio"
REPO_URL="https://github.com/roydenlyr/cate-PA.git"

echo "========================================="
echo "PA Audio System - Setup"
echo "========================================="

# ---- System Packages ----
echo "[1/10] Installing system packages..."
sudo apt update -qq
sudo apt install git vim python3-flask -y -qq

# ---- Enable VNC ----
echo "[2/10] Enabling VNC server..."
sudo raspi-config nonint do_vnc 0

# ---- Auto-detect headphone audio card ----
echo "[3/10] Configuring audio card..."
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

# ---- Max Volume ----
echo "[4/10] Maxing audio volume..."
amixer -c $CARD_NUM set PCM 100% unmute 2>/dev/null || true
sudo alsactl store

# ---- Clone project repo ----
echo "[5/10] Setting up project repository..."
if [ -d "$PROJECT_DIR" ]; then
    echo "Project directory already exists. Pulling latest changes..."
    cd "$PROJECT_DIR"
    git fetch --all
    git reset --hard origin/main
else
    echo "Cloning project repository..."
    cd "$(dirname "$PROJECT_DIR")"
    git clone "$REPO_URL" "$(basename "$PROJECT_DIR")"
fi

rm -rf "$PROJECT_DIR/docs"

# ---- Configure FS1 ----
echo "[6/10] Configuring FS1 IP..."
CONFIG_FILE="$PROJECT_DIR/src/stations.json"

if [ ! -f "$CONFIG_FILE" ]; then
    read -p "Enter FS1 IP address: " FS1_IP
    echo "{\"FS1\": \"$FS1_IP\"}" > "$CONFIG_FILE"
    echo "Created stations.json with FS1 IP."
else
    echo "stations.json already exists, skipping."
fi

# ---- Fetch config script ----
echo "[7/10] Setting up config fetch script..."
chmod +x "$PROJECT_DIR/scripts/fetch_config.sh"
chmod +x "$PROJECT_DIR/scripts/reboot_all.sh"

# ---- SSH key for passwordless config fetch ----
echo "[8/10] Setting up SSH key for config fetch..."
if [ ! -f /home/cate/.ssh/id_ed25519 ]; then
    ssh-keygen -t ed25519 -f /home/cate/.ssh/id_ed25519 -N ""
    echo "SSH key generated."
else
    echo "SSH key already exists, skipping generation."
fi

# ---- Systemd service (only add if not already present) ----
echo "[9/10] Setting up auto-start service..."
sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null << EOF
[Unit]
Description=PA Audio Server
After=network-online.target sound.target
Wants=network-online.target

[Service]
Type=simple
User=cate
WorkingDirectory=${PROJECT_DIR}/src
ExecStartPre=/bin/bash ${PROJECT_DIR}/scripts/fetch_config.sh
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable "${SERVICE_NAME}.service"

# ---- Passwordless reboot ----
echo "[10/10] Configuring remote reboot access..."
echo "cate ALL=(ALL) NOPASSWD: /sbin/reboot" | sudo tee /etc/sudoers.d/reboot-nopasswd > /dev/null

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
echo "Hostname:      $(hostname)"
echo "Station ID:    Auto-detected from hostname"
echo "Audio card:    $CARD_NUM"
echo "Project:       $PROJECT_DIR"
echo "Service:       $SERVICE_NAME"
echo ""
echo "Remaining manual steps (on deployment ground):"
echo "  1. Copy SSH key to FS1:    ssh-copy-id cate@{FS1 IP Address}"
echo "  2. Verify stations.json is correct on FS1"
echo "  3. Start service:          sudo systemctl start $SERVICE_NAME"
echo "     Or reboot:              sudo reboot"
echo "========================================="
