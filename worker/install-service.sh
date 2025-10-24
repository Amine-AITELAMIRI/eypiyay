#!/bin/bash
#
# Install ChatGPT Relay Worker as a systemd service
#

set -e

# Get the current username
CURRENT_USER=$(whoami)
USER_HOME=$(eval echo ~$CURRENT_USER)

echo "Installing ChatGPT Relay Worker service..."
echo "Detected user: $CURRENT_USER"
echo "Home directory: $USER_HOME"

# Check if we're in the right directory
if [ ! -f "start-all.sh" ]; then
    echo "Error: Must run this script from the worker directory"
    exit 1
fi

# Make the startup script executable
chmod +x start-all.sh

# Create logs directory
mkdir -p "$USER_HOME/eypiyay/logs"

# Create a temporary service file with the correct paths
cat > /tmp/chatgpt-relay-worker.service <<EOF
[Unit]
Description=ChatGPT Relay Worker
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$USER_HOME/eypiyay
ExecStart=$USER_HOME/eypiyay/worker/start-all.sh
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Environment variables
Environment="SERVER_URL=https://chatgpt-relay-api.onrender.com"
Environment="API_KEY=72b0253ba06e73484e2b71370a503ce00183b59750e4be1dd5eb10896587954a"
Environment="WORKER_ID=raspberry-pi-worker"
Environment="CHATGPT_URL=https://chatgpt.com/g/g-p-68d04e772ef881918e915068fbe126e4-api-auto/project"
Environment="CHROME_HOST=localhost"
Environment="CHROME_PORT=9222"
Environment="POLL_INTERVAL=3.0"

[Install]
WantedBy=multi-user.target
EOF

# Copy to systemd directory
echo "Copying service file to /etc/systemd/system/..."
sudo cp /tmp/chatgpt-relay-worker.service /etc/systemd/system/

# Clean up temp file
rm /tmp/chatgpt-relay-worker.service

# Reload systemd
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

# Enable the service
echo "Enabling service to start on boot..."
sudo systemctl enable chatgpt-relay-worker.service

echo ""
echo "Installation complete!"
echo ""
echo "To start the service now, run:"
echo "  sudo systemctl start chatgpt-relay-worker.service"
echo ""
echo "To check the status, run:"
echo "  sudo systemctl status chatgpt-relay-worker.service"
echo ""
echo "To view logs, run:"
echo "  journalctl -u chatgpt-relay-worker.service -f"
echo "  or"
echo "  tail -f $USER_HOME/eypiyay/logs/worker.log"

