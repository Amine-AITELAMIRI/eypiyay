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
  "model_mode": "string (optional)",
  "image_url": "string (optional)",
  "follow_up_chat_url": "string (optional)"
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
**Valid Values:** `"search"`, `"study"`, `"deep"`, or `null`/omitted

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

```json
{
  "prompt": "Conduct comprehensive research on quantum computing applications",
  "prompt_mode": "deep"
}
```
*Result: Types `/deep` + Enter, then "Conduct comprehensive research on quantum computing applications"*

**Note:** Deep research mode may take significantly longer (5-30 minutes) to complete as it performs thorough, comprehensive analysis.

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

### `follow_up_chat_url` (Optional)
**Type:** `string`  
**Description:** ChatGPT chat URL to continue an existing conversation instead of starting a new chat  
**Format:** Valid ChatGPT chat URL (e.g., `https://chatgpt.com/c/...`)

**How it works:**
1. When you create a request, the response includes a `chat_url` field with the ChatGPT conversation link
2. To continue that conversation, pass the `chat_url` back as `follow_up_chat_url` in your next request
3. The worker will navigate to that specific chat and add your new prompt there
4. Omit this field to start a fresh conversation

**Examples:**
```json
{
  "prompt": "What is quantum computing?",
}
```
*Initial request - creates a new chat*

**Response includes:**
```json
{
  "id": 123,
  "chat_url": "https://chatgpt.com/c/abc-123-def",
  ...
}
```

**Follow-up request:**
```json
{
  "prompt": "Can you explain quantum entanglement in more detail?",
  "follow_up_chat_url": "https://chatgpt.com/c/abc-123-def"
}
```
*Continues the same conversation - ChatGPT will have context from previous messages*

**Benefits:**
- Build complex conversations with context
- ChatGPT remembers previous messages
- Refine or expand on earlier responses
- Multi-turn conversations without losing context
- **Performance Optimized**: Worker skips page reload if already on the target chat (saves 3+ seconds)
- **Guaranteed Fresh Chats**: Omit `follow_up_chat_url` (or set to `null`) to always start a new conversation

## 📤 Response Fields

