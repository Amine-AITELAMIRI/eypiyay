#!/bin/bash
cd ~/eypiyay
source ~/worker-config.sh

# Build VPN arguments
VPN_ARGS=""
if [ "$VPN_ROTATE" = "true" ]; then
    VPN_ARGS="--vpn-rotate"
    if [ -n "$VPN_REGION" ]; then
        VPN_ARGS="$VPN_ARGS --vpn-region $VPN_REGION"
    fi
    if [ -n "$VPN_MAX_RETRIES" ]; then
        VPN_ARGS="$VPN_ARGS --vpn-max-retries $VPN_MAX_RETRIES"
    fi
fi

# Start the worker
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
  $VPN_ARGS
