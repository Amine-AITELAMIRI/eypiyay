# Migration Guide: Enhanced API Features

This guide helps you migrate from the original ChatGPT Relay API to the enhanced version with new prompt modes and database cleanup features.

## 🆕 New Features Overview

### 1. Special Prompt Modes
- **Search Mode**: Automatically types `/sear` + Enter before user prompts
- **Study Mode**: Automatically types `/stu` + Enter before user prompts
- **Normal Mode**: No special commands (existing behavior)

### 2. Database Cleanup Features
- **Fetch-and-Delete**: Retrieve responses and automatically remove them from database
- **Automatic Background Cleanup**: Removes old completed requests hourly
- **Manual Cleanup**: Admin endpoint for maintenance

## 📋 Migration Checklist

### For API Consumers

- [ ] **Update request payloads** to include `prompt_mode` field (optional)
- [ ] **Choose cleanup strategy** for response handling
- [ ] **Update response handling** to work with fetch-and-delete patterns
- [ ] **Test new endpoints** in development environment

### For Server Administrators

- [ ] **Set environment variables** for retention period
- [ ] **Update deployment configuration** with new environment variables
- [ ] **Monitor automatic cleanup** logs
- [ ] **Configure retention period** based on your needs

## 🔄 API Changes

### Request Creation (POST /requests)

#### Before (Original API)
```json
{
  "prompt": "What is machine learning?",
  "webhook_url": "https://your-webhook.com/endpoint"
}
```

#### After (Enhanced API)
```json
{
  "prompt": "What is machine learning?",
  "webhook_url": "https://your-webhook.com/endpoint",
  "prompt_mode": "study"
}
```

**Migration Notes:**
- `prompt_mode` is **optional** - existing code will work without changes
- Valid values: `"search"`, `"study"`, or `null`/omitted for normal mode
- Webhook URL behavior remains unchanged

### Response Retrieval

#### Option 1: Traditional Fetch (No Changes Required)
```bash
GET /requests/{id}
```
- **Behavior**: Unchanged - fetches response without deleting
- **Compatibility**: 100% backward compatible
- **Use Case**: When you need to fetch the same response multiple times

#### Option 2: Fetch-and-Delete (New)
```bash
# Method 1: Query parameter
GET /requests/{id}?delete_after_fetch=true

# Method 2: Dedicated endpoint
POST /requests/{id}/fetch-and-delete
```

**Migration Notes:**
- **New endpoints** - add these to your client code
- **One-time use** - response is deleted after fetch
- **Recommended** for most use cases to prevent database bloat

## 🛠 Code Migration Examples

### Python Client Migration

#### Before
```python
import requests

def create_and_get_response(prompt, webhook_url=None):
    # Create request
    response = requests.post(
        "https://your-api.com/requests",
        headers={"X-API-Key": "your-key"},
        json={"prompt": prompt, "webhook_url": webhook_url}
    )
    request_id = response.json()["id"]
    
    # Poll for completion
    while True:
        result = requests.get(
            f"https://your-api.com/requests/{request_id}",
            headers={"X-API-Key": "your-key"}
        )
        data = result.json()
        if data["status"] == "completed":
            return data["response"]
        elif data["status"] == "failed":
            raise Exception(data["error"])
        time.sleep(2)
```

#### After (Minimal Changes)
```python
import requests

def create_and_get_response(prompt, webhook_url=None, prompt_mode=None):
    # Create request with optional prompt_mode
    payload = {"prompt": prompt}
    if webhook_url:
        payload["webhook_url"] = webhook_url
    if prompt_mode:  # New: Add prompt mode
        payload["prompt_mode"] = prompt_mode
    
    response = requests.post(
        "https://your-api.com/requests",
        headers={"X-API-Key": "your-key"},
        json=payload
    )
    request_id = response.json()["id"]
    
    # Poll for completion (unchanged)
    while True:
        result = requests.get(
            f"https://your-api.com/requests/{request_id}",
            headers={"X-API-Key": "your-key"}
        )
        data = result.json()
        if data["status"] == "completed":
            return data["response"]
        elif data["status"] == "failed":
            raise Exception(data["error"])
        time.sleep(2)
```