### Request Response Object
```json
{
  "id": 123,
  "prompt": "string",
  "status": "string",
  "response": "string|null",
  "sources": "array|null",
  "error": "string|null",
  "worker_id": "string|null",
  "webhook_url": "string|null",
  "webhook_delivered": "boolean",
  "prompt_mode": "string|null",
  "model_mode": "string|null",
  "image_url": "string|null",
  "chat_url": "string|null",
  "follow_up_chat_url": "string|null",
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
| `response` | `string\|null` | ChatGPT's response (JSON string when completed, clean content without source citations) |
| `sources` | `array\|null` | Array of source objects if ChatGPT provided sources (common in search mode) |
| `error` | `string\|null` | Error message if request failed |
| `worker_id` | `string\|null` | ID of worker processing the request |
| `webhook_url` | `string\|null` | Webhook URL if provided |
| `webhook_delivered` | `boolean` | Whether webhook was successfully delivered |
| `prompt_mode` | `string\|null` | Prompt mode used (`search`, `study`, or `null`) |
| `model_mode` | `string\|null` | Model mode used (`auto`, `thinking`, `instant`, or `null`) |
| `image_url` | `string\|null` | Image URL or base64 data if image was provided |
| `chat_url` | `string\|null` | ChatGPT conversation URL - use this for follow-up requests |
| `follow_up_chat_url` | `string\|null` | The chat URL that was used for this request (if it was a follow-up) |
| `created_at` | `string` | Request creation timestamp (ISO 8601) |
| `updated_at` | `string` | Last update timestamp (ISO 8601) |

### Sources Format

When ChatGPT provides sources (especially in search mode), they are parsed and returned separately:

```json
{
  "response": "{\"prompt\":\"...\",\"response\":\"Clean content here\",\"sources\":[...],\"timestamp\":\"...\",\"url\":\"...\"}",
  "sources": [
    {
      "number": 1,
      "url": "https://example.com/article",
      "title": "Article Title or Description"
    },
    {
      "number": 2,
      "url": "https://another-site.com/page",
      "title": "Page Title"
    }
  ]
}
```

**Benefits:**
- Clean response content without [1], [2] citations cluttering the text
- Structured source data for easy display
- Preserves all source information that ChatGPT provides

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

> **🔒 VPN Rotation**: When the worker is configured with `--vpn-rotate`, search mode requests automatically rotate the IP address using NordVPN to avoid getting blacklisted. See `worker/VPN_ROTATION_GUIDE.md` for setup instructions.

```json
{
  "prompt": "Find information about renewable energy trends",
  "prompt_mode": "search"
}
```

### `"deep"`
**Description:** Adds `/deep` command before prompt  
**Use Case:** Comprehensive research, in-depth analysis, complex investigations  
**Effect:** ChatGPT performs thorough, deep research with comprehensive analysis  
**Response Time:** ⚠️ **5-30 minutes** (significantly longer than other modes)

> **⏱️ Long-Running Requests**: Deep research mode is designed for comprehensive analysis and may take 5-30 minutes to complete. The system is configured to handle these long-running requests without timeouts:
> - Worker waits indefinitely for ChatGPT to complete the response
> - Asynchronous processing pattern (claim → process → complete) prevents API timeouts
> - No server-side timeouts will interrupt the request

```json
{
  "prompt": "Conduct comprehensive research on quantum computing applications",
  "prompt_mode": "deep"
}
```

**Best Practices for Deep Research:**
- Use specific, well-defined research questions
- Combine with `"model_mode": "thinking"` for best results
- Consider using webhooks for notification when complete
- Poll the API periodically or use webhooks instead of waiting synchronously

```json
{
  "prompt": "Analyze the historical development and future prospects of renewable energy technology",
  "prompt_mode": "deep",
  "model_mode": "thinking",
  "webhook_url": "https://your-server.com/webhook"
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

### Request with Search Mode (includes sources)
```python
import requests
import json
import time

# Create request with search mode
response = requests.post(
    "https://chatgpt-relay-api.onrender.com/requests",
    headers={"X-API-Key": "f2cd09510f1c537f53d0fcdae11528eef32de93a26e4237874447724be01e1d8"},
    json={
        "prompt": "What are the latest developments in quantum computing?",
        "prompt_mode": "search"  # Search mode often includes sources
    }
)

request_id = response.json()["id"]

# Poll for completion
while True:
    status_response = requests.get(
        f"https://chatgpt-relay-api.onrender.com/requests/{request_id}",
        headers={"X-API-Key": "f2cd09510f1c537f53d0fcdae11528eef32de93a26e4237874447724be01e1d8"}
    )
    
    data = status_response.json()
    
    if data["status"] == "completed":
        # Parse the response JSON
        response_data = json.loads(data["response"])
        
        print("Response:", response_data["response"])
        
        # Check if sources are provided
        if response_data.get("sources"):
            print("\nSources:")
            for source in response_data["sources"]:
                print(f"  [{source['number']}] {source['title']}")
                print(f"      {source['url']}")
        break
    elif data["status"] == "failed":
        print(f"Request failed: {data['error']}")
        break
    
    time.sleep(5)
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

### Follow-Up Conversation Pattern
```python
import requests
import json
import time

API_KEY = "f2cd09510f1c537f53d0fcdae11528eef32de93a26e4237874447724be01e1d8"
BASE_URL = "https://chatgpt-relay-api.onrender.com"

def create_request(prompt, follow_up_chat_url=None):
    """Create a request, optionally continuing an existing conversation"""
    payload = {"prompt": prompt}
    if follow_up_chat_url:
        payload["follow_up_chat_url"] = follow_up_chat_url
    
    response = requests.post(
        f"{BASE_URL}/requests",
        headers={"X-API-Key": API_KEY},
        json=payload
    )
    return response.json()

def wait_for_completion(request_id):
    """Poll until request is completed"""
    while True:
        response = requests.get(
            f"{BASE_URL}/requests/{request_id}",
            headers={"X-API-Key": API_KEY}
        )
        data = response.json()
        
        if data["status"] == "completed":
            result = json.loads(data["response"])
            return {
                "response": result["response"],
                "chat_url": data["chat_url"]
            }
        elif data["status"] == "failed":
            raise Exception(data["error"])
        
        time.sleep(5)

# Example: Multi-turn conversation
# Step 1: Initial question
print("Asking initial question...")
request1 = create_request("What is machine learning?")
result1 = wait_for_completion(request1["id"])
print(f"Response: {result1['response'][:100]}...")
print(f"Chat URL: {result1['chat_url']}")

# Step 2: Follow-up question in same conversation
print("\nAsking follow-up question...")
request2 = create_request(
    "Can you give me an example?",
    follow_up_chat_url=result1["chat_url"]
)
result2 = wait_for_completion(request2["id"])
print(f"Response: {result2['response'][:100]}...")

# Step 3: Another follow-up
print("\nAsking another follow-up...")
request3 = create_request(
    "What are the main challenges?",
    follow_up_chat_url=result2["chat_url"]
)
result3 = wait_for_completion(request3["id"])
print(f"Response: {result3['response'][:100]}...")
```

### Conversation Manager Class
```python
import requests
import json
import time

class ChatGPTConversation:
    """Helper class to manage multi-turn conversations"""
    
    def __init__(self, api_key, base_url="https://chatgpt-relay-api.onrender.com"):
        self.api_key = api_key
        self.base_url = base_url
        self.chat_url = None
        self.history = []
    
    def ask(self, prompt, **kwargs):
        """
        Send a prompt to ChatGPT.
        Automatically continues the conversation if chat_url exists.
        
        Args:
            prompt: The question/prompt to send
            **kwargs: Additional parameters (prompt_mode, model_mode, etc.)
        
        Returns:
            ChatGPT's response text
        """
        # Create request
        payload = {"prompt": prompt, **kwargs}
        if self.chat_url:
            payload["follow_up_chat_url"] = self.chat_url
        
        response = requests.post(
            f"{self.base_url}/requests",
            headers={"X-API-Key": self.api_key},
            json=payload
        )
        request_data = response.json()
        request_id = request_data["id"]
        
        # Wait for completion
        while True:
            response = requests.get(
                f"{self.base_url}/requests/{request_id}",
                headers={"X-API-Key": self.api_key}
            )
            data = response.json()
            
            if data["status"] == "completed":
                result = json.loads(data["response"])
                response_text = result["response"]
                
                # Update chat URL for next message
                self.chat_url = data["chat_url"]
                
                # Store in history
                self.history.append({
                    "prompt": prompt,
                    "response": response_text,
                    "request_id": request_id
                })
                
                return response_text
            
            elif data["status"] == "failed":
                raise Exception(data["error"])
            
            time.sleep(5)
    
    def start_new_conversation(self):
        """Reset to start a fresh conversation"""
        self.chat_url = None
        self.history = []

# Usage example
conversation = ChatGPTConversation(api_key="your-api-key")

# Multi-turn conversation
response1 = conversation.ask("Explain quantum computing")
print(response1)

response2 = conversation.ask("What are its practical applications?")
print(response2)

response3 = conversation.ask("What companies are leading in this field?")
print(response3)

# Start a new conversation
conversation.start_new_conversation()
response4 = conversation.ask("Tell me about artificial intelligence")
print(response4)
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
