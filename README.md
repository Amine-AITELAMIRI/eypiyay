# ChatGPT Relay Automation

This repository contains a FastAPI relay server and a local Chrome/ChatGPT worker for automated ChatGPT interactions.

## Components

- `server/`: FastAPI application that accepts user prompts, tracks their status, and stores results in PostgreSQL (Supabase).
- `worker/cdp_worker.py`: Long-running process that polls the server, drives the ChatGPT web UI through the existing bookmarklet (via CDP), and pushes responses back.
- `render.yaml`: Render deployment configuration for hosting the API with Supabase PostgreSQL database.

## Prerequisites

1. Python 3.11+ on both the server host and the worker machine.
2. Google Chrome (or Chromium) launched locally with remote debugging enabled:
   ```bash
   chrome --remote-debugging-port=9222 --remote-allow-origins=http://localhost:9222 --user-data-dir="YOUR_PROFILE_DIR"
   ```
3. The `bookmarklet.js` file from this repo available to the worker (it is loaded and executed verbatim).

## Deployment

### Deploy to Render (with Supabase Database)

1. **Set up Supabase Database:**
   - Go to [supabase.com](https://supabase.com) and create a project (or use existing)
   - Get your database password from Settings → Database
   - Your connection string format:
     ```
     postgresql://postgres.PROJECT_REF:PASSWORD@aws-0-REGION.pooler.supabase.com:6543/postgres
     ```
   - See [SUPABASE_MIGRATION_GUIDE.md](SUPABASE_MIGRATION_GUIDE.md) for detailed setup

2. **Fork this repository** to your GitHub account.

3. **Connect to Render:**
   - Go to [render.com](https://render.com) and sign up/login
   - Click "New +" → "Blueprint"
   - Connect your GitHub account and select this repository
   - Render will automatically detect the `render.yaml` configuration

4. **Set Environment Variables:**
   - In the Render dashboard, go to your web service
   - Navigate to "Environment" tab
   - Add the following environment variables:
     - `DATABASE_URL`: Your Supabase connection string (see step 1)
     - `API_KEY`: Generate a secure random string (e.g., using `openssl rand -hex 32`)
     - `RETENTION_HOURS`: Hours to retain completed requests (optional, default: 24)

5. **Deploy:**
   - Render will automatically deploy your application
   - The database tables will be created automatically on first startup
   - Your API will be available at `https://your-app-name.onrender.com`

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://postgres.hizcmicfsbirljnfaogr:[YOUR-PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
export API_KEY="your-secure-api-key"
export RETENTION_HOURS="24"  # Optional: hours to retain completed requests

# Run the server
uvicorn server.main:app --host 0.0.0.0 --port 8000
```

**Note**: Replace `[YOUR-PASSWORD]` with your actual Supabase database password. See [SUPABASE_MIGRATION_GUIDE.md](SUPABASE_MIGRATION_GUIDE.md) for details.

### API Overview

All endpoints require API key authentication via the `X-API-Key` header.

- `GET /health` -> Health check (no auth required)
- `GET /` or `GET /database-viewer` -> Web GUI database viewer (no auth required)
- `POST /requests` `{ "prompt": "...", "prompt_mode": "search|study" }` -> `201` with request id
- `GET /requests/{id}?delete_after_fetch=true` -> returns status and optionally deletes after fetch
- `POST /requests/{id}/fetch-and-delete` -> returns response and immediately deletes from database
- `POST /admin/cleanup?retention_hours=24` -> manually trigger cleanup of old requests
- `GET /admin/database/requests?limit=10&status=completed` -> view database records
- `GET /admin/database/stats` -> get database statistics
- Worker-only endpoints:
  - `POST /worker/claim` `{ "worker_id": "worker-1" }`
  - `POST /worker/{id}/complete` `{ "response": "..." }`
  - `POST /worker/{id}/fail` `{ "error": "..." }`

#### Special Prompt Modes

The API supports special prompt modes that activate ChatGPT's built-in commands:

- **`"search"`** - Types `/sear` and presses Enter before the user prompt to activate search mode
- **`"study"`** - Types `/stu` and presses Enter before the user prompt to activate study mode
- **`"deep"`** - Types `/deep` and presses Enter before the user prompt to activate deep research mode (⚠️ 5-30 minutes response time)
- **`null` or omitted** - No special mode is applied (default behavior)

Example requests:

```json
// Normal prompt
{
  "prompt": "What is the capital of France?"
}

// Search mode prompt  
{
  "prompt": "Find information about Python programming",
  "prompt_mode": "search"
}

// Study mode prompt
{
  "prompt": "Explain machine learning concepts", 
  "prompt_mode": "study"
}

// Deep research mode prompt (takes 5-30 minutes)
{
  "prompt": "Conduct comprehensive research on quantum computing applications",
  "prompt_mode": "deep",
  "webhook_url": "https://your-server.com/webhook"
}
```

**Note:** Deep research mode is designed for comprehensive analysis and may take 5-30 minutes to complete. The system handles these long-running requests without timeouts using an asynchronous worker pattern. Consider using webhooks for notification when the research is complete.

#### Database Cleanup

The API provides automatic database cleanup to manage storage efficiently:

**Option 1: Query Parameter**
```bash
# Fetch and delete in one request
GET /requests/{id}?delete_after_fetch=true
```

**Option 2: Dedicated Endpoint**
```bash
# Fetch and delete using dedicated endpoint
POST /requests/{id}/fetch-and-delete
```

**Benefits:**
- Automatic storage management - responses are deleted after being fetched
- Prevents database bloat from accumulated responses
- One-time use pattern - each response can only be fetched once
- Atomic operation - fetch and delete happen in a single transaction

**Usage Examples:**
```bash
# Create a request
curl -X POST "https://your-api.com/requests" \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello world", "prompt_mode": "search"}'

# Fetch response and delete immediately
curl -X POST "https://your-api.com/requests/123/fetch-and-delete" \
  -H "X-API-Key: your-key"

# Or fetch with delete-after-fetch parameter
curl "https://your-api.com/requests/123?delete_after_fetch=true" \
  -H "X-API-Key: your-key"
```

#### Automatic Cleanup

The server includes automatic cleanup features to maintain database health:

**Automatic Background Cleanup:**
- Runs every hour to remove completed/failed requests older than the retention period
- Configurable via `RETENTION_HOURS` environment variable (default: 24 hours)
- Only removes requests that are in `completed` or `failed` status

**Manual Cleanup:**
```bash
# Trigger manual cleanup
curl -X POST "https://your-api.com/admin/cleanup" \
  -H "X-API-Key: your-key"

# Cleanup with custom retention period
curl -X POST "https://your-api.com/admin/cleanup?retention_hours=12" \
  -H "X-API-Key: your-key"
```

**Environment Variables:**
```bash
# Set retention period (default: 24 hours)
export RETENTION_HOURS=48  # Keep requests for 48 hours
```

## Viewing Database Content

### Quick Database Access
```bash
# View recent requests
curl "https://your-api.com/admin/database/requests?limit=10" \
  -H "X-API-Key: your-key"

# Get database statistics
curl "https://your-api.com/admin/database/stats" \
  -H "X-API-Key: your-key"

# View completed requests only
curl "https://your-api.com/admin/database/requests?status=completed" \
  -H "X-API-Key: your-key"
```

### Direct Database Access
```bash
# Connect to database
psql $DATABASE_URL

# View all requests
SELECT * FROM requests ORDER BY created_at DESC LIMIT 10;

# View by status
SELECT * FROM requests WHERE status = 'completed';
```

See [DATABASE_VIEWING_GUIDE.md](DATABASE_VIEWING_GUIDE.md) for comprehensive database viewing options.

### Web GUI Database Viewer

Access the built-in web interface for easy database monitoring:

```bash
# Open in browser
https://your-api.com/
# or
https://your-api.com/database-viewer
```

**Features:**
- 📊 Real-time database statistics
- 📋 Interactive table view with filtering
- 🔍 Detailed record inspection
- ⏰ Auto-refresh capability
- 📱 Mobile-responsive design
- ⚡ Pre-configured API settings (ready to use)

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

- `DATABASE_URL`: Supabase PostgreSQL connection string (set manually in Render dashboard)
  - Format: `postgresql://postgres.PROJECT_REF:PASSWORD@aws-0-REGION.pooler.supabase.com:6543/postgres`
- `API_KEY`: Secure API key for authentication (set manually in Render dashboard)
- `RETENTION_HOURS`: Hours to retain completed requests (optional, default: 24)

### Worker Configuration

The worker now requires an API key as the third argument. Make sure to use the same API key that you set in the Render environment variables.

### Security Notes

- All API endpoints (except `/health`) require authentication via the `X-API-Key` header
- Generate a secure API key using: `openssl rand -hex 32`
- Keep your API key secret and don't commit it to version control
- The worker authenticates with the same API key used by the server

## New Features

### ✨ Automatic Source Extraction

The API now automatically extracts and returns **sources** separately from the response content. When ChatGPT provides citations (especially in search mode), they are parsed into structured data:

```json
{
  "response": "Clean content without source list...",
  "sources": [
    {
      "number": 1,
      "url": "https://example.com/article",
      "title": "Article Title"
    }
  ]
}
```

**Benefits:**
- Clean content display without citation clutter
- Structured source data for easy access
- Perfect for research and fact-checking
- Automatic parsing of `[1]: URL "Title"` format

See [SOURCES_FEATURE.md](SOURCES_FEATURE.md) for details and [MIGRATION_GUIDE_SOURCES.md](MIGRATION_GUIDE_SOURCES.md) for migration instructions.

## Notes

- The worker stores the ChatGPT response exactly as the bookmarklet saves it (JSON string with prompt/response/sources/timestamp/url). Downstream consumers can parse it for richer data.
- Failures (timeouts, CDP issues) are reported back via `/worker/{id}/fail` so clients can retry or inspect `error`.
- The PostgreSQL database is hosted on Supabase with automatic backups and excellent monitoring tools.
- The API is served over HTTPS when deployed to Render.
- See [SUPABASE_MIGRATION_GUIDE.md](SUPABASE_MIGRATION_GUIDE.md) for database setup and migration instructions.


