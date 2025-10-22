# ChatGPT Relay API Usage Guide

This guide provides comprehensive documentation for using the ChatGPT Relay API, including all available fields, parameters, and best practices.

> **Note**: This API now uses Supabase for database storage. See [SUPABASE_MIGRATION_GUIDE.md](SUPABASE_MIGRATION_GUIDE.md) for database setup and [setup_supabase.md](setup_supabase.md) for quick start instructions.

## 📋 Table of Contents

- [Quick Reference](#quick-reference)
- [API Endpoints](#api-endpoints)
- [Request Fields](#request-fields)
- [Response Fields](#response-fields)
- [Model Modes](#model-modes)
- [Prompt Modes](#prompt-modes)
- [Webhook Integration](#webhook-integration)
- [Usage Examples](#usage-examples)
- [Error Handling](#error-handling)
- [Rate Limits](#rate-limits)
- [Best Practices](#best-practices)

## 🚀 Quick Reference

### Base URL
```
https://chatgpt-relay-api.onrender.com
```

### Authentication
```bash
X-API-Key: f2cd09510f1c537f53d0fcdae11528eef32de93a26e4237874447724be01e1d8
```

### Create Request
```bash
POST /requests
```

### Get Request Status
```bash
GET /requests/{id}
```

## 🔗 API Endpoints

### Create Request
**Endpoint:** `POST /requests`

**Description:** Submit a new prompt to ChatGPT for processing.

**Headers:**
```
X-API-Key: your-api-key
Content-Type: application/json
```

**Request Body:**
```json
{
  "prompt": "string (required)",
  "webhook_url": "string (optional)",
  "prompt_mode": "string (optional)",
  "model_mode": "string (optional)"
}
```

### Get Request Status
**Endpoint:** `GET /requests/{id}`

**Description:** Retrieve the status and response of a request.

**Headers:**
```
X-API-Key: your-api-key
```

**Query Parameters:**
- `delete_after_fetch` (optional): `true` to delete request after fetching

### Fetch and Delete
**Endpoint:** `POST /requests/{id}/fetch-and-delete`

**Description:** Retrieve response and immediately delete the request.

**Headers:**
```
X-API-Key: your-api-key
```

## 📝 Request Fields

### `prompt` (Required)
**Type:** `string`  
**Description:** The text prompt to send to ChatGPT  
**Min Length:** 1 character  
**Max Length:** No limit (ChatGPT's limits apply)

**Examples:**
```json
{
  "prompt": "Explain quantum computing in simple terms"
}
```

```json
{
  "prompt": "Write a Python function to calculate fibonacci numbers"
}
```

### `webhook_url` (Optional)
**Type:** `string` (URL)  
**Description:** URL to receive webhook notifications when request completes  
**Format:** Valid HTTP/HTTPS URL

**Examples:**
```json
{
  "prompt": "Analyze this data",
  "webhook_url": "https://your-server.com/webhook"
}
```

```json
{
  "prompt": "Generate a report",
  "webhook_url": "https://api.your-app.com/chatgpt-callback"
}
```

**Webhook Payload:**
```json
{
  "request_id": 123,
  "status": "completed",
  "response": "ChatGPT's response here",
  "prompt": "Original prompt",
  "model_mode": "thinking",
  "prompt_mode": "study"
}
```

### `prompt_mode` (Optional)
**Type:** `string`  
**Description:** Special prompt mode that adds commands before the user prompt  
**Valid Values:** `"search"`, `"study"`, or `null`/omitted

**Examples:**
```json
{
  "prompt": "What is machine learning?",
  "prompt_mode": "study"
}
```
*Result: Types `/stu` + Enter, then "What is machine learning?"*

```json
{
  "prompt": "Find information about climate change",
  "prompt_mode": "search"
}
```
*Result: Types `/sear` + Enter, then "Find information about climate change"*

### `model_mode` (Optional)
**Type:** `string`  
**Description:** Specifies which ChatGPT model to use  
**Valid Values:** `"auto"`, `"thinking"`, `"instant"`, or `null`/omitted

**Examples:**
```json
{
  "prompt": "Analyze market trends",
  "model_mode": "thinking"
}
```
*Uses gpt-5-thinking for thorough analysis*

```json
{
  "prompt": "What is 2+2?",
  "model_mode": "instant"
}
```
*Uses gpt-5-instant for quick responses*

### `image_url` (Optional)
**Type:** `string`  
**Description:** URL or base64-encoded image to send along with the prompt  
**Format:** Valid HTTP/HTTPS URL or base64 data URI

**Examples:**
```json
{
  "prompt": "What's in this image?",
  "image_url": "https://example.com/photo.jpg"
}
```
*Sends an image from a public URL*

```json
{
  "prompt": "Analyze this screenshot",
  "image_url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA..."
}
```
*Sends a base64-encoded image*

```json
{
  "prompt": "Describe the differences between these architectural styles",
  "image_url": "https://images.example.com/architecture.jpg",
  "model_mode": "thinking"
}
```
*Combines image analysis with detailed thinking mode*

## 📤 Response Fields

### Request Response Object
```json
{
  "id": 123,
  "prompt": "string",
  "status": "string",
  "response": "string|null",
  "error": "string|null",
  "worker_id": "string|null",
  "webhook_url": "string|null",
  "webhook_delivered": "boolean",
  "prompt_mode": "string|null",
  "model_mode": "string|null",
  "image_url": "string|null",
  "created_at": "string (ISO 8601)",
  "updated_at": "string (ISO 8601)"
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `id` | `integer` | Unique request identifier |
| `prompt` | `string` | Original prompt text |
| `status` | `string` | Request status: `pending`, `processing`, `completed`, `failed` |
| `response` | `string\|null` | ChatGPT's response (JSON string when completed) |
| `error` | `string\|null` | Error message if request failed |
| `worker_id` | `string\|null` | ID of worker processing the request |
| `webhook_url` | `string\|null` | Webhook URL if provided |
| `webhook_delivered` | `boolean` | Whether webhook was successfully delivered |
| `prompt_mode` | `string\|null` | Prompt mode used (`search`, `study`, or `null`) |
| `model_mode` | `string\|null` | Model mode used (`auto`, `thinking`, `instant`, or `null`) |
| `image_url` | `string\|null` | Image URL or base64 data if image was provided |
| `created_at` | `string` | Request creation timestamp (ISO 8601) |
| `updated_at` | `string` | Last update timestamp (ISO 8601) |

## 🤖 Model Modes

### `"auto"` (Default)
**Description:** Default ChatGPT behavior  
**Use Case:** General conversations, standard queries  
**Response Time:** Variable  
**Best For:** Most use cases

```json
{
  "prompt": "Explain photosynthesis",
  "model_mode": "auto"
}
```

### `"thinking"`
**Description:** Uses gpt-5-thinking for thorough analysis  
**Use Case:** Complex analysis, detailed explanations  
**Response Time:** Slower but more thorough  
**Best For:** Research, analysis, problem-solving

```json
{
  "prompt": "Analyze the pros and cons of renewable energy",
  "model_mode": "thinking"
}
```

### `"instant"`
**Description:** Uses gpt-5-instant for quick responses  
**Use Case:** Simple questions, quick answers  
**Response Time:** Faster but more concise  
**Best For:** Simple queries, quick facts

```json
{
  "prompt": "What is the capital of France?",
  "model_mode": "instant"
}
```

## 📚 Prompt Modes

### `"study"`
**Description:** Adds `/stu` command before prompt  
**Use Case:** Educational content, learning materials  
**Effect:** ChatGPT provides more educational, structured responses

```json
{
  "prompt": "Explain the water cycle",
  "prompt_mode": "study"
}
```

### `"search"`
**Description:** Adds `/sear` command before prompt  
**Use Case:** Research queries, information gathering  
**Effect:** ChatGPT provides more research-focused responses

```json
{
  "prompt": "Find information about renewable energy trends",
  "prompt_mode": "search"
}
```

## 🔗 Webhook Integration

### Setting Up Webhooks
1. **Create webhook endpoint** on your server
2. **Provide webhook URL** in request
3. **Handle webhook payload** when request completes

### Webhook Endpoint Example (Python/Flask)
```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    data = request.json
    
    request_id = data['request_id']
    status = data['status']
    response = data.get('response')
    prompt = data['prompt']
    model_mode = data.get('model_mode')
    
    if status == 'completed':
        # Process successful response
        chatgpt_response = json.loads(response)
        print(f"ChatGPT Response: {chatgpt_response['response']}")
    elif status == 'failed':
        # Handle error
        print(f"Request failed: {data.get('error')}")
    
    return jsonify({"status": "received"})
```

### Webhook Payload Structure
```json
{
  "request_id": 123,
  "status": "completed",
  "response": "{\"prompt\":\"...\",\"response\":\"...\",\"timestamp\":\"...\",\"url\":\"...\"}",
  "prompt": "Original prompt text",
  "model_mode": "thinking",
  "prompt_mode": "study",
  "webhook_url": "https://your-server.com/webhook",
  "webhook_delivered": true
}
```

## 💡 Usage Examples

### Basic Request
```python
import requests

response = requests.post(
    "https://chatgpt-relay-api.onrender.com/requests",
    headers={"X-API-Key": "f2cd09510f1c537f53d0fcdae11528eef32de93a26e4237874447724be01e1d8"},
    json={"prompt": "Hello, how are you?"}
)

request_id = response.json()["id"]
print(f"Request ID: {request_id}")
```

### Request with Model Mode
```python
import requests

response = requests.post(
    "https://chatgpt-relay-api.onrender.com/requests",
    headers={"X-API-Key": "f2cd09510f1c537f53d0fcdae11528eef32de93a26e4237874447724be01e1d8"},
    json={
        "prompt": "Analyze the stock market trends",
        "model_mode": "thinking"
    }
)
```

### Request with Prompt Mode
```python
import requests

response = requests.post(
    "https://chatgpt-relay-api.onrender.com/requests",
    headers={"X-API-Key": "f2cd09510f1c537f53d0fcdae11528eef32de93a26e4237874447724be01e1d8"},
    json={
        "prompt": "Explain machine learning algorithms",
        "prompt_mode": "study"
    }
)
```

### Request with Webhook
```python
import requests

response = requests.post(
    "https://chatgpt-relay-api.onrender.com/requests",
    headers={"X-API-Key": "f2cd09510f1c537f53d0fcdae11528eef32de93a26e4237874447724be01e1d8"},
    json={
        "prompt": "Generate a report on climate change",
        "webhook_url": "https://your-server.com/webhook",
        "model_mode": "thinking"
    }
)
```

### Request with Image (URL)
```python
import requests

response = requests.post(
    "https://chatgpt-relay-api.onrender.com/requests",
    headers={"X-API-Key": "f2cd09510f1c537f53d0fcdae11528eef32de93a26e4237874447724be01e1d8"},
    json={
        "prompt": "What objects are in this image?",
        "image_url": "https://example.com/photo.jpg"
    }
)

request_id = response.json()["id"]
print(f"Request ID: {request_id}")
```

### Request with Image (Base64)
```python
import requests
import base64

# Read and encode image
with open("screenshot.png", "rb") as image_file:
    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    image_data_url = f"data:image/png;base64,{encoded_string}"

response = requests.post(
    "https://chatgpt-relay-api.onrender.com/requests",
    headers={"X-API-Key": "f2cd09510f1c537f53d0fcdae11528eef32de93a26e4237874447724be01e1d8"},
    json={
        "prompt": "Analyze this screenshot and describe what you see",
        "image_url": image_data_url,
        "model_mode": "thinking"
    }
)

request_id = response.json()["id"]
print(f"Request ID: {request_id}")
```

### Request with Multiple Parameters
```python
import requests

response = requests.post(
    "https://chatgpt-relay-api.onrender.com/requests",
    headers={"X-API-Key": "f2cd09510f1c537f53d0fcdae11528eef32de93a26e4237874447724be01e1d8"},
    json={
        "prompt": "Research the architectural style shown in this image",
        "image_url": "https://example.com/building.jpg",
        "prompt_mode": "search",
        "model_mode": "thinking",
        "webhook_url": "https://your-server.com/webhook"
    }
)

request_id = response.json()["id"]
print(f"Request ID: {request_id}")
```

### Polling for Response
```python
import requests
import time
import json

def wait_for_response(request_id):
    while True:
        response = requests.get(
            f"https://chatgpt-relay-api.onrender.com/requests/{request_id}",
            headers={"X-API-Key": "f2cd09510f1c537f53d0fcdae11528eef32de93a26e4237874447724be01e1d8"}
        )
        
        data = response.json()
        
        if data["status"] == "completed":
            chatgpt_response = json.loads(data["response"])
            return chatgpt_response["response"]
        elif data["status"] == "failed":
            raise Exception(data["error"])
        
        time.sleep(5)  # Wait 5 seconds before checking again

# Usage
request_id = 123
response_text = wait_for_response(request_id)
print(response_text)
```

### Fetch and Delete Pattern
```python
import requests

def get_response_and_cleanup(request_id):
    response = requests.post(
        f"https://chatgpt-relay-api.onrender.com/requests/{request_id}/fetch-and-delete",
        headers={"X-API-Key": "f2cd09510f1c537f53d0fcdae11528eef32de93a26e4237874447724be01e1d8"}
    )
    
    data = response.json()
    chatgpt_response = json.loads(data["response"])
    return chatgpt_response["response"]
```

## ⚠️ Error Handling

### Common Error Responses

#### 401 Unauthorized
```json
{
  "detail": "Invalid API key"
}
```
**Solution:** Check your API key

#### 404 Not Found
```json
{
  "detail": "Request 123 not found"
}
```
**Solution:** Verify request ID exists

#### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "prompt"],
      "msg": "ensure this value has at least 1 characters",
      "type": "value_error.any_str.min_length"
    }
  ]
}
```
**Solution:** Ensure prompt is not empty

### Request Status Values

| Status | Description | Action Required |
|--------|-------------|-----------------|
| `pending` | Request queued, waiting for worker | Wait and poll again |
| `processing` | Worker is processing the request | Wait and poll again |
| `completed` | Request completed successfully | Parse response |
| `failed` | Request failed | Check error message |

## 🚦 Rate Limits

### Current Limits
- **No explicit rate limits** on API requests
- **Worker capacity** determines processing speed
- **ChatGPT limits** apply to underlying model usage

### Best Practices
- **Poll every 5-10 seconds** for status updates
- **Use webhooks** for faster response handling
- **Implement retry logic** for failed requests
- **Batch requests** when possible

## 🎯 Best Practices

### Request Design
1. **Be specific** in your prompts
2. **Use appropriate model modes** for your use case
3. **Include context** when needed
4. **Test prompts** before production use

### Response Handling
1. **Always check status** before processing response
2. **Handle errors gracefully**
3. **Use fetch-and-delete** to prevent database bloat
4. **Implement timeouts** for long-running requests

### Performance Optimization
1. **Use webhooks** instead of polling when possible
2. **Choose appropriate model modes** for response time needs
3. **Implement caching** for repeated requests
4. **Monitor request patterns** and optimize accordingly

### Security
1. **Keep API keys secure**
2. **Use HTTPS** for webhook URLs
3. **Validate webhook payloads**
4. **Implement proper authentication** for webhook endpoints

## 📞 Support

### Getting Help
1. **Check this guide** for common issues
2. **Review error messages** carefully
3. **Test with minimal examples** using cURL
4. **Check worker logs** for processing issues

### Common Issues
- **Worker not responding**: Check if worker is running
- **Slow responses**: Consider using `instant` model mode
- **Webhook not received**: Verify webhook URL is accessible
- **Response parsing errors**: Check JSON format of responses

---

**API Version:** 1.0  
**Last Updated:** 2024  
**Status:** ✅ Production Ready
