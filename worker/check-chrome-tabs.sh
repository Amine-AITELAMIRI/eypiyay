#!/bin/bash
# Quick diagnostic script to check what tabs Chrome has open

echo "=== Checking Chrome Debugging Tabs ==="
echo ""

CHROME_PORT="${CHROME_PORT:-9222}"

# Check if Chrome is listening
if ! nc -z localhost $CHROME_PORT 2>/dev/null; then
    echo "ERROR: Chrome is not listening on port $CHROME_PORT"
    exit 1
fi

echo "✓ Chrome is listening on port $CHROME_PORT"
echo ""

# Fetch and display tabs
echo "Available tabs:"
echo "----------------"

curl -s http://localhost:$CHROME_PORT/json | python3 -c "
import sys, json
try:
    tabs = json.load(sys.stdin)
    for i, tab in enumerate(tabs):
        print(f\"[{i}] Type: {tab.get('type', 'unknown')}\")
        print(f\"    Title: {tab.get('title', '<no title>')}\")
        print(f\"    URL: {tab.get('url', '<no url>')}\")
        print(f\"    WebSocket: {'✓' if tab.get('webSocketDebuggerUrl') else '✗'}\")
        print()
except Exception as e:
    print(f'Error: {e}')
    sys.exit(1)
"

echo "----------------"
echo ""
echo "If you see tabs above, Chrome is working correctly."
echo "If the worker can't connect, check the filter string matches a tab URL or title."

