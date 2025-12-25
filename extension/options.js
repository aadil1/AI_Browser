// SafeBrowse Options Page

const DEFAULTS = {
    apiKey: "test-key",
    environment: "dev",
    scanOnly: false,
    enterpriseMode: false,
    allowedDomains: "",
};

// Load settings on page load
async function loadSettings() {
    const data = await chrome.storage.sync.get(Object.keys(DEFAULTS));

    document.getElementById("apiKey").value = data.apiKey || DEFAULTS.apiKey;
    document.getElementById("environment").value = data.environment || DEFAULTS.environment;
    document.getElementById("scanOnly").checked = data.scanOnly ?? DEFAULTS.scanOnly;
    document.getElementById("enterpriseMode").checked = data.enterpriseMode ?? DEFAULTS.enterpriseMode;
    document.getElementById("allowedDomains").value = data.allowedDomains || DEFAULTS.allowedDomains;

    // Update UI based on enterprise mode
    updateEnterpriseUI(data.enterpriseMode);
}

// Update UI when enterprise mode changes
function updateEnterpriseUI(enabled) {
    const scanOnlyCheckbox = document.getElementById("scanOnly");
    if (enabled) {
        scanOnlyCheckbox.checked = true;
        scanOnlyCheckbox.disabled = true;
    } else {
        scanOnlyCheckbox.disabled = false;
    }
}

// Save settings
async function saveSettings() {
    const apiKey = document.getElementById("apiKey").value.trim();
    const environment = document.getElementById("environment").value;
    const scanOnly = document.getElementById("scanOnly").checked;
    const enterpriseMode = document.getElementById("enterpriseMode").checked;
    const allowedDomains = document.getElementById("allowedDomains").value.trim();

    // Validate API key format
    if (apiKey && !apiKey.match(/^(sb_|test-|demo-)/)) {
        showStatus("Invalid API key format", "error");
        return;
    }

    await chrome.storage.sync.set({
        apiKey,
        environment,
        scanOnly: enterpriseMode ? true : scanOnly, // Enterprise forces scan-only
        enterpriseMode,
        allowedDomains,
    });

    showStatus("Settings saved successfully!", "success");
}

// Reset to defaults
async function resetSettings() {
    if (!confirm("Reset all settings to defaults?")) return;

    await chrome.storage.sync.set(DEFAULTS);
    await loadSettings();
    showStatus("Settings reset to defaults", "success");
}

// Show status message
function showStatus(message, type) {
    const statusEl = document.getElementById("status");
    statusEl.textContent = message;
    statusEl.className = `status ${type}`;

    setTimeout(() => {
        statusEl.textContent = "";
        statusEl.className = "status";
    }, 3000);
}

// Event listeners
document.getElementById("save").addEventListener("click", saveSettings);
document.getElementById("reset").addEventListener("click", resetSettings);

document.getElementById("enterpriseMode").addEventListener("change", (e) => {
    updateEnterpriseUI(e.target.checked);
});

// Initialize
loadSettings();
