# Quick Supabase Setup

This is a quick reference guide for setting up your Supabase database with this project.

## Step 1: Get Your Database Password

1. Go to: https://app.supabase.com/project/hizcmicfsbirljnfaogr/settings/database
2. Scroll to **Connection String** section
3. Find your database password (or reset it if you don't have it)

## Step 2: Set Up Environment Variables

### For Local Development:

```bash
# Copy the example file
cp env.example .env

# Edit .env and add your password
# Replace [YOUR-PASSWORD] with your actual password
```

Or set directly:
```bash
export DATABASE_URL="postgresql://postgres.hizcmicfsbirljnfaogr:YOUR_PASSWORD_HERE@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
export API_KEY=$(openssl rand -hex 32)
export RETENTION_HOURS=24
```

### For Render Deployment:

1. Go to your Render dashboard: https://dashboard.render.com
2. Select your web service
3. Click **Environment** tab
4. Add/Update these variables:
   - `DATABASE_URL`: `postgresql://postgres.hizcmicfsbirljnfaogr:YOUR_PASSWORD@aws-0-us-west-1.pooler.supabase.com:6543/postgres`
   - `API_KEY`: Generate with `openssl rand -hex 32`
   - `RETENTION_HOURS`: `24`

## Step 3: Test Connection

### Local Test:
```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn server.main:app --reload

# In another terminal, test the health endpoint
curl http://localhost:8000/health
```

### Test Database Connection:
```bash
# Using psql
psql "postgresql://postgres.hizcmicfsbirljnfaogr:YOUR_PASSWORD@aws-0-us-west-1.pooler.supabase.com:6543/postgres" -c "SELECT 1;"
```

## Step 4: Verify Database Tables

The application will automatically create the `requests` table on startup. To verify:

1. Go to Supabase Table Editor: https://app.supabase.com/project/hizcmicfsbirljnfaogr/editor
2. You should see a `requests` table with these columns:
   - id (int8)
   - prompt (text)
   - status (text)
   - response (text)
   - error (text)
   - worker_id (text)
   - created_at (timestamp)
   - updated_at (timestamp)
   - webhook_url (text)
   - webhook_delivered (bool)
   - prompt_mode (text)
   - model_mode (text)

## Step 5: Test API

```bash
# Create a test request
curl -X POST "http://localhost:8000/requests" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Test prompt"}'

# Get database stats
curl "http://localhost:8000/admin/database/stats" \
  -H "X-API-Key: YOUR_API_KEY"
```

## Troubleshooting

### Can't connect to database
- Verify your password is correct
- Check that the URL format matches exactly
- Supabase uses port 6543 for connection pooling (not 5432)

### SSL errors
Add `?sslmode=require` to the end of your connection string:
```
postgresql://postgres.hizcmicfsbirljnfaogr:PASSWORD@aws-0-us-west-1.pooler.supabase.com:6543/postgres?sslmode=require
```

### Table not created
Check the server logs. The table should be created automatically on startup. If not:
1. Go to SQL Editor in Supabase: https://app.supabase.com/project/hizcmicfsbirljnfaogr/sql
2. Run the SQL from `server/database.py` `init_db()` function manually

## Next Steps

- ✅ Database is connected and working
- ✅ Run the worker: `python -m worker.cdp_worker http://localhost:8000 worker-1 YOUR_API_KEY chatgpt.com --pick-first`
- ✅ Access the web GUI: http://localhost:8000/database-viewer
- ✅ Deploy to Render following the instructions in README.md

## Your Supabase Project Info

- **Project URL**: https://hizcmicfsbirljnfaogr.supabase.co
- **Dashboard**: https://app.supabase.com/project/hizcmicfsbirljnfaogr
- **Project Reference**: hizcmicfsbirljnfaogr
- **Region**: US West (Oregon)

For more detailed information, see [SUPABASE_MIGRATION_GUIDE.md](SUPABASE_MIGRATION_GUIDE.md)

