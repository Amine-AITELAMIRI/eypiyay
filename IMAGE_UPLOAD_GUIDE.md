# Image Upload Feature Guide

This guide explains how to use the new image upload capability in the ChatGPT Relay API.

## Overview

The API now supports sending images along with text prompts to ChatGPT. Images can be provided as:
- **Public URLs** (e.g., `https://example.com/image.jpg`)
- **Base64-encoded data URIs** (e.g., `data:image/png;base64,...`)

## Setup for Existing Installations

If you already have the database set up, you need to run the migration to add the `image_url` column:

### Option 1: Supabase Dashboard
1. Go to your Supabase SQL Editor: https://app.supabase.com/project/YOUR_PROJECT_ID/sql
2. Copy and paste the contents of `supabase_migration_add_image_url.sql`
3. Run the migration

### Option 2: Quick SQL Command
```sql
ALTER TABLE requests ADD COLUMN IF NOT EXISTS image_url TEXT;
```

## API Usage

### Basic Image Upload (URL)

```python
import requests

response = requests.post(
    "https://chatgpt-relay-api.onrender.com/requests",
    headers={"X-API-Key": "your-api-key"},
    json={
        "prompt": "What's in this image?",
        "image_url": "https://example.com/photo.jpg"
    }
)

request_id = response.json()["id"]
print(f"Request created: {request_id}")
```

### Image Upload with Base64

```python
import requests
import base64

# Read and encode image file
with open("screenshot.png", "rb") as image_file:
    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    image_data_url = f"data:image/png;base64,{encoded_string}"

response = requests.post(
    "https://chatgpt-relay-api.onrender.com/requests",
    headers={"X-API-Key": "your-api-key"},
    json={
        "prompt": "Analyze this screenshot",
        "image_url": image_data_url
    }
)
```

### Combining with Other Features

```python
import requests

response = requests.post(
    "https://chatgpt-relay-api.onrender.com/requests",
    headers={"X-API-Key": "your-api-key"},
    json={
        "prompt": "Provide a detailed architectural analysis of this building",
        "image_url": "https://example.com/building.jpg",
        "model_mode": "thinking",  # Use thinking mode for detailed analysis
        "webhook_url": "https://your-server.com/webhook"
    }
)
```

## How It Works

1. **API Request**: You send a request with both `prompt` and `image_url` fields
2. **Database Storage**: The request is stored in the database with the image URL
3. **Worker Processing**: The worker retrieves the request and passes both prompt and image URL to the bookmarklet
4. **Image Upload**: The bookmarklet:
   - Converts the image URL/base64 to a File object
   - Locates ChatGPT's file upload input
   - Simulates a file upload by programmatically setting the file
   - Waits for the upload to complete
5. **Prompt Submission**: After the image is uploaded, the text prompt is sent
6. **Response Collection**: ChatGPT processes both the image and text, and the response is captured

## Supported Image Formats

The following image formats are supported:
- **PNG** (`.png`)
- **JPEG** (`.jpg`, `.jpeg`)
- **GIF** (`.gif`)
- **WebP** (`.webp`)

## Size Limitations

- **URL Images**: No size limit on the API side, but ChatGPT has its own upload limits (typically 20MB)
- **Base64 Images**: Be mindful of HTTP request size limits (typically 10-100MB depending on your server configuration)

## Best Practices

### 1. Use URLs for Large Images
For images larger than a few MB, it's better to host them and use URLs rather than base64 encoding:

```python
# Good for large images
response = requests.post(url, json={
    "prompt": "Analyze this high-resolution photo",
    "image_url": "https://your-cdn.com/large-image.jpg"
})
```

### 2. Use Base64 for Small Images
For smaller images (< 1MB) or when you don't have a hosting solution:

```python
# Good for small images or screenshots
with open("small-screenshot.png", "rb") as f:
    encoded = base64.b64encode(f.read()).decode()
    image_data_url = f"data:image/png;base64,{encoded}"
    
response = requests.post(url, json={
    "prompt": "What's in this screenshot?",
    "image_url": image_data_url
})
```

### 3. Combine with Thinking Mode
For complex image analysis, use `"model_mode": "thinking"`:

