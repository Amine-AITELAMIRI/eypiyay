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
    
    const isAutomated = typeof window !== "undefined" && Object.prototype.hasOwnProperty.call(window, "__chatgptBookmarkletPrompt");
    
    if (isAutomated) {
      console.log(`[AUTOMATED] Prompt received: ${promptTextSource}`);
      console.log(`[AUTOMATED] ChatGPT UI detected using selector: ${ready ? 'found' : 'not found'}`);
    }
    
    if (typeof window !== "undefined" && Object.prototype.hasOwnProperty.call(window, "__chatgptBookmarkletPrompt")) {
      delete window.__chatgptBookmarkletPrompt;
    }
    if (typeof window !== "undefined" && Object.prototype.hasOwnProperty.call(window, "__chatgptBookmarkletPromptMode")) {
      delete window.__chatgptBookmarkletPromptMode;
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
    if (promptMode && (promptMode === "search" || promptMode === "study")) {
      const modeCommand = promptMode === "search" ? "/sear" : "/stu";
      
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

    // Prepend markdown formatting instruction to make responses easier to parse for API clients
    const markdownInstruction = "System: You are ChatGPT.\nPlease obey these rules:\n1. All your output must be in *raw Markdown syntax*. Do **not** render headings, bold, italics, bullet lists, or code blocks—show the literal Markdown (with `#`, `*`, `[ ]` etc.).\n2. Wrap the *entire* response inside a fenced code block using three backticks ```\n3. If you include any code blocks inside your content, use a different fence so that the outer fence is not broken (for example ~~~ or another distinctive delimiter).\n4. Do not add any extra explanation about formatting. Only provide the content requested in raw Markdown.\n\n";
    const finalPromptText = markdownInstruction + promptText;
  
    try {
      const range = document.createRange();
      range.selectNodeContents(composer);
      range.deleteContents();
      const selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
      document.execCommand("insertText", false, finalPromptText);
    } catch (error) {
      composer.innerHTML = "";
      composer.textContent = finalPromptText;
      const inputEvent = new InputEvent("input", {
        data: finalPromptText,
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
      while (true) {
        // Check for the stop button (square icon) - indicates still processing
        const stopButton = document.querySelector('button[data-testid="stop-button"]');
        
        // Check for the voice mode button (sound waves icon) - indicates finished
        const voiceButton = document.querySelector('button[data-testid="composer-speech-button"]');
        
        // If we have the voice button and no stop button, ChatGPT has finished processing
        if (voiceButton && !stopButton) {
          console.log("ChatGPT finished processing - voice button detected");
          return voiceButton;
        }
        
        // If we still have the stop button, ChatGPT is still processing
        if (stopButton) {
          console.log("ChatGPT still processing - stop button detected");
          await sleep(250);
          continue;
        }
        
        await sleep(250);
      }
    };
  
    const copyButton = await waitForResponseMarker();
    
    if (isAutomated) {
      console.log("[AUTOMATED] Response detected, waiting for text to load");
    }
  
    showToast("Response detected! Waiting for text to load...", "info");
    await sleep(2000);
  
    const cleanResponseText = (text) => {
      // Remove common UI artifacts that appear in ChatGPT responses
      const artifacts = [
        /^mdCopy code\s*/gi,           // Handle "mdCopy code" at start
        /^markdownCopy code\s*/gi,     // Handle "markdownCopy code" at start
        /^Copy code\s*/gi,             // Handle "Copy code" at start
        /^markdown\s*/gi,              // Handle "markdown" at start
        /^Copy\s*/gi,                  // Handle "Copy" at start
        /^code\s*/gi,                  // Handle "code" at start
        /\s*mdCopy code\s*$/gi,        // Handle "mdCopy code" at end
        /\s*Copy code\s*$/gi,          // Handle "Copy code" at end
        /\s*markdownCopy code\s*$/gi,  // Handle "markdownCopy code" at end
        /\s*Copy\s*$/gi,               // Handle "Copy" at end
        /\s*markdown\s*$/gi,           // Handle "markdown" at end
        /\s*code\s*$/gi                // Handle "code" at end
      ];
      
      let cleanedText = text;
      artifacts.forEach(pattern => {
        cleanedText = cleanedText.replace(pattern, '');
      });
      
      return cleanedText.trim();
    };

    const waitForResponseText = async () => {
      for (let i = 0; i < 200; i += 1) {
        // Try multiple selectors for response text
        const selectors = [
          ".markdown.prose",
          "[data-message-author-role='assistant'] .markdown",
          ".prose.markdown",
          "[data-testid='conversation-turn-3'] .markdown", // Often the latest response
          ".markdown"
        ];
        
        for (const selector of selectors) {
          const elements = document.querySelectorAll(selector);
          // Get the last (most recent) element
          for (let j = elements.length - 1; j >= 0; j--) {
            const element = elements[j];
            const rawText = element.textContent.trim();
            if (rawText && rawText.length > 10) { // Ensure it's substantial content
              const cleanedText = cleanResponseText(rawText);
              if (cleanedText && cleanedText.length > 5) { // Ensure cleaned text is still substantial
                return cleanedText;
              }
            }
          }
        }
        
        await sleep(500);
      }
      return null;
    };
  
    const responseText = await waitForResponseText();
    if (!responseText) {
      if (isAutomated) {
        console.log("[AUTOMATED] ERROR: Response text not found");
        throw new Error("Response text not found after waiting");
      }
      showToast("Response text not found after waiting", "warning");
      return;
    }
    
    if (isAutomated) {
      console.log(`[AUTOMATED] Response text found (${responseText.length} characters)`);
    }
  
    if (
      responseText &&
      !responseText.includes("window.__oai_") &&
      !responseText.includes("async()=>{") &&
      !responseText.includes("const sleep=")
    ) {
      const responsePayload = {
        prompt: promptText, // Store original prompt without markdown instruction
        response: responseText,
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

