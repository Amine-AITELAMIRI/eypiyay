# Follow-Up System Implementation Guide

This document explains the follow-up conversation system that allows clients to continue multi-turn conversations with ChatGPT through the API.

## Overview

The follow-up system enables clients to maintain conversation context across multiple API requests by continuing existing ChatGPT conversations instead of starting new chats each time.

## How It Works

### 1. Initial Request (New Conversation)

When you create a request without `follow_up_chat_url`, a new ChatGPT conversation starts:

```python
response = requests.post(
    "https://chatgpt-relay-api.onrender.com/requests",
    headers={"X-API-Key": "your-api-key"},
    json={"prompt": "What is quantum computing?"}
)
```

### 2. Response Includes Chat URL

The response includes a `chat_url` field with the ChatGPT conversation link:

```json
{
  "id": 123,
  "prompt": "What is quantum computing?",
  "status": "completed",
  "response": "{...}",
  "chat_url": "https://chatgpt.com/c/abc-123-def",
  ...
}
```

### 3. Follow-Up Request (Continue Conversation)

Pass the `chat_url` as `follow_up_chat_url` to continue the conversation:

```python
response = requests.post(
    "https://chatgpt-relay-api.onrender.com/requests",
    headers={"X-API-Key": "your-api-key"},
    json={
        "prompt": "Can you explain quantum entanglement?",
        "follow_up_chat_url": "https://chatgpt.com/c/abc-123-def"
    }
)
```

ChatGPT will now have context from the previous message and respond accordingly.

## Technical Implementation

### Database Changes

Two new fields were added to the `requests` table:

- **`chat_url`**: The ChatGPT conversation URL (populated when request completes)
- **`follow_up_chat_url`**: The chat URL used for this request (if it was a follow-up)

**Migration:**
```sql
-- Run this in Supabase SQL Editor
ALTER TABLE requests ADD COLUMN IF NOT EXISTS chat_url TEXT;
ALTER TABLE requests ADD COLUMN IF NOT EXISTS follow_up_chat_url TEXT;
CREATE INDEX IF NOT EXISTS idx_requests_chat_url ON requests(chat_url);
```

### API Changes

#### Request Model (`CreateRequest`)
Added optional field:
- `follow_up_chat_url`: String - ChatGPT chat URL to continue an existing conversation

#### Response Model (`RequestResponse`)
Added fields:
- `chat_url`: String - The ChatGPT conversation URL (use for follow-ups)
- `follow_up_chat_url`: String - The chat URL that was used (if this was a follow-up)

#### Completion Endpoint
Updated `POST /worker/{request_id}/complete` to accept `chat_url` in the payload.

### Worker Changes

#### Navigation Logic
The worker now checks for `follow_up_chat_url` in the job and intelligently skips navigation if already on the target page:

```python
# Get current page URL
current_url = get_current_page_url()

# Determine target URL (follow-up or new chat)
if follow_up_chat_url:
    target_url = follow_up_chat_url
else:
    target_url = default_chatgpt_url

# Only navigate if current page is different (optimization!)
if normalize_url(current_url) != normalize_url(target_url):
    navigate_to(target_url)
else:
    # Already on the right page, skip navigation
    logger.info("Already on target page, skipping navigation")
```

**Performance Optimization**: The worker checks if the target URL is already open before navigating. This saves 3+ seconds when continuing conversations in the same chat, as it avoids unnecessary page reloads.

**Important**: The optimization **only applies to follow-ups**. When `follow_up_chat_url` is `null` (or not provided), the worker **always navigates** to ensure a fresh new chat is created, even if already on a ChatGPT page.

#### Response Handling
The worker extracts the chat URL from the bookmarklet response and includes it in the completion payload:

```python
chat_url = result.get("url")  # ChatGPT conversation URL
post_completion(server, request_id, result, chat_url)
```

### Bookmarklet

No changes needed! The bookmarklet already captures `window.location.href` as the `url` field in the response payload.

## Usage Examples

### Basic Multi-Turn Conversation

```python
import requests
import json
import time

API_KEY = "your-api-key"
BASE_URL = "https://chatgpt-relay-api.onrender.com"

def ask(prompt, chat_url=None):
    # Create request
    payload = {"prompt": prompt}
    if chat_url:
        payload["follow_up_chat_url"] = chat_url
    
    response = requests.post(
        f"{BASE_URL}/requests",
        headers={"X-API-Key": API_KEY},
        json=payload
    )
    request_id = response.json()["id"]
    
    # Wait for completion
    while True:
        response = requests.get(
            f"{BASE_URL}/requests/{request_id}",
            headers={"X-API-Key": API_KEY}
        )
        data = response.json()
        
        if data["status"] == "completed":
            result = json.loads(data["response"])
            return result["response"], data["chat_url"]
        elif data["status"] == "failed":
            raise Exception(data["error"])
        
        time.sleep(5)

# Conversation flow
response1, chat_url = ask("What is machine learning?")
print(response1)

response2, chat_url = ask("Can you give me an example?", chat_url)
print(response2)

response3, chat_url = ask("What are the challenges?", chat_url)
print(response3)
```

