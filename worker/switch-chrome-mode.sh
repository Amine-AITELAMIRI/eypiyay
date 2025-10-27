#!/bin/bash
# Helper script to switch between headless and GUI Chrome modes

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAIN_SCRIPT="$SCRIPT_DIR/start-chrome-debuger.sh"
BACKUP_SCRIPT="$SCRIPT_DIR/start-chrome-debuger.sh.backup"

if [ ! -f "$BACKUP_SCRIPT" ]; then
    echo "Error: Backup file not found at $BACKUP_SCRIPT"
    exit 1
fi

# Check current mode
if grep -q "headless=new" "$MAIN_SCRIPT"; then
    CURRENT_MODE="headless"
else
    CURRENT_MODE="GUI"
fi

echo "Current mode: $CURRENT_MODE"
echo ""
echo "What would you like to do?"
echo "1) Switch to GUI mode (with display)"
echo "2) Switch to HEADLESS mode (optimized for Pi)"
echo "3) Cancel"
echo ""
read -p "Enter choice [1-3]: " choice

case $choice in
    1)
        echo "Switching to GUI mode..."
        cp "$BACKUP_SCRIPT" "$MAIN_SCRIPT"
        echo "✓ Switched to GUI mode"
        echo "Restart Chrome using: ./start-chrome-debuger.sh"
        ;;
    2)
        echo "Switching to HEADLESS mode..."
        # Recreate the headless version
        cat > "$MAIN_SCRIPT" << 'EOF'
#!/bin/bash
# Chrome Startup Script with HEADLESS mode
# Optimized for Raspberry Pi - reduced memory and CPU usage
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
  --headless=new
  --disable-gpu
  --disable-dev-shm-usage
  --disable-software-rasterizer
  --disable-extensions
  --disable-logging
  --disable-animations
  --no-sandbox
  --js-flags="--max-old-space-size=512"
)

# Add initial URL if provided
if [ -n "$INITIAL_URL" ]; then
  CHROME_CMD+=("$INITIAL_URL")
fi

# Start Chrome
"${CHROME_CMD[@]}" > /dev/null 2>&1 &

CHROME_PID=$!

echo "Chrome started in HEADLESS mode with remote debugging on port $CHROME_PORT"
echo "PID: $CHROME_PID"
if [ -n "$INITIAL_URL" ]; then
  echo "Initial URL: $INITIAL_URL"
fi
echo "Note: To revert to GUI mode, restore from start-chrome-debuger.sh.backup"

# Return the PID for calling scripts
exit 0
EOF
        chmod +x "$MAIN_SCRIPT"
        echo "✓ Switched to HEADLESS mode"
        echo "Restart Chrome using: ./start-chrome-debuger.sh"
        ;;
    3)
        echo "Cancelled."
        exit 0
        ;;
    *)
        echo "Invalid choice."
        exit 1
        ;;
esac

