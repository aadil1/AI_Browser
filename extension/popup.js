/**
 * SafeBrowse AI Security - Popup Script
 * v1.0.0 - Production Ready
 * 
 * Handles user interaction, API calls, and Markdown rendering
 * Supports enterprise mode and scan-only mode
 */

// DOM Elements
const queryInput = document.getElementById("query");
const askBtn = document.getElementById("ask");
const btnText = askBtn.querySelector(".btn-text");
const btnLoading = askBtn.querySelector(".btn-loading");
const statusEl = document.getElementById("status");
const answerContainer = document.getElementById("answer-container");
const answerEl = document.getElementById("answer");
const riskScoreEl = document.getElementById("risk-score");

// State
let isLoading = false;
let settings = {};

/**
 * Load settings from storage
 */
async function loadSettings() {
    try {
        const response = await chrome.runtime.sendMessage({ type: "GET_SETTINGS" });
        settings = response || {};
        updateUIForMode();
    } catch (error) {
        console.warn("Failed to load settings:", error);
    }
}

/**
 * Update UI based on mode (enterprise/scan-only)
 */
function updateUIForMode() {
    if (settings.enterpriseMode) {
        // Enterprise mode UI
        queryInput.placeholder = "Enterprise mode: Scan-only enabled";
        queryInput.disabled = true;
        btnText.textContent = "Scan Page";

        // Add enterprise badge
        addEnterpriseBadge();
    } else if (settings.scanOnly) {
        // Scan-only mode
        queryInput.placeholder = "Scan-only mode enabled";
        queryInput.disabled = true;
        btnText.textContent = "Scan Page";
    } else {
        // Normal mode
        queryInput.placeholder = "Ask about this page...";
        queryInput.disabled = false;
        btnText.textContent = "Ask SafeBrowse";
    }
}

/**
 * Add enterprise badge to UI
 */
function addEnterpriseBadge() {
    const header = document.querySelector(".header h1") || document.querySelector("h1");
    if (header && !document.querySelector(".enterprise-badge")) {
        const badge = document.createElement("span");
        badge.className = "enterprise-badge";
        badge.textContent = "Enterprise";
        badge.style.cssText = `
            background: #6366f1;
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 10px;
            margin-left: 8px;
            vertical-align: middle;
        `;
        header.appendChild(badge);
    }
}

/**
 * Simple Markdown to HTML converter
 */
