# VPN Rotation Enhancement - Change Summary

## Overview

This enhancement adds automatic VPN IP rotation for search mode requests to avoid getting blacklisted by search engines. The system uses NordVPN to automatically rotate to a new server before processing any request with `prompt_mode: "search"`.

## Changes Made

### 1. New Files Created

#### `worker/vpn_rotate_min.py`
- **Purpose**: Core VPN rotation logic
- **Features**:
  - Disconnects from current VPN server
  - Connects to fastest available server (or fastest in specified region)
  - Ensures connection to a different server than before
  - Returns detailed connection information (server, country, city, protocol)
  - Handles retries and timeouts gracefully
  - Can be used as standalone script or imported as module

#### `worker/VPN_ROTATION_GUIDE.md`
- **Purpose**: Comprehensive documentation
- **Contents**:
  - How VPN rotation works
  - Usage examples and configuration options
  - Logging and monitoring
  - Troubleshooting guide
  - Performance impact details
  - API usage examples

#### `worker/ENABLE_VPN_ROTATION.md`
- **Purpose**: Quick start guide
- **Contents**:
  - Prerequisites check
  - 3-step setup process
  - Verification steps
  - Common troubleshooting scenarios
  - Configuration reference
  - Best practices

#### `worker/VPN_ROTATION_CHANGES.md` (this file)
- **Purpose**: Technical change documentation
- **Contents**: Summary of all modifications

### 2. Modified Files

#### `worker/cdp_worker.py`
**Changes:**
- Added `vpn_rotate_min` module import with availability check
- Added command-line arguments:
  - `--vpn-rotate`: Enable VPN rotation (default: False)
  - `--vpn-region`: Optional region preference
  - `--vpn-max-retries`: Maximum retry attempts (default: 2)
- Added `rotate_vpn_if_needed()` function:
  - Checks if prompt_mode is "search"
  - Only rotates if VPN rotation is enabled
  - Logs rotation status (success/failure)
  - Gracefully handles failures (continues with request)
- Modified `run_prompt()` function:
  - Added VPN configuration parameters
  - Calls `rotate_vpn_if_needed()` before processing prompt
  - Rotates VPN before establishing WebSocket connection
- Updated `main()` function:
  - Passes VPN parameters to `run_prompt()`

#### `worker/worker-config.sh`
**Changes:**
- Added VPN configuration section:
  ```bash
  export VPN_ROTATE="false"        # Enable/disable
  export VPN_REGION=""             # Optional region
  export VPN_MAX_RETRIES="2"       # Retry attempts
  ```

#### `worker/start-worker.sh`
**Changes:**
- Added VPN argument building logic
- Conditionally adds `--vpn-rotate`, `--vpn-region`, and `--vpn-max-retries` flags
- Uses environment variables from `worker-config.sh`

#### `worker/start-all.sh`
**Changes:**
- Added inline VPN configuration variables
- Added VPN argument building logic with logging
- Logs VPN status at startup ("enabled" or "disabled")
- Logs region preference when set
- Passes VPN arguments to worker process

#### `API_USAGE_GUIDE.md`
**Changes:**
- Added note in "Prompt Modes" section under `"search"` mode
- Documents VPN rotation feature
- References detailed setup guide

## Technical Details

### How It Works

