# Database Table Viewing Guide

This guide shows you multiple ways to view the contents of your ChatGPT Relay database tables (hosted on Supabase).

> **Note**: This project now uses Supabase for database hosting. See [SUPABASE_MIGRATION_GUIDE.md](SUPABASE_MIGRATION_GUIDE.md) for setup instructions.

## 🔍 **Method 1: New API Endpoints (Easiest)**

I've added new admin endpoints to view database content through your API:

### **View Database Records**
```bash
# View latest 10 records
curl "https://your-api.com/admin/database/requests?limit=10" \
  -H "X-API-Key: your-key"

# View all completed requests
curl "https://your-api.com/admin/database/requests?status=completed&limit=50" \
  -H "X-API-Key: your-key"

# View pending requests
curl "https://your-api.com/admin/database/requests?status=pending" \
  -H "X-API-Key: your-key"

# View failed requests
curl "https://your-api.com/admin/database/requests?status=failed" \
  -H "X-API-Key: your-key"
```

### **View Database Statistics**
```bash
# Get overview statistics
curl "https://your-api.com/admin/database/stats" \
  -H "X-API-Key: your-key"
```

**Example Response:**
```json
{
  "status": "success",
  "total_requests": 25,
  "status_breakdown": {
    "completed": 20,
    "pending": 2,
    "failed": 3
  },
  "oldest_request": "2024-01-15T10:30:00",
  "newest_request": "2024-01-15T15:45:00"
}
```

## 🗄️ **Method 2: Supabase Dashboard (Recommended)**

### **Using Supabase Studio**

