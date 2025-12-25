# 🚀 Deployment Guide

This guide details how to deploy **SafeBrowse** to production environments.

## Prerequisities
- Docker & Docker Compose
- Access to an LLM Provider (OpenAI, Groq, etc.)
- A secret key for JWT (generated via `openssl rand -hex 32`)

---

## 🐳 Docker Deployment (Recommended)

The easiest way to run SafeBrowse is using Docker Compose.

## 🚀 Launch Sequence (What to Deploy First?)

SafeBrowse is a **single deployment**. The Backend (Python) and Frontend (Dashboard) are bundled together.

1.  **Deploy the Repo**: Push this code to Railway, Render, or your server.
2.  **Set Environment Variables**:
    *   `OPENAI_API_KEY`: Required for the LLM firewall.
    *   `JWT_SECRET_KEY`: Required for security.
    *   `SAFEBROWSE_API_KEYS`: (Optional) Admin keys, comma-separated.
3.  **Wait for Build**: The build process will install dependencies and start the server.
4.  **Go Live**:
    *   Visit your public URL (e.g., `https://safebrowse-production.up.railway.app/`).
    *   **First Action**: Go to `/dashboard/` -> **Settings** -> Change "Backend URL" to your new public HTTPS URL -> Click **Save**.
    *   **Second Action**: Share the Landing Page (`/`) with users so they can request keys.

---

### 1. Preparation
Ensure your `.env` file in `backend/.env` is configured for production:

```ini
# backend/.env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
# Generate a strong secret: openssl rand -hex 32
JWT_SECRET_KEY=your-super-secret-key-change-this
# Set to 0.0.0.0 for Docker
database_url=sqlite:///./audit.db
```

### 2. Run with Compose
```bash
docker-compose up -d --build
```
This will start:
- **API**: `http://localhost:8000`
- **Audit DB**: Persisted in `./backend/audit.db`

### 3. Verify
```bash
curl http://localhost:8000/health
```

### 4. Access Dashboard
Once running, the Management Console is available at:
`http://localhost:8000/dashboard/`

**New User Signup:**
Users can now visit the landing page (`http://localhost:8000/`) and click **"Get Free API Key"** to self-register.
- Creates an Organization and API Key automatically.
- Redirects to Dashboard.


---

## ☁️ Cloud Deployment

### Option A: Railway / Render (PaaS)
SafeBrowse is ready for PaaS deployment.

1. **Connect GitHub/GitLab Repo**: Point to this repository.
2. **Root Directory**: Set to `/` (or specified repo root).
3. **Build Command**: `pip install -r backend/requirements.txt`.
4. **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
5. **Environment Variables**:
   - `OPENAI_API_KEY`: ...
   - `JWT_SECRET_KEY`: ...
   - `SAFEBROWSE_API_KEYS`: `prod-key-1,prod-key-2`
   - `PYTHONPATH`: `backend`

### Option B: AWS EC2 / VM
1. Provision a t3.small (Ubuntu).
2. Install Docker.
3. Clone repo.
4. Run `docker-compose up -d`.

---

## 🛡️ Production Checklist
- [ ] **Change the JWT Secret**: Never use the default "test-secret".
- [ ] **HTTPS**: Use a reverse proxy (Nginx/Caddy) or Cloud Load Balancer for SSL.
- [ ] **Database**: For high-scale, switch `db.py` to use PostgreSQL instead of SQLite.
- [ ] **CORS**: Update `CORS_ORIGINS` in `.env` to match your frontend domain.
