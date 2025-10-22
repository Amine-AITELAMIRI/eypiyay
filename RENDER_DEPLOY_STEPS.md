# 🚀 Render Deployment - Exact Steps

Follow these exact steps to deploy with Supabase REST API.

## Step 1: Create Database Table in Supabase (Do This First!)

1. **Open Supabase SQL Editor**:
   - Go to: https://app.supabase.com/project/hizcmicfsbirljnfaogr/sql
   - Click **"New Query"** button

2. **Copy the SQL Schema**:
   - Open the file `supabase_schema.sql` in this repository
   - Copy ALL the contents

3. **Run the SQL**:
   - Paste into the SQL editor
   - Click **"Run"** or press `Ctrl+Enter`
   - You should see: ✅ **"Database schema created successfully!"**

4. **Verify Table Created**:
   - Go to: https://app.supabase.com/project/hizcmicfsbirljnfaogr/editor
   - You should see a **"requests"** table with these columns:
     - id, prompt, status, response, error, worker_id
     - created_at, updated_at, webhook_url, webhook_delivered
     - prompt_mode, model_mode

## Step 2: Update Render Environment Variables

1. **Go to Render Dashboard**:
   - Open: https://dashboard.render.com
   - Find your service: **chatgpt-relay-api**
   - Click on it

2. **Go to Environment Tab**:
   - Click **"Environment"** in the left sidebar
   - You'll see the environment variables section

3. **Delete Old Variables** (if they exist):
   - Remove `DATABASE_URL` if it exists
   - We don't need it anymore!

4. **Add These Three Variables**:

   ### Variable 1: SUPABASE_URL
   - Click **"Add Environment Variable"**
   - **Key**: `SUPABASE_URL`
   - **Value**: `https://hizcmicfsbirljnfaogr.supabase.co`
   - Click **"Save"**

   ### Variable 2: SUPABASE_KEY
   - Click **"Add Environment Variable"**
   - **Key**: `SUPABASE_KEY`
   - **Value**: 
     ```
     eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhpemNtaWNmc2JpcmxqbmZhb2dyIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTE0NDYwNywiZXhwIjoyMDc2NzIwNjA3fQ.CBEWhlsxBUqfNTCYRMJjD3w_A_egg_a7vS3dYXRZjYk
     ```
   - Click **"Save"**

   ### Variable 3: API_KEY (if not already set)
   - Click **"Add Environment Variable"**
   - **Key**: `API_KEY`
   - **Value**: 
     ```
     72b0253ba06e73484e2b71370a503ce00183b59750e4be1dd5eb10896587954a
     ```
   - Click **"Save"**

5. **Final Environment Variables Should Look Like**:
   ```
   SUPABASE_URL  =  https://hizcmicfsbirljnfaogr.supabase.co
   SUPABASE_KEY  =  eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   API_KEY       =  72b0253ba06e73484e2b71370a503ce00183b59750e4be1dd5eb10896587954a
   RETENTION_HOURS = 24 (optional, set in render.yaml)
   ```

## Step 3: Deploy!

### Option A: Automatic Deploy (Recommended)
```bash
# Commit all changes
git add .
git commit -m "Migrate to Supabase REST API"
git push origin main
```

Render will automatically detect the push and deploy!

### Option B: Manual Deploy
1. Go to your Render dashboard
2. Click on your service
3. Click **"Manual Deploy"** → **"Deploy latest commit"**

## Step 4: Verify Deployment

### Watch the Logs:
1. In Render dashboard, click on **"Logs"** tab
2. Watch for these messages:
   ```
   INFO:     Started server process [XX]
   INFO:     Waiting for application startup.
   ✅ Connected to Supabase - 'requests' table exists
   INFO:     Application startup complete.
   ```

3. **If you see errors**, check:
   - ❌ "SUPABASE_KEY environment variable is required" → Add SUPABASE_KEY
   - ❌ "Table 'requests' does not exist" → Run SQL schema (Step 1)
   - ❌ "Row Level Security policy violation" → You're using anon key instead of service_role key

### Test the API:

```bash
# 1. Health check (should return {"status":"ok"})
curl https://chatgpt-relay-api.onrender.com/health

# 2. Database stats
curl "https://chatgpt-relay-api.onrender.com/admin/database/stats" \
  -H "X-API-Key: 72b0253ba06e73484e2b71370a503ce00183b59750e4be1dd5eb10896587954a"

# Should return:
# {
#   "status": "success",
#   "total_requests": 0,
#   "status_breakdown": {},
#   "oldest_request": null,
#   "newest_request": null
# }

# 3. Create a test request
curl -X POST "https://chatgpt-relay-api.onrender.com/requests" \
  -H "X-API-Key: 72b0253ba06e73484e2b71370a503ce00183b59750e4be1dd5eb10896587954a" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Test prompt from deployment"}'

# Should return a request object with id, status: "pending", etc.
```

### Check Supabase Dashboard:
1. Go to: https://app.supabase.com/project/hizcmicfsbirljnfaogr/editor
2. Click on **"requests"** table
3. You should see your test request!

## Step 5: Run the Worker

Once the API is deployed and working:

```bash
python -m worker.cdp_worker \
  https://chatgpt-relay-api.onrender.com \
  worker-1 \
  72b0253ba06e73484e2b71370a503ce00183b59750e4be1dd5eb10896587954a \
  chatgpt.com \
  --pick-first
```

## 🎉 Success Checklist

- [ ] SQL schema run in Supabase ✅
- [ ] Environment variables set in Render ✅
- [ ] Code deployed successfully ✅
- [ ] Health endpoint responds ✅
- [ ] Database stats endpoint works ✅
- [ ] Test request created ✅
- [ ] Request visible in Supabase ✅
- [ ] Worker can claim requests ✅

## 🐛 Troubleshooting

### "Application startup failed"
**Check**: Did you run the SQL schema in Supabase? (Step 1)

### "SUPABASE_KEY environment variable is required"
**Check**: Did you add SUPABASE_KEY in Render environment? (Step 2)

### "Tenant or user not found" (OLD ERROR - Should be gone!)
**This means**: You're still using the old PostgreSQL connection
**Solution**: Make sure you pushed the latest code and Render redeployed

### "Row Level Security policy violation"
**Check**: Make sure you're using the service_role key (starts with `eyJhbG...role":"service_role"...`)

### API works but no data in Supabase
**Check**: 
1. Supabase logs: https://app.supabase.com/project/hizcmicfsbirljnfaogr/logs
2. Render logs: Check for detailed error messages
3. Make sure table was created with correct schema

## 📞 Need Help?

1. **Check Render Logs**: Most errors show up here
2. **Check Supabase Logs**: https://app.supabase.com/project/hizcmicfsbirljnfaogr/logs
3. **Verify Environment**: Make sure all 3 variables are set correctly
4. **Test Locally**: Run `uvicorn server.main:app --reload` and test locally first

## 🎊 You're Done!

Your ChatGPT Relay API is now running on Render with Supabase REST API!

**No more password issues!** 
**No more connection errors!** 
**Just clean, modern REST API!** 🚀

