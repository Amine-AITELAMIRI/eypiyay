# Quick Start: Enable VPN Rotation

This guide will help you quickly enable VPN rotation to avoid getting blacklisted when using search mode.

## Prerequisites Check

Verify NordVPN is installed and working:

```bash
# Check if NordVPN is installed
nordvpn --version

# Check login status
nordvpn account

# Test a manual connection
nordvpn connect
nordvpn status
```

If NordVPN is not installed or you're not logged in, see the **Troubleshooting** section below.

## Quick Setup (3 Steps)

### 1. Enable VPN Rotation

Edit your configuration file:

```bash
nano ~/worker-config.sh
```

Or if using `start-all.sh` directly:

```bash
nano ~/eypiyay/worker/start-all.sh
```

Change this line:
```bash
export VPN_ROTATE="false"
```

To:
```bash
export VPN_ROTATE="true"
```

### 2. (Optional) Set Preferred Region

If you want to limit VPN servers to a specific region:

```bash
export VPN_REGION="united_states"
```

Popular regions:
- `united_states`
- `france`
- `united_kingdom`
- `canada`
- `germany`
- `japan`

To use any region (fastest available), leave it empty:
```bash
export VPN_REGION=""
```

### 3. Restart the Worker

```bash
# Stop the current worker
~/eypiyay/worker/stop-service.sh

# Start with new configuration
~/eypiyay/worker/start-all.sh
```

Or if using systemd:
```bash
sudo systemctl restart chatgpt-relay-worker
```

## Verify It's Working

### Check Logs

```bash
tail -f ~/eypiyay/logs/worker.log
```

When a search request comes in, you should see:
```
[INFO] Search mode detected, rotating VPN to get fresh IP address...
[INFO] VPN rotation successful! Connected to: us9876.nordvpn.com (United States, New York) [UDP] (retries: 0)
```

### Send a Test Request

```bash
curl -X POST "https://your-server.com/requests" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "search for information about quantum computing",
    "prompt_mode": "search"
  }'
```

## Configuration Reference

### Full Configuration Options

In `worker-config.sh` or `start-all.sh`:

```bash
# Enable/disable VPN rotation
export VPN_ROTATE="true"          # "true" or "false"

# Preferred region (optional)
export VPN_REGION=""               # Empty for fastest, or region name

# Maximum connection retries
export VPN_MAX_RETRIES="2"         # Number of retries if connection fails
```

## Performance Impact

- **VPN Rotation Time**: 5-15 seconds per rotation
- **Trigger**: Only on `prompt_mode: "search"` requests
- **Regular Prompts**: Unaffected (no rotation)

## Troubleshooting

### NordVPN Not Installed

**Symptoms:**
```
[ERROR] Unexpected error during VPN rotation: [Errno 2] No such file or directory: 'nordvpn'
```

**Solution:**
```bash
# Download and install NordVPN
sh <(curl -sSf https://downloads.nordcdn.com/apps/linux/install.sh)

# Login to NordVPN
nordvpn login

# Configure NordVPN
nordvpn set technology nordlynx  # Faster protocol
nordvpn set killswitch off       # Avoid connectivity issues
```

### Not Logged In

**Symptoms:**
```
[ERROR] You are not logged in.
```

**Solution:**
```bash
nordvpn login
# Follow the prompts to authenticate
```

### Permission Denied

**Symptoms:**
```
[ERROR] Permission denied when running nordvpn commands
```

**Solution:**
```bash
# Add your user to nordvpn group
sudo usermod -aG nordvpn $USER

# Logout and login again for changes to take effect
# Or, for immediate effect without logout:
newgrp nordvpn
```

### VPN Module Not Found

**Symptoms:**
```
[WARNING] vpn_rotate_min module not available, VPN rotation will be disabled
```

**Solution:**
```bash
# Ensure you're in the project directory
cd ~/eypiyay/worker

# Verify the file exists
ls -la vpn_rotate_min.py

# If missing, re-download the project or copy the file
```

### Connection Keeps Failing

**Symptoms:**
```
[WARNING] VPN rotation failed: Failed to confirm connected status quickly.
```

**Solutions:**

1. **Increase retries:**
   ```bash
   export VPN_MAX_RETRIES="5"
   ```

2. **Test manual connection:**
   ```bash
   nordvpn disconnect
   nordvpn connect
   nordvpn status
   ```

3. **Check NordVPN service:**
   ```bash
   sudo systemctl status nordvpnd
   sudo systemctl restart nordvpnd
   ```

4. **Try a specific region:**
   ```bash
   export VPN_REGION="united_states"
   ```

### Verify Region Support

Check available regions:
```bash
nordvpn countries
```

Check servers in a region:
```bash
nordvpn cities united_states
```

## Disable VPN Rotation

To disable VPN rotation:

```bash
# Edit configuration
nano ~/worker-config.sh

# Set to false
export VPN_ROTATE="false"

# Restart worker
~/eypiyay/worker/stop-service.sh
~/eypiyay/worker/start-all.sh
```

## Advanced: Manual Testing

Test VPN rotation directly:

```bash
cd ~/eypiyay/worker

# Rotate to fastest server
python3 vpn_rotate_min.py

# Rotate to specific region
python3 vpn_rotate_min.py france

# Check output (JSON format)
python3 vpn_rotate_min.py | jq .
```

Example output:
```json
{
  "ok": true,
  "status": "Connected",
  "server": "us9876.nordvpn.com",
  "country": "United States",
  "city": "New York",
  "technology": "NordLynx",
  "protocol": "UDP",
  "retries": 0
}
```

## Monitoring

### Check Current VPN Status

```bash
nordvpn status
```

### Monitor Worker Logs in Real-time

```bash
tail -f ~/eypiyay/logs/worker.log | grep -i vpn
```

### Check IP Changes

Before VPN rotation:
```bash
curl -s https://api.ipify.org
```

After each search request, your IP should change.

## Best Practices

1. **Start with local testing**: Test VPN rotation manually before enabling in production
2. **Monitor logs**: Watch the first few search requests to ensure rotation works
3. **Set reasonable retries**: Default of 2 is usually sufficient
4. **Use regional preferences**: If targeting specific markets, set appropriate region
5. **Keep NordVPN updated**: Regular updates ensure best performance

## Support

For more detailed information:
- See `VPN_ROTATION_GUIDE.md` for complete documentation
- Check NordVPN logs: `nordvpn settings`
- Test connectivity: `nordvpn connect && nordvpn status`


