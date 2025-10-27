#!/bin/bash
# Kill any existing Chrome processes
pkill -f chromium

# Start Chrome in HEADLESS mode with remote debugging enabled
# Optimized for Raspberry Pi - reduced memory and CPU usage
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
  --headless=new \
  --disable-gpu \
  --disable-dev-shm-usage \
  --disable-software-rasterizer \
  --disable-extensions \
  --disable-logging \
  --disable-animations \
  --no-sandbox \
  --js-flags="--max-old-space-size=512" \
  > /dev/null 2>&1 &

echo "Chrome started in HEADLESS mode with remote debugging on port 9222"
echo "PID: $!"
echo "Note: To revert to GUI mode, restore from start-chrome-debuger.sh.backup"
