javascript:(async () => {
    const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  
    const showToast = (message, type = "success") => {
      // For automated worker usage, reduce toast visibility and duration
      const isAutomated = typeof window !== "undefined" && Object.prototype.hasOwnProperty.call(window, "__chatgptBookmarkletPrompt");
      
      // Log for debugging in automated mode
      if (isAutomated) {
        console.log(`[AUTOMATED] Toast: ${message} (${type})`);
      }
      
      const toast = document.createElement("div");
      toast.textContent = message;
      const colors = {
        success: "#0f766e",
        error: "#dc2626",
        info: "#2563eb",
        warning: "#d97706",
      };
      Object.assign(toast.style, {
        position: "fixed",
        bottom: "16px",
        right: "16px",
        zIndex: 9999,
        background: colors[type] || colors.success,
        color: "#fff",
        padding: "10px 14px",
        borderRadius: "6px",
        fontSize: "13px",
        boxShadow: "0 4px 12px rgba(0,0,0,0.2)",
        fontFamily: "system-ui, sans-serif",
        maxWidth: "320px",
        wordWrap: "break-word",
        opacity: isAutomated ? "0.8" : "1", // Slightly less visible for automated usage
      });
      document.body.appendChild(toast);
      // Shorter duration for automated usage
      setTimeout(() => toast.remove(), isAutomated ? 3000 : 5000);
    };
  
    const API_ENDPOINT = "";
    const API_KEY = "";
    const EXTRA_HEADERS = {};
  
    const sendToApi = async (payload) => {
      if (!API_ENDPOINT) {
        console.warn("API endpoint not configured; skipping forward.");
        return null;
      }
      try {
        const headers = {
          "Content-Type": "application/json",
          ...EXTRA_HEADERS,
        };
        if (API_KEY) {
          headers.Authorization = `Bearer ${API_KEY}`;
        }
        const response = await fetch(API_ENDPOINT, {
          method: "POST",
          headers,
          body: JSON.stringify(payload),
          mode: "cors",
          credentials: "omit",
        });
  
        const responseBody = await response.text();
        let parsed;
        try {
          parsed = responseBody ? JSON.parse(responseBody) : null;
        } catch (err) {
          parsed = responseBody;
        }
  
        if (!response.ok) {
          const errorMessage =
            (parsed && parsed.error) ||
            `API responded with status ${response.status}`;
          throw new Error(errorMessage);
        }
  
        showToast("Response forwarded to API server", "success");
        return parsed;
      } catch (error) {
        console.error("Failed to forward to API", error);
        showToast(`API forward failed: ${error.message}`, "error");
        return null;
      }
    };
  
    // More flexible ChatGPT UI detection - try multiple selectors
    const chatgptSelectors = [
      'main[id="main"]',           // Original selector
      'main',                      // Simple main element
      '[data-testid="chat-page"]', // ChatGPT chat page
      '.chat-container',           // Chat container
      '#__next',                   // Next.js root
      'body'                       // Fallback to body
    ];
    
    let ready = null;
    for (const selector of chatgptSelectors) {
      ready = document.querySelector(selector);
      if (ready) {
        console.log(`ChatGPT UI detected using selector: ${selector}`);
        break;
      }
    }
    
    if (!ready) {
      alert("ChatGPT UI not detected on this page. Please ensure you're on the ChatGPT website (chatgpt.com) and try again.");
      return;
    }

  
    const promptTextSource = typeof window !== "undefined" && Object.prototype.hasOwnProperty.call(window, "__chatgptBookmarkletPrompt")
      ? window.__chatgptBookmarkletPrompt
      : prompt("Prompt to send to ChatGPT:");
    
    const promptMode = typeof window !== "undefined" && Object.prototype.hasOwnProperty.call(window, "__chatgptBookmarkletPromptMode")
      ? window.__chatgptBookmarkletPromptMode
      : null;
    
    const imageUrl = typeof window !== "undefined" && Object.prototype.hasOwnProperty.call(window, "__chatgptBookmarkletImageUrl")
      ? window.__chatgptBookmarkletImageUrl
      : null;
    
    const isAutomated = typeof window !== "undefined" && Object.prototype.hasOwnProperty.call(window, "__chatgptBookmarkletPrompt");
    
    if (isAutomated) {
      console.log(`[AUTOMATED] Prompt received: ${promptTextSource}`);
      console.log(`[AUTOMATED] ChatGPT UI detected using selector: ${ready ? 'found' : 'not found'}`);
      if (imageUrl) {
        console.log(`[AUTOMATED] Image URL received: ${imageUrl.substring(0, 100)}...`);
      }
    }
    
    if (typeof window !== "undefined" && Object.prototype.hasOwnProperty.call(window, "__chatgptBookmarkletPrompt")) {
      delete window.__chatgptBookmarkletPrompt;
    }
    if (typeof window !== "undefined" && Object.prototype.hasOwnProperty.call(window, "__chatgptBookmarkletPromptMode")) {
      delete window.__chatgptBookmarkletPromptMode;
    }
    if (typeof window !== "undefined" && Object.prototype.hasOwnProperty.call(window, "__chatgptBookmarkletImageUrl")) {
      delete window.__chatgptBookmarkletImageUrl;
    }
    const promptText =
      promptTextSource !== null && promptTextSource !== undefined
        ? String(promptTextSource)
        : "";
    if (!promptText) {
      if (isAutomated) {
        console.log("[AUTOMATED] No prompt text provided, exiting");
      }
      return;
    }
  
    showToast("Sending prompt to ChatGPT...", "info");
  
    // Helper function to convert image URL to File object
    const imageUrlToFile = async (url) => {
      try {
        let blob;
        
        if (url.startsWith('data:')) {
          // Handle base64 data URL - convert directly without fetch
          const base64Data = url.split(',')[1];
          const mimeType = url.split(',')[0].split(':')[1].split(';')[0];
          
          // Convert base64 to binary
          const binaryString = atob(base64Data);
          const bytes = new Uint8Array(binaryString.length);
          for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
          }
          
          blob = new Blob([bytes], { type: mimeType });
        } else {
          // Handle regular URL - fetch it
          const response = await fetch(url);
          if (!response.ok) {
            throw new Error(`Failed to fetch image: ${response.statusText}`);
          }
          blob = await response.blob();
        }
        
        // Extract filename and extension
        let filename = 'image.png';
        if (!url.startsWith('data:')) {
          try {
            const urlObj = new URL(url);
            const pathname = urlObj.pathname;
            const parts = pathname.split('/');
            const lastPart = parts[parts.length - 1];
            if (lastPart && lastPart.includes('.')) {
              filename = lastPart;
            }
          } catch (e) {
            // Use default filename if URL parsing fails
          }
        } else {
          // For base64, extract MIME type
          const mimeMatch = url.match(/^data:([^;]+);/);
          if (mimeMatch) {
            const mime = mimeMatch[1];
            const ext = mime.split('/')[1] || 'png';
            filename = `image.${ext}`;
          }
        }
        
        return new File([blob], filename, { type: blob.type });
      } catch (error) {
        console.error('[IMAGE] Failed to convert URL to file:', error);
        throw error;
      }
    };
    
    // Helper function to upload image to ChatGPT
    const uploadImage = async (imageFile) => {
      try {
        if (isAutomated) {
          console.log(`[AUTOMATED] Uploading image: ${imageFile.name}`);
        }
        showToast("Uploading image...", "info");
        
        // Try multiple approaches to find file input
        let fileInput = null;
        
        // Method 1: Look for visible file inputs
        const visibleInputs = document.querySelectorAll('input[type="file"]:not([style*="display: none"])');
        for (const input of visibleInputs) {
          if (!input.disabled && (input.accept.includes('image') || input.accept === '*' || input.accept === '')) {
            fileInput = input;
            console.log('[IMAGE] Found visible file input:', input);
            break;
          }
        }
        
        // Method 2: Look for hidden file inputs
        if (!fileInput) {
          const hiddenInputs = document.querySelectorAll('input[type="file"]');
          for (const input of hiddenInputs) {
            if (!input.disabled && (input.accept.includes('image') || input.accept === '*' || input.accept === '')) {
              fileInput = input;
              console.log('[IMAGE] Found hidden file input:', input);
              break;
            }
          }
        }
        
        // Method 3: Look for any file input and make it visible
        if (!fileInput) {
          const anyInput = document.querySelector('input[type="file"]');
          if (anyInput) {
            fileInput = anyInput;
            // Make it visible temporarily
            fileInput.style.display = 'block';
            fileInput.style.position = 'absolute';
            fileInput.style.top = '0';
            fileInput.style.left = '0';
            fileInput.style.opacity = '0.1';
            console.log('[IMAGE] Made file input visible:', fileInput);
          }
        }
        
        // Method 4: Try to trigger file upload via click simulation
        if (!fileInput) {
          console.log('[IMAGE] No file input found, trying click simulation');
          
          // Look for any button or element that might trigger file upload
          const uploadTriggers = [
            'button[aria-label*="upload"]',
            'button[aria-label*="attach"]',
            'button[aria-label*="file"]',
            'button[title*="upload"]',
            'button[title*="attach"]',
            '[data-testid*="upload"]',
            '[data-testid*="attach"]',
            '.upload-button',
            '.attach-button',
            'button:has(svg[data-testid="paperclip"])',
            'button:has(svg[data-testid="attach"])'
          ];
          
          let uploadButton = null;
          for (const selector of uploadTriggers) {
            uploadButton = document.querySelector(selector);
            if (uploadButton) {
              console.log('[IMAGE] Found upload trigger:', selector);
              break;
            }
          }
          
          if (uploadButton) {
            // Click the upload button to reveal file input
            uploadButton.click();
            await sleep(1000);
            
            // Now look for the file input again
            const newInputs = document.querySelectorAll('input[type="file"]');
            for (const input of newInputs) {
              if (!input.disabled && (input.accept.includes('image') || input.accept === '*' || input.accept === '')) {
                fileInput = input;
                console.log('[IMAGE] Found file input after button click:', input);
                break;
              }
            }
          }
          
          // Method 5: Create a new file input if still none found
          if (!fileInput) {
            console.log('[IMAGE] Still no file input found, creating new one');
            fileInput = document.createElement('input');
            fileInput.type = 'file';
            fileInput.accept = 'image/*';
            fileInput.style.display = 'none';
            document.body.appendChild(fileInput);
          }
        }
        
        if (!fileInput) {
          throw new Error('Could not find or create file upload input');
        }
        
        // Create a DataTransfer object to simulate file selection
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(imageFile);
        fileInput.files = dataTransfer.files;
        
        // Trigger change event to notify ChatGPT
        const changeEvent = new Event('change', { bubbles: true });
        fileInput.dispatchEvent(changeEvent);
        
        // Also try input event
        const inputEvent = new Event('input', { bubbles: true });
        fileInput.dispatchEvent(inputEvent);
        
        // Try click event to trigger any click handlers
        const clickEvent = new Event('click', { bubbles: true });
        fileInput.dispatchEvent(clickEvent);
        
        console.log('[IMAGE] File uploaded, waiting for processing...');
        
        // Wait for upload to be processed
        await sleep(3000);
        
        if (isAutomated) {
          console.log('[AUTOMATED] Image upload completed');
        }
        showToast("Image uploaded successfully", "success");
      } catch (error) {
        console.error('[IMAGE] Failed to upload image:', error);
        showToast(`Image upload failed: ${error.message}`, "error");
        throw error;
      }
    };
    
    // Handle image upload if provided
    if (imageUrl) {
      try {
        const imageFile = await imageUrlToFile(imageUrl);
        await uploadImage(imageFile);
        
        // Wait a bit longer for ChatGPT to process the image
        if (isAutomated) {
          console.log('[AUTOMATED] Waiting for ChatGPT to process the uploaded image...');
        }
        await sleep(5000); // Wait 5 seconds for image processing
        
      } catch (error) {
        if (isAutomated) {
          console.log(`[AUTOMATED] ERROR: Image upload failed - ${error.message}`);
          throw new Error(`Image upload failed: ${error.message}`);
        }
        alert(`Failed to upload image: ${error.message}`);
        return;
      }
    }
  
    const waitForComposer = async () => {
      for (let i = 0; i < 40; i += 1) {
        // Try multiple selectors for the current ChatGPT interface
        const selectors = [
          'div[contenteditable="true"].ProseMirror#prompt-textarea', // Current ChatGPT interface
          'div[contenteditable="true"].ProseMirror',                 // Fallback to any ProseMirror
          'textarea[name="prompt-textarea"]',                        // Fallback textarea
          'div[contenteditable="true"]',                             // Any contenteditable div
          'textarea[placeholder*="Ask"]',                            // Textarea with "Ask" placeholder
          'textarea[data-virtualkeyboard="true"]'                    // Textarea with virtual keyboard
        ];
        
        for (const selector of selectors) {
          const node = document.querySelector(selector);
          if (node) {
            console.log(`Composer found using selector: ${selector}`);
            return node;
          }
        }
        await sleep(250);
      }
      return null;
    };
  
    const composer = await waitForComposer();
    if (!composer) {
      if (isAutomated) {
        console.log("[AUTOMATED] ERROR: Could not locate the ChatGPT composer");
        throw new Error("Could not locate the ChatGPT composer. Try refreshing the page.");
      }
      alert(
        "Could not locate the ChatGPT composer. Try refreshing the page."
      );
      return;
    }
    
    if (isAutomated) {
      console.log("[AUTOMATED] Composer found, inserting prompt");
    }
  
    composer.focus();
  
    // Handle special prompt modes
    if (promptMode && (promptMode === "search" || promptMode === "study" || promptMode === "deep")) {
      const modeCommand = promptMode === "search" ? "/sear" : (promptMode === "study" ? "/stu" : "/deep");
      
      if (isAutomated) {
        console.log(`[AUTOMATED] Applying prompt mode: ${promptMode} (typing: ${modeCommand})`);
      }
      
      try {
        const range = document.createRange();
        range.selectNodeContents(composer);
        range.deleteContents();
        const selection = window.getSelection();
        selection.removeAllRanges();
        selection.addRange(range);
        document.execCommand("insertText", false, modeCommand);
      } catch (error) {
        composer.innerHTML = "";
        composer.textContent = modeCommand;
        const inputEvent = new InputEvent("input", {
          data: modeCommand,
          bubbles: true,
          composed: true,
        });
        composer.dispatchEvent(inputEvent);
      }
      
      // Wait a moment for the mode command to be processed
      await sleep(200);
      
      // Press Enter to activate the mode
      const enterEvent = new KeyboardEvent("keydown", {
        key: "Enter",
        code: "Enter",
        keyCode: 13,
        which: 13,
        bubbles: true,
        composed: true,
      });
      composer.dispatchEvent(enterEvent);
      
      // Wait for the mode to be activated
      await sleep(500);
    }

    // Send the prompt as-is without markdown formatting instruction
    // This allows ChatGPT to respond naturally and we'll use the copy button to get the full response
    try {
      const range = document.createRange();
      range.selectNodeContents(composer);
      range.deleteContents();
      const selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
      document.execCommand("insertText", false, promptText);
    } catch (error) {
      composer.innerHTML = "";
      composer.textContent = promptText;
      const inputEvent = new InputEvent("input", {
        data: promptText,
        bubbles: true,
        composed: true,
      });
      composer.dispatchEvent(inputEvent);
    }
  
    await sleep(150);
  
    const sendButtonSelectors = [
      'button[data-testid="composer-send-button"]',
      'button[data-testid="send-button"]',
      'button[aria-label*="Send"]',
      'button[type="submit"]',
      'button[class*="composer"]', // ChatGPT composer buttons
      'button[class*="send"]',     // Any button with "send" in class
      'form button:not([type="button"])', // Submit button in form
      'button:not([type="button"])'       // Any button that's not explicitly type="button"
    ];
  
    let sendButton = null;
    for (const selector of sendButtonSelectors) {
      sendButton = document.querySelector(selector);
      if (sendButton) {
        break;
      }
    }
  
    if (!sendButton) {
      if (isAutomated) {
        console.log("[AUTOMATED] ERROR: No send button found");
        throw new Error("Prompt inserted, but no send button was found. Press Enter manually.");
      }
      alert(
        "Prompt inserted, but no send button was found. Press Enter manually."
      );
      return;
    }

    if (isAutomated) {
      console.log("[AUTOMATED] Send button found, clicking");
    }
    sendButton.click();
  
    showToast("Prompt sent! Waiting for response...", "info");
    
    // Add a delay before starting to monitor the submit button
    await sleep(1000);
  
    const waitForResponseMarker = async () => {
      let noStopButtonCount = 0;
      const requiredNoStopButtonCount = 4; // Wait for 4 consecutive checks without stop button
      
      while (true) {
        // Check for the stop button (square icon) - indicates still processing
        const stopButton = document.querySelector('button[data-testid="stop-button"]');
        
        // If we still have the stop button, ChatGPT is still processing
        if (stopButton) {
          console.log("ChatGPT still processing - stop button detected");
          noStopButtonCount = 0; // Reset counter
          await sleep(250);
          continue;
        }
        
        // No stop button found - increment counter
        noStopButtonCount++;
        
        if (noStopButtonCount >= requiredNoStopButtonCount) {
          console.log(`ChatGPT finished processing - stop button absent for ${noStopButtonCount} checks`);
          return true;
        }
        
        // Check for the voice mode button (sound waves icon) as confirmation
        const voiceButton = document.querySelector('button[data-testid="composer-speech-button"]');
        if (voiceButton) {
          console.log("ChatGPT finished processing - voice button detected");
          return voiceButton;
        }
        
        if (isAutomated) {
          console.log(`Waiting for response completion (no stop button count: ${noStopButtonCount}/${requiredNoStopButtonCount})`);
        }
        
        await sleep(250);
      }
    };
  
    const copyButton = await waitForResponseMarker();
    
    if (isAutomated) {
      console.log("[AUTOMATED] Response detected, waiting for text to load");
    }
  
    showToast("Response detected! Waiting for copy button...", "info");
    await sleep(2000); // Increased wait time for response to fully render
  
    // Find and click the copy button to get the response text
    const findAndClickCopyButton = async () => {
      if (isAutomated) {
        console.log("[AUTOMATED] Looking for copy button...");
      }
      
      for (let i = 0; i < 40; i += 1) {
        // Try multiple selectors for the copy button
        const copyButtonSelectors = [
          'button[data-testid="copy-turn-action-button"]',  // Primary selector
          'button[aria-label="Copy"]',                      // Fallback by aria-label
          'button[aria-label*="Copy"]',                     // Partial match
          'button:has(svg):not([data-testid="stop-button"])', // Button with SVG (but not stop button)
        ];
        
        for (const selector of copyButtonSelectors) {
          const buttons = document.querySelectorAll(selector);
          
          // Get the last (most recent) copy button
          if (buttons.length > 0) {
            const copyButton = buttons[buttons.length - 1];
            
            if (isAutomated) {
              console.log(`[AUTOMATED] Found copy button using selector: ${selector}`);
            }
            
            // Click the copy button
            copyButton.click();
            
            if (isAutomated) {
              console.log("[AUTOMATED] Copy button clicked, waiting for clipboard...");
            }
            
            // Wait for the clipboard operation to complete
            await sleep(1500); // Increased wait time for clipboard to populate
            
            return true;
          }
        }
        
        if (isAutomated && i % 5 === 0) {
          console.log(`[AUTOMATED] Copy button not found yet... attempt ${i}/40`);
        }
        
        await sleep(250);
      }
      
      if (isAutomated) {
        console.log("[AUTOMATED] ERROR: Copy button not found after waiting");
      }
      return false;
    };
  
    const copyButtonClicked = await findAndClickCopyButton();
    
    if (!copyButtonClicked) {
      if (isAutomated) {
        console.log("[AUTOMATED] ERROR: Could not find copy button");
        throw new Error("Could not find copy button to get response");
      }
      showToast("Could not find copy button", "error");
      return;
    }
    
    // Read from clipboard
    let responseText = null;
    try {
      if (isAutomated) {
        console.log("[AUTOMATED] Reading from clipboard...");
      }
      
      responseText = await navigator.clipboard.readText();
      
      if (isAutomated) {
        console.log(`[AUTOMATED] Successfully read ${responseText.length} characters from clipboard`);
      }
    } catch (error) {
      if (isAutomated) {
        console.log(`[AUTOMATED] ERROR: Failed to read clipboard: ${error.message}`);
        throw new Error(`Failed to read clipboard: ${error.message}`);
      }
      showToast(`Failed to read clipboard: ${error.message}`, "error");
      return;
    }
    if (!responseText || responseText.trim().length === 0) {
      if (isAutomated) {
        console.log(`[AUTOMATED] ERROR: Clipboard is empty or contains only whitespace. Length: ${responseText ? responseText.length : 0}, Trimmed: ${responseText ? responseText.trim().length : 0}`);
        console.log(`[AUTOMATED] Clipboard content: "${responseText}"`);
        throw new Error("Clipboard is empty or response text not found");
      }
      showToast("Clipboard is empty or response text not found", "warning");
      return;
    }
    
    if (isAutomated) {
      console.log(`[AUTOMATED] Response text captured from clipboard (${responseText.length} characters)`);
    }
    
    // Parse sources from the response if present
    const parseSourcesFromResponse = (text) => {
      const result = {
        content: text,
        sources: []
      };
      
      // Look for source citations pattern at the end of the response
      // Pattern: [number]: URL "title" or [number]: URL — title
      const sourcePattern = /\[(\d+)\]:\s*(https?:\/\/[^\s]+)(?:\s+"([^"]+)"|(?:\s+[—\-]\s+|\s+)(.+?))?$/gm;
      
      let match;
      const foundSources = [];
      const sourceLines = [];
      
      while ((match = sourcePattern.exec(text)) !== null) {
        const [fullMatch, number, url, titleQuoted, titleDash] = match;
        const title = titleQuoted || titleDash || url;
        
        foundSources.push({
          number: parseInt(number),
          url: url.trim(),
          title: title.trim()
        });
        
        sourceLines.push(fullMatch);
      }
      
      if (foundSources.length > 0) {
        // Remove source citations from content
        let cleanedContent = text;
        sourceLines.forEach(line => {
          cleanedContent = cleanedContent.replace(line, '');
        });
        
        // Also remove the empty lines and "---" separator if present
        cleanedContent = cleanedContent.replace(/\n*---\n*$/m, '');
        cleanedContent = cleanedContent.trim();
        
        result.content = cleanedContent;
        result.sources = foundSources.sort((a, b) => a.number - b.number);
        
        if (isAutomated) {
          console.log(`[AUTOMATED] Extracted ${foundSources.length} sources from response`);
        }
      }
      
      return result;
    };
  
    if (
      responseText &&
      !responseText.includes("window.__oai_") &&
      !responseText.includes("async()=>{") &&
      !responseText.includes("const sleep=")
    ) {
      // Parse response and sources separately
      const parsed = parseSourcesFromResponse(responseText);
      
      const responsePayload = {
        prompt: promptText, // Store original prompt without markdown instruction
        response: parsed.content,
        sources: parsed.sources.length > 0 ? parsed.sources : null,
        timestamp: new Date().toISOString(),
        url: window.location.href,
      };
  
      await sendToApi(responsePayload);
  
      const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
      const filename = `chatgpt-response-${timestamp}.json`;
      const jsonData = JSON.stringify(responsePayload, null, 2);
  
      localStorage.setItem(filename, jsonData);
      const existingFiles = JSON.parse(
        localStorage.getItem("chatgpt-files") || "[]"
      );
      existingFiles.push(filename);
      localStorage.setItem("chatgpt-files", JSON.stringify(existingFiles));
  
      // For automated worker usage, just show a brief success message
      showToast(`Response saved as ${filename}`, "success");
      
      // Log completion for worker detection
      if (isAutomated) {
        console.log(`[AUTOMATED] SUCCESS: Response saved as ${filename}`);
      }
      console.log(`ChatGPT bookmarklet completed: ${filename}`);
    } else {
      showToast("No valid response text found", "warning");
    }
  })();

