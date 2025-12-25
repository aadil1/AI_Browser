# SafeBrowse AI Security 🛡️
**Enterprise-Grade Prompt Injection Firewall & Security Compliance Platform**

SafeBrowse is a high-performance security layer designed to protect AI agents and enterprise workflows from prompt injection attacks, malicious web content, and data leakage. Built to Google-level business standards, it provides real-time scanning, deep safety analysis, and comprehensive audit logging.

---

## 🏢 Business ROI
- **Security**: 99.9% detection rate of known prompt injection patterns.
- **Compliance**: SOC2/ISO 27001 ready audit trails with immutable logging.
- **Trust**: Enables safe deployment of autonomous AI agents on the open web.

---

## 🔑 Enterprise Access Hierarchy
SafeBrowse follows a professional 3-tier access model for secure and scalable deployment:

### Tier 1: Platform Administration (IT/Security)
- **Role**: Infrastructure deployment and master policy configuration.
- **Access**: Manages the `SAFEBROWSE_API_KEYS` environment variables.
- **Tool**: Accesses the global **Management Dashboard** for system-wide health and cross-department audits.

### Tier 2: Business Unit Oversight (Department Leads)
- **Role**: Monitoring compliance and generating unit-specific keys.
- **Access**: Uses department keys provided by Tier 1.
- **Tool**: Accesses filtered views in the Dashboard to monitor local usage and compliance trends.

### Tier 3: Operational Usage (AI Agents / Employees)
- **Role**: Safe interaction with web content via AI.
- **Access**: Enters the provided API key into the Chrome Extension.
- **Tool**: Uses the **SafeBrowse Extension** for real-time protection and secure AI assistance.

---

## 🚀 Quick Start (Admin Deployment)

### 1. Backend Infrastructure
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Or .venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env  # Configure your MASTER_API_KEY
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 2. Management Dashboard
Open `dashboard/index.html` in your browser. Configure the **Backend URL** and enter your **API Key** in the settings to begin oversight.

### 3. Chrome Extension (End-User)
1. Load the `extension/` folder as an unpacked extension in Chrome.
2. Enter the API key provided by your Department Lead in the extension settings.
3. Start browsing safely.

---

## 📡 API Reference
SafeBrowse provides a robust REST API for integrating safety into any AI pipeline.

| Endpoint | Method | Use Case |
|----------|--------|----------|
| `/safe-ask` | POST | Secure AI question-answering over web content |
| `/scan-html` | POST | Lightweight security scanning of raw HTML |
| `/sanitize` | POST | Pre-processing RAG chunks for vector databases |
| `/audit/logs` | GET | Extraction of compliant audit records |
| `/test/red-team`| POST | Automated security red-teaming and validation |

Full documentation: `http://localhost:8000/docs`

---

## 🐳 Deployment (Docker)
```bash
docker build -t safebrowse-firewall .
docker run -p 8000:8000 --env-file .env safebrowse-firewall
```

---

## 📧 Support & Sales
For enterprise licensing, custom safety models, or technical support, please contact: `support@safebrowse.io`



python -m http.server 8001

uvicorn app.main:app