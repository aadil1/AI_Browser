# SafeBrowse Enterprise Extension Mode

Enterprise deployment guide for security teams.

---

## Overview

Enterprise mode transforms SafeBrowse from an AI assistant into a **pure security control**:

- ❌ No AI responses
- ❌ No free-text queries
- ✅ Security scanning only
- ✅ Policy enforcement
- ✅ Full audit trail

---

## Enabling Enterprise Mode

### Option 1: User Settings
1. Click extension icon → Settings (⚙️)
2. Check **"Enterprise mode"**
3. Click **Save Settings**

### Option 2: Managed Policy (IT Admin)

For organization-wide deployment, use Chrome's managed storage:

```json
{
  "apiKey": { "Value": "your-enterprise-key" },
  "environment": { "Value": "prod" },
  "enterpriseMode": { "Value": true },
  "allowedDomains": { "Value": "docs.company.com\ninternal.company.com" }
}
```

Deploy via:
- Google Workspace Admin Console
- Group Policy (Windows)
- Configuration Profile (macOS)

---

## Enterprise Mode Behavior

| Feature | Normal Mode | Enterprise Mode |
|---------|-------------|-----------------|
| Free-text queries | ✅ Enabled | ❌ Disabled |
| AI answers | ✅ Shown | ❌ Hidden |
| Scan-only | Optional | ✅ Forced |
| Policy violations | Shown | ✅ Shown |
| Request ID | Available | ✅ Always shown |
| Domain allowlist | Optional | Recommended |

---

## Domain Allowlist

Restrict scanning to approved domains only:

**Settings → Allowed Domains:**
```
docs.company.com
internal.company.com
confluence.company.io
```

**Subdomains are automatically included:**
- `docs.company.com` allows `api.docs.company.com`

**Blocked domains show:**
```
Domain not in allowlist
```

---

## Audit Trail

Every scan generates a unique request ID:

```
Request ID: req-abc123-def456
```

This ID appears in:
1. Extension popup
2. SafeBrowse API logs
3. Your SIEM (if configured)

Use this for:
- Incident investigation
- Compliance audits
- Correlation with internal logs

---

## UI in Enterprise Mode

### Popup Display:
```
┌─────────────────────────────────────────┐
│  🛡️ SafeBrowse [Enterprise]            │
├─────────────────────────────────────────┤
│  [Scan Page]                            │
├─────────────────────────────────────────┤
│  ✓ SAFE                                 │
│                                         │
│  No security threats detected           │
│                                         │
│  Request ID: req-abc123                 │
│  Risk Score: 12%                        │
└─────────────────────────────────────────┘
```

### Blocked Page:
```
┌─────────────────────────────────────────┐
│  🛡️ SafeBrowse [Enterprise]            │
├─────────────────────────────────────────┤
│  🚫 BLOCKED                             │
│                                         │
│  Hidden prompt injection detected       │
│                                         │
│  Policy: injection_hidden_html          │
│  Request ID: req-xyz789                 │
│  Risk Score: 92%                        │
└─────────────────────────────────────────┘
```

---

## Security Guarantees

| Guarantee | Implementation |
|-----------|----------------|
| **No data to LLM** | AI endpoints never called |
| **Fail-closed** | Errors always block |
| **Deterministic** | Same input = same decision |
| **Auditable** | Every scan logged |
| **No bypasses** | Enterprise mode cannot be overridden by users |

---

## Compliance Alignment

### SOC2
- ✅ Access controls (allowlist)
- ✅ Logging (request IDs)
- ✅ Change management (version tracking)

### GDPR
- ✅ No personal data collection
- ✅ Processing for security only
- ✅ User-initiated actions

### ISO 27001
- ✅ A.12.6.1 Management of technical vulnerabilities
- ✅ A.14.1.2 Securing application services

---

## Integration with SIEM

Configure backend to forward events:

```json
{
  "event": "safebrowse.scan",
  "timestamp": "2024-12-17T00:00:00Z",
  "request_id": "req-abc123",
  "url": "https://external.com/page",
  "decision": "blocked",
  "risk_score": 0.92,
  "policy_violations": ["injection_hidden_html"],
  "user_agent": "SafeBrowse-Extension/1.0.0"
}
```

Supported integrations:
- Splunk
- Datadog
- Elastic
- PagerDuty (alerting)

---

## Deployment Checklist

### Initial Setup
- [ ] Obtain enterprise API key
- [ ] Configure backend URL (prod)
- [ ] Test with single user

### Organization Rollout
- [ ] Create managed policy
- [ ] Deploy via MDM/GPO
- [ ] Configure domain allowlist
- [ ] Set up SIEM forwarding

### Monitoring
- [ ] Monitor blocked events
- [ ] Review audit logs weekly
- [ ] Track adoption metrics

---

## Support

**Enterprise support:** enterprise@safebrowse.io  
**SLA:** 4-hour response time  
**Documentation:** docs.safebrowse.io/enterprise
