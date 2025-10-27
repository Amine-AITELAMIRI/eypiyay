# Deep Research Mode Implementation

## Overview
Added a new prompt mode called **"deep research"** that can be triggered with `/deep`. This mode is designed for comprehensive, in-depth analysis and research tasks.

## Changes Made

### 1. Server (`server/main.py`)
- Updated `CreateRequest` model to accept `"deep"` as a valid `prompt_mode` value
- Added description: "Special prompt mode like 'search', 'study', or 'deep' that types /sear, /stu, or /deep before the prompt"

### 2. Bookmarklet (`bookmarklet.js` & `bookmarklet-inline.js`)
- Modified prompt mode handling to include "deep" mode
- Added logic to type `/deep` command when `prompt_mode === "deep"`
- Updated condition: `if (promptMode && (promptMode === "search" || promptMode === "study" || promptMode === "deep"))`
- Updated command mapping: `const modeCommand = promptMode === "search" ? "/sear" : (promptMode === "study" ? "/stu" : "/deep");`

### 3. Documentation

#### API_USAGE_GUIDE.md
- Updated `prompt_mode` field description to include "deep" as a valid value
- Added comprehensive "deep" mode section with:
  - Description and use cases
  - Response time warning (5-30 minutes)
  - Explanation of timeout handling
  - Best practices for deep research
  - Example usage with webhooks

#### README.md
- Added "deep" to the list of special prompt modes
- Included response time warning (⚠️ 5-30 minutes)
- Added example usage with webhook recommendation
- Added note about asynchronous handling of long-running requests

## Timeout Handling

### ✅ No Timeout Issues!

The system is already designed to handle long-running requests without timeouts:

1. **Worker Pattern**: Uses asynchronous claim-process-complete pattern
   - API requests complete immediately (just creates the request)
   - Worker claims and processes independently
   - No server-side timeout on the initial API call

2. **Worker Implementation**: 
   - `wait_for_new_file()` function loops **indefinitely** until ChatGPT responds
   - No timeout on waiting for response
   - CDP timeout (5s default) only affects WebSocket connection, not response waiting

3. **Configuration**:
   - `start-all.sh` already sets `CDP_TIMEOUT="300.0"` (5 minutes) for connection stability
   - Sufficient for maintaining WebSocket connection during long-running tasks

## Usage Examples

### Basic Deep Research Request
```json
{
  "prompt": "Conduct comprehensive research on quantum computing applications",
  "prompt_mode": "deep"
}
```

### Deep Research with Thinking Mode
```json
{
  "prompt": "Analyze the historical development and future prospects of renewable energy technology",
  "prompt_mode": "deep",
  "model_mode": "thinking"
}
```

### Deep Research with Webhook (Recommended)
```json
{
  "prompt": "Comprehensive analysis of blockchain technology in healthcare",
  "prompt_mode": "deep",
  "model_mode": "thinking",
  "webhook_url": "https://your-server.com/webhook"
}
```

## Best Practices

1. **Use Webhooks**: Deep research can take 5-30 minutes, so webhooks are highly recommended for notification when complete

2. **Combine with Thinking Mode**: For best results, use `"model_mode": "thinking"` with deep research

3. **Specific Questions**: Provide clear, well-defined research questions for better results

4. **Polling Strategy**: If not using webhooks, poll the API periodically (e.g., every 30-60 seconds) instead of waiting synchronously

## Testing

To test the new mode:

```bash
# Create a deep research request
curl -X POST "https://your-api.com/requests" \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Comprehensive analysis of AI safety research",
    "prompt_mode": "deep",
    "webhook_url": "https://your-server.com/webhook"
  }'

# Response:
{
  "id": 123,
  "prompt": "Comprehensive analysis of AI safety research",
  "status": "pending",
  "prompt_mode": "deep",
  ...
}

# Poll for completion (or wait for webhook)
curl "https://your-api.com/requests/123" \
  -H "X-API-Key: your-key"
```

## Implementation Date
October 27, 2025

## Notes
- The system is already configured to handle long-running requests without any timeout issues
- No additional timeout configuration changes were needed
- The asynchronous worker pattern prevents any API-level timeouts
- Deep research mode may take 5-30 minutes depending on the complexity of the query

