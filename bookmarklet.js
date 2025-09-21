javascript:(async () => {
    console.log("🚀 ChatGPT Bookmarklet starting...");
    const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  
    const showToast = (message, type = "success") => {
      // For automated worker usage, reduce toast visibility and duration
      const isAutomated = typeof window !== "undefined" && Object.prototype.hasOwnProperty.call(window, "__chatgptBookmarkletPrompt");
      
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
        opacity: isAutomated ? "0.7" : "1", // Make less visible for automated usage
      });
      document.body.appendChild(toast);
      // Shorter duration for automated usage
      setTimeout(() => toast.remove(), isAutomated ? 2000 : 5000);
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
  
    // Try multiple selectors to detect ChatGPT UI
    const chatgptSelectors = [
      'main[id="main"]',
      'main',
      '[data-testid="conversation-turn-1"]',
      '[data-testid="conversation-turn-2"]',
      '.conversation',
      'div[role="main"]',
      '#__next',
      'body'
    ];
    
    let ready = null;
    for (const selector of chatgptSelectors) {
      ready = document.querySelector(selector);
      if (ready) {
        console.log(`✅ ChatGPT UI detected using selector: ${selector}`);
        break;
      }
    }
    
    if (!ready) {
      console.log("❌ ChatGPT UI not detected. Available selectors:");
      chatgptSelectors.forEach(selector => {
        const element = document.querySelector(selector);
        console.log(`  ${selector}: ${element ? "Found" : "Not found"}`);
      });
      alert("ChatGPT UI not detected on this page. Check console for details.");
      return;
    }
  
    const promptTextSource = typeof window !== "undefined" && Object.prototype.hasOwnProperty.call(window, "__chatgptBookmarkletPrompt")
      ? window.__chatgptBookmarkletPrompt
      : prompt("Prompt to send to ChatGPT:");
    if (typeof window !== "undefined" && Object.prototype.hasOwnProperty.call(window, "__chatgptBookmarkletPrompt")) {
      delete window.__chatgptBookmarkletPrompt;
    }
    const promptText =
      promptTextSource !== null && promptTextSource !== undefined
        ? String(promptTextSource)
        : "";
    if (!promptText) {
      return;
    }
  
    showToast("Sending prompt to ChatGPT...", "info");
  
    const waitForComposer = async () => {
      console.log("🔍 Looking for ChatGPT composer...");
      
      const composerSelectors = [
        'div[contenteditable="true"].ProseMirror',
        'div[contenteditable="true"]',
        'textarea[placeholder*="Ask"]',
        'textarea[placeholder*="Message"]',
        'input[type="text"]',
        '.composer-input',
        '[data-testid="composer-input"]'
      ];
      
      for (let i = 0; i < 40; i += 1) {
        // Debug every 10 iterations
        if (i % 10 === 0) {
          console.log(`🔍 Composer detection attempt ${i}:`);
          composerSelectors.forEach(selector => {
            const element = document.querySelector(selector);
            console.log(`  ${selector}: ${element ? "Found" : "Not found"}`);
          });
        }
        
        for (const selector of composerSelectors) {
          const node = document.querySelector(selector);
          if (node) {
            console.log(`✅ Composer found using selector: ${selector}`);
            return node;
          }
        }
        await sleep(250);
      }
      
      console.log("❌ Composer not found after 40 attempts");
      return null;
    };
  
    const composer = await waitForComposer();
    if (!composer) {
      alert(
        "Could not locate the ChatGPT composer. Try refreshing the page."
      );
      return;
    }
  
    composer.focus();
  
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
    ];
  
    let sendButton = null;
    for (const selector of sendButtonSelectors) {
      sendButton = document.querySelector(selector);
      if (sendButton) {
        break;
      }
    }
  
    if (!sendButton) {
      alert(
        "Prompt inserted, but no send button was found. Press Enter manually."
      );
      return;
    }
  
    sendButton.click();
  
    showToast("Prompt sent! Waiting for response...", "info");
  
    const waitForResponseMarker = async () => {
      console.log("🔍 Starting response detection...");
      
      for (let i = 0; i < 120; i += 1) {
        // Primary detection: Check if send button has changed from "Stop streaming" to "Start voice mode"
        const stopButton = document.querySelector(
          'button[data-testid="stop-button"]'
        );
        const voiceButton = document.querySelector(
          'button[data-testid="composer-speech-button"]'
        );
        
        // Debug logging every 10 iterations (every 2.5 seconds)
        if (i % 10 === 0) {
          console.log(`🔍 Detection attempt ${i}:`, {
            stopButton: stopButton ? "✅ Found" : "❌ Not found",
            voiceButton: voiceButton ? "✅ Found" : "❌ Not found",
            stopButtonDetails: stopButton ? {
              id: stopButton.id,
              ariaLabel: stopButton.getAttribute('aria-label'),
              testId: stopButton.getAttribute('data-testid')
            } : null,
            voiceButtonDetails: voiceButton ? {
              id: voiceButton.id,
              ariaLabel: voiceButton.getAttribute('aria-label'),
              testId: voiceButton.getAttribute('data-testid')
            } : null
          });
        }
        
        // Response is complete when stop button is gone and voice button is present
        if (!stopButton && voiceButton) {
          console.log("✅ Response complete detected! Stop button gone, voice button present");
          return voiceButton;
        }
        
        await sleep(250);
      }
      
      console.log("❌ Timeout: Could not detect response completion");
      return null;
    };
  
    const copyButton = await waitForResponseMarker();
    if (!copyButton) {
      showToast(
        "Timeout waiting for response. Response may still be generating.",
        "warning"
      );
      return;
    }
  
    showToast("Response complete! Waiting for text to load...", "info");
    await sleep(2000);
  
    const waitForResponseText = async () => {
      console.log("📝 Starting response text detection...");
      
      for (let i = 0; i < 20; i += 1) {
        // Try multiple selectors for response text
        const selectors = [
          ".markdown.prose",
          "[data-message-author-role='assistant'] .markdown",
          ".prose.markdown",
          "[data-testid='conversation-turn-3'] .markdown", // Often the latest response
          ".markdown"
        ];
        
        // Debug logging every 5 iterations (every 2.5 seconds)
        if (i % 5 === 0) {
          console.log(`📝 Text detection attempt ${i}:`);
          selectors.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            console.log(`  ${selector}: ${elements.length} elements found`);
            if (elements.length > 0) {
              const lastElement = elements[elements.length - 1];
              const text = lastElement.textContent.trim();
              console.log(`    Last element text length: ${text.length}, preview: "${text.substring(0, 100)}..."`);
            }
          });
        }
        
        for (const selector of selectors) {
          const elements = document.querySelectorAll(selector);
          // Get the last (most recent) element
          for (let j = elements.length - 1; j >= 0; j--) {
            const element = elements[j];
            const text = element.textContent.trim();
            if (text && text.length > 10) { // Ensure it's substantial content
              console.log(`✅ Response text found using selector: ${selector}, length: ${text.length}`);
              return text;
            }
          }
        }
        
        await sleep(500);
      }
      
      console.log("❌ Timeout: Could not find response text");
      return null;
    };
  
    const responseText = await waitForResponseText();
    if (!responseText) {
      showToast("Response text not found after waiting", "warning");
      return;
    }
  
    if (
      responseText &&
      !responseText.includes("window.__oai_") &&
      !responseText.includes("async()=>{") &&
      !responseText.includes("const sleep=")
    ) {
      const responsePayload = {
        prompt: promptText,
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
      console.log(`ChatGPT bookmarklet completed: ${filename}`);
    } else {
      showToast("No valid response text found", "warning");
    }
  })();