### Conversation Manager Class

A reusable class for managing conversations:

```python
class ChatGPTConversation:
    def __init__(self, api_key, base_url="https://chatgpt-relay-api.onrender.com"):
        self.api_key = api_key
        self.base_url = base_url
        self.chat_url = None
        self.history = []
    
    def ask(self, prompt, **kwargs):
        # Create request
        payload = {"prompt": prompt, **kwargs}
        if self.chat_url:
            payload["follow_up_chat_url"] = self.chat_url
        
        response = requests.post(
            f"{self.base_url}/requests",
            headers={"X-API-Key": self.api_key},
            json=payload
        )
        request_id = response.json()["id"]
        
        # Wait for completion (polling)
        while True:
            response = requests.get(
                f"{self.base_url}/requests/{request_id}",
                headers={"X-API-Key": self.api_key}
            )
            data = response.json()
            
            if data["status"] == "completed":
                result = json.loads(data["response"])
                response_text = result["response"]
                self.chat_url = data["chat_url"]
                self.history.append({"prompt": prompt, "response": response_text})
                return response_text
            elif data["status"] == "failed":
                raise Exception(data["error"])
            
            time.sleep(5)
    
    def start_new_conversation(self):
        self.chat_url = None
        self.history = []

# Usage
conversation = ChatGPTConversation(api_key="your-api-key")

response1 = conversation.ask("Explain quantum computing")
response2 = conversation.ask("What are its applications?")
response3 = conversation.ask("Which companies lead in this field?")

# Start fresh
conversation.start_new_conversation()
response4 = conversation.ask("Tell me about AI")
```

## Benefits

1. **Context Preservation**: ChatGPT remembers previous messages in the conversation
2. **Natural Conversations**: Build complex multi-turn dialogues
3. **Flexibility**: Choose whether to follow up or start fresh for each request
4. **No Session Management**: Client controls conversation continuity via URLs
5. **Backward Compatible**: Existing code works unchanged (creates new chats)
6. **Performance Optimized**: Worker skips navigation for follow-ups on same page (saves 3+ seconds)
7. **Guaranteed Fresh Chats**: When `follow_up_chat_url` is null, always creates a new conversation

## Best Practices

### 1. Store Chat URLs
Keep track of chat URLs if you need to continue conversations:

```python
conversation_state = {
    "user_123": {
        "chat_url": "https://chatgpt.com/c/abc-123",
        "last_updated": "2024-01-15T10:30:00Z"
    }
}
```

### 2. Choose When to Follow Up
Not every request needs to be a follow-up:

```python
# Follow up when building on previous context
if needs_context:
    payload["follow_up_chat_url"] = chat_url

# Start fresh for new topics
else:
    # Omit follow_up_chat_url
    pass
```

### 3. Handle Errors Gracefully
If a follow-up fails, retry as a new conversation:

```python
try:
    response = ask(prompt, chat_url=old_chat_url)
except Exception:
    # Retry as new conversation
    response = ask(prompt)
```

### 4. Conversation Limits
ChatGPT has limits on conversation length. Consider starting a new chat periodically:

```python
if len(conversation.history) > 20:
    conversation.start_new_conversation()
```

## Limitations

1. **ChatGPT Conversation Limits**: Very long conversations may hit ChatGPT's context limits
2. **URL Validity**: Chat URLs are valid as long as the conversation exists in ChatGPT
3. **No Branching**: Cannot branch conversations - each follow-up appends to the existing chat

## Troubleshooting

### Follow-Up Not Working

**Problem**: Follow-up requests seem to start new conversations

**Solutions**:
1. Verify `follow_up_chat_url` is being passed correctly
2. Check that the chat URL is valid (still exists in ChatGPT)
3. Ensure worker has navigated to the correct URL (check worker logs)

### Missing Chat URL

**Problem**: Response doesn't include `chat_url`

**Solutions**:
1. Ensure database migration has been applied
2. Verify bookmarklet is capturing `window.location.href`
3. Check that worker is extracting and passing `chat_url` to completion endpoint

### Navigation Issues

**Problem**: Worker can't navigate to follow-up chat

**Solutions**:
1. Ensure chat URL format is correct
2. Check that the ChatGPT tab is accessible
3. Verify no authentication issues with ChatGPT

## Migration Checklist

- [x] Run database migration (`supabase_migration_add_chat_url.sql`)
- [x] Update server code (`server/main.py` and `server/database_supabase.py`)
- [x] Update worker code (`worker/cdp_worker.py`)
- [x] Update API documentation (`API_USAGE_GUIDE.md`)
- [ ] Test with real requests (initial + follow-up)
- [ ] Update client code to use follow-up feature

## API Reference

See [API_USAGE_GUIDE.md](API_USAGE_GUIDE.md) for complete API documentation including:
- Request fields
- Response fields
- Usage examples
- Error handling

---

**Version:** 1.0  
**Last Updated:** October 2025  
**Status:** ✅ Implemented and Documented

