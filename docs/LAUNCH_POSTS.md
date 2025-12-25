# SafeBrowse — Launch Assets

Complete launch materials for SafeBrowse v0.2.0.

---

## 📸 Screenshot & Demo Captions

Use these exact captions for screenshots / GIFs:

### Screenshot 1 — Malicious Page
```
This webpage looks normal — but contains hidden prompt injection.
```

### Screenshot 2 — Extension Block
```
SafeBrowse blocks the request before the AI sees it.
```

### Screenshot 3 — SDK Block
```
The agent never runs. Execution is stopped by SafeBrowse.
```

### Screenshot 4 — Audit Log
```
Every decision is logged with a request ID for audit and compliance.
```

### Screenshot 5 — RAG Sanitization
```
Poisoned data is removed before entering the vector database.
```

---

## 🔥 Hacker News Post

### Title
```
Show HN: A Prompt-Injection Firewall for AI Agents and RAG Pipelines
```

### Post Body
```
We built SafeBrowse — an open-source prompt-injection firewall for AI systems.

Instead of relying on better prompts, SafeBrowse enforces a hard security boundary between untrusted web content and LLMs.

It blocks hidden instructions, policy violations, and poisoned data before the AI ever sees it.

Features:
• Prompt injection detection (50+ patterns)
• Policy engine (login/payment blocking)
• Fail-closed by design
• Audit logs & request IDs  
• Python SDK (sync + async)
• RAG sanitization

Demo: [DEMO_LINK]
GitHub: [GITHUB_LINK]
PyPI: pip install safebrowse

Looking for feedback from AI infra, security, and agent builders.
```

---

## 🔗 LinkedIn Post

### Founder / Tech Lead Tone
```
AI systems are now browsing the web and ingesting data autonomously.

The web is not safe for AI.

We built SafeBrowse, a prompt-injection firewall that blocks malicious content before it reaches your LLMs, agents, or RAG pipelines.

This isn't a prompt trick.
It's an enforceable security boundary.

✓ Fail-closed by design
✓ Audit-ready
✓ Python SDK
✓ Open-source

▶ Watch the demo: [DEMO_LINK]
▶ pip install safebrowse

Would love feedback from AI infra and security engineers.

#AIAgent #LLM #Security #PromptInjection #OpenSource #Python
```

---

## 🐦 Twitter/X Thread

### Tweet 1 (Hook)
```
🛡️ Introducing SafeBrowse

A prompt-injection firewall for AI agents.

The web is not safe for AI.
We built a solution.

🧵 Thread:
```

### Tweet 2 (Problem)
```
The problem:

AI agents and RAG pipelines ingest untrusted web content.

Hidden instructions can hijack LLM behavior — without humans ever seeing it.

Prompting alone cannot solve this.
```

### Tweet 3 (Solution)
```
The solution:

SafeBrowse enforces a hard security boundary.

Before: Web → LLM → Hope nothing bad happens

After: Web → SafeBrowse → LLM

The AI never sees malicious content.
```

### Tweet 4 (Demo)
```
See it in action:

✓ Scans content before your AI
✓ Blocks prompt injection (50+ patterns)
✓ Blocks login/payment forms
✓ Sanitizes RAG chunks

[DEMO_GIF]
```

### Tweet 5 (SDK)
```
The SDK:

from safebrowse import SafeBrowseClient

with client.guard(html, url):
    agent.run()  # Only runs if safe

No silent failures. No bypasses.
Fail-closed by design.
```

### Tweet 6 (CTA)
```
Ready to protect your AI?

📦 pip install safebrowse
⭐ github.com/safebrowse/safebrowse-python

Open source. Enterprise ready.

Feedback welcome 🙏
```

---

## 📧 Product Hunt Tagline

```
SafeBrowse — Prompt-injection firewall for AI agents
```

### One-liner
```
Block malicious web content before it reaches your AI. Fail-closed by design.
```

### Maker Comment
```
Hey Product Hunt! 👋

We built SafeBrowse because AI agents are now browsing the web autonomously - but the web is full of content designed to hijack AI systems.

Instead of relying on clever prompts (which can be bypassed), SafeBrowse enforces a hard security boundary between untrusted content and your LLMs.

Key features:
• 50+ prompt injection patterns detected
• Policy engine for login/payment forms
• RAG sanitization for vector DBs
• Python SDK with sync/async support
• Fail-closed: security cannot be bypassed

We'd love your feedback! What security challenges are you facing with AI agents?
```
