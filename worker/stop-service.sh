#!/bin/bash
#
# Stop and remove the ChatGPT Relay Worker systemd service
#

echo "Stopping ChatGPT Relay Worker service..."
sudo systemctl stop chatgpt-relay-worker.service

echo "Disabling service from starting on boot..."
sudo systemctl disable chatgpt-relay-worker.service

echo "Removing service file..."
sudo rm /etc/systemd/system/chatgpt-relay-worker.service

echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

echo ""
echo "Service has been stopped and removed."
echo ""
echo "To verify it's stopped:"
echo "  sudo systemctl status chatgpt-relay-worker.service"
echo ""
echo "You can now run the worker manually with:"
echo "  ~/eypiyay/worker/start-all.sh"

