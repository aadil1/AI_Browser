/**
 * SafeBrowse AI Security - Background Service Worker
 * v1.0.0 - Production Ready
 * 
 * Handles communication between popup and backend API
 * Supports enterprise mode, scan-only mode, and secure API key storage
 */

// Defaults (fallback only)
const DEFAULTS = {
    apiKey: "test-key",
    environment: "dev",
    scanOnly: false,
    enterpriseMode: false,
    allowedDomains: "",
};

const ENVIRONMENTS = {
    prod: "https://ai-browser-5d4p.onrender.com",
    dev: "http://127.0.0.1:8000",
};

const REQUEST_TIMEOUT = 30000; // 30 seconds
const MAX_HTML_SIZE = 5_000_000; // 5 MB

/**
 * Get settings from chrome.storage
 */
async function getSettings() {
    try {
        const data = await chrome.storage.sync.get(Object.keys(DEFAULTS));
        return { ...DEFAULTS, ...data };
    } catch (error) {
        console.warn("Failed to get settings, using defaults:", error);
        return DEFAULTS;
    }
}

/**
 * Get backend URL based on environment setting
 */
async function getBackendUrl() {
    const settings = await getSettings();
    return ENVIRONMENTS[settings.environment] || ENVIRONMENTS.dev;
}

/**
 * Get API key from storage
 */
async function getApiKey() {
    const settings = await getSettings();
    return settings.apiKey || DEFAULTS.apiKey;
}

/**
 * Check if domain is allowed (for enterprise mode)
 */
async function isDomainAllowed(url) {
    const settings = await getSettings();

    if (!settings.allowedDomains || settings.allowedDomains.trim() === "") {
        return true; // No restrictions
    }

    const allowedList = settings.allowedDomains
        .split("\n")
        .map(d => d.trim().toLowerCase())
        .filter(d => d.length > 0);

    if (allowedList.length === 0) return true;

    const urlObj = new URL(url);
    const domain = urlObj.hostname.toLowerCase();

    return allowedList.some(allowed =>
        domain === allowed || domain.endsWith("." + allowed)
    );
}

/**
 * Fetch with timeout wrapper
 */
async function fetchWithTimeout(url, options, timeout = REQUEST_TIMEOUT) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
        const response = await fetch(url, {
            ...options,
            signal: controller.signal,
        });
        return response;
    } finally {
        clearTimeout(timeoutId);
    }
}

/**
 * Get page content from tab
 */
async function getPageContent(tabId) {
    try {
        const [{ result }] = await chrome.scripting.executeScript({
            target: { tabId },
            func: () => ({
                html: document.documentElement.outerHTML,
                url: window.location.href,
            }),
        });
        return result;
    } catch (error) {
        console.error("Failed to get page content:", error);
        throw new Error("Could not access page content. Try refreshing the page.");
    }
}

/**
 * Scan HTML only (no AI answer) - for enterprise/scan-only mode
 */
async function scanHtmlOnly(tabId) {
    const pageContent = await getPageContent(tabId);
    const backendUrl = await getBackendUrl();
    const apiKey = await getApiKey();

    if (!pageContent) {
        throw new Error("Could not retrieve page content.");
    }

    if (pageContent.html.length > MAX_HTML_SIZE) {
        throw new Error("Page too large to analyze safely (max 5MB).");
    }

    try {
        const res = await fetchWithTimeout(`${backendUrl}/scan-html`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-API-Key": apiKey,
            },
            body: JSON.stringify({
                url: pageContent.url,
                html: pageContent.html,
            }),
        });

        if (res.status === 401) {
            throw new Error("Invalid API key. Please update in Settings.");
        }

        if (res.status === 429) {
            throw new Error("Rate limit reached. Try again later.");
        }

        if (!res.ok) {
            const errorText = await res.text();
            throw new Error(`Server error (${res.status}): ${errorText}`);
        }

        const result = await res.json();

        // Format for enterprise mode
        return {
            status: result.is_safe ? "safe" : "blocked",
            isSafe: result.is_safe,
            riskScore: result.risk_score,
            reason: result.reason || "Content scanned",
            explanations: result.explanations || [],
            policyViolations: result.policy_violations || [],
            requestId: result.request_id,
            scanOnly: true,
        };

    } catch (err) {
        if (err.name === "AbortError") {
            throw new Error("Request timed out. Please try again.");
        }
        if (err.message.includes("Failed to fetch")) {
            throw new Error("Could not connect to backend. Is the server running?");
        }
        throw err;
    }
}

/**
 * Main function to ask about a page (with AI answer)
 */
async function safeAskPage(tabId, query) {
    const settings = await getSettings();

    // Check enterprise/scan-only mode
    if (settings.enterpriseMode || settings.scanOnly) {
        return await scanHtmlOnly(tabId);
    }

    // Get page content
    const pageContent = await getPageContent(tabId);
    const backendUrl = await getBackendUrl();
    const apiKey = await getApiKey();

    if (!pageContent) {
        throw new Error("Could not retrieve page content.");
    }

    // Check domain allowlist
    if (settings.enterpriseMode) {
        const allowed = await isDomainAllowed(pageContent.url);
        if (!allowed) {
            return {
                status: "blocked",
                isSafe: false,
                reason: "Domain not in allowlist",
                scanOnly: true,
            };
        }
    }

    // Check HTML size limit
    if (pageContent.html.length > MAX_HTML_SIZE) {
        throw new Error("Page too large to analyze safely (max 5MB).");
    }

    // Send to backend
    try {
        const res = await fetchWithTimeout(`${backendUrl}/safe-ask`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-API-Key": apiKey,
            },
            body: JSON.stringify({
                url: pageContent.url,
                html: pageContent.html,
                query,
            }),
        });

        if (res.status === 401) {
            throw new Error("Invalid API key. Please update in Settings.");
        }

        if (res.status === 429) {
            throw new Error("Rate limit reached. Try again later.");
        }

        if (!res.ok) {
            const errorText = await res.text();
            throw new Error(`Server error (${res.status}): ${errorText}`);
        }

        return await res.json();

    } catch (err) {
        if (err.name === "AbortError") {
            throw new Error("Request timed out. Please try again.");
        }
        if (err.message.includes("Failed to fetch")) {
            throw new Error("Could not connect to backend. Is the server running?");
        }
        throw err;
    }
}

/**
 * Message handler
 */
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    if (msg.type === "SAFE_ASK") {
        const { query, tabId } = msg;

        safeAskPage(tabId, query)
            .then(sendResponse)
            .catch((err) => {
                console.error("Safe Ask Error:", err);
                sendResponse({
                    status: "error",
                    reason: err.message || "Unknown error occurred",
                });
            });

        // Keep message channel open for async response
        return true;
    }

    if (msg.type === "SCAN_ONLY") {
        const { tabId } = msg;

        scanHtmlOnly(tabId)
            .then(sendResponse)
            .catch((err) => {
                console.error("Scan Error:", err);
                sendResponse({
                    status: "error",
                    reason: err.message || "Unknown error occurred",
                });
            });

        return true;
    }

    if (msg.type === "GET_SETTINGS") {
        getSettings().then(sendResponse);
        return true;
    }
});

// Log when service worker starts
console.log("SafeBrowse AI Security service worker started (v1.0.0)");
