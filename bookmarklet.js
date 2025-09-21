javascript:(async () => {
    const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  
    const showToast = (message, type = "success") => {
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
      });
      document.body.appendChild(toast);
      setTimeout(() => toast.remove(), 5000);
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
  
    const promptText = prompt("Prompt to send to ChatGPT:");
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
        const copyButton = document.querySelector(
          'button[data-testid="copy-turn-action-button"]'
        );
        if (copyButton) {
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
        const markdownDiv = document.querySelector(".markdown.prose");
        if (markdownDiv && markdownDiv.textContent.trim()) {
          return markdownDiv.textContent.trim();
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
  
      showToast(`Response saved as ${filename}`, "success");
  
      if (navigator.clipboard && window.isSecureContext) {
        try {
          await navigator.clipboard.writeText(responseText);
          showToast("Response also copied to clipboard!", "success");
        } catch (error) {
          console.log("Clipboard write failed:", error);
        }
      }
  
      const modal = document.createElement("div");
      modal.style.cssText =
        "position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.8);z-index:10000;display:flex;align-items:center;justify-content:center;padding:20px;box-sizing:border-box";
      const content = document.createElement("div");
      content.style.cssText =
        "background:white;padding:20px;border-radius:8px;max-width:80%;max-height:80%;overflow-y:auto;position:relative";
      const closeBtn = document.createElement("button");
      closeBtn.textContent = "�";
      closeBtn.style.cssText =
        "position:absolute;top:10px;right:15px;background:none;border:none;font-size:24px;cursor:pointer;color:#666";
      closeBtn.onclick = () => document.body.removeChild(modal);
      const title = document.createElement("h3");
      title.textContent = "Response Saved - Download JSON";
      title.style.cssText = "margin:0 0 15px 0;color:#333";
      const info = document.createElement("div");
      info.innerHTML = `<p><strong>Filename:</strong> ${filename}</p><p><strong>Prompt:</strong> ${promptText}</p><p><strong>Response:</strong> ${responseText.substring(0, 100)}...</p>`;
      info.style.cssText =
        "background:#f8f9fa;padding:15px;border-radius:4px;margin:0 0 15px 0;border:1px solid #dee2e6";
      const downloadBtn = document.createElement("button");
      downloadBtn.textContent = "Download JSON File";
      downloadBtn.style.cssText =
        "background:#0f766e;color:white;border:none;padding:10px 20px;border-radius:4px;cursor:pointer;font-size:14px;margin-right:10px";
      downloadBtn.onclick = () => {
        const blob = new Blob([jsonData], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showToast("JSON file downloaded!", "success");
      };
      const copyJsonBtn = document.createElement("button");
      copyJsonBtn.textContent = "Copy JSON";
      copyJsonBtn.style.cssText =
        "background:#2563eb;color:white;border:none;padding:10px 20px;border-radius:4px;cursor:pointer;font-size:14px";
      copyJsonBtn.onclick = () => {
        if (navigator.clipboard) {
          navigator.clipboard.writeText(jsonData);
          showToast("JSON copied to clipboard!", "success");
        } else {
          showToast("Clipboard not available", "warning");
        }
      };
      const buttonContainer = document.createElement("div");
      buttonContainer.style.cssText =
        "display:flex;gap:10px;justify-content:flex-end";
      buttonContainer.appendChild(downloadBtn);
      buttonContainer.appendChild(copyJsonBtn);
      content.appendChild(closeBtn);
      content.appendChild(title);
      content.appendChild(info);
      content.appendChild(buttonContainer);
      modal.appendChild(content);
      document.body.appendChild(modal);
  
      const handleEscape = (event) => {
        if (event.key === "Escape") {
          document.body.removeChild(modal);
          document.removeEventListener("keydown", handleEscape);
        }
      };
      document.addEventListener("keydown", handleEscape);
    } else {
      showToast("No valid response text found", "warning");
    }
  })();