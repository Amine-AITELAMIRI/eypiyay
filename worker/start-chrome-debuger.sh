#!/bin/bash
# Chrome Startup Script in GUI mode
# Optimized for Raspberry Pi but with visual window
#
# Usage: ./start-chrome-debuger.sh [URL]
#   If URL is provided, Chrome will open that page initially

# Get optional initial URL
INITIAL_URL="${1:-}"

# Use environment variables if set, otherwise use defaults
CHROME_PORT="${CHROME_PORT:-9222}"
CHROME_USER_DATA="${CHROME_USER_DATA:-$HOME/.config/chrome-debug}"

# Kill any existing Chrome processes
pkill -f chromium

# Build Chrome command
CHROME_CMD=(
  chromium-browser
  --remote-debugging-port=$CHROME_PORT
  --remote-allow-origins=http://localhost:$CHROME_PORT
  --user-data-dir="$CHROME_USER_DATA"
  --no-first-run
  --no-default-browser-check
  --disable-background-timer-throttling
  --disable-backgrounding-occluded-windows
  --disable-renderer-backgrounding
  --disable-features=TranslateUI
  --disable-ipc-flooding-protection
  --disable-web-security
  --disable-features=VizDisplayCompositor
  --memory-pressure-off
  --js-flags="--max-old-space-size=512"
)

# Add initial URL if provided
if [ -n "$INITIAL_URL" ]; then
  CHROME_CMD+=("$INITIAL_URL")
fi

# Start Chrome
"${CHROME_CMD[@]}" > /dev/null 2>&1 &

CHROME_PID=$!

echo "Chrome started in GUI mode with remote debugging on port $CHROME_PORT"
echo "PID: $CHROME_PID"
if [ -n "$INITIAL_URL" ]; then
  echo "Initial URL: $INITIAL_URL"
fi

# Return the PID for calling scripts
exit 0
