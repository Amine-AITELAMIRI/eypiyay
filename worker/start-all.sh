#!/bin/bash
#
# ChatGPT Relay Worker Startup Script
# This script starts Chrome with remote debugging and the worker process
#

# Configuration
export SERVER_URL="https://chatgpt-relay-api.onrender.com"
export API_KEY="72b0253ba06e73484e2b71370a503ce00183b59750e4be1dd5eb10896587954a"
export WORKER_ID="raspberry-pi-worker"
export CHATGPT_URL="https://chatgpt.com/g/g-p-68d04e772ef881918e915068fbe126e4-api-auto/project"
export CHROME_HOST="localhost"
export CHROME_PORT="9222"
export POLL_INTERVAL="3.0"
export CDP_TIMEOUT="300.0"

# VPN Rotation settings (for avoiding search engine blacklisting)
# Set to "true" to enable VPN rotation for search mode requests
export VPN_ROTATE="false"
export VPN_REGION=""  # Optional: specify region (e.g., "france", "united_states")
export VPN_MAX_RETRIES="2"

# Change to the project directory
cd ~/eypiyay || exit 1

# Log file location
LOG_DIR="$HOME/eypiyay/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/worker.log"

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=== Starting ChatGPT Relay Worker ==="

# Start Chrome using the dedicated startup script (with headless optimizations)
log "Starting Chrome with remote debugging on port $CHROME_PORT..."
log "Using start-chrome-debuger.sh (headless mode with Pi optimizations)"
log "Chrome will start with about:blank. Worker will navigate to ChatGPT when jobs arrive."

# Export port for start-chrome-debuger.sh to use
export CHROME_PORT
export CHROME_USER_DATA="$HOME/.config/chrome-debug"

# Call the Chrome startup script with about:blank
# This ensures Chrome starts with a simple page (not chrome://newtab which blocks CDP)
# The worker's modify_chatgpt_url() function will handle navigation before each request
# Note: We're in ~/eypiyay after the cd command, so use worker/script path
worker/start-chrome-debuger.sh "about:blank" 2>&1 | while IFS= read -r line; do
    log "$line"
done

# Get the PID of the most recent chromium process
sleep 1
CHROME_PID=$(pgrep -f "chromium-browser.*$CHROME_PORT" | tail -1)

if [ -z "$CHROME_PID" ]; then
    log "WARNING: Could not determine Chrome PID, proceeding anyway..."
else
    log "Chrome PID: $CHROME_PID"
fi

# Wait for Chrome to be ready
log "Waiting for Chrome to be ready..."
sleep 5

# Verify Chrome is running
if [ -n "$CHROME_PID" ] && ! ps -p $CHROME_PID > /dev/null 2>&1; then
    log "ERROR: Chrome process $CHROME_PID is not running!"
    exit 1
elif [ -z "$CHROME_PID" ]; then
    # Try alternative detection method
    if ! pgrep -f chromium > /dev/null; then
        log "ERROR: Chrome failed to start!"
        exit 1
    fi
    log "Chrome is running (PID detection used alternative method)"
fi

# Verify debugging port is listening
if ! nc -z localhost $CHROME_PORT; then
    log "ERROR: Chrome debugging port $CHROME_PORT is not accessible!"
    exit 1
fi

log "Chrome is ready on port $CHROME_PORT"

# Wait a bit for Chrome to be fully ready
# Since we're starting with a blank page, this is just to ensure Chrome is stable
log "Waiting for Chrome to stabilize..."
sleep 3

# Activate virtual environment
VENV_PATH="$HOME/chatgpt-relay-env"
if [ ! -d "$VENV_PATH" ]; then
    log "ERROR: Virtual environment not found at $VENV_PATH"
    exit 1
fi

log "Activating virtual environment: $VENV_PATH"
source "$VENV_PATH/bin/activate"

# Verify we're using the venv python
PYTHON_PATH=$(which python)
log "Using Python: $PYTHON_PATH"

# Build VPN arguments
VPN_ARGS=""
if [ "$VPN_ROTATE" = "true" ]; then
    log "VPN rotation enabled for search mode"
    VPN_ARGS="--vpn-rotate"
    if [ -n "$VPN_REGION" ]; then
        log "VPN region preference: $VPN_REGION"
        VPN_ARGS="$VPN_ARGS --vpn-region $VPN_REGION"
    fi
    if [ -n "$VPN_MAX_RETRIES" ]; then
        VPN_ARGS="$VPN_ARGS --vpn-max-retries $VPN_MAX_RETRIES"
    fi
else
    log "VPN rotation disabled"
fi

# Start the worker process
log "Starting worker process..."
log "Worker ID: $WORKER_ID"
log "Server URL: $SERVER_URL"
log "ChatGPT URL: $CHATGPT_URL"

# Run the worker and log output
# Filter by "about:blank" to find the actual page tab (not extension background pages)
# The worker will navigate to ChatGPT when a job arrives
python -m worker.cdp_worker \
  "$SERVER_URL" \
  "$WORKER_ID" \
  "$API_KEY" \
  "about:blank" \
  --pick-first \
  --host "$CHROME_HOST" \
  --port "$CHROME_PORT" \
  --timeout "$CDP_TIMEOUT" \
  --poll-interval "$POLL_INTERVAL" \
  --chatgpt-url "$CHATGPT_URL" \
  --script bookmarklet.js \
  $VPN_ARGS \
  2>&1 | tee -a "$LOG_FILE"

# If worker exits, log it
log "Worker process exited with code: $?"

