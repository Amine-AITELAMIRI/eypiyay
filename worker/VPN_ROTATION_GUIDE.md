# VPN Rotation for Search Mode

## Overview

This enhancement automatically rotates your IP address using NordVPN when processing search prompts to avoid getting blacklisted by search engines.

## Prerequisites

1. **NordVPN Installed**: Ensure NordVPN CLI is installed on your Raspberry Pi
2. **NordVPN Authenticated**: You must be logged in to NordVPN
3. **Python Module**: The `vpn_rotate_min.py` script is included in the worker directory

## How It Works

When a request comes in with `prompt_mode: "search"`:
1. The worker detects the search mode
2. Disconnects from the current VPN server
3. Connects to a new VPN server (ensuring it's different from the previous one)
4. Proceeds with the search request using the new IP address

## Usage

### Basic Usage (Enable VPN Rotation)

Add the `--vpn-rotate` flag when starting the worker:

```bash
python3 cdp_worker.py http://your-server.com worker-id your-api-key chatgpt \
    --vpn-rotate
```

### Advanced Options

#### Specify a Preferred Region

```bash
python3 cdp_worker.py http://your-server.com worker-id your-api-key chatgpt \
    --vpn-rotate \
    --vpn-region france
```

Available regions include:
- `france`
- `united_states`
- `united_kingdom`
- `germany`
- `japan`
- ... (any region supported by NordVPN)

#### Configure Retry Attempts

```bash
python3 cdp_worker.py http://your-server.com worker-id your-api-key chatgpt \
    --vpn-rotate \
    --vpn-max-retries 3
```

### Complete Example

```bash
python3 cdp_worker.py http://your-server.com worker-id your-api-key chatgpt \
    --script ../bookmarklet.js \
    --host localhost \
    --port 9222 \
    --vpn-rotate \
    --vpn-region united_states \
    --vpn-max-retries 3 \
    --log-level INFO
```

## Configuration in Startup Scripts

### Updating `start-worker.sh`

To enable VPN rotation in your startup script, add the flags:

```bash
# In start-worker.sh
python3 cdp_worker.py "$SERVER_URL" "$WORKER_ID" "$API_KEY" "$FILTER" \
    --script "$SCRIPT_PATH" \
    --host "$CDP_HOST" \
    --port "$CDP_PORT" \
    --chatgpt-url "$CHATGPT_URL" \
    --vpn-rotate \
    --vpn-region "$VPN_REGION" \
    --log-level INFO
```

### Adding VPN Config to `worker-config.sh`

Add these variables:

```bash
# VPN Configuration
export VPN_ENABLED="true"
export VPN_REGION="united_states"  # Optional, leave empty for fastest server
export VPN_MAX_RETRIES="2"
```

Then update your start script to use them:

```bash
# Source configuration
source worker-config.sh

# Build VPN arguments
VPN_ARGS=""
if [ "$VPN_ENABLED" = "true" ]; then
    VPN_ARGS="--vpn-rotate"
    if [ -n "$VPN_REGION" ]; then
        VPN_ARGS="$VPN_ARGS --vpn-region $VPN_REGION"
    fi
    if [ -n "$VPN_MAX_RETRIES" ]; then
        VPN_ARGS="$VPN_ARGS --vpn-max-retries $VPN_MAX_RETRIES"
    fi
fi

# Start worker with VPN args
python3 cdp_worker.py "$SERVER_URL" "$WORKER_ID" "$API_KEY" "$FILTER" \
    --script "$SCRIPT_PATH" \
    $VPN_ARGS
```

## Testing VPN Rotation Manually

Test the VPN rotation script directly:

```bash
# Connect to fastest server anywhere
python3 vpn_rotate_min.py

# Connect to fastest server in a specific region
python3 vpn_rotate_min.py france
```

Example output:
```json
{
  "ok": true,
  "status": "Connected",
  "server": "us9876.nordvpn.com",
  "country": "United States",
  "city": "New York",
  "technology": "OpenVPN",
  "protocol": "UDP",
  "retries": 0
}
```

## Logging

When VPN rotation is enabled, you'll see log messages like:

```
[INFO] Search mode detected, rotating VPN to get fresh IP address...
[INFO] VPN rotation successful! Connected to: us9876.nordvpn.com (United States, New York) [UDP] (retries: 0)
```

If rotation fails:
```
[WARNING] VPN rotation failed: Failed to confirm connected status quickly. Continuing with current connection (retries: 2)
```

## Behavior Notes

1. **Non-blocking**: VPN rotation failures won't stop the request from processing
2. **Search Mode Only**: VPN only rotates for requests with `prompt_mode: "search"`
3. **Server Diversity**: The script tries to ensure you connect to a different server than before
4. **Graceful Degradation**: If VPN rotation fails, the request continues with the current connection

## Troubleshooting

### VPN Module Not Available

```
[WARNING] vpn_rotate_min module not available, VPN rotation will be disabled
```

**Solution**: Ensure `vpn_rotate_min.py` is in the same directory as `cdp_worker.py`

### NordVPN Not Installed

```
[ERROR] Unexpected error during VPN rotation: [Errno 2] No such file or directory: 'nordvpn'
```

**Solution**: Install NordVPN CLI:
```bash
# Download and install NordVPN
sh <(curl -sSf https://downloads.nordcdn.com/apps/linux/install.sh)

# Login to NordVPN
nordvpn login
```

### Connection Timeout

```
[WARNING] VPN rotation failed: Failed to confirm connected status quickly.
```

**Solution**: Increase `--vpn-max-retries` or check your internet connection

### Permission Denied

If you get permission errors running nordvpn commands, add your user to the nordvpn group:

```bash
sudo usermod -aG nordvpn $USER
# Logout and login again for changes to take effect
```

## API Usage

To send a search request that will trigger VPN rotation:

```bash
curl -X POST "http://your-server.com/requests" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "find information about quantum computing",
    "prompt_mode": "search"
  }'
```

The worker will automatically rotate the VPN before processing this request.

## Performance Impact

- VPN rotation adds approximately 5-15 seconds to request processing time
- This happens only for search mode requests
- Regular prompts are unaffected

## Security & Privacy

- Each search gets a fresh IP address, reducing the risk of rate limiting or blacklisting
- NordVPN provides encryption and privacy for all traffic
- Server selection can be constrained to specific regions for compliance needs

