# Setting Up Auto-Start on Raspberry Pi (Using Cron)

**Note:** This guide uses cron for auto-start. For a more robust systemd-based approach with automatic restarts, see [SETUP_STARTUP.md](SETUP_STARTUP.md).

This guide explains how to configure the ChatGPT Relay Worker to start automatically on Raspberry Pi boot using cron instead of systemd.

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

### 3. Set up cron job for auto-start

Edit your crontab:

```bash
crontab -e
```

Add this line to run the worker on boot:

```bash
@reboot /home/YOUR_USERNAME/eypiyay/worker/start-all.sh >> /home/YOUR_USERNAME/eypiyay/logs/cron.log 2>&1
```

**Important:** Replace `YOUR_USERNAME` with your actual username.

### 4. Alternative: Create a wrapper script for cron

For better control, create a wrapper script:

```bash
nano ~/eypiyay/worker/start-worker-wrapper.sh
```

Add this content:

```bash
#!/bin/bash
# Wrapper script for cron to start the worker

# Set up environment
export DISPLAY=:0
export HOME=/home/YOUR_USERNAME

# Change to project directory
cd /home/YOUR_USERNAME/eypiyay || exit 1

# Run the start script
exec /home/YOUR_USERNAME/eypiyay/worker/start-all.sh
```

Replace `YOUR_USERNAME` with your actual username, then make it executable:

```bash
chmod +x ~/eypiyay/worker/start-worker-wrapper.sh
```

Then add to crontab:

```bash
crontab -e
```

Add this line:

```bash
@reboot /home/YOUR_USERNAME/eypiyay/worker/start-worker-wrapper.sh
```

### 5. Verify cron is set up

Check your crontab:

```bash
crontab -l
```

You should see the @reboot line you added.

## Managing the Worker

### Start manually

```bash
~/eypiyay/worker/start-all.sh
```

Or run in background:

```bash
nohup ~/eypiyay/worker/start-all.sh > /dev/null 2>&1 &
```

### Stop the worker

Find the process:

```bash
ps aux | grep start-all.sh
ps aux | grep cdp_worker
```

Kill it:

```bash
pkill -f start-all.sh
pkill -f cdp_worker
pkill -f chromium
```

### Check if running

```bash
# Check worker process
ps aux | grep cdp_worker

# Check Chrome
ps aux | grep chromium

# Check logs
tail -f ~/eypiyay/logs/worker.log
```

## Viewing Logs

### Worker logs

```bash
tail -f ~/eypiyay/logs/worker.log
```

### Cron logs

```bash
tail -f ~/eypiyay/logs/cron.log
```

### Check cron execution

```bash
grep CRON /var/log/syslog | tail -20
```

## Removing Auto-Start

To remove the cron job:

```bash
crontab -e
```

Remove the `@reboot` line, save and exit.

Or edit crontab programmatically:

```bash
crontab -l | grep -v start-all | crontab -
```

## Troubleshooting

### Worker doesn't start on boot

1. Check cron is running:
   ```bash
   sudo systemctl status cron
   ```

2. Check crontab:
   ```bash
   crontab -l
   ```

3. Check cron logs:
   ```bash
   grep CRON /var/log/syslog | tail -20
   ```

4. Check worker logs:
   ```bash
   tail -f ~/eypiyay/logs/worker.log
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

### Worker can't connect to server

1. Check network connectivity:
   ```bash
   ping chatgpt-relay-api.onrender.com
   ```

2. Check if server is running and accessible

## Updating Configuration

If you need to change configuration (API key, server URL, etc.):

1. Edit the configuration variables in `~/eypiyay/worker/start-all.sh`

2. Restart the worker:
   ```bash
   pkill -f start-all.sh
   ~/eypiyay/worker/start-all.sh
   ```

## Advantages of Cron vs Systemd

**Cron advantages:**
- Simpler setup
- No sudo required
- Easier to debug
- User-specific execution

**Systemd advantages:**
- Better process management
- Automatic restarts on failure
- More detailed logging
- More reliable

If you need automatic restarts on failure, you can create a simple restart script:

```bash
nano ~/eypiyay/worker/keep-alive.sh
```

Add:

```bash
#!/bin/bash
while true; do
    ~/eypiyay/worker/start-all.sh
    sleep 10
done
```

Then run:

```bash
chmod +x ~/eypiyay/worker/keep-alive.sh
nohup ~/eypiyay/worker/keep-alive.sh > /dev/null 2>&1 &
```