1. Go to [Supabase Dashboard](https://app.supabase.com/project/hizcmicfsbirljnfaogr)
2. Navigate to **Table Editor** to view your `requests` table
3. Use **SQL Editor** to run custom queries
4. View **Database** → **Tables** for schema information

### **Using psql (PostgreSQL Command Line)**

#### **Connect to Database**
```bash
# Using Supabase connection string
psql "postgresql://postgres.hizcmicfsbirljnfaogr:[YOUR-PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres"

# Or using environment variable
psql $DATABASE_URL
```

#### **Basic Commands**
```sql
-- List all tables
\dt

-- Describe table structure
\d requests

-- View all records
SELECT * FROM requests;

-- View recent records (last 10)
SELECT * FROM requests ORDER BY created_at DESC LIMIT 10;

-- View only specific columns
SELECT id, prompt, status, created_at FROM requests;

-- View completed requests only
SELECT * FROM requests WHERE status = 'completed';

-- View requests with specific prompt mode
SELECT * FROM requests WHERE prompt_mode = 'search';

-- Count requests by status
SELECT status, COUNT(*) FROM requests GROUP BY status;

-- View requests from today
SELECT * FROM requests WHERE DATE(created_at) = CURRENT_DATE;

-- View requests with webhooks
SELECT * FROM requests WHERE webhook_url IS NOT NULL;

-- View failed requests with error messages
SELECT id, prompt, error, created_at FROM requests WHERE status = 'failed';

-- Exit psql
\q
```

### **Advanced Queries**

#### **Performance Monitoring**
```sql
-- Requests processed per hour
SELECT 
    DATE_TRUNC('hour', created_at) as hour,
    COUNT(*) as requests,
    COUNT(*) FILTER (WHERE status = 'completed') as completed,
    COUNT(*) FILTER (WHERE status = 'failed') as failed
FROM requests 
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY hour 
ORDER BY hour DESC;

-- Average response time (if you track completion times)
SELECT 
    AVG(EXTRACT(EPOCH FROM (updated_at - created_at))) as avg_seconds
FROM requests 
WHERE status = 'completed';
```

#### **Content Analysis**
```sql
-- Most common prompt patterns
SELECT 
    SUBSTRING(prompt FROM 1 FOR 50) as prompt_start,
    COUNT(*) as frequency
FROM requests 
WHERE status = 'completed'
GROUP BY prompt_start
ORDER BY frequency DESC
LIMIT 10;

-- Prompt mode usage
SELECT 
    prompt_mode,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
FROM requests 
GROUP BY prompt_mode
ORDER BY count DESC;
```

## 🖥️ **Method 3: GUI Database Tools**

### **pgAdmin (Recommended)**
1. Download and install [pgAdmin](https://www.pgadmin.org/)
2. Add your database connection:
   - Host: `your-database-host`
   - Port: `5432`
   - Database: `your-database-name`
   - Username/Password: Your credentials
3. Navigate to: `Databases` → `your_db` → `Schemas` → `public` → `Tables`
4. Right-click `requests` → `View/Edit Data` → `All Rows`

### **DBeaver (Free Alternative)**
1. Download [DBeaver](https://dbeaver.io/)
2. Create new PostgreSQL connection
3. Enter your database credentials
4. Navigate to `requests` table and view data

### **TablePlus (macOS)**
1. Download [TablePlus](https://tableplus.com/)
2. Create PostgreSQL connection
3. Browse `requests` table

## 🌐 **Method 4: Supabase Advanced Features**

Supabase provides additional tools beyond basic database access:

### **Database Performance Monitoring**
1. Go to [Supabase Dashboard](https://app.supabase.com/project/hizcmicfsbirljnfaogr)
2. Navigate to **Database** → **Query Performance**
3. View slow queries and optimize them

### **Real-time Subscriptions** (Future Enhancement)
```javascript
// Optional: Add real-time updates to your application
const { createClient } = require('@supabase/supabase-js')
const supabase = createClient('https://hizcmicfsbirljnfaogr.supabase.co', 'ANON_KEY')

// Listen to database changes
supabase
  .from('requests')
  .on('INSERT', payload => {
    console.log('New request:', payload.new)
  })
  .subscribe()
```

### **Database Backups**
- Automatic daily backups included in Supabase free tier
- Manual backups available in Settings → Database → Backups

## 📊 **Method 5: Create a Simple Web Interface**

You can create a simple HTML page to view your database:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Database Viewer</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .status-completed { color: green; }
        .status-failed { color: red; }
        .status-pending { color: orange; }
    </style>
</head>
<body>
    <h1>ChatGPT Relay Database</h1>
    <div id="stats"></div>
    <div id="requests"></div>

    <script>
        const API_KEY = 'your-api-key';
        const API_BASE = 'https://your-api.com';

        async function loadStats() {
            const response = await fetch(`${API_BASE}/admin/database/stats`, {
                headers: { 'X-API-Key': API_KEY }
            });
            const data = await response.json();
            
            document.getElementById('stats').innerHTML = `
                <h2>Statistics</h2>
                <p>Total Requests: ${data.total_requests}</p>
                <p>Status Breakdown: ${JSON.stringify(data.status_breakdown)}</p>
                <p>Oldest: ${data.oldest_request}</p>
                <p>Newest: ${data.newest_request}</p>
            `;
        }

        async function loadRequests() {
            const response = await fetch(`${API_BASE}/admin/database/requests?limit=20`, {
                headers: { 'X-API-Key': API_KEY }
            });
            const data = await response.json();
            
            const table = `
                <h2>Recent Requests</h2>
                <table>
                    <tr>
                        <th>ID</th>
                        <th>Prompt</th>
                        <th>Status</th>
                        <th>Mode</th>
                        <th>Created</th>
                    </tr>
                    ${data.records.map(record => `
                        <tr>
                            <td>${record.id}</td>
                            <td>${record.prompt.substring(0, 50)}...</td>
                            <td class="status-${record.status}">${record.status}</td>
                            <td>${record.prompt_mode || 'normal'}</td>
                            <td>${new Date(record.created_at).toLocaleString()}</td>
                        </tr>
                    `).join('')}
                </table>
            `;
            
            document.getElementById('requests').innerHTML = table;
        }

        // Load data on page load
        loadStats();
        loadRequests();
        
        // Refresh every 30 seconds
        setInterval(() => {
            loadStats();
            loadRequests();
        }, 30000);
    </script>
</body>
</html>
```

## 🔧 **Troubleshooting**

### **Common Issues**

**Q: Can't connect to database**
```bash
# Check if DATABASE_URL is set
echo $DATABASE_URL

# Test connection to Supabase
psql $DATABASE_URL -c "SELECT 1;"

# If connection fails, verify:
# 1. Your database password is correct
# 2. The connection string format is correct
# 3. SSL mode is enabled (Supabase requires SSL)
```

**Q: Permission denied**
- Ensure your database user has SELECT permissions
- Check if you're using the correct credentials

**Q: Table doesn't exist**
```sql
-- Check if table exists
SELECT table_name FROM information_schema.tables 
WHERE table_name = 'requests';

-- List all tables
\dt
```

**Q: API endpoints return 404**
- Ensure your server is running the latest version
- Check that the endpoints are properly deployed

### **Security Notes**

⚠️ **Important Security Considerations:**

1. **API Endpoints**: The new database viewing endpoints require API key authentication
2. **Production Use**: Consider disabling these endpoints in production or restricting access
3. **Sensitive Data**: Be careful when viewing prompts as they may contain sensitive information
4. **Rate Limiting**: Consider adding rate limiting to prevent abuse

### **Environment Variables**

Make sure these are set correctly:
```bash
# Required
export DATABASE_URL="postgresql://postgres.hizcmicfsbirljnfaogr:[YOUR-PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
export API_KEY="your-secure-api-key"

# Optional
export RETENTION_HOURS="24"
```

**Note**: Replace `[YOUR-PASSWORD]` with your Supabase database password from the dashboard.

## 📈 **Monitoring Best Practices**

1. **Regular Monitoring**: Check database stats regularly using Supabase Dashboard
2. **Cleanup Monitoring**: Watch cleanup logs for effectiveness
3. **Performance**: Use Supabase's Query Performance tool to monitor slow queries
4. **Storage**: Monitor database size in Supabase Settings → Database → Usage
5. **Backup**: Automatic daily backups are enabled by default in Supabase

## 🔗 **Quick Links**

- **Supabase Dashboard**: https://app.supabase.com/project/hizcmicfsbirljnfaogr
- **Table Editor**: https://app.supabase.com/project/hizcmicfsbirljnfaogr/editor
- **SQL Editor**: https://app.supabase.com/project/hizcmicfsbirljnfaogr/sql
- **Database Settings**: https://app.supabase.com/project/hizcmicfsbirljnfaogr/settings/database

---

**Choose the method that works best for your setup!** 

- ✨ **Easiest**: Supabase Dashboard (visual interface, no commands needed)
- 🚀 **Quick Check**: API endpoints (curl commands)
- 🔧 **Power User**: Direct psql access (full SQL control)
