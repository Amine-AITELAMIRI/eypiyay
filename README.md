# ChatGPT Relay Automation

This repository now contains a small relay server plus a local Chrome/ChatGPT worker.

## Components

- `server/`: FastAPI application that accepts user prompts, tracks their status, and stores results in SQLite (`server/server.db`).
- `worker/cdp_worker.py`: Long-running process that polls the server, drives the ChatGPT web UI through the existing bookmarklet (via CDP), and pushes responses back.

## Prerequisites

1. Python 3.11+ on both the server host and the worker machine.
2. Google Chrome (or Chromium) launched locally with remote debugging enabled:
   ```bash
   chrome --remote-debugging-port=9222 --remote-allow-origins=http://localhost:9222 --user-data-dir="YOUR_PROFILE_DIR"
   ```
3. The `bookmarklet.js` file from this repo available to the worker (it is loaded and executed verbatim).

## Running the Server

```bash
cd server
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn server.main:app --host 0.0.0.0 --port 8000
```

### API Overview

- `POST /requests` `{ "prompt": "..." }` -> `201` with request id.
- `GET /requests/{id}` -> returns status (`pending | processing | completed | failed`).
- Worker-only endpoints:
  - `POST /worker/claim` `{ "worker_id": "worker-1" }`
  - `POST /worker/{id}/complete` `{ "response": "..." }`
  - `POST /worker/{id}/fail` `{ "error": "..." }`

## Running the Worker

```bash
cd worker
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python cdp_worker.py http://localhost:8000 worker-1 chatgpt.com --pick-first
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

## Notes

- The worker stores the ChatGPT response exactly as the bookmarklet saves it (JSON string with prompt/response/timestamp/url). Downstream consumers can parse it for richer data.
- Failures (timeouts, CDP issues) are reported back via `/worker/{id}/fail` so clients can retry or inspect `error`.
- The SQLite file lives next to the server code; adjust `DB_PATH` in `server/database.py` if you need a different location.


