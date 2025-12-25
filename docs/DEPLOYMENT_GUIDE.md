# Centralized Backend Deployment Guide

## Option 1: Railway (Recommended)

### Step 1: Push to GitHub
```bash
cd g:\AI_Browser
git init
git add .
git commit -m "Initial commit - Prompt Injection Firewall"
git remote add origin https://github.com/YOUR_USERNAME/prompt-injection-firewall.git
git push -u origin main
```

### Step 2: Deploy on Railway
1. Go to https://railway.app
2. Sign in with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repo
5. Railway auto-detects Dockerfile

### Step 3: Set Environment Variables
In Railway dashboard, add:
```
OPENAI_API_KEY=your-groq-or-openai-key
OPENAI_BASE_URL=https://api.groq.com/openai/v1
OPENAI_MODEL=llama-3.3-70b-versatile
INJECTION_THRESHOLD=0.5
```

### Step 4: Get Your URL
Railway gives you a URL like:
```
https://prompt-injection-firewall-production.up.railway.app
```

### Step 5: Update Extension
Edit `extension/config.json`:
```json
{
  "BACKEND_URL": "https://YOUR-APP.up.railway.app",
  "API_KEY": "public-demo-key"
}
```

### Step 6: Re-package Extension
```powershell
Compress-Archive -Path extension\* -DestinationPath "PromptInjectionFirewall-v0.3.0.zip" -Force
```

---

## Option 2: Render.com

### Step 1: Create render.yaml
```yaml
services:
  - type: web
    name: prompt-injection-firewall
    env: docker
    plan: free
    healthCheckPath: /health
    envVars:
      - key: OPENAI_API_KEY
        sync: false
      - key: OPENAI_BASE_URL
        value: https://api.groq.com/openai/v1
```

### Step 2: Deploy
1. Go to https://render.com
2. New → Web Service → Connect GitHub
3. Select repo, choose Docker
4. Add environment variables
5. Deploy

---

## Important: API Key Security

For production, update `app/main.py`:

```python
import os

# Load from environment variable
VALID_API_KEYS = set(os.getenv("VALID_API_KEYS", "public-demo-key").split(","))
```

Then set in Railway/Render:
```
VALID_API_KEYS=key1,key2,key3
```

---

## Verify Deployment

```bash
curl https://YOUR-APP.up.railway.app/health

curl -X POST https://YOUR-APP.up.railway.app/scan-html \
  -H "X-API-Key: public-demo-key" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://test.com", "html": "<html>test</html>"}'
```

Your centralized API is live! 🚀
