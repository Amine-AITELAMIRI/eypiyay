# Migration Guide: Model Mode Features

This guide helps you migrate to the enhanced ChatGPT Relay API with model mode selection and project-based URLs.

## 🆕 New Features Overview

### 1. Model Mode Selection
- **Auto Mode**: Default ChatGPT behavior (recommended for most use cases)
- **Thinking Mode**: Uses gpt-5-thinking for thorough, analytical responses
- **Instant Mode**: Uses gpt-5-instant for fast, concise responses

### 2. Project-Based URLs
- **Fresh Discussions**: Each request starts a new conversation thread
- **Model Isolation**: Different model modes use separate project contexts
- **Better Organization**: All API requests are grouped in a dedicated project
- **No Context Pollution**: Previous conversations don't interfere with new requests

## 📋 Migration Checklist

### For API Consumers

- [ ] **Update request payloads** to include `model_mode` field (optional)
- [ ] **Choose appropriate model modes** for different use cases
- [ ] **Test new model behaviors** in development environment
- [ ] **Update documentation** to reflect model mode options

### For Server Administrators

- [ ] **Deploy updated server** with model mode support
- [ ] **Update worker configuration** if needed
- [ ] **Monitor project URL navigation** in worker logs
- [ ] **Verify database schema** includes model_mode column

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
  "model_mode": "thinking"
}
```

**Migration Notes:**
- `model_mode` is **optional** - existing code will work without changes
- Valid values: `"auto"`, `"thinking"`, `"instant"`, or `null`/omitted for auto mode
- Webhook URL behavior remains unchanged

### Response Format

The response format now includes the model mode used:

```json
{
  "id": 123,
  "prompt": "What is machine learning?",
  "status": "completed",
  "response": "...",
  "model_mode": "thinking",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:05:00Z"
}
```

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

#### After (With Model Mode)
```python
import requests

def create_and_get_response(prompt, webhook_url=None, model_mode="auto"):
    # Create request with model mode
    payload = {
        "prompt": prompt,
        "model_mode": model_mode
    }
    if webhook_url:
        payload["webhook_url"] = webhook_url
    
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

# Usage examples
def analyze_data(data):
    return create_and_get_response(
        f"Analyze this data: {data}",
        model_mode="thinking"  # Use thinking model for analysis
    )

def quick_answer(question):
    return create_and_get_response(
        question,
        model_mode="instant"  # Use instant model for quick answers
    )
```

### JavaScript/Node.js Client Migration

#### Before
```javascript
async function createAndGetResponse(prompt, webhookUrl = null) {
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

#### After (With Model Mode)
```javascript
async function createAndGetResponse(prompt, webhookUrl = null, modelMode = 'auto') {
  const payload = {
    prompt: prompt,
    model_mode: modelMode
  };
  if (webhookUrl) payload.webhook_url = webhookUrl;
  
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
      return data.response;
    } else if (data.status === 'failed') {
      throw new Error(data.error);
    }
    
    await new Promise(resolve => setTimeout(resolve, 2000));
  }
}

// Usage examples
async function analyzeData(data) {
  return createAndGetResponse(
    `Analyze this data: ${data}`,
    null,
    'thinking'  // Use thinking model for analysis
  );
}

async function quickAnswer(question) {
  return createAndGetResponse(
    question,
    null,
    'instant'  // Use instant model for quick answers
  );
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
```

#### After (With Model Mode)
```bash
# Create request with thinking model
curl -X POST "https://your-api.com/requests" \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Explain quantum computing", "model_mode": "thinking"}'

# Create request with instant model
curl -X POST "https://your-api.com/requests" \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is 2+2?", "model_mode": "instant"}'

# Create request with auto model (default)
curl -X POST "https://your-api.com/requests" \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello world", "model_mode": "auto"}'
```

## 🚀 Deployment Migration

### Environment Variables

No new environment variables are required for model mode functionality. The existing configuration remains the same:

```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/dbname"
export API_KEY="your-secure-api-key"
```

### Database Migration

The database schema is automatically migrated when the server starts:

- **New column**: `model_mode` (TEXT, nullable)
- **Automatic migration**: Runs on server startup
- **No manual intervention required**

### Worker Configuration

The worker automatically handles model mode navigation. No configuration changes are needed, but you can monitor the logs for URL navigation:

```
INFO: Navigating to project URL with model: https://chatgpt.com/g/g-p-68d04e772ef881918e915068fbe126e4-api-auto/project?model=gpt-5-thinking
```

## 📊 Monitoring and Maintenance

### New Log Messages

Monitor your worker logs for these new messages:

```
INFO: Navigating to project URL with model: https://chatgpt.com/g/g-p-68d04e772ef881918e915068fbe126e4-api-auto/project?model=gpt-5-thinking
```

### Model Mode Usage Tracking

You can track which model modes are being used by querying the database:

```sql
SELECT model_mode, COUNT(*) as usage_count 
FROM requests 
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY model_mode;
```

## ⚠️ Breaking Changes

**None!** This is a fully backward-compatible update:

- ✅ All existing API endpoints work unchanged
- ✅ All existing request payloads are valid
- ✅ All existing response formats are preserved
- ✅ Database schema is automatically migrated
- ✅ Worker behavior unchanged for requests without model_mode

## 🎯 Best Practices

### Model Mode Selection

1. **Use "thinking" for complex analysis**:
   ```python
   response = requests.post("https://your-api.com/requests", 
     json={"prompt": "Analyze market trends", "model_mode": "thinking"})
   ```

2. **Use "instant" for quick responses**:
   ```python
   response = requests.post("https://your-api.com/requests", 
     json={"prompt": "What time is it?", "model_mode": "instant"})
   ```

3. **Use "auto" for general use**:
   ```python
   response = requests.post("https://your-api.com/requests", 
     json={"prompt": "Explain photosynthesis", "model_mode": "auto"})
   ```

### Project URL Benefits

1. **Fresh context for each request**: No interference from previous conversations
2. **Better organization**: All API requests grouped in dedicated project
3. **Model isolation**: Different models use separate contexts
4. **Improved reliability**: Consistent starting point for each request

## 🔧 Troubleshooting

### Common Issues

**Q: Model mode not working as expected**
A: Ensure you're passing valid values: `"auto"`, `"thinking"`, or `"instant"`. Check worker logs for URL navigation messages.

**Q: Worker not navigating to project URL**
A: Verify the worker is receiving the model_mode parameter and check for error messages in worker logs.

**Q: Fresh discussions not being created**
A: The worker automatically navigates to a fresh project URL for each request. Check worker logs for URL navigation messages.

**Q: Responses seem inconsistent**
A: Each request now starts fresh. This is expected behavior - previous context is intentionally cleared.

### Support

For issues or questions:
1. Check worker logs for URL navigation messages
2. Verify model_mode parameter is being passed correctly
3. Test with minimal examples using cURL
4. Monitor worker behavior during URL navigation

## 📈 Performance Impact

### Positive Impacts
- **Fresh context**: Each request gets clean starting point
- **Better responses**: Model-specific optimization
- **Improved organization**: Dedicated project for API requests
- **Reduced context pollution**: No interference between requests

### Considerations
- **Navigation overhead**: Worker navigates to project URL (adds ~3 seconds)
- **Fresh discussions**: Each request starts from scratch
- **Model-specific behavior**: Different models may have different response times

---

**Migration Status**: ✅ Ready for production use
**Backward Compatibility**: ✅ 100% compatible
**Recommended Action**: Add model_mode parameter to requests for better ChatGPT interactions