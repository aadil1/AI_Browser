# Chrome Web Store Listing

Copy-paste ready content for Chrome Web Store submission.

---

## Extension Name
```
SafeBrowse AI Security
```

---

## Short Description (132 chars max)
```
Blocks malicious web content from hijacking AI systems. Prompt injection firewall for safe AI browsing.
```

---

## Full Description
```
SafeBrowse is a prompt-injection firewall for AI-powered browsing.

THE PROBLEM
Webpages can contain hidden instructions that hijack AI behavior — without humans ever seeing it. These attacks are invisible to users but fully readable by AI systems.

THE SOLUTION
SafeBrowse detects and blocks these attacks BEFORE they reach your AI.

FEATURES
• Prompt injection detection (50+ patterns)
• Hidden HTML & CSS attack blocking
• Policy-based blocking (login pages, payment forms)
• Fail-closed security design
• Clear explanations for every block
• Request IDs for audit trails

HOW IT WORKS
1. Navigate to any webpage
2. Click the SafeBrowse icon
3. Ask your question about the page
4. SafeBrowse scans for attacks FIRST
5. Only safe content reaches the AI

PERFECT FOR
• AI power users
• Developers building AI agents
• Security-conscious teams
• Anyone using AI to browse the web

SECURITY GUARANTEES
✓ Fail-closed: Errors always block, never fail open
✓ Deterministic: Same input = same decision
✓ Auditable: Every request logged with unique ID
✓ No bypasses: Security cannot be disabled

PRIVACY
✓ No personal data collected
✓ Page content processed only for safety analysis
✓ No tracking or analytics
✓ Works with your own API endpoint

Open source: github.com/safebrowse

Protect your AI browsing today.
```

---

## Category
```
Primary: Developer Tools
Secondary: Productivity
```

---

## Language
```
English
```

---

## Screenshots Needed

### Screenshot 1 — Extension Popup
- Show extension popup on a webpage
- Clean, professional look

### Screenshot 2 — Safe Response
- Show successful AI response
- Green "SAFE" indicator

### Screenshot 3 — Blocked Attack
- Show blocked prompt injection
- Red "BLOCKED" with reason

### Screenshot 4 — Settings Panel
- Show configuration options
- API endpoint setting

---

## Privacy Policy URL
```
https://safebrowse.io/privacy
```

### Privacy Policy Content
```
SafeBrowse Privacy Policy

Last updated: [DATE]

1. DATA COLLECTION
SafeBrowse does not collect personal data. Page content is processed 
only for safety analysis and is not stored permanently.

2. DATA PROCESSING
When you use SafeBrowse, page content is sent to your configured API 
endpoint for safety scanning. No data is sent to third parties.

3. LOCAL STORAGE
SafeBrowse stores only your API configuration locally in your browser.
No browsing history or personal information is stored.

4. THIRD PARTIES
SafeBrowse does not share any data with third-party services.

5. CONTACT
For privacy questions: privacy@safebrowse.io
```

---

## Version
```
0.3.0
```

---

## Required Permissions (Justification)

| Permission | Justification |
|------------|---------------|
| `activeTab` | To access current page content for safety scanning |
| `storage` | To save API configuration locally |
| `host_permissions` | To send content to SafeBrowse API for analysis |

---

## Review Notes for Google
```
This extension is a security tool that helps protect users from 
prompt injection attacks when using AI assistants. It scans webpage 
content before sending it to AI systems, blocking malicious content 
that could hijack AI behavior.

The extension requires page access only when the user explicitly 
clicks the extension icon. No background scanning or tracking occurs.

Source code: github.com/safebrowse/safebrowse-extension
```