function renderMarkdown(text) {
    if (!text) return "";

    let html = text
        // Escape HTML
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        // Headers
        .replace(/^### (.+)$/gm, "<h3>$1</h3>")
        .replace(/^## (.+)$/gm, "<h2>$1</h2>")
        .replace(/^# (.+)$/gm, "<h1>$1</h1>")
        // Bold and Italic
        .replace(/\*\*\*(.+?)\*\*\*/g, "<strong><em>$1</em></strong>")
        .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
        .replace(/\*(.+?)\*/g, "<em>$1</em>")
        // Code blocks
        .replace(/```(\w*)\n([\s\S]*?)```/g, "<pre><code>$2</code></pre>")
        // Inline code
        .replace(/`([^`]+)`/g, "<code>$1</code>")
        // Blockquotes
        .replace(/^> (.+)$/gm, "<blockquote>$1</blockquote>")
        // Unordered lists
        .replace(/^- (.+)$/gm, "<li>$1</li>")
        .replace(/(<li>.*<\/li>\n?)+/g, "<ul>$&</ul>")
        // Links
        .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>')
        // Paragraphs
        .replace(/\n\n/g, "</p><p>")
        // Line breaks
        .replace(/\n/g, "<br>");

    return `<p>${html}</p>`;
}

/**
 * Update UI state
 */
function setLoading(loading) {
    isLoading = loading;
    askBtn.disabled = loading;

    if (loading) {
        btnText.style.display = "none";
        btnLoading.style.display = "inline-flex";
        if (settings.enterpriseMode || settings.scanOnly) {
            showStatus("Scanning page for security threats...", "loading");
        } else {
            showStatus("Analyzing page and generating response...", "loading");
        }
    } else {
        btnText.style.display = "inline";
        btnLoading.style.display = "none";
    }
}

/**
 * Show status message
 */
function showStatus(message, type = "loading") {
    statusEl.textContent = message;
    statusEl.className = `status visible ${type}`;
}

/**
 * Hide status
 */
function hideStatus() {
    statusEl.className = "status";
}

/**
 * Update risk score display
 */
function updateRiskScore(score) {
    if (score === null || score === undefined) {
        riskScoreEl.textContent = "--";
        riskScoreEl.className = "risk-score";
        return;
    }

    const percentage = (score * 100).toFixed(0);
    riskScoreEl.textContent = `${percentage}%`;

    if (score < 0.3) {
        riskScoreEl.className = "risk-score safe";
    } else if (score < 0.5) {
        riskScoreEl.className = "risk-score warning";
    } else {
        riskScoreEl.className = "risk-score danger";
    }
}

/**
 * Show answer - with optional markdown rendering
 */
function showAnswer(content, useMarkdown = true) {
    if (useMarkdown) {
        answerEl.innerHTML = renderMarkdown(content);
    } else {
        answerEl.textContent = content;
    }
    answerContainer.style.display = "block";
}

/**
 * Show scan-only result (for enterprise/scan-only mode)
 */
function showScanResult(response) {
    const isSafe = response.isSafe || response.status === "safe";
    const riskScore = response.riskScore || response.risk_score;

    updateRiskScore(riskScore);

    let resultHtml = "";

    if (isSafe) {
        resultHtml = `
            <div class="scan-result safe">
                <div class="scan-icon">✓</div>
                <div class="scan-title">SAFE</div>
                <div class="scan-detail">No security threats detected</div>
            </div>
        `;
        showStatus("Page passed security scan", "success");
    } else {
        resultHtml = `
            <div class="scan-result blocked">
                <div class="scan-icon">🚫</div>
                <div class="scan-title">BLOCKED</div>
                <div class="scan-detail">${response.reason || "Security threat detected"}</div>
            </div>
        `;
        showStatus("Page blocked for security reasons", "warning");
    }

    // Add request ID for audit
    if (response.requestId) {
        resultHtml += `<div class="request-id">Request ID: ${response.requestId}</div>`;
    }

    // Add policy violations
    if (response.policyViolations && response.policyViolations.length > 0) {
        resultHtml += `<div class="policy-violations">Policy: ${response.policyViolations.join(", ")}</div>`;
    }

    // Add explanations
    if (response.explanations && response.explanations.length > 0) {
        resultHtml += `<div class="explanations">${response.explanations.slice(0, 3).join("<br>")}</div>`;
    }

    answerEl.innerHTML = resultHtml;
    answerContainer.style.display = "block";
}

/**
 * Hide answer
 */
function hideAnswer() {
    answerContainer.style.display = "none";
    answerEl.innerHTML = "";
}

/**
 * Handle ask button click
 */
async function handleAsk() {
    const query = queryInput.value.trim();

    // In enterprise/scan-only mode, query is not required
    if (!settings.enterpriseMode && !settings.scanOnly && !query) {
        showStatus("Please enter a question.", "warning");
        return;
    }

    if (isLoading) return;

    setLoading(true);
    hideAnswer();
    updateRiskScore(null);

    try {
        // Get current tab
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

        if (!tab) {
            throw new Error("No active tab found.");
        }

        // Choose message type based on mode
        const messageType = (settings.enterpriseMode || settings.scanOnly) ? "SCAN_ONLY" : "SAFE_ASK";

        // Send message to background script
        const response = await chrome.runtime.sendMessage({
            type: messageType,
            query: query || "Analyze this page",
            tabId: tab.id,
        });

        if (chrome.runtime.lastError) {
            throw new Error(chrome.runtime.lastError.message);
        }

        if (!response) {
            throw new Error("No response from backend. Is the server running?");
        }

        // Handle scan-only response
        if (response.scanOnly || settings.enterpriseMode || settings.scanOnly) {
            showScanResult(response);
            return;
        }

        // Update risk score
        updateRiskScore(response.risk_score);

        // Handle response status
        if (response.status === "ok") {
            hideStatus();
            showAnswer(response.answer, true);
        } else if (response.status === "blocked") {
            showStatus("⚠️ Page blocked for safety reasons", "warning");
            showAnswer(response.reason || "This page may contain malicious instructions.", false);
        } else {
            showStatus("❌ " + (response.reason || "Unknown error"), "error");
        }

    } catch (error) {
        console.error("Error:", error);
        showStatus("❌ " + error.message, "error");
    } finally {
        setLoading(false);
    }
}

// Event Listeners
askBtn.addEventListener("click", handleAsk);

queryInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleAsk();
    }
});

// Add settings link
function addSettingsLink() {
    const footer = document.createElement("div");
    footer.className = "popup-footer";
    footer.innerHTML = `<a href="#" id="open-settings">⚙️ Settings</a>`;
    footer.style.cssText = `
        text-align: center;
        padding: 8px;
        font-size: 12px;
        border-top: 1px solid #3f3f46;
        margin-top: 12px;
    `;
    document.body.appendChild(footer);

    document.getElementById("open-settings").addEventListener("click", (e) => {
        e.preventDefault();
        chrome.runtime.openOptionsPage();
    });
}

// Initialize
loadSettings();
addSettingsLink();
queryInput.focus();
