# ChatGPT Relay API Integration Guide

This guide shows you how to integrate the ChatGPT Relay API into your projects to get AI-powered responses from ChatGPT.

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [API Reference](#api-reference)
- [Python Integration](#python-integration)
- [JavaScript/Node.js Integration](#javascriptnodejs-integration)
- [Webhook Integration](#webhook-integration)
- [Command Line Usage](#command-line-usage)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)
- [Examples](#examples)

## 🚀 Quick Start

### Prerequisites

1. **API Access**: Your ChatGPT Relay API deployed at `https://chatgpt-relay-api.onrender.com`
2. **API Key**: `f2cd09510f1c537f53d0fcdae11528eef32de93a26e4237874447724be01e1d8`
3. **Worker Running**: Chrome worker must be running locally to process requests

### ⚠️ Important: Webhooks are Optional!

**You can use this API from anywhere** - local scripts, Jupyter notebooks, command line, etc. The `webhook_url` field is completely optional:

- **Without webhook**: Use polling (check status every few seconds)
- **With webhook**: Get instant notifications when done (requires a server)

Both methods work perfectly fine!

### Start the Worker

```bash
# Terminal 1: Start Chrome with remote debugging
chrome --remote-debugging-port=9222 --remote-allow-origins=http://localhost:9222 --user-data-dir="YOUR_PROFILE_DIR"

# Terminal 2: Start the worker
python -m worker.cdp_worker https://chatgpt-relay-api.onrender.com worker-1 f2cd09510f1c537f53d0fcdae11528eef32de93a26e4237874447724be01e1d8 chatgpt.com --pick-first
```

### Basic Usage (No Webhook Required)

```python
import requests
import time

# Submit a request (webhook_url is optional - you can omit it)
response = requests.post(
    "https://chatgpt-relay-api.onrender.com/requests",
    headers={"X-API-Key": "f2cd09510f1c537f53d0fcdae11528eef32de93a26e4237874447724be01e1d8"},
    json={"prompt": "Write a Python function to calculate fibonacci numbers"}
)

request_id = response.json()["id"]
print(f"Request submitted: {request_id}")

# Poll for completion (this works from anywhere - local scripts, notebooks, etc.)
while True:
    status_response = requests.get(
        f"https://chatgpt-relay-api.onrender.com/requests/{request_id}",
        headers={"X-API-Key": "f2cd09510f1c537f53d0fcdae11528eef32de93a26e4237874447724be01e1d8"}
    )
    
    data = status_response.json()
    if data["status"] == "completed":
        import json
        chatgpt_response = json.loads(data["response"])
        print(f"ChatGPT Response: {chatgpt_response['response']}")
        break
    elif data["status"] == "failed":
        print(f"Error: {data['error']}")
        break
    
    time.sleep(5)  # Wait 5 seconds
```

### With Webhook (Optional Enhancement)

```python
# If you have a server, you can use webhooks for faster responses
response = requests.post(
    "https://chatgpt-relay-api.onrender.com/requests",
    headers={"X-API-Key": "f2cd09510f1c537f53d0fcdae11528eef32de93a26e4237874447724be01e1d8"},
    json={
        "prompt": "Write a Python function to calculate fibonacci numbers",
        "webhook_url": "https://your-server.com/webhook"  # Optional!
    }
)

# With webhook, you get notified immediately when done
# No need to poll - just wait for the webhook notification
```

### Simple Local Script Example

```python
#!/usr/bin/env python3
# Save this as ask_chatgpt.py and run: python ask_chatgpt.py "Your question"

import requests
import time
import sys

def ask_chatgpt(question):
    # Submit request (no webhook needed)
    response = requests.post(
        "https://chatgpt-relay-api.onrender.com/requests",
        headers={"X-API-Key": "f2cd09510f1c537f53d0fcdae11528eef32de93a26e4237874447724be01e1d8"},
        json={"prompt": question}
    )
    
    request_id = response.json()["id"]
    print(f"Question submitted: {question}")
    print(f"Request ID: {request_id}")
    print("Waiting for response...")
    
    # Poll for completion
    while True:
        status_response = requests.get(
            f"https://chatgpt-relay-api.onrender.com/requests/{request_id}",
            headers={"X-API-Key": "f2cd09510f1c537f53d0fcdae11528eef32de93a26e4237874447724be01e1d8"}
        )
        
        data = status_response.json()
        if data["status"] == "completed":
            import json
            chatgpt_response = json.loads(data["response"])
            print(f"\nChatGPT Response:\n{chatgpt_response['response']}")
            break
        elif data["status"] == "failed":
            print(f"Error: {data['error']}")
            break
        
        time.sleep(5)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python ask_chatgpt.py 'Your question here'")
        sys.exit(1)
    
    ask_chatgpt(sys.argv[1])
```

**Usage:**
```bash
python ask_chatgpt.py "Write a Python function to calculate prime numbers"
```

## 📚 API Reference

### Base URL
```
https://chatgpt-relay-api.onrender.com
```

### Authentication
All requests require the `X-API-Key` header:
```
X-API-Key: f2cd09510f1c537f53d0fcdae11528eef32de93a26e4237874447724be01e1d8
```

### Endpoints

#### Submit Request
```http
POST /requests
Content-Type: application/json
X-API-Key: YOUR_API_KEY

{
  "prompt": "Your question here",
  "webhook_url": "https://your-app.com/webhook"  // Optional
}
```

**Response:**
```json
{
  "id": 123,
  "prompt": "Your question here",
  "status": "pending",
  "response": null,
  "error": null,
  "worker_id": null,
  "webhook_url": "https://your-app.com/webhook",
  "webhook_delivered": false,
  "created_at": "2025-01-21T14:30:00Z",
  "updated_at": "2025-01-21T14:30:00Z"
}
```

#### Check Request Status
```http
GET /requests/{request_id}
X-API-Key: YOUR_API_KEY
```

**Response:**
```json
{
  "id": 123,
  "prompt": "Your question here",
  "status": "completed",
  "response": "{\"prompt\":\"Your question here\",\"response\":\"ChatGPT's answer\",\"timestamp\":\"2025-01-21T14:35:00Z\",\"url\":\"https://chatgpt.com/...\"}",
  "error": null,
  "worker_id": "worker-1",
  "webhook_url": "https://your-app.com/webhook",
  "webhook_delivered": true,
  "created_at": "2025-01-21T14:30:00Z",
  "updated_at": "2025-01-21T14:35:00Z"
}
```

#### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "ok"
}
```

### Status Values
- `pending`: Request submitted, waiting for worker
- `processing`: Worker is handling the request
- `completed`: Request completed successfully
- `failed`: Request failed with error

## 🐍 Python Integration

### Simple Client Class

```python
import requests
import time
import json
from typing import Optional, Callable

class ChatGPTClient:
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.headers = {"X-API-Key": api_key}
    
    def ask_chatgpt(self, prompt: str, webhook_url: Optional[str] = None, timeout: int = 120) -> str:
        """
        Ask ChatGPT a question and get the response
        
        Args:
            prompt: The question to ask ChatGPT
            webhook_url: Optional webhook URL for async notifications
            timeout: Maximum time to wait for response (seconds)
            
        Returns:
            ChatGPT's response text
        """
        # Submit request
        payload = {"prompt": prompt}
        if webhook_url:
            payload["webhook_url"] = webhook_url
            
        response = requests.post(
            f"{self.api_url}/requests",
            headers=self.headers,
            json=payload,
            timeout=10
        )
        
        if response.status_code != 201:
            raise Exception(f"Failed to submit request: {response.text}")
        
        request_data = response.json()
        request_id = request_data["id"]
        
        # If webhook provided, return immediately
        if webhook_url:
            return request_id
        
        # Otherwise, poll for completion
        return self._poll_for_response(request_id, timeout)
    
    def _poll_for_response(self, request_id: int, timeout: int) -> str:
        """Poll for response completion"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            response = requests.get(
                f"{self.api_url}/requests/{request_id}",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data["status"] == "completed":
                    # Parse ChatGPT response
                    chatgpt_data = json.loads(data["response"])
                    return chatgpt_data["response"]
                elif data["status"] == "failed":
                    raise Exception(f"Request failed: {data['error']}")
            
            time.sleep(5)  # Wait 5 seconds before checking again
        
        raise Exception("Request timeout")
    
    def get_request_status(self, request_id: int) -> dict:
        """Get the current status of a request"""
        response = requests.get(
            f"{self.api_url}/requests/{request_id}",
            headers=self.headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get request status: {response.text}")

# Usage
client = ChatGPTClient(
    api_url="https://chatgpt-relay-api.onrender.com",
    api_key="f2cd09510f1c537f53d0fcdae11528eef32de93a26e4237874447724be01e1d8"
)

# Ask ChatGPT a question
try:
    response = client.ask_chatgpt("Write a Python function to calculate fibonacci numbers")
    print(f"ChatGPT Response: {response}")
except Exception as e:
    print(f"Error: {e}")
```

### Advanced Usage with Callbacks

```python
class ChatGPTCallbackClient(ChatGPTClient):
    def __init__(self, api_url: str, api_key: str, webhook_url: str):
        super().__init__(api_url, api_key)
        self.webhook_url = webhook_url
        self.pending_requests = {}
    
    def ask_chatgpt_async(self, prompt: str, callback: Callable[[str, Optional[str]], None]) -> int:
        """
        Submit request asynchronously with callback
        
        Args:
            prompt: The question to ask ChatGPT
            callback: Function to call when response is ready
                     callback(response_text, error)
        
        Returns:
            Request ID
        """
        request_id = self.ask_chatgpt(prompt, webhook_url=self.webhook_url)
        self.pending_requests[request_id] = callback
        return request_id
    
    def handle_webhook(self, webhook_data: dict):
        """Handle incoming webhook notification"""
        request_id = webhook_data["request_id"]
        
        if request_id in self.pending_requests:
            callback = self.pending_requests.pop(request_id)
            
            if webhook_data["status"] == "completed":
                chatgpt_data = json.loads(webhook_data["response"])
                callback(chatgpt_data["response"], None)
            else:
                callback(None, webhook_data["error"])
```

## 🌐 Web Interface Integration

### CORS Support

The API now includes CORS (Cross-Origin Resource Sharing) support, allowing you to use it directly from web browsers. This means you can:

- Create HTML pages that call the API
- Use the API from any web application
- Test the API directly in your browser

### Simple Web Interface

Here's a complete HTML page that demonstrates how to use the API from a web browser:

```html
<!DOCTYPE html>
<html>
<head>
    <title>ChatGPT API Test</title>
</head>
<body>
    <h1>Ask ChatGPT</h1>
    <form id="chatForm">
        <textarea id="prompt" placeholder="Ask ChatGPT anything..." required></textarea>
        <button type="submit">Ask ChatGPT</button>
    </form>
    <div id="response"></div>

    <script>
        const form = document.getElementById('chatForm');
        const promptInput = document.getElementById('prompt');
        const responseDiv = document.getElementById('response');

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const prompt = promptInput.value.trim();
            if (!prompt) return;

            try {
                // Submit request
                const response = await fetch('https://chatgpt-relay-api.onrender.com/requests', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-API-Key': 'f2cd09510f1c537f53d0fcdae11528eef32de93a26e4237874447724be01e1d8'
                    },
                    body: JSON.stringify({ prompt })
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const data = await response.json();
                const requestId = data.id;

                // Poll for completion
                const pollForResponse = async () => {
                    const statusResponse = await fetch(`https://chatgpt-relay-api.onrender.com/requests/${requestId}`, {
                        headers: {
                            'X-API-Key': 'f2cd09510f1c537f53d0fcdae11528eef32de93a26e4237874447724be01e1d8'
                        }
                    });

                    const statusData = await statusResponse.json();
                    
                    if (statusData.status === 'completed') {
                        const chatgptData = JSON.parse(statusData.response);
                        responseDiv.innerHTML = `<h3>Response:</h3><p>${chatgptData.response}</p>`;
                    } else if (statusData.status === 'failed') {
                        responseDiv.innerHTML = `<h3>Error:</h3><p>${statusData.error}</p>`;
                    } else {
                        // Still processing, check again in 3 seconds
                        setTimeout(pollForResponse, 3000);
                    }
                };

                pollForResponse();

            } catch (error) {
                responseDiv.innerHTML = `<h3>Error:</h3><p>${error.message}</p>`;
            }
        });
    </script>
</body>
</html>
```

### Testing the Web Interface

1. **Save the HTML code** above as `test.html`
2. **Open it in your browser** (double-click the file)
3. **Enter a question** and click "Ask ChatGPT"
4. **Wait for the response** (it will poll automatically)

### Webhook Integration in Web Apps

For web applications, you can also use webhooks with a local server:

```javascript
// Webhook handler for web apps
class ChatGPTWebhookClient {
    constructor(apiUrl, apiKey, webhookUrl) {
        this.apiUrl = apiUrl;
        this.apiKey = apiKey;
        this.webhookUrl = webhookUrl;
        this.pendingRequests = new Map();
    }
    
    async askChatGPT(prompt, callback) {
        const response = await fetch(`${this.apiUrl}/requests`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': this.apiKey
            },
            body: JSON.stringify({
                prompt,
                webhook_url: this.webhookUrl
            })
        });
        
        const data = await response.json();
        this.pendingRequests.set(data.id, callback);
        return data.id;
    }
    
    handleWebhook(webhookData) {
        const requestId = webhookData.request_id;
        
        if (this.pendingRequests.has(requestId)) {
            const callback = this.pendingRequests.get(requestId);
            this.pendingRequests.delete(requestId);
            
            if (webhookData.status === 'completed') {
                const chatgptData = JSON.parse(webhookData.response);
                callback(chatgptData.response, null);
            } else {
                callback(null, webhookData.error);
            }
        }
    }
}
```

## 🌐 JavaScript/Node.js Integration

### Simple Client Class

```javascript
class ChatGPTClient {
    constructor(apiUrl, apiKey) {
        this.apiUrl = apiUrl.replace(/\/$/, '');
        this.apiKey = apiKey;
        this.headers = { 'X-API-Key': apiKey };
    }
    
    async askChatGPT(prompt, webhookUrl = null, timeout = 120000) {
        /**
         * Ask ChatGPT a question and get the response
         * 
         * @param {string} prompt - The question to ask ChatGPT
         * @param {string} webhookUrl - Optional webhook URL for async notifications
         * @param {number} timeout - Maximum time to wait for response (milliseconds)
         * @returns {Promise<string>} ChatGPT's response text
         */
        
        // Submit request
        const payload = { prompt };
        if (webhookUrl) payload.webhook_url = webhookUrl;
        
        const response = await fetch(`${this.apiUrl}/requests`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...this.headers
            },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            throw new Error(`Failed to submit request: ${response.statusText}`);
        }
        
        const requestData = await response.json();
        const requestId = requestData.id;
        
        // If webhook provided, return request ID
        if (webhookUrl) {
            return requestId;
        }
        
        // Otherwise, poll for completion
        return await this.pollForResponse(requestId, timeout);
    }
    
    async pollForResponse(requestId, timeout) {
        const startTime = Date.now();
        
        while (Date.now() - startTime < timeout) {
            const response = await fetch(`${this.apiUrl}/requests/${requestId}`, {
                headers: this.headers
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.status === 'completed') {
                    const chatgptData = JSON.parse(data.response);
                    return chatgptData.response;
                } else if (data.status === 'failed') {
                    throw new Error(`Request failed: ${data.error}`);
                }
            }
            
            await new Promise(resolve => setTimeout(resolve, 5000));
        }
        
        throw new Error('Request timeout');
    }
    
    async getRequestStatus(requestId) {
        const response = await fetch(`${this.apiUrl}/requests/${requestId}`, {
            headers: this.headers
        });
        
        if (response.ok) {
            return await response.json();
        } else {
            throw new Error(`Failed to get request status: ${response.statusText}`);
        }
    }
}

// Usage
const client = new ChatGPTClient(
    'https://chatgpt-relay-api.onrender.com',
    'f2cd09510f1c537f53d0fcdae11528eef32de93a26e4237874447724be01e1d8'
);

// Ask ChatGPT a question
client.askChatGPT('Write a JavaScript function to sort an array')
    .then(response => console.log('ChatGPT Response:', response))
    .catch(error => console.error('Error:', error));
```

### Express.js Webhook Handler

```javascript
const express = require('express');
const app = express();

app.use(express.json());

class ChatGPTWebhookClient extends ChatGPTClient {
    constructor(apiUrl, apiKey, webhookUrl) {
        super(apiUrl, apiKey);
        this.webhookUrl = webhookUrl;
        this.pendingRequests = new Map();
    }
    
    async askChatGPTAsync(prompt, callback) {
        const requestId = await this.askChatGPT(prompt, this.webhookUrl);
        this.pendingRequests.set(requestId, callback);
        return requestId;
    }
    
    handleWebhook(webhookData) {
        const requestId = webhookData.request_id;
        
        if (this.pendingRequests.has(requestId)) {
            const callback = this.pendingRequests.get(requestId);
            this.pendingRequests.delete(requestId);
            
            if (webhookData.status === 'completed') {
                const chatgptData = JSON.parse(webhookData.response);
                callback(chatgptData.response, null);
            } else {
                callback(null, webhookData.error);
            }
        }
    }
}

// Initialize client
const client = new ChatGPTWebhookClient(
    'https://chatgpt-relay-api.onrender.com',
    'f2cd09510f1c537f53d0fcdae11528eef32de93a26e4237874447724be01e1d8',
    'https://your-app.com/webhook'
);

// Webhook endpoint
app.post('/webhook', (req, res) => {
    client.handleWebhook(req.body);
    res.json({ status: 'received' });
});

// Example usage
app.post('/ask-chatgpt', async (req, res) => {
    try {
        const { prompt } = req.body;
        
        const requestId = await client.askChatGPTAsync(prompt, (response, error) => {
            if (error) {
                console.error('ChatGPT Error:', error);
            } else {
                console.log('ChatGPT Response:', response);
                // Send response to client via WebSocket, etc.
            }
        });
        
        res.json({ requestId, status: 'submitted' });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.listen(3000, () => {
    console.log('Server running on port 3000');
});
```

## 🔗 Webhook Integration

### Webhook Payload Format

When a request completes, your webhook URL will receive a POST request with this payload:

```json
{
  "request_id": 123,
  "status": "completed",
  "prompt": "Your original question",
  "response": "{\"prompt\":\"Your original question\",\"response\":\"ChatGPT's answer\",\"timestamp\":\"2025-01-21T14:35:00Z\",\"url\":\"https://chatgpt.com/...\"}",
  "timestamp": "2025-01-21T14:35:00Z",
  "worker_id": "worker-1"
}
```

### Flask Webhook Handler

```python
from flask import Flask, request, jsonify
import json

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    webhook_data = request.json
    
    request_id = webhook_data['request_id']
    status = webhook_data['status']
    
    if status == 'completed':
        # Parse ChatGPT response
        chatgpt_data = json.loads(webhook_data['response'])
        response_text = chatgpt_data['response']
        
        # Process the response
        print(f"Request {request_id} completed: {response_text}")
        
        # Store in database, send to user, etc.
        # ...
        
    elif status == 'failed':
        error = webhook_data['error']
        print(f"Request {request_id} failed: {error}")
    
    return jsonify({"status": "received"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

### Testing Webhooks Locally

Use ngrok to expose your local webhook server:

```bash
# Install ngrok
npm install -g ngrok

# Expose your local server
ngrok http 5000

# Use the ngrok URL in your requests
payload = {
    "prompt": "Test question",
    "webhook_url": "https://abc123.ngrok.io/webhook"
}
```

## 💻 Command Line Usage

### Simple CLI Tool

```python
#!/usr/bin/env python3
"""
ChatGPT CLI Tool
Usage: python chatgpt_cli.py "Your question here"
"""

import argparse
import sys
import requests
import time
import json

def main():
    parser = argparse.ArgumentParser(description='Ask ChatGPT questions from command line')
    parser.add_argument('prompt', help='Question to ask ChatGPT')
    parser.add_argument('--api-url', default='https://chatgpt-relay-api.onrender.com')
    parser.add_argument('--api-key', default='f2cd09510f1c537f53d0fcdae11528eef32de93a26e4237874447724be01e1d8')
    parser.add_argument('--timeout', type=int, default=120, help='Timeout in seconds')
    parser.add_argument('--webhook', help='Webhook URL for async responses')
    
    args = parser.parse_args()
    
    try:
        # Submit request
        payload = {"prompt": args.prompt}
        if args.webhook:
            payload["webhook_url"] = args.webhook
        
        response = requests.post(
            f"{args.api_url}/requests",
            headers={"X-API-Key": args.api_key},
            json=payload,
            timeout=10
        )
        
        if response.status_code != 201:
            print(f"Error: Failed to submit request: {response.text}", file=sys.stderr)
            sys.exit(1)
        
        request_data = response.json()
        request_id = request_data["id"]
        
        if args.webhook:
            print(f"Request submitted: {request_id}")
            print(f"Webhook will be sent to: {args.webhook}")
            return
        
        # Poll for completion
        print(f"Request submitted: {request_id}")
        print("Waiting for response...")
        
        start_time = time.time()
        while time.time() - start_time < args.timeout:
            status_response = requests.get(
                f"{args.api_url}/requests/{request_id}",
                headers={"X-API-Key": args.api_key},
                timeout=10
            )
            
            if status_response.status_code == 200:
                data = status_response.json()
                if data["status"] == "completed":
                    chatgpt_data = json.loads(data["response"])
                    print(f"\nChatGPT Response:\n{chatgpt_data['response']}")
                    return
                elif data["status"] == "failed":
                    print(f"Error: {data['error']}", file=sys.stderr)
                    sys.exit(1)
            
            time.sleep(5)
        
        print("Error: Request timeout", file=sys.stderr)
        sys.exit(1)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### Usage Examples

```bash
# Basic usage
python chatgpt_cli.py "Write a Python function to calculate prime numbers"

# With custom timeout
python chatgpt_cli.py "Explain machine learning" --timeout 60

# With webhook
python chatgpt_cli.py "Write a haiku" --webhook "https://your-app.com/webhook"
```

## ⚠️ Error Handling

### Common Errors and Solutions

#### 1. Worker Not Running
```
Error: No pending requests (404)
```
**Solution**: Start the Chrome worker locally

#### 2. Request Timeout
```
Error: Request timeout
```
**Solution**: Increase timeout or check worker status

#### 3. Invalid API Key
```
Error: Invalid API key (401)
```
**Solution**: Check your API key

#### 4. Webhook Delivery Failed
```
Webhook delivery failed after 3 attempts
```
**Solution**: Check webhook URL accessibility

### Robust Error Handling

```python
import requests
import time
import json
from typing import Optional

class RobustChatGPTClient:
    def __init__(self, api_url: str, api_key: str, max_retries: int = 3):
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.headers = {"X-API-Key": api_key}
        self.max_retries = max_retries
    
    def ask_chatgpt(self, prompt: str, timeout: int = 120) -> Optional[str]:
        """Ask ChatGPT with robust error handling"""
        
        for attempt in range(self.max_retries):
            try:
                return self._submit_and_poll(prompt, timeout)
            except requests.RequestException as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise Exception(f"All {self.max_retries} attempts failed")
            except Exception as e:
                print(f"Unexpected error: {e}")
                raise
    
    def _submit_and_poll(self, prompt: str, timeout: int) -> str:
        """Submit request and poll for response"""
        
        # Submit request
        response = requests.post(
            f"{self.api_url}/requests",
            headers=self.headers,
            json={"prompt": prompt},
            timeout=10
        )
        
        if response.status_code == 401:
            raise Exception("Invalid API key")
        elif response.status_code != 201:
            raise Exception(f"Failed to submit request: {response.text}")
        
        request_data = response.json()
        request_id = request_data["id"]
        
        # Poll for completion
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                status_response = requests.get(
                    f"{self.api_url}/requests/{request_id}",
                    headers=self.headers,
                    timeout=10
                )
                
                if status_response.status_code == 200:
                    data = status_response.json()
                    if data["status"] == "completed":
                        chatgpt_data = json.loads(data["response"])
                        return chatgpt_data["response"]
                    elif data["status"] == "failed":
                        raise Exception(f"Request failed: {data['error']}")
                
                time.sleep(5)
                
            except requests.RequestException as e:
                print(f"Polling error: {e}")
                time.sleep(5)
        
        raise Exception("Request timeout")
```

## 🎯 Best Practices

### 1. Always Handle Errors
```python
try:
    response = client.ask_chatgpt("Your question")
    print(response)
except Exception as e:
    print(f"Error: {e}")
    # Handle error appropriately
```

### 2. Use Appropriate Timeouts
```python
# For quick questions
response = client.ask_chatgpt("What is 2+2?", timeout=30)

# For complex questions
response = client.ask_chatgpt("Write a detailed analysis", timeout=300)
```

### 3. Implement Rate Limiting
```python
import time

class RateLimitedClient(ChatGPTClient):
    def __init__(self, api_url: str, api_key: str, requests_per_minute: int = 10):
        super().__init__(api_url, api_key)
        self.requests_per_minute = requests_per_minute
        self.requests = []
    
    def ask_chatgpt(self, prompt: str, **kwargs):
        # Rate limiting
        now = time.time()
        self.requests = [req_time for req_time in self.requests if now - req_time < 60]
        
        if len(self.requests) >= self.requests_per_minute:
            sleep_time = 60 - (now - self.requests[0])
            print(f"Rate limit reached. Sleeping for {sleep_time:.1f} seconds...")
            time.sleep(sleep_time)
        
        self.requests.append(now)
        return super().ask_chatgpt(prompt, **kwargs)
```

### 4. Cache Responses
```python
import hashlib
import json

class CachedChatGPTClient(ChatGPTClient):
    def __init__(self, api_url: str, api_key: str, cache_file: str = "chatgpt_cache.json"):
        super().__init__(api_url, api_key)
        self.cache_file = cache_file
        self.cache = self._load_cache()
    
    def _load_cache(self):
        try:
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def _save_cache(self):
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f)
    
    def ask_chatgpt(self, prompt: str, **kwargs):
        # Create cache key
        cache_key = hashlib.md5(prompt.encode()).hexdigest()
        
        # Check cache
        if cache_key in self.cache:
            print("Returning cached response")
            return self.cache[cache_key]
        
        # Get fresh response
        response = super().ask_chatgpt(prompt, **kwargs)
        
        # Cache response
        self.cache[cache_key] = response
        self._save_cache()
        
        return response
```

### 5. Use Webhooks for Better Performance
```python
# Instead of polling
response = client.ask_chatgpt("Complex question", timeout=300)  # Slow

# Use webhooks
request_id = client.ask_chatgpt("Complex question", webhook_url="https://your-app.com/webhook")
# Handle response in webhook handler - much faster
```

## 📝 Examples

### Content Generation Bot

```python
class ContentBot:
    def __init__(self, client):
        self.client = client
    
    def generate_blog_post(self, topic: str, length: str = "medium") -> str:
        prompt = f"Write a {length} blog post about {topic}. Include an introduction, main points, and conclusion."
        return self.client.ask_chatgpt(prompt)
    
    def generate_social_media_post(self, topic: str, platform: str = "twitter") -> str:
        prompt = f"Write a {platform} post about {topic}. Keep it engaging and under 280 characters."
        return self.client.ask_chatgpt(prompt)
    
    def generate_email_subject(self, content: str) -> str:
        prompt = f"Write an engaging email subject line for this content: {content}"
        return self.client.ask_chatgpt(prompt)

# Usage
client = ChatGPTClient("https://chatgpt-relay-api.onrender.com", "your-api-key")
bot = ContentBot(client)

blog_post = bot.generate_blog_post("Python best practices", "long")
tweet = bot.generate_social_media_post("AI trends", "twitter")
subject = bot.generate_email_subject("New product launch")
```

### Code Review Assistant

```python
class CodeReviewer:
    def __init__(self, client):
        self.client = client
    
    def review_code(self, code: str, language: str = "python") -> str:
        prompt = f"Review this {language} code for best practices, potential bugs, and improvements:\n\n{code}"
        return self.client.ask_chatgpt(prompt)
    
    def explain_code(self, code: str) -> str:
        prompt = f"Explain what this code does:\n\n{code}"
        return self.client.ask_chatgpt(prompt)
    
    def suggest_improvements(self, code: str) -> str:
        prompt = f"Suggest improvements for this code:\n\n{code}"
        return self.client.ask_chatgpt(prompt)

# Usage
reviewer = CodeReviewer(client)

code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""

review = reviewer.review_code(code)
explanation = reviewer.explain_code(code)
improvements = reviewer.suggest_improvements(code)
```

### Documentation Generator

```python
class DocumentationGenerator:
    def __init__(self, client):
        self.client = client
    
    def generate_function_docs(self, function_code: str) -> str:
        prompt = f"Generate comprehensive documentation for this function:\n\n{function_code}"
        return self.client.ask_chatgpt(prompt)
    
    def generate_readme(self, project_description: str) -> str:
        prompt = f"Generate a README.md file for a project with this description: {project_description}"
        return self.client.ask_chatgpt(prompt)
    
    def generate_api_docs(self, api_endpoints: str) -> str:
        prompt = f"Generate API documentation for these endpoints:\n\n{api_endpoints}"
        return self.client.ask_chatgpt(prompt)

# Usage
doc_gen = DocumentationGenerator(client)

function_code = """
def calculate_fibonacci(n):
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)
"""

docs = doc_gen.generate_function_docs(function_code)
print(docs)
```

## 🚀 Getting Started Checklist

- [ ] Deploy your ChatGPT Relay API to Render
- [ ] Start Chrome with remote debugging enabled
- [ ] Start the worker process locally
- [ ] Test the API with a simple request
- [ ] Choose your integration method (Python, JavaScript, webhooks, web interface)
- [ ] Implement error handling
- [ ] Add rate limiting if needed
- [ ] Test with your specific use cases
- [ ] Test web interface with `test_web_interface.html`

## 📞 Support

If you encounter any issues:

1. Check that the worker is running locally
2. Verify your API key is correct
3. Check the Render logs for errors
4. Ensure your webhook URLs are accessible
5. Test with the health endpoint first

---

**Happy coding with ChatGPT! 🎉**
