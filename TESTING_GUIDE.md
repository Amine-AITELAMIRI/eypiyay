# 🧪 Complete Testing Guide

## Step-by-Step Testing Process

### **Phase 1: Firefox Setup**

#### 1.1 Close All Firefox Instances
```powershell
# Kill any running Firefox processes
taskkill /f /im firefox.exe
```

#### 1.2 Launch Firefox with Remote Debugging
```powershell
& "C:\Program Files\Mozilla Firefox\firefox.exe" --start-debugger-server=9222
```

**Alternative method if the above doesn't work:**
```powershell
# Try with different flags
& "C:\Program Files\Mozilla Firefox\firefox.exe" --start-debugger-server=9222 --new-instance
```

#### 1.3 Verify Firefox is Running
- You should see a Firefox window open
- Check if the debugging server is running:
```powershell
netstat -an | findstr :9222
```
You should see something like: `TCP 0.0.0.0:9222 0.0.0.0:0 LISTENING`

### **Phase 2: ChatGPT Setup**

#### 2.1 Open ChatGPT
- In the Firefox window, navigate to: `https://chat.openai.com`
- Log in to your account
- Make sure you can see the ChatGPT interface

#### 2.2 Test Connection
Run our test script:
```powershell
python test_setup.py
```

You should see:
```
✅ websocket-client is installed
✅ requests is installed
✅ Firefox debugging server is running!
📊 Found X open tabs
🎯 Found 1 ChatGPT tab(s):
   1. ChatGPT - https://chat.openai.com/...
✅ WebSocket URL available: ws://127.0.0.1:9222/...
```

### **Phase 3: Bookmarklet Testing**

#### 3.1 Install the Bookmarklet
1. Copy the entire content of `bookmarklet.js`
2. Create a new bookmark in Firefox:
   - Right-click bookmark bar → "Add Bookmark"
   - Name: "ChatGPT Data Extractor"
   - URL: Paste the entire bookmarklet code (starts with `javascript:(async () => {`)
3. Save the bookmark

#### 3.2 Test the Bookmarklet
1. **In ChatGPT**, ask a simple question like: "What is 2+2?"
2. **Wait for the response** to complete
3. **Click your bookmarklet** in the bookmark bar
4. **Enter a test prompt** when prompted (e.g., "Test prompt for data extraction")
5. **Wait for the process** to complete
6. **You should see**:
   - Toast notifications showing progress
   - A modal dialog with download/copy options
   - Success message: "Response saved as chatgpt-response-..."

### **Phase 4: Data Extraction Testing**

#### 4.1 Run the Extractor
```powershell
python chatgpt_data_extractor.py
```

Expected output:
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
📁 Found X localStorage entries
📋 File list contains 1 entries
✅ Extracted 1 ChatGPT responses

📊 Found 1 ChatGPT responses:
================================================================================

📝 Response #1
   🕒 Time: 2024-01-15T10:30:00.000Z
   🌐 URL: https://chat.openai.com/...
   ❓ Prompt: Test prompt for data extraction
   💬 Response: What is 2+2?...
----------------------------------------

💡 Use --export-json or --export-csv to save data to files
```

#### 4.2 Test Export Functionality
```powershell
# Export to JSON
python chatgpt_data_extractor.py --export-json test_data.json

# Export to CSV
python chatgpt_data_extractor.py --export-csv test_data.csv
```

### **Phase 5: Troubleshooting**

#### Common Issues and Solutions

**Issue: "Cannot connect to Firefox debugging server"**
- Solution: Make sure Firefox was launched with `--start-debugger-server=9222`
- Check: `netstat -an | findstr :9222` should show the port is listening

**Issue: "No ChatGPT tab found"**
- Solution: Make sure ChatGPT is open in the Firefox instance with debugging enabled
- Check: The URL should contain `chat.openai.com`

**Issue: "Failed to read localStorage"**
- Solution: Make sure you've used the bookmarklet to save data first
- Check: The ChatGPT tab should be fully loaded

**Issue: "No valid response text found"**
- Solution: The bookmarklet might have detected its own code in the response
- Try: Ask a different question and use the bookmarklet again

#### Debug Commands

```powershell
# Check if Firefox is running
tasklist | findstr firefox

# Check debugging port
netstat -an | findstr :9222

# Test HTTP connection to debugging server
curl http://localhost:9222/json/list

# Check Python packages
python -c "import websocket, requests; print('All packages OK')"
```

### **Phase 6: Full Workflow Test**

1. **Launch Firefox**: `& "C:\Program Files\Mozilla Firefox\firefox.exe" --start-debugger-server=9222`
2. **Open ChatGPT**: Navigate to `https://chat.openai.com`
3. **Ask a question**: "Explain quantum computing in simple terms"
4. **Use bookmarklet**: Click your bookmarklet, enter "Test quantum explanation"
5. **Extract data**: `python chatgpt_data_extractor.py --export-json quantum_test.json`
6. **Verify file**: Check that `quantum_test.json` was created with your data

## Success Criteria

✅ Firefox launches with debugging enabled  
✅ ChatGPT tab is detected  
✅ Bookmarklet saves data to localStorage  
✅ Python script extracts the data  
✅ Export functions work correctly  
✅ Data structure is correct (prompt, response, timestamp, URL)

## Next Steps After Testing

Once everything works:
1. Use the bookmarklet regularly to collect ChatGPT conversations
2. Run the extractor periodically to export your data
3. Process the exported data for analysis or backup
4. Consider automating the extraction process

---

**Need Help?** If any step fails, check the troubleshooting section above or run `python test_setup.py` to diagnose the issue.
