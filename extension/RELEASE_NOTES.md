# SafeBrowse Extension v1.0.0 — Release Notes

## 🚀 What's New

### Secure API Key Storage
- API keys now stored securely in Chrome sync storage
- No more hardcoded credentials
- Keys sync across devices

### Options Page
- New settings UI for configuration
- Set API key without touching code
- Switch between dev/prod environments

### Enterprise Mode
- Strict policy enforcement
- Scan-only (no AI answers)
- Domain allowlist support
- Audit-ready request IDs

### Scan-Only Mode
- Security scanning without AI responses
- Faster, lighter footprint
- Perfect for compliance workflows

### Improved Error Handling
- Clear messages for 401 (invalid key)
- Clear messages for 429 (rate limit)
- Graceful timeout handling

---

## 🔒 Security Improvements

| Feature | Description |
|---------|-------------|
| No hardcoded keys | API key in chrome.storage |
| Fail-closed | Errors always block |
| Request IDs | Every scan logged |
| Domain allowlist | Enterprise control |

---

## 🛠️ How to Upgrade

1. Update extension files
2. Reload extension in Chrome
3. Open Settings (⚙️ icon)
4. Enter your API key
5. Select environment (dev/prod)

---

## 📋 Chrome Store Compliance

- ✅ No hardcoded API keys
- ✅ Clear permission justifications
- ✅ Privacy-first design
- ✅ User-initiated actions only

---

## 🏢 Enterprise Features

### Enable Enterprise Mode:
1. Open extension settings
2. Check "Enterprise mode"
3. (Optional) Add allowed domains

### Behavior in Enterprise Mode:
- Free-text queries disabled
- LLM answers disabled
- Scan-only output
- Policy violations shown
- Request IDs always displayed

---

## 📦 Files Changed

| File | Change |
|------|--------|
| `manifest.json` | v1.0.0, added storage permission, options_page |
| `background.js` | chrome.storage, enterprise mode, domain allowlist |
| `popup.js` | Scan-only mode, settings link, scan result display |
| `options.html` | New settings page |
| `options.js` | Settings management |
| `options.css` | Settings page styles |

---

## 🔗 Links

- [Settings Page](chrome-extension://EXTENSION_ID/options.html)
- [Documentation](https://docs.safebrowse.io)
- [Support](mailto:support@safebrowse.io)
