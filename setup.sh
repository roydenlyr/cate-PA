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
echo "[1/9] Installing system packages..."
sudo apt update -qq
sudo apt install git vim python3-flask -y -qq

# ---- Enable VNC ----
echo "[2/9] Enabling VNC server..."
sudo raspi-config nonint do_vnc 0

# ---- Auto-detect headphone audio card ----
echo "[3/9] Configuring audio card..."
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
echo "[4/9] Setting up audio inbox folder..."
mkdir -p "$AUDIO_INBOX"
sudo chmod 777 "$AUDIO_INBOX"

# ---- Samba config (only add if not already configured) ----
echo "[5/9] Configuring Samba..."
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
echo "[6/9] Setting up project repository..."
if [ -d "$PROJECT_DIR" ]; then
    echo "Project directory already exists. Pulling latest changes..."
    cd "$PROJECT_DIR"
    git pull
else
    echo "Cloning project repository..."
    cd "$(dirname "$PROJECT_DIR")"
    git clone "$REPO_URL" "$(basename "$PROJECT_DIR")"
fi

# ---- Fetch config script ----
echo "[7/9] Setting up config fetch script..."
cat > "$PROJECT_DIR/fetch_config.sh" << 'FETCHEOF'
#!/bin/bash
FS1_IP="128.127.1.50"
LOCAL_CONFIG="/home/cate/cate-PA/src/stations.json"
HOSTNAME=$(hostname)

# FS1 is the source of truth, no need to fetch from itself
if echo "$HOSTNAME" | grep -qi "fs1"; then
    echo "This is FS1, skipping config fetch."
    exit 0
fi

scp -o ConnectTimeout=5 -o StrictHostKeyChecking=no cate@${FS1_IP}:/home/cate/cate-PA/src/stations.json "$LOCAL_CONFIG" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "Updated stations.json from FS1."
else
    echo "Could not reach FS1, using existing stations.json."
fi
FETCHEOF
chmod +x "$PROJECT_DIR/fetch_config.sh"

# ---- SSH key for passwordless config fetch ----
echo "[8/9] Setting up SSH key for config fetch..."
if [ ! -f /home/cate/.ssh/id_ed25519 ]; then
    ssh-keygen -t ed25519 -f /home/cate/.ssh/id_ed25519 -N ""
    echo "SSH key generated."
else
    echo "SSH key already exists, skipping generation."
fi

# ---- Systemd service (only add if not already present) ----
echo "[9/9] Setting up auto-start service..."
sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null << EOF
[Unit]
Description=PA Audio Server
After=network.target sound.target

[Service]
Type=simple
User=cate
WorkingDirectory=${PROJECT_DIR}/src
ExecStartPre=/bin/bash ${PROJECT_DIR}/fetch_config.sh
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

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
echo "Hostname:      $(hostname)"
echo "Station ID:    Auto-detected from hostname"
echo "Audio card:    $CARD_NUM"
echo "Project:       $PROJECT_DIR"
echo "Audio inbox:   $AUDIO_INBOX"
echo "Samba share:   \\\\$(hostname -I | awk '{print $1}')\\audio_inbox"
echo "Service:       $SERVICE_NAME"
echo ""
echo "Remaining manual steps:"
echo "  1. Set Samba password:     sudo smbpasswd -a cate"
echo "  2. Copy SSH key to FS1:    ssh-copy-id cate@128.127.1.50"
echo "  3. Verify stations.json is correct on FS1"
echo "  4. Start service:          sudo systemctl start $SERVICE_NAME"
echo "     Or reboot:              sudo reboot"
echo "========================================="
