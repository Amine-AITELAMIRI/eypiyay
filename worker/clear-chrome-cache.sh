#!/bin/bash
# Clear Chrome user data to remove cached localStorage data

CHROME_USER_DATA="${CHROME_USER_DATA:-$HOME/.config/chrome-debug}"

echo "=== Clearing Chrome Cache ==="
echo ""

# Kill Chrome if running
echo "Stopping Chrome..."
pkill -f chromium
sleep 2

# Check if user data directory exists
if [ ! -d "$CHROME_USER_DATA" ]; then
    echo "Chrome user data directory not found at: $CHROME_USER_DATA"
    echo "Nothing to clear."
    exit 0
fi

echo "Clearing user data directory: $CHROME_USER_DATA"
echo ""

# Ask for confirmation
read -p "This will delete Chrome profile data (localStorage, cookies, etc.). Continue? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

# Remove the directory
rm -rf "$CHROME_USER_DATA"

echo "✓ Chrome cache cleared!"
echo ""
echo "Next time Chrome starts, it will have a fresh profile."
echo "Old test data in localStorage has been removed."

