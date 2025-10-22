# Supabase Migration Guide

This guide explains how to migrate from Render's PostgreSQL database to Supabase.

## Overview

Your project has been configured to use Supabase as the database backend instead of Render's managed PostgreSQL. Supabase provides:

- Free PostgreSQL database with 500MB storage
- Real-time subscriptions
- Built-in authentication (if needed later)
- Better dashboard and monitoring tools
- Direct database access via Supabase Studio

## Supabase Configuration

### Your Supabase Project Details

- **Project URL**: `https://hizcmicfsbirljnfaogr.supabase.co`
- **Project Reference**: `hizcmicfsbirljnfaogr`
- **Region**: US West (Oregon)

### Important: Get Your Database Password

⚠️ **You need to get your database password from Supabase Dashboard:**

1. Go to [Supabase Dashboard](https://app.supabase.com/project/hizcmicfsbirljnfaogr/settings/database)
2. Navigate to: **Settings** → **Database**
3. Find the **Connection String** section
4. Copy your database password (it was shown when you created the project)
5. Or reset it if you don't have it saved

### Database Connection String Format

```
postgresql://postgres.hizcmicfsbirljnfaogr:[YOUR-PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres
```

Replace `[YOUR-PASSWORD]` with your actual database password from Supabase.

## Migration Steps

### 1. Update Environment Variables

#### For Render Deployment:

1. Go to your Render dashboard
2. Select your web service (`chatgpt-relay-api`)
3. Go to **Environment** tab
4. Update the `DATABASE_URL` variable:
   ```
   postgresql://postgres.hizcmicfsbirljnfaogr:[YOUR-PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres
   ```

#### For Local Development:

```bash
# Update your environment variables
export DATABASE_URL="postgresql://postgres.hizcmicfsbirljnfaogr:[YOUR-PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
export API_KEY="your-secure-api-key"
export RETENTION_HOURS="24"
```

### 2. Initialize Database Schema

The application will automatically create the required tables on startup. The `requests` table will be created with this schema:

```sql
CREATE TABLE IF NOT EXISTS requests (
    id SERIAL PRIMARY KEY,
    prompt TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    response TEXT,
    error TEXT,
    worker_id TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    webhook_url TEXT,
    webhook_delivered BOOLEAN NOT NULL DEFAULT FALSE,
    prompt_mode TEXT,
    model_mode TEXT
);
```

### 3. Deploy Updated Configuration

If using Render Blueprint deployment:

```bash
# Commit the updated render.yaml
git add render.yaml
git commit -m "Migrate to Supabase database"
git push origin main
```

Render will automatically redeploy with the new configuration.

### 4. Verify Connection

After deployment, check that the database is working:

```bash
# Health check
curl https://your-app.onrender.com/health

# Database stats (requires API key)
curl "https://your-app.onrender.com/admin/database/stats" \
  -H "X-API-Key: your-api-key"
```

## Supabase Dashboard Access

### Access Your Database

1. Go to [Supabase Dashboard](https://app.supabase.com/project/hizcmicfsbirljnfaogr)
2. Navigate to **Table Editor** to view your `requests` table
3. Use **SQL Editor** to run custom queries

### Useful SQL Queries

```sql
-- View all requests
SELECT * FROM requests ORDER BY created_at DESC LIMIT 10;

-- Count requests by status
SELECT status, COUNT(*) 
FROM requests 
GROUP BY status;

-- View recent completed requests
SELECT id, prompt, response, created_at 
FROM requests 
WHERE status = 'completed' 
ORDER BY created_at DESC 
LIMIT 10;

-- Clean up old completed requests
DELETE FROM requests 
WHERE status IN ('completed', 'failed') 
AND updated_at < NOW() - INTERVAL '24 hours';
```

### Database Monitoring

Supabase provides excellent monitoring tools:

1. **Database Health**: Settings → Database → Health
2. **Query Performance**: Database → Query Performance
3. **Storage Usage**: Settings → Database → Usage
4. **Real-time Logs**: Logs → Database Logs

## Migration from Render Database (Optional)

If you have existing data in Render's database that you want to migrate:

### Export from Render Database

```bash
# Connect to Render database
psql "$OLD_RENDER_DATABASE_URL"

# Export data
\copy requests TO 'requests_backup.csv' CSV HEADER;
```

### Import to Supabase

```bash
# Connect to Supabase database
psql "postgresql://postgres.hizcmicfsbirljnfaogr:[YOUR-PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres"

# Import data
\copy requests FROM 'requests_backup.csv' CSV HEADER;
```

## Supabase API Keys (JWT Tokens)

The JWT tokens you provided are for Supabase's REST API and Realtime features:

- **Public Key (anon)**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhpemNtaWNmc2JpcmxqbmZhb2dyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjExNDQ2MDcsImV4cCI6MjA3NjcyMDYwN30.l83wb0ccF4FhNr-t3GoofPLcXL0MqjhLME2XmGUsWmk`
- **Secret Key (service_role)**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhpemNtaWNmc2JpcmxqbmZhb2dyIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTE0NDYwNywiZXhwIjoyMDc2NzIwNjA3fQ.CBEWhlsxBUqfNTCYRMJjD3w_A_egg_a7vS3dYXRZjYk`

**Note**: These are NOT used for direct PostgreSQL connections. They're for Supabase's REST API and Realtime subscriptions. Your current setup uses direct PostgreSQL connections (psycopg), so you only need the database password.

## Benefits of Supabase

1. **Better Free Tier**: 500MB storage, unlimited API requests
2. **Superior Dashboard**: Table editor, SQL editor, query analyzer
3. **Real-time Capabilities**: Can add real-time subscriptions later
4. **Automatic Backups**: Daily backups included in free tier
5. **Better Performance**: Connection pooling built-in
6. **Global CDN**: Faster access from different regions

## Troubleshooting

### Connection Issues

If you can't connect to Supabase:

1. **Verify password**: Make sure you're using the correct database password
2. **Check connection string**: Ensure no typos in the URL
3. **Network access**: Supabase allows all IPs by default, no whitelist needed
4. **Use pooler**: The connection string uses `pooler.supabase.com` for connection pooling

### SSL/TLS Errors

Supabase requires SSL connections. If you get SSL errors, update your connection string:

```
postgresql://postgres.hizcmicfsbirljnfaogr:[YOUR-PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres?sslmode=require
```

### Performance Issues

If you experience slow queries:

1. Check **Database → Query Performance** in Supabase dashboard
2. Consider adding indexes for frequently queried columns
3. Use the connection pooler (default in the provided URL)

## Next Steps

After successful migration:

1. ✅ Test all API endpoints
2. ✅ Run worker to verify full workflow
3. ✅ Monitor database usage in Supabase dashboard
4. ✅ Set up automatic backups (included by default)
5. ✅ Consider adding indexes for better performance

## Support

- **Supabase Documentation**: https://supabase.com/docs
- **Supabase Community**: https://github.com/supabase/supabase/discussions
- **Database Connection Issues**: Check Supabase Settings → Database → Connection Info

---

**Your Supabase project is ready to use!** Just add your database password to the connection string and deploy.

