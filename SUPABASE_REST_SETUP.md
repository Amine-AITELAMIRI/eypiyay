# ✨ Supabase REST API Setup (Modern Approach!)

This guide shows you how to set up your ChatGPT Relay API using Supabase's REST API instead of direct PostgreSQL connections. **This is much simpler and more reliable!**

## 🎯 Why REST API Instead of PostgreSQL?

- ✅ **No password needed** - Uses JWT tokens
- ✅ **No connection errors** - More reliable than direct database connections
- ✅ **Modern & Fast** - Built on REST principles
- ✅ **Real-time capable** - Can add subscriptions later
- ✅ **Better security** - Row Level Security built-in

## 🚀 Quick Setup (3 Steps!)

### Step 1: Create Database Table

1. Go to **Supabase SQL Editor**: https://app.supabase.com/project/hizcmicfsbirljnfaogr/sql

2. Click **"New Query"**

3. Copy and paste the contents of `supabase_schema.sql` 

4. Click **"Run"** or press `Ctrl+Enter`

5. You should see: ✅ "Database schema created successfully!"

### Step 2: Update Render Environment Variables

Go to your Render dashboard and set these environment variables:

1. **SUPABASE_URL**
   ```
   https://hizcmicfsbirljnfaogr.supabase.co
   ```

2. **SUPABASE_KEY** (Your service_role secret key)
   ```
   eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhpemNtaWNmc2JpcmxqbmZhb2dyIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTE0NDYwNywiZXhwIjoyMDc2NzIwNjA3fQ.CBEWhlsxBUqfNTCYRMJjD3w_A_egg_a7vS3dYXRZjYk
   ```

3. **API_KEY** (Your ChatGPT Relay API key)
   ```
   72b0253ba06e73484e2b71370a503ce00183b59750e4be1dd5eb10896587954a
   ```

4. **RETENTION_HOURS** (Optional, already set in render.yaml)
   ```
   24
   ```

### Step 3: Deploy!

That's it! Render will automatically deploy when you push to GitHub, or you can manually trigger a deploy.

## 🧪 Testing Locally

```bash
# Copy the environment file
cp env.example .env

# The file already has the correct Supabase credentials!

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn server.main:app --reload
```

Test it:
```bash
# Health check
curl http://localhost:8000/health

# Expected: {"status":"ok"}
```

## ✅ Verification Checklist

After deployment, verify everything works:

```bash
# 1. Health check
curl https://chatgpt-relay-api.onrender.com/health

# 2. Database stats
curl "https://chatgpt-relay-api.onrender.com/admin/database/stats" \
  -H "X-API-Key: 72b0253ba06e73484e2b71370a503ce00183b59750e4be1dd5eb10896587954a"

# 3. Create test request
curl -X POST "https://chatgpt-relay-api.onrender.com/requests" \
  -H "X-API-Key: 72b0253ba06e73484e2b71370a503ce00183b59750e4be1dd5eb10896587954a" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Test prompt"}'

# 4. Check Supabase dashboard
# Go to: https://app.supabase.com/project/hizcmicfsbirljnfaogr/editor
# You should see your test request in the requests table!
```

## 🎉 What Changed?

### New Files:
- ✨ `server/database_supabase.py` - New Supabase REST API implementation
- 📄 `supabase_schema.sql` - Database schema for Supabase
- 📚 `SUPABASE_REST_SETUP.md` - This guide!

### Updated Files:
- ✅ `requirements.txt` - Added `supabase==2.10.0` package
- ✅ `server/main.py` - Now uses `database_supabase` instead of `database`
- ✅ `render.yaml` - Updated to use `SUPABASE_URL` and `SUPABASE_KEY`
- ✅ `env.example` - Updated with Supabase credentials

### What Stayed The Same:
- ✅ All API endpoints unchanged
- ✅ Worker code unchanged
- ✅ Database schema identical
- ✅ All functionality works exactly the same

## 🔐 Security Notes

**Service Role Key (secret)**:
- This key bypasses Row Level Security
- Keep it secret - only use in server-side code
- Never expose it to the client/frontend
- It's already configured correctly in your setup

**Anon Key (public)**:
- This key is for client-side use (not needed for this project)
- Has Row Level Security restrictions
- Safe to expose in frontend code

## 🆚 REST API vs PostgreSQL

| Feature | REST API ✨ | PostgreSQL |
|---------|-------------|------------|
| Setup | Simple - just JWT tokens | Complex - need password |
| Connection | Always stable | Can have DNS/network issues |
| Security | Built-in RLS | Manual configuration |
| Real-time | Native support | Requires additional setup |
| Debugging | Easy - view in dashboard | Requires SQL knowledge |
| Scaling | Automatic | Manual tuning |

## 📊 Monitoring

### Supabase Dashboard
- **Table Editor**: https://app.supabase.com/project/hizcmicfsbirljnfaogr/editor
- **SQL Editor**: https://app.supabase.com/project/hizcmicfsbirljnfaogr/sql
- **API Logs**: https://app.supabase.com/project/hizcmicfsbirljnfaogr/logs/edge-logs

### API Stats
```bash
curl "https://chatgpt-relay-api.onrender.com/admin/database/stats" \
  -H "X-API-Key: YOUR_API_KEY"
```

### Web GUI
Visit: https://chatgpt-relay-api.onrender.com/database-viewer

## 🐛 Troubleshooting

### Error: "SUPABASE_KEY environment variable is required"
**Solution**: Make sure you set `SUPABASE_KEY` in Render's environment variables.

### Error: "Table 'requests' does not exist"
**Solution**: Run the SQL schema in Supabase SQL Editor (see Step 1).

### Error: "Row Level Security policy violation"
**Solution**: Make sure you're using the `service_role` key (secret), not the `anon` key.

### API responds but no data in Supabase
**Solution**: Check API logs in Render dashboard for detailed error messages.

## 🎓 Next Steps

1. ✅ Deploy and test the API
2. ✅ Run the worker to process requests
3. ✅ Monitor via Supabase dashboard
4. 🔮 Optional: Add real-time subscriptions for live updates
5. 🔮 Optional: Add user authentication with Supabase Auth

## 📚 Resources

- **Supabase Docs**: https://supabase.com/docs
- **Supabase Python Client**: https://github.com/supabase-community/supabase-py
- **Your Project Dashboard**: https://app.supabase.com/project/hizcmicfsbirljnfaogr

---

**You're all set!** 🚀 The REST API approach is much simpler and more reliable than direct PostgreSQL connections.

