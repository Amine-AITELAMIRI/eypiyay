# ChatGPT Data Extractor

Extract ChatGPT conversation data from localStorage using Firefox DevTools Protocol.

## Overview

This tool connects to a running Firefox instance and extracts data saved by the ChatGPT bookmarklet. It reads localStorage data directly from the ChatGPT tab without requiring file access or browser extensions.

## Prerequisites

1. **Python 3.7+**
2. **Firefox browser** with remote debugging enabled
3. **ChatGPT bookmarklet** (already saved data to localStorage)

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Launch Firefox with Remote Debugging

```bash
firefox --start-debugger-server=9222
```

**Alternative methods:**

**Windows:**
```bash
"C:\Program Files\Mozilla Firefox\firefox.exe" --start-debugger-server=9222
```

**macOS:**
```bash
/Applications/Firefox.app/Contents/MacOS/firefox --start-debugger-server=9222
```

**Linux:**
```bash
firefox --start-debugger-server=9222
```

### 3. Open ChatGPT

Navigate to ChatGPT in the Firefox instance you just launched.

## Usage

### Basic Usage

```bash
python chatgpt_data_extractor.py
```

This will:
- Connect to Firefox's debugging port
- Find the ChatGPT tab automatically
- Extract all localStorage data saved by the bookmarklet
- Display the data in a readable format

### Export Options

**Export to JSON:**
```bash
python chatgpt_data_extractor.py --export-json responses.json
```

**Export to CSV:**
```bash
python chatgpt_data_extractor.py --export-csv responses.csv
```

**Custom Debug Port:**
```bash
python chatgpt_data_extractor.py --port 9223
```

**Quiet Mode (no output except errors):**
```bash
python chatgpt_data_extractor.py --quiet --export-json data.json
```

## How It Works

1. **Connection**: Connects to Firefox's DevTools Protocol via WebSocket
2. **Tab Detection**: Automatically finds the ChatGPT tab by URL pattern
3. **Data Extraction**: Executes JavaScript to read localStorage data
4. **Parsing**: Filters and parses ChatGPT response data
5. **Export**: Provides multiple export formats (JSON, CSV)

## Data Structure

The extracted data includes:

```json
{
  "prompt": "Your question to ChatGPT",
  "response": "ChatGPT's response",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "url": "https://chat.openai.com/..."
}
```

## Troubleshooting

### "No ChatGPT tab found"
- Make sure ChatGPT is open in the Firefox instance with remote debugging
- Check that the URL contains `chat.openai.com` or `chatgpt.com`

### "Failed to connect to tab"
- Verify Firefox is running with `--start-debugger-server=9222`
- Check that the port isn't blocked by firewall
- Try a different port if 9222 is in use

### "Failed to read localStorage"
- Make sure you've used the bookmarklet to save data
- Check that the ChatGPT tab is fully loaded
- Try refreshing the ChatGPT page

### Connection Issues
- Ensure Firefox was launched with the correct flags
- Check that no other tools are using the debugging port
- Restart Firefox with debugging enabled

## Security Notes

- This tool only reads data from localStorage
- No data is sent to external servers
- All communication is local between Python and Firefox
- The Firefox instance must be launched with debugging enabled

## Example Output

```
🚀 ChatGPT Data Extractor (Firefox)
==================================================
Make sure Firefox is running with:
firefox --start-debugger-server=9222

🔍 Looking for ChatGPT tab...
✅ Found ChatGPT tab: ChatGPT
   URL: https://chat.openai.com/...
✅ Connected to ChatGPT tab
📊 Extracting localStorage data...
📁 Found 15 localStorage entries
📋 File list contains 5 entries
✅ Extracted 5 ChatGPT responses

📊 Found 5 ChatGPT responses:
================================================================================

📝 Response #1
   🕒 Time: 2024-01-15T10:30:00.000Z
   🌐 URL: https://chat.openai.com/...
   ❓ Prompt: How do I implement a REST API?
   💬 Response: To implement a REST API, you'll need to follow these key principles...
----------------------------------------
```

## License

This project is open source and available under the MIT License.