#### After (With Cleanup)
```python
import requests

def create_and_get_response_with_cleanup(prompt, webhook_url=None, prompt_mode=None):
    # Create request (same as above)
    payload = {"prompt": prompt}
    if webhook_url:
        payload["webhook_url"] = webhook_url
    if prompt_mode:
        payload["prompt_mode"] = prompt_mode
    
    response = requests.post(
        "https://your-api.com/requests",
        headers={"X-API-Key": "your-key"},
        json=payload
    )
    request_id = response.json()["id"]
    
    # Poll for completion
    while True:
        result = requests.get(
            f"https://your-api.com/requests/{request_id}",
            headers={"X-API-Key": "your-key"}
        )
        data = result.json()
        if data["status"] == "completed":
            # New: Fetch and delete in one operation
            fetch_response = requests.post(
                f"https://your-api.com/requests/{request_id}/fetch-and-delete",
                headers={"X-API-Key": "your-key"}
            )
            return fetch_response.json()["response"]
        elif data["status"] == "failed":
            raise Exception(data["error"])
        time.sleep(2)
```

### JavaScript/Node.js Client Migration

#### Before
```javascript
async function createAndGetResponse(prompt, webhookUrl = null) {
  // Create request
  const createResponse = await fetch('https://your-api.com/requests', {
    method: 'POST',
    headers: {
      'X-API-Key': 'your-key',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      prompt: prompt,
      webhook_url: webhookUrl
    })
  });
  
  const { id } = await createResponse.json();
  
  // Poll for completion
  while (true) {
    const result = await fetch(`https://your-api.com/requests/${id}`, {
      headers: { 'X-API-Key': 'your-key' }
    });
    
    const data = await result.json();
    if (data.status === 'completed') {
      return data.response;
    } else if (data.status === 'failed') {
      throw new Error(data.error);
    }
    
    await new Promise(resolve => setTimeout(resolve, 2000));
  }
}
```

#### After (Enhanced)
```javascript
async function createAndGetResponse(prompt, webhookUrl = null, promptMode = null) {
  // Create request with optional prompt_mode
  const payload = { prompt: prompt };
  if (webhookUrl) payload.webhook_url = webhookUrl;
  if (promptMode) payload.prompt_mode = promptMode;  // New
  
  const createResponse = await fetch('https://your-api.com/requests', {
    method: 'POST',
    headers: {
      'X-API-Key': 'your-key',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload)
  });
  
  const { id } = await createResponse.json();
  
  // Poll for completion (unchanged)
  while (true) {
    const result = await fetch(`https://your-api.com/requests/${id}`, {
      headers: { 'X-API-Key': 'your-key' }
    });
    
    const data = await result.json();
    if (data.status === 'completed') {
      // New: Fetch and delete in one operation
      const fetchResponse = await fetch(`https://your-api.com/requests/${id}/fetch-and-delete`, {
        method: 'POST',
        headers: { 'X-API-Key': 'your-key' }
      });
      
      const fetchData = await fetchResponse.json();
      return fetchData.response;
    } else if (data.status === 'failed') {
      throw new Error(data.error);
    }
    
    await new Promise(resolve => setTimeout(resolve, 2000));
  }
}
```

### cURL Examples

#### Before
```bash
# Create request
curl -X POST "https://your-api.com/requests" \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Explain quantum computing"}'

# Get response
curl "https://your-api.com/requests/123" \
  -H "X-API-Key: your-key"
```

#### After (With Prompt Mode)
```bash
# Create request with study mode
curl -X POST "https://your-api.com/requests" \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Explain quantum computing", "prompt_mode": "study"}'

# Get response and delete (recommended)
curl -X POST "https://your-api.com/requests/123/fetch-and-delete" \
  -H "X-API-Key: your-key"
