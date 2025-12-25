# SafeBrowse Extension — Chrome Store Policy Compliance

Copy-paste answers for Chrome Web Store review.

---

## Permission Justifications

### `activeTab`
```
SafeBrowse only analyzes the currently active tab when the user explicitly 
clicks the extension icon. This permission is required to extract page 
content for security scanning. No background scanning occurs.
```

### `scripting`
```
The scripting permission is used to safely read the page's HTML content 
for security analysis. SafeBrowse does not modify page behavior, inject 
scripts, or alter the DOM in any way.
```

### `storage`
```
Storage is used to securely save user preferences such as API 
configuration and mode settings. No personal data is stored.
```

### `host_permissions` (`<all_urls>`)
```
SafeBrowse needs to send page content to the SafeBrowse API for 
security analysis. This permission allows the extension to make 
requests to the user's configured API endpoint. Users can configure 
their own endpoint in settings.
```

---

## Privacy Disclosure

### What data is collected?
```
SafeBrowse does not collect personal data. When the user initiates 
a scan, page HTML and URL are sent to the SafeBrowse API for 
security analysis only.
```

### Is data stored?
```
Page content is processed in memory only and is not permanently 
stored. User settings (API key, preferences) are stored locally 
in Chrome sync storage.
```

### Is data shared with third parties?
```
No. Page content is sent only to the user's configured SafeBrowse 
API endpoint. Content is never sold, shared for advertising, or 
used for tracking purposes.
```

### How is AI used?
```
The extension itself does not run AI. All AI processing happens 
on the backend server after content passes security checks. In 
enterprise/scan-only mode, no AI processing occurs at all.
```

---

## Single Purpose Description
```
SafeBrowse is a security tool that protects users from prompt 
injection attacks when using AI assistants with web content. 
It scans pages for hidden malicious instructions before they 
can reach AI systems.
```

---

## User Data Declaration

| Data Type | Collected | Shared | Purpose |
|-----------|-----------|--------|---------|
| Page content | Yes (on user action) | To SafeBrowse API only | Security scanning |
| URLs | Yes (on user action) | To SafeBrowse API only | Security scanning |
| Personal info | No | No | N/A |
| Authentication | No | No | N/A |
| Financial | No | No | N/A |
| Health | No | No | N/A |
| Location | No | No | N/A |

---

## Developer Contact

```
Developer Name: SafeBrowse Team
Email: support@safebrowse.io
Website: https://safebrowse.io
Privacy Policy: https://safebrowse.io/privacy
```

---

## Review Notes for Google

```
SafeBrowse is a security tool for AI applications. 

Key points for review:

1. MINIMAL PERMISSIONS: Only activeTab, scripting, and storage 
   are used. No background scanning.

2. USER-INITIATED: All page scanning happens only when the 
   user clicks the extension icon.

3. NO DATA COLLECTION: We don't collect personal data. Page 
   content is processed only for security analysis.

4. ENTERPRISE READY: Includes scan-only mode for organizations 
   that need security controls without AI processing.

5. OPEN SOURCE: Source code available at github.com/safebrowse

The extension follows all Chrome Web Store policies for security 
tools and does not modify page behavior or inject content.
```
