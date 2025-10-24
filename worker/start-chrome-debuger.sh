#!/bin/bash
# Kill any existing Chrome processes
pkill -f chromium

# Start Chrome with remote debugging enabled
chromium-browser \
  --remote-debugging-port=9222 \
  --remote-allow-origins=http://localhost:9222 \
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

echo "Chrome started with remote debugging on port 9222"
echo "PID: $!"
