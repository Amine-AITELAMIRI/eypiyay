javascript:(async () => {
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
  
    const ready = document.querySelector('main[id="main"]');
    if (!ready) {
      alert("ChatGPT UI not detected on this page.");
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
      for (let i = 0; i < 40; i += 1) {
        const node = document.querySelector(
          'div[contenteditable="true"].ProseMirror'
        );
        if (node) {
          return node;
        }
        await sleep(250);
      }
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
      for (let i = 0; i < 120; i += 1) {
        // Look for the complete action buttons container - this indicates response is fully finished
        const actionButtonsContainer = document.querySelector(
          'div.flex.min-h-\\[46px\\].justify-start div.touch\\:-me-2.touch\\:-ms-3\\.5.-ms-2\\.5.-me-1.flex.flex-wrap.items-center.gap-y-4.p-1.select-none'
        );
        
        // Also check for the action buttons container with a more flexible selector
        const flexibleContainer = document.querySelector(
          'div[class*="flex"][class*="min-h-"] div[class*="flex"][class*="items-center"][class*="gap-y-4"]'
        );
        
        // Check for all the expected action buttons within the container
        const copyButton = document.querySelector(
          'button[data-testid="copy-turn-action-button"]'
        );
        const goodResponseButton = document.querySelector(
          'button[data-testid="good-response-turn-action-button"]'
        );
        const badResponseButton = document.querySelector(
          'button[data-testid="bad-response-turn-action-button"]'
        );
        const shareButton = document.querySelector(
          'button[aria-label="Share"]'
        );
        const moreActionsButton = document.querySelector(
          'button[aria-label="More actions"]'
        );
        
        // Check if we have the complete set of action buttons
        const hasCompleteActionSet = copyButton && goodResponseButton && badResponseButton && shareButton && moreActionsButton;
        
        // Also check for stop button to ensure generation has stopped
        const stopButton = document.querySelector(
          'button[data-testid="stop-generating-button"]'
        );
        
        // Response is complete if we have the action buttons container and all expected buttons, and no stop button
        if ((actionButtonsContainer || flexibleContainer) && hasCompleteActionSet && !stopButton) {
          return actionButtonsContainer || flexibleContainer || copyButton;
        }
        
        // Fallback: Check for regenerate button as an indicator (older detection method)
        const regenerateButton = document.querySelector(
          'button[data-testid="regenerate-response-button"]'
        );
        if (regenerateButton && !stopButton) {
          return regenerateButton;
        }
        
        // Additional fallback: Just copy button without stop button
        if (copyButton && !stopButton) {
          return copyButton;
        }
        
        await sleep(250);
      }
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
  
    showToast("Response detected! Waiting for text to load...", "info");
    await sleep(2000);
  
    const waitForResponseText = async () => {
      for (let i = 0; i < 20; i += 1) {
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
            const text = element.textContent.trim();
            if (text && text.length > 10) { // Ensure it's substantial content
              return text;
            }
          }
        }
        
        await sleep(500);
      }
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