```

## 🚀 Deployment Migration

### Environment Variables

#### New Environment Variables
```bash
# Optional: Set retention period for automatic cleanup
export RETENTION_HOURS=24  # Default: 24 hours
```

#### Updated Deployment Commands

**Local Development:**
```bash
# Set environment variables
export DATABASE_URL="postgresql://user:password@localhost:5432/dbname"
export API_KEY="your-secure-api-key"
export RETENTION_HOURS="24"  # New: Optional retention period

# Run the server
uvicorn server.main:app --host 0.0.0.0 --port 8000
```

**Render Deployment:**
1. Add `RETENTION_HOURS` environment variable in Render dashboard
2. Set value (e.g., `24`, `48`, `168` for 1 week)
3. Redeploy your application

### Database Migration

The database schema is automatically migrated when the server starts:

- **New column**: `prompt_mode` (TEXT, nullable)
- **Automatic migration**: Runs on server startup
- **No manual intervention required**

## 📊 Monitoring and Maintenance

### New Log Messages

Monitor your server logs for these new messages:

```
Started periodic cleanup task (retention: 24h)
Cleaned up 5 old requests (retention: 24h)
```

### Manual Cleanup

```bash
# Trigger manual cleanup
curl -X POST "https://your-api.com/admin/cleanup" \
  -H "X-API-Key: your-key"

# Cleanup with custom retention
curl -X POST "https://your-api.com/admin/cleanup?retention_hours=12" \
  -H "X-API-Key: your-key"
```

## ⚠️ Breaking Changes

**None!** This is a fully backward-compatible update:

- ✅ All existing API endpoints work unchanged
- ✅ All existing request payloads are valid
- ✅ All existing response formats are preserved
- ✅ Database schema is automatically migrated

## 🎯 Best Practices

### For New Implementations

1. **Use prompt modes** for better ChatGPT interactions:
   - `"search"` for research queries
   - `"study"` for educational content
   - `null` for general conversation

2. **Use fetch-and-delete** to prevent database bloat:
   ```bash
   POST /requests/{id}/fetch-and-delete
   ```

3. **Set appropriate retention period**:
   - Short retention (6-12 hours) for high-volume applications
   - Longer retention (24-48 hours) for debugging/audit needs

### For Existing Applications

1. **Gradual migration**: Add `prompt_mode` support incrementally
2. **Test fetch-and-delete**: Ensure your application handles one-time responses
3. **Monitor cleanup**: Watch logs for automatic cleanup activity
4. **Adjust retention**: Set `RETENTION_HOURS` based on your needs

## 🔧 Troubleshooting

### Common Issues

**Q: My existing code stopped working after update**
A: Check if you're using any hardcoded response handling that expects responses to persist. Consider switching to fetch-and-delete pattern.

**Q: Responses are being deleted too quickly**
A: Increase `RETENTION_HOURS` environment variable or avoid using fetch-and-delete endpoints.

**Q: Database is still growing despite cleanup**
A: Check that `RETENTION_HOURS` is set appropriately and monitor cleanup logs.

**Q: Prompt modes not working**
A: Ensure you're passing valid values: `"search"`, `"study"`, or `null`/omitted.

### Support

For issues or questions:
1. Check server logs for error messages
2. Verify environment variables are set correctly
3. Test with minimal examples using cURL
4. Review this migration guide for implementation patterns

## 📈 Performance Impact

### Positive Impacts
- **Reduced database size** through automatic cleanup
- **Better ChatGPT responses** with prompt modes
- **Improved storage efficiency** with fetch-and-delete

### Considerations
- **One-time responses**: Plan for responses that can only be fetched once
- **Background processing**: Cleanup runs hourly (minimal CPU impact)
- **Network efficiency**: Fetch-and-delete reduces total requests

---

**Migration Status**: ✅ Ready for production use
**Backward Compatibility**: ✅ 100% compatible
**Recommended Action**: Update client code to use new features for better performance and functionality
