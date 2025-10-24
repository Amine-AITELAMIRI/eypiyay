#!/bin/bash
# Configuration for ChatGPT Relay Worker

# Server URL (replace with your actual server URL)
export SERVER_URL="https://chatgpt-relay-api.onrender.com"

# API Key (replace with your actual API key)
export API_KEY="72b0253ba06e73484e2b71370a503ce00183b59750e4be1dd5eb10896587954a"

# Worker ID (unique identifier for this worker)
export WORKER_ID="raspberry-pi-worker"

# ChatGPT URL (the URL to navigate to for each request)
# This URL will be reloaded for each new request
export CHATGPT_URL="https://chatgpt.com/g/g-p-68d04e772ef881918e915068fbe126e4-api-auto/project"
#export CHATGPT_URL=
#https://chatgpt.com/?temporary-chat=true
# Chrome debugging settings
export CHROME_HOST="localhost"
export CHROME_PORT="9222"

# Worker settings
export POLL_INTERVAL="3.0"
