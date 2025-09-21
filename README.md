# ChatGPT Relay Automation

This repository contains a FastAPI relay server and a local Chrome/ChatGPT worker for automated ChatGPT interactions.

## Components

- `server/`: FastAPI application that accepts user prompts, tracks their status, and stores results in PostgreSQL.
- `worker/cdp_worker.py`: Long-running process that polls the server, drives the ChatGPT web UI through the existing bookmarklet (via CDP), and pushes responses back.
- `render.yaml`: Render deployment configuration for hosting the API with managed PostgreSQL.

## Prerequisites

1. Python 3.11+ on both the server host and the worker machine.
2. Google Chrome (or Chromium) launched locally with remote debugging enabled:
   ```bash
   chrome --remote-debugging-port=9222 --remote-allow-origins=http://localhost:9222 --user-data-dir="YOUR_PROFILE_DIR"
   ```
3. The `bookmarklet.js` file from this repo available to the worker (it is loaded and executed verbatim).

## Deployment

### Deploy to Render

1. **Fork this repository** to your GitHub account.

2. **Connect to Render:**
   - Go to [render.com](https://render.com) and sign up/login
   - Click "New +" → "Blueprint"
   - Connect your GitHub account and select this repository
   - Render will automatically detect the `render.yaml` configuration

3. **Set Environment Variables:**
   - In the Render dashboard, go to your web service
   - Navigate to "Environment" tab
   - Add the following environment variables:
     - `DATABASE_URL`: Will be automatically set by Render when you create the PostgreSQL database
     - `API_KEY`: Generate a secure random string (e.g., using `openssl rand -hex 32`)

4. **Deploy:**
   - Render will automatically deploy your application
   - The PostgreSQL database will be created and connected automatically
   - Your API will be available at `https://your-app-name.onrender.com`

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://user:password@localhost:5432/dbname"
export API_KEY="your-secure-api-key"

# Run the server
uvicorn server.main:app --host 0.0.0.0 --port 8000
```

### API Overview

All endpoints require API key authentication via the `X-API-Key` header.

- `GET /health` -> Health check (no auth required)
- `POST /requests` `{ "prompt": "..." }` -> `201` with request id
- `GET /requests/{id}` -> returns status (`pending | processing | completed | failed`)
- Worker-only endpoints:
  - `POST /worker/claim` `{ "worker_id": "worker-1" }`
  - `POST /worker/{id}/complete` `{ "response": "..." }`
  - `POST /worker/{id}/fail` `{ "error": "..." }`

## Running the Worker

### Against Hosted API

```bash
# Install dependencies
pip install -r requirements.txt

# Run worker against hosted API
python -m worker.cdp_worker https://your-app-name.onrender.com worker-1 YOUR_API_KEY chatgpt.com --pick-first
```

### Against Local API

```bash
# Install dependencies
pip install -r requirements.txt

# Run worker against local API
python -m worker.cdp_worker http://localhost:8000 worker-1 YOUR_API_KEY chatgpt.com --pick-first
```

Important CLI flags:

- `--script PATH` ? alternative bookmarklet source.
- `--response-timeout` ? seconds to wait for ChatGPT to finish (default 120).
- `--poll-interval` ? idle wait time when no jobs are queued.
- `--host/--port` ? Chrome CDP endpoint if non-default.

The worker claims pending prompts, injects them through your existing bookmarklet automation, waits for the JSON blob saved in localStorage, and posts that JSON back to the server. Downloaded results are stored with the original prompt and URL; clients read them via `GET /requests/{id}`.

## Typical Flow

1. Client: `POST /requests` with prompt.
2. Worker (already running) claims the job, drives ChatGPT, and posts the resulting JSON string to `/worker/{id}/complete`.
3. Client polls or fetches `GET /requests/{id}` until `status == "completed"`, then parses the `response` field.

## Configuration

### Environment Variables

- `DATABASE_URL`: PostgreSQL connection string (automatically set by Render)
- `API_KEY`: Secure API key for authentication (set manually in Render dashboard)

### Worker Configuration

The worker now requires an API key as the third argument. Make sure to use the same API key that you set in the Render environment variables.

### Security Notes

- All API endpoints (except `/health`) require authentication via the `X-API-Key` header
- Generate a secure API key using: `openssl rand -hex 32`
- Keep your API key secret and don't commit it to version control
- The worker authenticates with the same API key used by the server

## Notes

- The worker stores the ChatGPT response exactly as the bookmarklet saves it (JSON string with prompt/response/timestamp/url). Downstream consumers can parse it for richer data.
- Failures (timeouts, CDP issues) are reported back via `/worker/{id}/fail` so clients can retry or inspect `error`.
- The PostgreSQL database is automatically managed by Render and includes automatic backups.
- The API is served over HTTPS when deployed to Render.


