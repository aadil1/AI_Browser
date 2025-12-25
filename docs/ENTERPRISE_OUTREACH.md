# Enterprise Outreach Templates

High-conversion email templates for enterprise sales.

---

## Template 1: Cold Outreach (Security Teams)

**Subject:** Prompt injection firewall for [Company] AI systems

---

Hi [Name],

I noticed [Company] is building AI-powered [agents/products/features]. 

We built SafeBrowse — a prompt injection firewall that blocks malicious content before it reaches your LLMs.

**The problem:** AI systems ingest untrusted data. Hidden instructions can hijack AI behavior without anyone noticing.

**Our solution:** SafeBrowse enforces a hard security boundary:

```
Web/Documents → SafeBrowse → Your AI (safe)
```

Quick stats:
- 50+ attack patterns detected
- <50ms average scan time
- 100% fail-closed (no bypasses)
- Full audit trail with request IDs

Would you be open to a 15-minute demo? I can show how it works with your existing stack.

Best,
[Your name]

P.S. We're offering a free pilot for early enterprise customers.

---

## Template 2: Follow-up (No Response)

**Subject:** Re: Prompt injection firewall for [Company] AI systems

---

Hi [Name],

Following up on my previous email about SafeBrowse.

In case it's helpful — here's a 2-minute demo showing how we blocked a real prompt injection attack:

[Demo Video Link]

Key points:
1. The attack was hidden in HTML comments (invisible to users)
2. SafeBrowse detected and blocked it
3. The AI never saw the malicious content
4. Full audit log was generated

Happy to jump on a quick call if you're evaluating AI security.

Best,
[Your name]

---

## Template 3: Referral Request

**Subject:** Quick question about AI security at [Company]

---

Hi [Name],

I'm reaching out because [mutual connection/reason] mentioned you might be the right person to talk to about AI security.

We built SafeBrowse, a prompt injection firewall for AI systems. We're working with teams building AI agents and RAG pipelines who need to protect against malicious content.

If this isn't your area, could you point me to the right person on your team?

Thanks,
[Your name]

---

## Template 4: Event/Conference Follow-up

**Subject:** Great meeting you at [Event] — SafeBrowse demo

---

Hi [Name],

Great chatting at [Event] about [topic discussed].

As promised, here's more info on SafeBrowse:

**What it does:**
Blocks prompt injection attacks before they reach your AI systems.

**How it works:**
- Python SDK: `pip install safebrowse`
- Chrome extension for browsing
- REST API for pipelines

**Key features:**
- 50+ attack patterns
- RAG sanitization
- Policy engine
- Full audit logs

Want to schedule a quick demo? I can show it working with your stack.

Best,
[Your name]

---

## Template 5: Compliance-Focused

**Subject:** AI security for [SOC2/ISO/compliance] at [Company]

---

Hi [Name],

As [Company] scales AI capabilities, you may be facing questions about AI security and compliance.

We built SafeBrowse to help teams like yours:

**Audit-ready:**
- Every request logged with unique ID
- Full decision trail
- Correlation ID support

**Fail-closed:**
- Security cannot be bypassed
- Errors always block
- Deterministic decisions

**SOC2 aligned:**
- Policy-based controls
- Access logging
- Retention policies

We're currently working with [similar company type] to implement AI security controls for their compliance requirements.

Would a 20-minute call be helpful to discuss your needs?

Best,
[Your name]

---

## Template 6: Technical Decision Maker

**Subject:** Python SDK for AI agent security

---

Hi [Name],

I saw your work on [their project/blog/talk] — impressive stuff.

We built SafeBrowse, an open-source prompt injection firewall. Thought you might find it useful:

```python
from safebrowse import SafeBrowseClient

with client.guard(html, url):
    agent.run()  # Only runs if safe
```

Key design decisions:
- **Fail-closed:** Errors always block
- **No bypasses:** No `allow_unsafe` flags
- **Deterministic:** Same input = same decision
- **Auditable:** Request IDs for every decision

GitHub: [link]
PyPI: `pip install safebrowse`

Would love your feedback if you have 10 minutes.

Best,
[Your name]

---

## Response Handling

### If they ask about pricing:
> "We have a free tier for developers and Pro tier starting at $29/month. For enterprise, we customize based on your needs. Happy to discuss what would work best for your team."

### If they ask about integration:
> "Integration takes about 5 minutes. It's a Python SDK with a simple context manager. I can walk you through it on a quick call."

### If they ask about competitors:
> "Most alternatives focus on prompt engineering or model-level guards. SafeBrowse is different — it's a hard security boundary that works with any LLM. The content is blocked before it reaches your AI."

### If they say "not now":
> "Totally understand. Mind if I check back in [1-2 months]? In the meantime, feel free to try the free tier: pip install safebrowse"

---

## Email Signatures

### Standard:
```
[Name]
SafeBrowse — AI Security
📧 name@safebrowse.io
🔗 safebrowse.io
```

### With social proof:
```
[Name]
SafeBrowse — AI Security

"SafeBrowse blocked an attack we didn't even know existed." 
— [Customer name], [Company]

📧 name@safebrowse.io
```

---

## Outreach Cadence

```
Day 1:  Send initial email
Day 3:  LinkedIn connection request
Day 7:  Follow-up email
Day 14: Final follow-up with different angle
Day 30: Add to nurture list
```
