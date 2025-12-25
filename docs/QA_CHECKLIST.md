# Prompt Injection Firewall - Launch QA Checklist

## 🔴 Pre-Launch Critical

### Backend API
- [ ] Server starts without errors
- [ ] Health endpoint returns `healthy`
- [ ] API key authentication working
- [ ] LLM integration responding
- [ ] Audit logs being created

### Chrome Extension
- [ ] Extension loads without errors
- [ ] Icon displays correctly
- [ ] Popup opens on click
- [ ] Query input accepts text
- [ ] Results display correctly
- [ ] Error messages show properly

### Security
- [ ] Invalid API keys rejected (401)
- [ ] HTML size limits enforced
- [ ] Fail-closed on errors
- [ ] No sensitive data in responses

---

## 🟠 Feature Testing

### Core Safety Scanning
- [ ] Safe pages return `is_safe: true`
- [ ] Injection patterns detected
- [ ] Risk scores in 0-1 range
- [ ] Request IDs in all responses
- [ ] Explanations included when blocked

### Policy Engine
- [ ] Login page detection works
- [ ] Suspicious TLD blocking works
- [ ] Domain allowlist/blocklist works

### RAG Sanitization
- [ ] `/sanitize` accepts chunk arrays
- [ ] Returns per-chunk results
- [ ] Counts match input length

### Agent Guardrails
- [ ] Sessions start correctly
- [ ] Steps are recorded
- [ ] Step limits enforced
- [ ] Loop detection works
- [ ] Sessions can be ended

### Red Team Testing
- [ ] All scenarios listed
- [ ] Individual scenarios testable
- [ ] Full red team run works
- [ ] Detection rate calculated

---

## 🟡 Integration Testing

### End-to-End Flow
- [ ] Open extension on safe page → Get answer
- [ ] Open extension on blocked page → See warning
- [ ] Check audit logs show requests
- [ ] Run red team → Review results

### Performance
- [ ] Response time < 5 seconds
- [ ] Large pages handled (up to 2MB)
- [ ] Multiple concurrent requests work

---

## 🟢 Documentation

- [ ] README has correct setup steps
- [ ] API docs accessible at /docs
- [ ] Environment variables documented
- [ ] Docker build works

---

## ✅ Sign-Off

| Area | Tester | Date | Status |
|------|--------|------|--------|
| Backend API | | | ⬜ |
| Extension | | | ⬜ |
| Security | | | ⬜ |
| Integration | | | ⬜ |

**Launch Approved:** ⬜ Yes / ⬜ No

**Notes:**
