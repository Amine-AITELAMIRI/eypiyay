# Setting Up Auto-Start on Raspberry Pi (Systemd Method)

**Note:** This guide uses systemd to manage the service. For a simpler cron-based approach, see [SETUP_STARTUP_CRON.md](SETUP_STARTUP_CRON.md).

This guide explains how to configure the ChatGPT Relay Worker to start automatically on Raspberry Pi boot using systemd.

## Prerequisites

- Raspberry Pi with Raspbian/Ubuntu installed
- Python virtual environment created at `~/chatgpt-relay-env` with all dependencies installed
- Chromium browser installed
- Project cloned to `~/eypiyay`

### Setting up the Virtual Environment

If you haven't created the virtual environment yet:

```bash
# Create virtual environment
python3 -m venv ~/chatgpt-relay-env

# Activate it
source ~/chatgpt-relay-env/bin/activate

# Install dependencies
cd ~/eypiyay
pip install -r worker/requirements.txt

# Verify installation
python -m worker.cdp_worker --help
```

## Setup Steps

### 1. Make the startup script executable

```bash
chmod +x ~/eypiyay/worker/start-all.sh
```

### 2. Test the script manually

Run the script to ensure it works before setting up auto-start:

```bash
~/eypiyay/worker/start-all.sh
```

Check the logs:
```bash
tail -f ~/eypiyay/logs/worker.log
```

Press `Ctrl+C` to stop the worker.

### 3. Install the systemd service

Run the installer script (it will automatically detect your username and configure paths):

```bash
cd ~/eypiyay/worker
chmod +x install-service.sh
./install-service.sh
```

The installer will:
- Detect your username automatically
- Create the logs directory
- Copy the service file with correct paths
- Enable the service to start on boot

**Alternative: Manual Installation**

If you prefer to install manually:

```bash
cd ~/eypiyay/worker
# Create logs directory
mkdir -p ~/eypiyay/logs

# Create customized service file
cat > /tmp/chatgpt-relay-worker.service << 'EOF'
[Unit]
Description=ChatGPT Relay Worker
After=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$(eval echo ~$(whoami))/eypiyay
ExecStart=$(eval echo ~$(whoami))/eypiyay/worker/start-all.sh
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

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

# Copy and configure
sudo cp /tmp/chatgpt-relay-worker.service /etc/systemd/system/
sudo sed -i "s|User=$(whoami)|User=$(whoami)|g" /etc/systemd/system/chatgpt-relay-worker.service
sudo sed -i "s|WorkingDirectory=.*|WorkingDirectory=$(eval echo ~$(whoami))/eypiyay|g" /etc/systemd/system/chatgpt-relay-worker.service
sudo sed -i "s|ExecStart=.*|ExecStart=$(eval echo ~$(whoami))/eypiyay/worker/start-all.sh|g" /etc/systemd/system/chatgpt-relay-worker.service
sudo systemctl daemon-reload
sudo systemctl enable chatgpt-relay-worker.service
```

### 4. Start the service

```bash
sudo systemctl start chatgpt-relay-worker.service
```

### 7. Check service status

```bash
sudo systemctl status chatgpt-relay-worker.service
```

### 8. View logs

View live logs:
```bash
journalctl -u chatgpt-relay-worker.service -f
```

View recent logs:
```bash
journalctl -u chatgpt-relay-worker.service -n 50
```

View worker-specific logs:
```bash
tail -f ~/eypiyay/logs/worker.log
```

## Managing the Service

### Stop the service
```bash
sudo systemctl stop chatgpt-relay-worker.service
```

### Restart the service
```bash
sudo systemctl restart chatgpt-relay-worker.service
```

### Disable auto-start on boot
```bash
sudo systemctl disable chatgpt-relay-worker.service
```

### Check if service is enabled
```bash
sudo systemctl is-enabled chatgpt-relay-worker.service
```

## Troubleshooting

### Quick Fix: Service Fails with "status=217/USER" Error

If you see `status=217/USER` error, the username in the service file is incorrect. Fix it:

```bash
# Stop the service
sudo systemctl stop chatgpt-relay-worker.service

# Get your actual username
echo $USER

# Edit the service file to use the correct username
sudo nano /etc/systemd/system/chatgpt-relay-worker.service
# Change "User=pi" to "User=YOUR_ACTUAL_USERNAME"

# Update the paths too if needed
# WorkingDirectory=/home/YOUR_ACTUAL_USERNAME/eypiyay
# ExecStart=/home/YOUR_ACTUAL_USERNAME/eypiyay/worker/start-all.sh

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl start chatgpt-relay-worker.service
```

Or simply re-run the installer script:
```bash
cd ~/eypiyay/worker
./install-service.sh
```

### Service fails to start

1. Check service status:
   ```bash
   sudo systemctl status chatgpt-relay-worker.service
   ```

2. Check logs:
   ```bash
   journalctl -u chatgpt-relay-worker.service -n 100
   ```

3. Verify the script is executable:
   ```bash
   ls -l ~/eypiyay/worker/start-all.sh
   ```

4. Check file paths in the service file match your setup:
   ```bash
   cat /etc/systemd/system/chatgpt-relay-worker.service
   ```

### Chrome won't start

1. Check if Chromium is installed:
   ```bash
   which chromium-browser
   ```

2. If not installed:
   ```bash
   sudo apt-get update
   sudo apt-get install chromium-browser
   ```

3. Check if another process is using port 9222:
   ```bash
   sudo lsof -i :9222
   ```

### Virtual environment not found

If you see "ERROR: Virtual environment not found at ~/chatgpt-relay-env":

1. Create the virtual environment:
   ```bash
   python3 -m venv ~/chatgpt-relay-env
   source ~/chatgpt-relay-env/bin/activate
   cd ~/eypiyay
   pip install -r worker/requirements.txt
   ```

2. Verify it exists:
   ```bash
   ls -la ~/chatgpt-relay-env
   ```

3. Restart the service:
   ```bash
   sudo systemctl restart chatgpt-relay-worker.service
   ```

### Worker can't connect to server

1. Check network connectivity:
   ```bash
   ping chatgpt-relay-api.onrender.com
   ```

2. Verify API key is correct in the service file

3. Check if server is running and accessible

## Updating Configuration

If you need to change configuration (API key, server URL, etc.):

1. Edit the configuration variables in `~/eypiyay/worker/start-all.sh`

2. Restart the service:
   ```bash
   sudo systemctl restart chatgpt-relay-worker.service
   ```

## Verifying Auto-Start

After reboot, verify the service started automatically:

```bash
sudo systemctl status chatgpt-relay-worker.service
```

You should see `Active: active (running)` and a recent start time.

