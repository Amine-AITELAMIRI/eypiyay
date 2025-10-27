# Migration Guide: Adding Sources Support

## Overview

The API now automatically extracts and returns **sources** separately from the response content. This guide helps you migrate your application to take advantage of this new feature.

## What Changed?

### Before (Old Format)
```json
{
  "response": "{\"prompt\":\"...\",\"response\":\"Here is the answer [1] with citations [2] at the end.\\n\\n---\\n\\n[1]: https://example.com/article \\\"Article Title\\\"\\n[2]: https://another-site.com \\\"Page\\\"\",\"timestamp\":\"...\",\"url\":\"...\"}"
}
```

**Issues:**
- Sources mixed with content (e.g., `[1]`, `[2]` citations)
- Source list at bottom of response
- Hard to parse and display separately

### After (New Format)
```json
{
  "response": "{\"prompt\":\"...\",\"response\":\"Here is the answer [1] with citations [2] without the source list.\",\"sources\":[{\"number\":1,\"url\":\"https://example.com/article\",\"title\":\"Article Title\"},{\"number\":2,\"url\":\"https://another-site.com\",\"title\":\"Page\"}],\"timestamp\":\"...\",\"url\":\"...\"}",
  "sources": [
    {
      "number": 1,
      "url": "https://example.com/article",
      "title": "Article Title"
    },
    {
      "number": 2,
      "url": "https://another-site.com",
      "title": "Page"
    }
  ]
}
```

**Benefits:**
- Clean response without source list
- Structured sources array for easy access
- Separated for clean UI presentation

## Migration Steps

### Step 1: Update Response Parsing (Optional but Recommended)

**Old Code:**
```python
import requests
import json

response = requests.get(
    f"https://chatgpt-relay-api.onrender.com/requests/{request_id}",
    headers={"X-API-Key": "your-api-key"}
)

data = response.json()
response_data = json.loads(data["response"])

# Display everything together (includes sources at bottom)
print(response_data["response"])
```

**New Code (with sources support):**
```python
import requests
import json

response = requests.get(
    f"https://chatgpt-relay-api.onrender.com/requests/{request_id}",
    headers={"X-API-Key": "your-api-key"}
)

data = response.json()
response_data = json.loads(data["response"])

# Display clean content
print(response_data["response"])

# Display sources separately (if present)
if response_data.get("sources"):
    print("\n📚 Sources:")
    for source in response_data["sources"]:
        print(f"  [{source['number']}] {source['title']}")
        print(f"      {source['url']}")
```

### Step 2: Handle Missing Sources (Backward Compatible)

The `sources` field will be `null` if no sources are present, so always check:

```python
# Safe approach - works with old and new responses
if response_data.get("sources"):
    # Display sources
    for source in response_data["sources"]:
        display_source(source)
else:
    # No sources available
    print("No sources provided")
```

### Step 3: Update Your UI (If Applicable)

**Old UI:**
```html
<div id="response">
  <!-- Shows response with sources mixed in -->
</div>
```

**New UI:**
```html
<div id="response">
  <!-- Shows clean response content -->
</div>

<div id="sources" style="margin-top: 2rem; padding-top: 2rem; border-top: 1px solid #ddd;">
  <!-- Shows sources separately -->
</div>
```

```javascript
// Parse and display separately
const responseData = JSON.parse(data.response);

// Main content
document.getElementById('response').innerHTML = 
    marked.parse(responseData.response);

// Sources separately
if (responseData.sources) {
    const sourcesHTML = responseData.sources.map(source => `
        <div class="source-item">
            <strong>[${source.number}]</strong>
            <a href="${source.url}" target="_blank">${source.title}</a>
        </div>
    `).join('');
    
    document.getElementById('sources').innerHTML = 
        '<h3>Sources</h3>' + sourcesHTML;
}
```

## Compatibility

### ✅ Fully Backward Compatible

Your existing code will **continue to work** without changes because:
1. The `response` field still contains the full text (now clean)
2. The `sources` field is new and optional (`null` if absent)
3. No breaking changes to the API structure

### What Stays the Same

- API endpoints remain unchanged
- Request format unchanged
- Response structure unchanged (just new `sources` field added)
- Error handling unchanged

### What's New

- New `sources` array field in the response payload
- Cleaner `response` content (without source list at bottom)
- Better structure for displaying sources

## Testing Your Migration

### 1. Test with Search Mode (Has Sources)

```bash
curl -X POST https://chatgpt-relay-api.onrender.com/requests \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Latest AI research breakthroughs",
    "prompt_mode": "search"
  }'
```

Check the response for the `sources` field.

### 2. Test with Standard Mode (No Sources)

```bash
curl -X POST https://chatgpt-relay-api.onrender.com/requests \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is 2 + 2?"
  }'
```

Verify that `sources` is `null`.

### 3. Test Your Display Logic

Ensure your UI handles both cases gracefully:
- ✅ Sources present: Display in a separate section
- ✅ Sources absent: Hide or show "No sources available"
- ✅ Old response format: Still displays correctly

## Example: Complete Migration

### Before (Basic Implementation)
```python
def display_response(request_id):
    response = requests.get(
        f"https://chatgpt-relay-api.onrender.com/requests/{request_id}",
        headers={"X-API-Key": api_key}
    )
    data = response.json()
    
    if data["status"] == "completed":
        response_data = json.loads(data["response"])
        print(response_data["response"])  # Shows everything including sources
```

### After (Enhanced with Sources)
```python
def display_response(request_id):
    response = requests.get(
        f"https://chatgpt-relay-api.onrender.com/requests/{request_id}",
        headers={"X-API-Key": api_key}
    )
    data = response.json()
    
    if data["status"] == "completed":
        response_data = json.loads(data["response"])
        
        # Display main content (clean, without source list)
        print("Answer:")
        print(response_data["response"])
        
        # Display sources separately (if available)
        if response_data.get("sources"):
            print("\n" + "="*50)
            print("Sources:")
            for source in response_data["sources"]:
                print(f"  [{source['number']}] {source['title']}")
                print(f"      {source['url']}")
```

## Benefits of Migration

### Why You Should Migrate

1. **Better UX**: Cleaner content, sources in separate section
2. **Structured Data**: Easy to access URLs and titles programmatically
3. **Flexible Display**: Show/hide sources, style separately, link directly
4. **Compliance**: Proper attribution for academic/research use

### What You Can Do Now

- Link directly to source URLs
- Extract all source titles for display
- Count how many sources were used
- Hide sources on mobile, show on desktop
- Add "Copy source URL" buttons
- Build source preview tooltips

## Timeline

- **No urgent migration required** - old code continues to work
- **Gradual adoption recommended** - update when convenient
- **No breaking changes** - take your time to test

## Support

If you encounter any issues during migration:
1. Check the `sources` field is being parsed correctly
2. Verify `sources` can be `null` in your code
3. Test with both search mode (has sources) and standard mode (no sources)

## Summary

This is a **non-breaking enhancement** that adds:
- ✨ New `sources` field (optional, `null` if not present)
- ✨ Cleaner response content
- ✨ Structured source data

**No migration required immediately** - your existing code will continue working. Update at your convenience to take advantage of the new sources feature!

