# ChatGPT Relay Worker

This directory contains the worker components for the ChatGPT Relay system.

## Files

- **`start-all.sh`** - Main startup script that starts Chrome and the worker
- **`cdp_worker.py`** - The worker Python module
- **`install-service.sh`** - Installer for systemd service (advanced)
- **`stop-service.sh`** - Removes the systemd service
- **`SETUP_STARTUP.md`** - Guide for systemd-based auto-start
- **`SETUP_STARTUP_CRON.md`** - Guide for cron-based auto-start (simpler)
- **`QUICK_FIX.md`** - Troubleshooting guide

## Quick Start

### Manual Run

```bash
# Make script executable
chmod +x start-all.sh

# Run it
./start-all.sh
```

### Auto-Start Options

**Option 1: Cron (Simpler)**
See [SETUP_STARTUP_CRON.md](SETUP_STARTUP_CRON.md)

**Option 2: Systemd (More Robust)**
See [SETUP_STARTUP.md](SETUP_STARTUP.md)

## Requirements

- Python virtual environment at `~/chatgpt-relay-env`
- Chromium browser installed
- Dependencies from `requirements.txt` installed in venv

## Configuration

Edit the variables at the top of `start-all.sh` to configure:
- `SERVER_URL` - Your relay server URL
- `API_KEY` - Your API key
- `WORKER_ID` - Unique worker identifier
- `CHATGPT_URL` - ChatGPT URL to use
- `CHROME_PORT` - Chrome debugging port (default: 9222)
- `POLL_INTERVAL` - Polling interval in seconds (default: 3.0)

## Logs

Logs are written to: `~/eypiyay/logs/worker.log`

View logs:
```bash
tail -f ~/eypiyay/logs/worker.log
```

## Stopping the Worker

```bash
# Stop all processes
pkill -f start-all.sh
pkill -f cdp_worker
pkill -f chromium
```

Or if using systemd:
```bash
sudo systemctl stop chatgpt-relay-worker.service
```

