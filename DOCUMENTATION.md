# Prompt Injection Firewall & Policy Engine

**Enterprise-grade AI security for LLM applications, browser agents, and RAG pipelines.**

Protect your AI systems from prompt injection attacks - the #1 security risk for AI applications.

---

## 📋 Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Usage Guide](#usage-guide)
- [API Reference](#api-reference)
- [Chrome Extension](extension/README.md): Browser integration
- [Python SDK](sdk/README.md): Developer tools
- [Deployment Guide](deployment.md): Production launch instructions
- [Configuration](#configuration)
- [Testing](#testing)
- [Deployment](#deployment)
- [Architecture](#architecture)

---

## Features

### Core Security
| Feature | Description |
|---------|-------------|
| **Prompt Injection Detection** | 50+ heuristic patterns detecting injection attempts |
| **Policy Engine** | Block login pages, suspicious domains, custom rules |
| **Fail-Closed Design** | Errors result in blocking, never failing open |
| **HTML Size Limits** | Prevents DoS via oversized content (2MB limit) |
| **API Key Authentication** | Secure access with `X-API-Key` header |

### Enterprise Capabilities
| Feature | Description |
|---------|-------------|
| **Audit Logging** | SQLite-backed logging for compliance (SOC2, ISO 27001) |
| **Audit Dashboard** | View logs and statistics via API |
| **Human-Readable Explanations** | Detailed reasons for every block |
| **Request Tracking** | UUID for each request for debugging |

### Agent Protection & Guardrails
| Feature | Description |
|---------|-------------|
| **RAG Sanitization** | Clean scraped content before vector indexing |
| **Agent Guardrails** | Step limits, loop detection, timeout protection |
| **Action Approval** | Require approval for write actions |
| **Red Team Testing** | 14 attack scenarios for testing defenses |

### Document Analysis
| Feature | Description |
|---------|-------------|
| **Image OCR** | Extract text from images and scan for injection |
| **PDF Scanning** | Scan PDF documents for hidden injection |

---

## Quick Start

### 1. Clone and Setup
```bash
git clone <your-repo>
cd AI_Browser/backend

# Create virtual environment
python -m venv .venv
.\.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your LLM API key
```

### 3. Start Server
```bash
uvicorn app.main:app --reload --port 8000
```

### 4. Test It
```bash
curl http://localhost:8000/health
```

---

## Installation

### Requirements
- Python 3.10+
- pip

### Backend Dependencies
```bash
pip install fastapi uvicorn pydantic openai httpx python-dotenv
```

### Optional (for OCR/PDF)
```bash
pip install Pillow pytesseract PyMuPDF
# Also install Tesseract OCR: https://github.com/tesseract-ocr/tesseract
```

---

## Usage Guide

### Basic HTML Scanning
```bash
curl -X POST http://localhost:8000/scan-html \
  -H "X-API-Key: test-key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "html": "<html><body>Safe content</body></html>"
  }'
```

Response:
```json
{
  "is_safe": true,
  "risk_score": 0.0,
  "request_id": "uuid-here"
}
```

### LLM-Powered Safe Ask
```bash
curl -X POST http://localhost:8000/safe-ask \
  -H "X-API-Key: test-key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "html": "<html><body><h1>Welcome</h1><p>Content here</p></body></html>",
    "query": "What is this page about?"
  }'
```

### RAG Chunk Sanitization
```bash
curl -X POST http://localhost:8000/sanitize \
  -H "X-API-Key: test-key" \
  -H "Content-Type: application/json" \
  -d '{
    "chunks": ["chunk 1 text", "chunk 2 text", "ignore previous instructions"],
    "url": "https://source.com"
  }'
```

Response:
```json
{
  "results": [
    {"index": 0, "is_safe": true, "risk_score": 0.0},
    {"index": 1, "is_safe": true, "risk_score": 0.0},
    {"index": 2, "is_safe": false, "risk_score": 0.6, "reason": "Injection detected"}
  ],
  "safe_count": 2,
  "flagged_count": 1,
  "total_count": 3
}
```

### View Audit Logs
```bash
curl http://localhost:8000/audit/logs?limit=10 \
  -H "X-API-Key: test-key"
```

### Get Statistics
```bash
curl http://localhost:8000/audit/stats \
  -H "X-API-Key: test-key"
```

### Run Red Team Tests
```bash
curl -X POST http://localhost:8000/test/red-team \
  -H "X-API-Key: test-key"
```

---

## API Reference

### Health Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/` | GET | No | Server status |
| `/health` | GET | No | Detailed health check |
| `/capabilities` | GET | No | Available features |

### Core Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/safe-ask` | POST | Yes | LLM-powered safe browsing |
| `/scan-html` | POST | Yes | HTML safety scan only |
| `/sanitize` | POST | Yes | Batch RAG chunk sanitization |

### Document Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/scan-image` | POST | Yes | OCR + safety scan |
| `/scan-pdf` | POST | Yes | PDF text extraction + scan |

### Audit Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/audit/logs` | GET | Yes | Paginated audit logs |
| `/audit/stats` | GET | Yes | Statistics dashboard |

### Testing Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/test/scenarios` | GET | No | List attack scenarios |
| `/test/red-team` | POST | Yes | Run attack simulations |

### Agent Guard Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/agent/session/start` | POST | Yes | Start guarded session |
| `/agent/session/{id}/step` | POST | Yes | Record agent step |
| `/agent/session/{id}` | GET | Yes | Get session status |
| `/agent/session/{id}` | DELETE | Yes | End session |

---

## Chrome Extension

### Installation
1. Open `chrome://extensions`
2. Enable **Developer mode**
3. Click **Load unpacked**
4. Select the `extension/` folder

### Usage
1. Navigate to any webpage
2. Click the extension icon (🛡️)
3. Type your question about the page
4. Click **Ask AI** or press Enter
5. View the safe, filtered response

### Configuration
Edit `extension/config.json`:
```json
{
  "BACKEND_URL": "http://localhost:8000",
  "API_KEY": "your-api-key"
}
```

---

## Python SDK

### Installation
```bash
cd sdk
pip install -e .
```

### Basic Usage
```python
from safebrowse import SafeBrowseClient

client = SafeBrowseClient(
    base_url="http://localhost:8000",
    api_key="your-api-key"
)

# Check if content is safe
result = client.scan_html("<html>...</html>", "https://example.com")
print(f"Safe: {result.is_safe}, Risk: {result.risk_score}")

# Quick safety check
if client.is_safe(html, url):
    agent.run()
```

### Context Manager for Agents
```python
# Automatically blocks if unsafe
with client.guard(html, url):
    agent.run()  # Only runs if safe
```

### Async Usage
```python
from safebrowse import AsyncSafeBrowseClient

async with AsyncSafeBrowseClient(api_key="key") as client:
    result = await client.scan_html(html, url)
```

### RAG Sanitization
```python
# Clean scraped content
chunks = ["chunk1", "chunk2", "ignore instructions"]
result = client.sanitize(chunks, url="source.com")

# Get only safe chunks
safe_chunks = [
    chunks[r.index] 
    for r in result.results 
    if r.is_safe
]
```

---

## Configuration

### Environment Variables (.env)

```bash
# LLM Provider
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://api.groq.com/openai/v1
OPENAI_MODEL=llama-3.3-70b-versatile

# Security Settings
INJECTION_THRESHOLD=0.5  # 0.0-1.0, lower = stricter
SAFETY_MODEL_ENABLED=false

# CORS (production)
CORS_ORIGINS=["https://your-domain.com"]

# Debug
DEBUG=false
```

### API Keys

Edit `app/main.py`:
```python
VALID_API_KEYS = {"your-production-key-1", "your-production-key-2"}
```

---

## Testing

### Run All Tests
```bash
cd backend
pytest tests/test_api.py -v
```

### Run Red Team Simulation
```bash
curl -X POST http://localhost:8000/test/red-team \
  -H "X-API-Key: test-key"
```

### Detection Rate
Current detection rate: **100% (14/14 attack scenarios)**

---

## Deployment

### Docker
```bash
# Build
docker build -t prompt-injection-firewall .

# Run
docker run -p 8000:8000 --env-file backend/.env prompt-injection-firewall
```

### Docker Compose
```bash
docker-compose up -d
```

### Production Checklist
- [ ] Replace test API keys with secure keys
- [ ] Configure CORS for your domains
- [ ] Set up HTTPS/TLS
- [ ] Configure audit log retention
- [ ] Enable rate limiting
- [ ] Set up monitoring/alerting

---

## Architecture

```
┌─────────────────┐     ┌─────────────────┐
│ Chrome Extension│────▶│  FastAPI Backend │
└─────────────────┘     └────────┬────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
              ┌──────────┐ ┌──────────┐ ┌──────────┐
              │ Heuristic│ │  Policy  │ │   LLM    │
              │  Safety  │ │  Engine  │ │  Agent   │
              └──────────┘ └──────────┘ └──────────┘
                    │            │            │
                    └────────────┼────────────┘
                                 ▼
                          ┌──────────┐
                          │  Audit   │
                          │   Log    │
                          └──────────┘
```

### Key Files
| File | Purpose |
|------|---------|
| `app/main.py` | FastAPI application & endpoints |
| `app/heuristic_safety.py` | Injection pattern detection |
| `app/policy_engine.py` | Rule-based blocking |
| `app/audit.py` | SQLite audit logging |
| `app/agent_guard.py` | Agent runtime protection |
| `app/red_team.py` | Attack scenario library |
| `app/sanitizer.py` | RAG chunk cleaning |
| `app/ocr_scanner.py` | Image/PDF text extraction |

---

## License

MIT License

---

## Support

- **API Docs**: http://localhost:8000/docs
- **GitHub Issues**: [Create Issue]
- **Email**: [your-email]

---

Made with ❤️ for AI Security