```python
response = requests.post(url, json={
    "prompt": "Provide a detailed analysis of the design principles",
    "image_url": "https://example.com/design.png",
    "model_mode": "thinking"  # More thorough analysis
})
```

### 4. Use Search Mode for Research
When analyzing images for research purposes:

```python
response = requests.post(url, json={
    "prompt": "Research the historical context of this artwork",
    "image_url": "https://example.com/artwork.jpg",
    "prompt_mode": "search"  # Activates search capabilities
})
```

## Troubleshooting

### Image Upload Fails

**Problem**: The bookmarklet reports "Could not find file upload input"

**Solution**: 
- Ensure you're using the latest version of the bookmarklet
- Make sure ChatGPT's interface is fully loaded before the worker processes the request
- Check that the ChatGPT page hasn't been updated with a new UI structure

### Image Not Displaying in ChatGPT

**Problem**: The prompt is sent but the image doesn't appear

**Solutions**:
- **For URLs**: Ensure the URL is publicly accessible (not behind authentication)
- **For Base64**: Verify the image encoding is correct and includes the proper data URI prefix
- Check that the image format is supported by ChatGPT

### Large Images Cause Timeouts

**Problem**: Requests with large images timeout

**Solutions**:
- Resize images before sending them
- Use image compression tools
- Host large images on a CDN and use URLs instead of base64
- Increase the worker timeout if you control the infrastructure

### CORS Errors with Image URLs

**Problem**: The bookmarklet can't fetch the image from the URL

**Solutions**:
- Ensure the image host has proper CORS headers
- Use base64 encoding instead of URLs for problematic sources
- Host images on a CORS-friendly service

## Example Use Cases

### 1. Screenshot Analysis
```python
import requests
import base64
from PIL import Image
import io

# Capture and optimize screenshot
img = Image.open("screenshot.png")
img.thumbnail((1920, 1080))  # Resize if too large

buffer = io.BytesIO()
img.save(buffer, format="PNG")
encoded = base64.b64encode(buffer.getvalue()).decode()

response = requests.post(url, json={
    "prompt": "Analyze the UI/UX of this interface and suggest improvements",
    "image_url": f"data:image/png;base64,{encoded}",
    "model_mode": "thinking"
})
```

### 2. Document OCR and Analysis
```python
response = requests.post(url, json={
    "prompt": "Extract and summarize the text from this document",
    "image_url": "https://example.com/document-scan.jpg"
})
```

### 3. Product Image Description
```python
response = requests.post(url, json={
    "prompt": "Write a detailed product description for this item",
    "image_url": "https://example.com/product.jpg",
    "webhook_url": "https://your-ecommerce-site.com/webhook"
})
```

### 4. Architectural Analysis
```python
response = requests.post(url, json={
    "prompt": "Identify the architectural style and provide historical context",
    "image_url": "https://example.com/building.jpg",
    "prompt_mode": "search",
    "model_mode": "thinking"
})
```

## Technical Details

### Database Schema Changes
The `requests` table now includes:
```sql
image_url TEXT  -- Stores the image URL or base64 data URI
```

### API Response Structure
The response now includes the `image_url` field:
```json
{
  "id": 123,
  "prompt": "What's in this image?",
  "image_url": "https://example.com/photo.jpg",
  "status": "pending",
  ...
}
```

### Worker Behavior
The worker now:
1. Checks for `image_url` in the job
2. If present, sets `window.__chatgptBookmarkletImageUrl` 
3. The bookmarklet detects this and uploads the image before sending the prompt

## Migration Checklist

If you're upgrading from a previous version:

- [ ] Run the database migration (`supabase_migration_add_image_url.sql`)
- [ ] Update your server code (already done in this commit)
- [ ] Update your worker script (already done in this commit)
- [ ] Update the bookmarklet (already done in this commit)
- [ ] Test with a simple image URL
- [ ] Test with a base64-encoded image
- [ ] Verify webhook payloads include `image_url`

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the API_USAGE_GUIDE.md for complete API documentation
3. Check worker logs for detailed error messages
4. Verify the bookmarklet is running the latest version

---

**Feature Added**: 2024  
**Compatible With**: ChatGPT web interface (chatgpt.com)  
**Status**: ✅ Production Ready

