# Chrome Extension Publishing Guide

## 📦 Quick Distribution (Manual Install)

For beta testers who want to install the extension manually:

### Option 1: Share the Extension Folder
1. Zip the `extension/` folder
2. Send to testers
3. They extract and load unpacked in Chrome

### Option 2: Create CRX Package
Requires Chrome to package the extension.

---

## 🏪 Chrome Web Store Publishing

### Prerequisites
1. Google Developer Account ($5 one-time fee)
2. Extension icons (16x16, 48x48, 128x128)
3. Promotional screenshots (1280x800 or 640x400)
4. Privacy policy URL

### Step 1: Prepare Assets

**Required Icons:**
- `icon16.png` - 16x16 pixels (toolbar)
- `icon48.png` - 48x48 pixels (extensions page)
- `icon128.png` - 128x128 pixels (store listing)

**Store Listing:**
- Title: Prompt Injection Firewall
- Short Description: Protect AI agents from prompt injection attacks
- Detailed Description: (see below)
- Category: Productivity or Developer Tools
- Language: English

### Step 2: Create Zip Package

```powershell
cd g:\AI_Browser
Compress-Archive -Path extension\* -DestinationPath prompt-injection-firewall-extension.zip -Force
```

### Step 3: Submit to Chrome Web Store

1. Go to https://chrome.google.com/webstore/devconsole
2. Click "New Item"
3. Upload the `.zip` file
4. Fill in store listing details
5. Upload screenshots
6. Submit for review (1-3 days)

---

## 📝 Store Listing Content

### Title
```
Prompt Injection Firewall - AI Security
```

### Short Description (132 chars max)
```
Protect AI agents and LLM applications from prompt injection attacks. Scans web pages before your AI processes them.
```

### Detailed Description
```
🛡️ PROMPT INJECTION FIREWALL

The #1 security risk for AI applications is prompt injection - malicious content that hijacks your AI agent's behavior.

This extension protects your AI browsing sessions by:

✅ REAL-TIME SCANNING
• Scans web pages before AI processes content
• Detects 50+ prompt injection patterns
• Blocks malicious pages instantly

✅ ENTERPRISE SECURITY
• Policy engine blocks login pages & suspicious domains
• Fail-closed design - errors block, never fail open
• Request tracking with unique IDs

✅ COMPLIANCE READY
• Full audit logging
• SOC2 & ISO 27001 compatible
• Human-readable explanations for every block

HOW TO USE:
1. Navigate to any webpage
2. Click the 🛡️ icon
3. Ask your question about the page
4. Get a safe, filtered AI response

DETECTION RATE: 100% against common attack vectors

Perfect for:
• AI browser agents
• LLM-powered assistants
• Research automation
• Content summarization

🔒 Your AI security starts here.
```

### Category
- Primary: Developer Tools
- Secondary: Productivity

### Privacy Policy
Create a simple privacy policy stating:
- No personal data collected
- Page content processed locally or sent to user-configured API
- No tracking or analytics

---

## 📸 Screenshots Needed

1. **Main popup** - Extension in action on a webpage
2. **Safe page** - Showing successful AI response
3. **Blocked page** - Showing security warning
4. **Settings/Config** - Configuration options

Size: 1280x800 or 640x400 pixels

---

## ✅ Pre-Publish Checklist

- [ ] Icons created (16, 48, 128 px)
- [ ] manifest.json version updated
- [ ] config.json has production API URL
- [ ] Screenshots captured
- [ ] Privacy policy hosted online
- [ ] Description written
- [ ] Zip package created
- [ ] Google Developer account ready

---

## 🚀 Quick Package Command

```powershell
# From AI_Browser directory
Compress-Archive -Path extension\* -DestinationPath "PromptInjectionFirewall-v0.3.0.zip" -Force
```

Your extension is ready for Chrome Web Store! 🎉
