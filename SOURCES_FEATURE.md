# Sources Feature - Separate Response Content from Citations

## Overview

The bookmarklet now automatically **parses and separates sources from the main response content**. When ChatGPT includes source citations (especially in search mode), they are extracted into a structured format and returned separately from the main content.

## The Problem This Solves

When ChatGPT provides sources (particularly in search mode), the response includes:
1. The main content with inline citations like `[1]`, `[2]`, `[3]`
2. Source list at the bottom in the format:
   ```
   [1]: https://example.com/article "Article Title"
   [2]: https://another-site.com/page — Page Description
   ```

Previously, this was all returned as one block of text, making it difficult to:
- Display the content without cluttering citations
- Present sources in a user-friendly format
- Programmatically access source URLs and titles

## How It Works

### 1. Copy Button Captures Full Response

The bookmarklet uses ChatGPT's native copy button to capture the complete response including all sources.

### 2. Automatic Source Parsing

The response is automatically parsed using regex to detect and extract:
- Source citation numbers (e.g., `[1]`, `[2]`)
- Source URLs (e.g., `https://example.com`)
- Source titles (from quoted strings or after em-dash)

### 3. Clean Response + Structured Sources

The response is split into two parts:
- **`response`**: Clean content without the source list
- **`sources`**: Array of source objects with `number`, `url`, and `title`

## Example Response Structure

### Input (from ChatGPT copy button)
```markdown
If you're looking for a dictionary of the Klingon language, here are some excellent resources:

1. **Klingonska Akademien** - They host a searchable version derived from *The Klingon Dictionary*
2. **Klingon Language Institute (KLI)** - A hub for the language with vocabulary and grammar resources

---

[1]: https://klingonska.org/dict/?utm_source=chatgpt.com "Klingon Pocket Dictionary - Klingonska Akademien"
[2]: https://www.kli.org/?utm_source=chatgpt.com "Klingon Language Institute — Language Opens Worlds"
```

### Output (parsed and saved to localStorage)
```json
{
  "prompt": "Tell me about Klingon dictionaries",
  "response": "If you're looking for a dictionary of the Klingon language, here are some excellent resources:\n\n1. **Klingonska Akademien** - They host a searchable version derived from *The Klingon Dictionary*\n2. **Klingon Language Institute (KLI)** - A hub for the language with vocabulary and grammar resources",
  "sources": [
    {
      "number": 1,
      "url": "https://klingonska.org/dict/?utm_source=chatgpt.com",
      "title": "Klingon Pocket Dictionary - Klingonska Akademien"
    },
    {
      "number": 2,
      "url": "https://www.kli.org/?utm_source=chatgpt.com",
      "title": "Klingon Language Institute — Language Opens Worlds"
    }
  ],
  "timestamp": "2024-01-15T10:30:00.000Z",
  "url": "https://chatgpt.com/..."
}
```

## Usage in Your Application

### Python Example

```python
import requests
import json
import time

# Create request with search mode
response = requests.post(
    "https://chatgpt-relay-api.onrender.com/requests",
    headers={"X-API-Key": "your-api-key"},
    json={
        "prompt": "What are the latest developments in quantum computing?",
        "prompt_mode": "search"
    }
)

request_id = response.json()["id"]

# Poll for completion
while True:
    status_response = requests.get(
        f"https://chatgpt-relay-api.onrender.com/requests/{request_id}",
        headers={"X-API-Key": "your-api-key"}
    )
    
    data = status_response.json()
    
    if data["status"] == "completed":
        # Parse the response
        response_data = json.loads(data["response"])
        
        # Display main content
        print("Answer:")
        print(response_data["response"])
        
        # Display sources separately
        if response_data.get("sources"):
            print("\n📚 Sources:")
            for source in response_data["sources"]:
                print(f"  [{source['number']}] {source['title']}")
                print(f"      🔗 {source['url']}\n")
        break
    
    time.sleep(5)
```

### JavaScript Example

```javascript
// Fetch completed request
const response = await fetch(`https://chatgpt-relay-api.onrender.com/requests/${requestId}`, {
  headers: { 'X-API-Key': 'your-api-key' }
});

const data = await response.json();

if (data.status === 'completed') {
  const responseData = JSON.parse(data.response);
  
  // Display main content
  document.getElementById('answer').innerHTML = marked.parse(responseData.response);
  
  // Display sources separately
  if (responseData.sources) {
    const sourcesHTML = responseData.sources.map(source => `
      <div class="source">
        <span class="source-number">[${source.number}]</span>
        <a href="${source.url}" target="_blank">${source.title}</a>
      </div>
    `).join('');
    
    document.getElementById('sources').innerHTML = sourcesHTML;
  }
}
```

## Technical Implementation

### Source Pattern Recognition

The bookmarklet uses this regex pattern to detect source citations:

```javascript
const sourcePattern = /\[(\d+)\]:\s*(https?:\/\/[^\s]+)(?:\s+"([^"]+)"|(?:\s+[—\-]\s+|\s+)(.+?))?$/gm;
```

This matches:
- `[1]: URL "Title"` - Quoted title format
- `[2]: URL — Title` - Em-dash format
- `[3]: URL - Title` - Hyphen format  
- `[4]: URL Title` - Space-separated format

### Source Extraction Process

1. **Find all source citations** at the end of the response
2. **Extract** number, URL, and title from each
3. **Remove source lines** from content
4. **Clean up** trailing separators (`---`)
5. **Return** both cleaned content and sources array

## Benefits

### For Users
- ✅ Cleaner, more readable responses
- ✅ Easy access to source URLs for verification
- ✅ Professional presentation of citations

### For Developers
- ✅ Structured data for programmatic access
- ✅ No need to parse citations manually
- ✅ Easy to display sources in custom UI

### For Applications
- ✅ Better SEO with proper source attribution
- ✅ Compliance with content citation requirements
- ✅ Trust building through transparent sourcing

## When Are Sources Included?

Sources are most commonly included when:
- Using **search mode** (`prompt_mode: "search"`)
- Asking for research or fact-finding
- ChatGPT accesses web search results
- Questions about current events or recent information

Sources may **not** be included when:
- Using standard or study mode without search
- Asking general knowledge questions
- Requesting creative content or opinions

## Backward Compatibility

This feature is **fully backward compatible**:
- If no sources are present, `sources` will be `null`
- Existing applications continue to work unchanged
- The `response` field still contains the full text (clean version)

## Testing

To test the sources feature:

```bash
curl -X POST https://chatgpt-relay-api.onrender.com/requests \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What are the latest breakthroughs in AI research?",
    "prompt_mode": "search"
  }'
```

Then fetch the result and check for the `sources` array in the response.

## Troubleshooting

### Sources Not Being Detected

If sources aren't being extracted, check:
1. Is `prompt_mode` set to `"search"`?
2. Did ChatGPT actually provide sources?
3. Are the sources in the expected format?

### Debugging

The bookmarklet logs source extraction:
```
[AUTOMATED] Extracted 4 sources from response
```

Check the console logs to see if sources were detected.

## Future Enhancements

Potential improvements:
- Support for additional citation formats
- Extract inline citations `[1]` from content
- Link inline citations to sources array
- Deduplicate sources if repeated

---

**Version:** 1.0  
**Last Updated:** 2024  
**Status:** ✅ Production Ready

