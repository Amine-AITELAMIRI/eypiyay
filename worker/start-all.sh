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

# Kill any existing Chrome processes
log "Killing existing Chrome processes..."
pkill -f chromium || true
sleep 2

# Start Chrome with remote debugging enabled
log "Starting Chrome with remote debugging on port $CHROME_PORT..."
chromium-browser \
  --remote-debugging-port=$CHROME_PORT \
  --remote-allow-origins=http://localhost:$CHROME_PORT \
  --user-data-dir="$HOME/.config/chrome-debug" \
  --no-first-run \
  --no-default-browser-check \
  --disable-background-timer-throttling \
  --disable-backgrounding-occluded-windows \
  --disable-renderer-backgrounding \
  --disable-features=TranslateUI \
  --disable-ipc-flooding-protection \
  --disable-web-security \
  --disable-features=VizDisplayCompositor \
  --memory-pressure-off \
  --max_old_space_size=4096 \
  > /dev/null 2>&1 &

CHROME_PID=$!
log "Chrome started with PID: $CHROME_PID"

# Wait for Chrome to be ready
log "Waiting for Chrome to be ready..."
sleep 5

# Verify Chrome is running
if ! ps -p $CHROME_PID > /dev/null; then
    log "ERROR: Chrome failed to start!"
    exit 1
fi

# Verify debugging port is listening
if ! nc -z localhost $CHROME_PORT; then
    log "ERROR: Chrome debugging port $CHROME_PORT is not accessible!"
    exit 1
fi

log "Chrome is ready on port $CHROME_PORT"

# Start the worker process
log "Starting worker process..."
log "Worker ID: $WORKER_ID"
log "Server URL: $SERVER_URL"
log "ChatGPT URL: $CHATGPT_URL"

# Run the worker and log output
python -m worker.cdp_worker \
  "$SERVER_URL" \
  "$WORKER_ID" \
  "$API_KEY" \
  chatgpt.com \
  --pick-first \
  --host "$CHROME_HOST" \
  --port "$CHROME_PORT" \
  --poll-interval "$POLL_INTERVAL" \
  --chatgpt-url "$CHATGPT_URL" \
  2>&1 | tee -a "$LOG_FILE"

# If worker exits, log it
log "Worker process exited with code: $?"

