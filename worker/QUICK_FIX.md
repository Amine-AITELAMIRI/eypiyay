# Quick Fix: Service Fails with status=217/USER Error

If you're seeing this error, the username in the service file doesn't match your actual username.

**Note:** Make sure you have created the virtual environment at `~/chatgpt-relay-env` before running the installer.

## Prefer Cron Instead?

If you want to avoid systemd complexity, consider using cron instead. See [SETUP_STARTUP_CRON.md](SETUP_STARTUP_CRON.md) for the simpler cron-based approach.

## Solution 1: Use the Installer Script (Recommended)

Run this single command to fix everything:

```bash
cd ~/eypiyay/worker
chmod +x install-service.sh
./install-service.sh
```

## Solution 2: Manual Fix

1. **Stop the service:**
   ```bash
   sudo systemctl stop chatgpt-relay-worker.service
   ```

2. **Find your username:**
   ```bash
   echo $USER
   ```

3. **Edit the service file:**
   ```bash
   sudo nano /etc/systemd/system/chatgpt-relay-worker.service
   ```

4. **Change these lines to match your actual username:**
   ```
   User=YOUR_ACTUAL_USERNAME
   WorkingDirectory=/home/YOUR_ACTUAL_USERNAME/eypiyay
   ExecStart=/home/YOUR_ACTUAL_USERNAME/eypiyay/worker/start-all.sh
   ```

5. **Save and exit** (Ctrl+X, then Y, then Enter)

6. **Reload and restart:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl start chatgpt-relay-worker.service
   ```

7. **Check status:**
   ```bash
   sudo systemctl status chatgpt-relay-worker.service
   ```

## Verify It's Working

After starting, check that it's running properly:

```bash
# Check service status
sudo systemctl status chatgpt-relay-worker.service

# Check logs
journalctl -u chatgpt-relay-worker.service -f

# Or check the worker log file
tail -f ~/eypiyay/logs/worker.log
```

You should see messages like:
- "Starting Chrome with remote debugging..."
- "Chrome is ready on port 9222"
- "Starting worker process..."

If you see errors, check the troubleshooting section in SETUP_STARTUP.md