1. **Request Received**: Worker polls server and claims a request
2. **Mode Check**: Worker extracts `prompt_mode` from job
3. **VPN Rotation**:
   - If `prompt_mode == "search"` AND `--vpn-rotate` is enabled:
     - Disconnect from current VPN server
     - Connect to new server (ensuring it's different)
     - Wait for connection confirmation
     - Log connection details
   - If rotation fails: Log warning and continue
4. **Process Request**: Continue with normal request processing

### Function Call Flow

```
main()
  → claim_request()
  → run_prompt()
      → rotate_vpn_if_needed()  ← NEW
          → vpn_rotate_min.rotate()
              → nordvpn disconnect
              → nordvpn connect [region]
              → nordvpn status (polling)
      → websocket.create_connection()
      → [execute bookmarklet]
      → [wait for response]
```

### VPN Rotation Logic

```python
def rotate_vpn_if_needed(prompt_mode, vpn_enabled, vpn_region, vpn_max_retries):
    if not vpn_enabled:
        return  # Feature disabled
    
    if prompt_mode != "search":
        return  # Only rotate for search mode
    
    if not VPN_AVAILABLE:
        log warning and return
    
    try:
        result = vpn_rotate_min.rotate(region, require_new=True, max_retries)
        if result["ok"]:
            log success with server details
        else:
            log failure warning
    except Exception:
        log error and continue
```

### Error Handling

- **VPN Module Missing**: Logs warning, continues without rotation
- **NordVPN Not Installed**: Logs error, continues without rotation
- **Connection Failed**: Logs warning with retry count, continues
- **Connection Timeout**: Logs warning, continues with current connection
- **Unexpected Error**: Logs error with exception, continues

**Philosophy**: Never fail a request due to VPN issues. VPN rotation is a best-effort enhancement.

## Configuration Options

### Command Line Arguments

```bash
--vpn-rotate              # Enable VPN rotation for search mode
--vpn-region REGION       # Prefer specific region (optional)
--vpn-max-retries N       # Max retry attempts (default: 2)
```

### Environment Variables

```bash
VPN_ROTATE="true|false"   # Enable/disable
VPN_REGION="region_name"  # Optional region preference
VPN_MAX_RETRIES="2"       # Retry attempts
```

### Supported Regions

Any region supported by NordVPN, including:
- `united_states`, `france`, `united_kingdom`
- `germany`, `canada`, `japan`
- `australia`, `netherlands`, `sweden`
- Many more (check with `nordvpn countries`)

## Logging

### Success Logs

```
[INFO] Search mode detected, rotating VPN to get fresh IP address...
[INFO] VPN rotation successful! Connected to: us9876.nordvpn.com (United States, New York) [UDP] (retries: 0)
[INFO] Processing request 123
```

### Failure Logs

```
[INFO] Search mode detected, rotating VPN to get fresh IP address...
[WARNING] VPN rotation failed: Failed to confirm connected status quickly. Continuing with current connection (retries: 2)
[INFO] Processing request 123
```

### Disabled Logs

```
[DEBUG] Skipping VPN rotation for prompt_mode=study
[INFO] Processing request 123
```

## Performance Impact

| Scenario | Impact |
|----------|--------|
| **Search Mode (VPN enabled)** | +5-15 seconds for VPN rotation |
| **Search Mode (VPN disabled)** | No impact |
| **Other Modes (study, normal)** | No impact |
| **VPN Rotation Failure** | ~2-5 seconds overhead for retries |

## Security & Privacy

### Benefits
- Fresh IP address for each search request
- Reduces risk of rate limiting and blacklisting
- Encrypted traffic via NordVPN
- Regional compliance (can constrain to specific countries)

### Considerations
- Requires NordVPN subscription
- VPN credentials stored on Raspberry Pi
- Connection logs may exist on VPN provider side

## Testing

### Manual Testing

Test VPN rotation directly:
```bash
cd ~/eypiyay/worker
python3 vpn_rotate_min.py
python3 vpn_rotate_min.py france
```

### Integration Testing

1. Enable VPN rotation in config
2. Send search mode request via API
3. Check worker logs for rotation confirmation
4. Verify IP changed: `curl https://api.ipify.org`

### Test API Request

```bash
curl -X POST "https://your-server.com/requests" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "search for quantum computing information",
    "prompt_mode": "search"
  }'
```

## Backward Compatibility

✅ **Fully Backward Compatible**

- Default: VPN rotation is **disabled** (`VPN_ROTATE="false"`)
- Existing deployments work without changes
- No new Python dependencies required (uses only stdlib)
- NordVPN is optional (feature gracefully degrades if not available)
- Workers without NordVPN continue functioning normally

## Dependencies

### Python Modules (stdlib only)
- `subprocess` - for running nordvpn commands
- `time` - for delays and timeouts
- `json` - for output formatting
- `typing` - for type hints

### External Dependencies
- NordVPN CLI (`nordvpn` command)
- Active NordVPN subscription
- Authenticated NordVPN session

## Troubleshooting Quick Reference

| Issue | Solution |
|-------|----------|
| Module not found | Ensure `vpn_rotate_min.py` is in worker/ directory |
| NordVPN not installed | Run NordVPN installer: `sh <(curl -sSf https://downloads.nordcdn.com/apps/linux/install.sh)` |
| Not logged in | Run `nordvpn login` |
| Permission denied | Add user to nordvpn group: `sudo usermod -aG nordvpn $USER` |
| Connection timeouts | Increase `--vpn-max-retries` |
| Wrong region | Check available regions: `nordvpn countries` |

## Future Enhancements (Not Implemented)

Possible future improvements:
- [ ] Track rotation statistics (success rate, average time)
- [ ] Intelligent region selection based on prompt language
- [ ] IP blacklist detection and automatic rotation
- [ ] Support for other VPN providers (ExpressVPN, etc.)
- [ ] Configurable rotation triggers (not just search mode)
- [ ] IP address caching to avoid duplicate servers
- [ ] Rotation scheduling (rotate after N requests or M minutes)

## Files Changed Summary

```
worker/
├── vpn_rotate_min.py               [NEW] - Core VPN rotation logic
├── cdp_worker.py                   [MODIFIED] - Integrated VPN rotation
├── worker-config.sh                [MODIFIED] - Added VPN config
├── start-worker.sh                 [MODIFIED] - Added VPN args
├── start-all.sh                    [MODIFIED] - Added VPN args + logging
├── VPN_ROTATION_GUIDE.md           [NEW] - Detailed documentation
├── ENABLE_VPN_ROTATION.md          [NEW] - Quick start guide
└── VPN_ROTATION_CHANGES.md         [NEW] - This file

API_USAGE_GUIDE.md                  [MODIFIED] - Documented feature
```

## Migration Path

### For Existing Deployments

1. **Pull Latest Code**
   ```bash
   cd ~/eypiyay
   git pull origin main
   ```

2. **Review Configuration**
   ```bash
   # VPN rotation is disabled by default - no immediate action needed
   cat worker/worker-config.sh | grep VPN
   ```

3. **Optional: Enable VPN Rotation**
   ```bash
   # Edit config
   nano worker/worker-config.sh
   # Set VPN_ROTATE="true"
   
   # Restart worker
   worker/stop-service.sh
   worker/start-all.sh
   ```

### For New Deployments

Follow `ENABLE_VPN_ROTATION.md` if VPN rotation is desired.

## Support & Documentation

- **Quick Start**: `worker/ENABLE_VPN_ROTATION.md`
- **Full Guide**: `worker/VPN_ROTATION_GUIDE.md`
- **API Docs**: See "Prompt Modes" section in `API_USAGE_GUIDE.md`
- **This Document**: Technical details and change summary


