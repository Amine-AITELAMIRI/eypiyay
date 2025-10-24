#!/bin/bash
cd ~/eypiyay
source ~/worker-config.sh

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
  --chatgpt-url "$CHATGPT_URL"
