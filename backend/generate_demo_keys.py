import requests
import json

BASE_URL = "http://localhost:8000"
OUTPUT_FILE = "DEMO_CREDENTIALS.md"

USERS = [
    {"email": "free@example.com", "password": "password", "tier": "Free", "desc": "Limited to 100/day. No PDF/Image."},
    {"email": "pro@example.com", "password": "password", "tier": "Pro", "desc": "1,000/day. PDF & Image Scanning enabled."},
    {"email": "admin@bigcorp.com", "password": "password", "tier": "Enterprise", "desc": "Unlimited. Audit Logs & SSO."}
]

def generate_keys():
    credentials = "# 🔑 SafeBrowse Demo Credentials\nUse these keys to demonstrate the tiered features.\n\n"
    
    print("🔄 Generating fresh keys...")
    
    for u in USERS:
        try:
            # 1. Login
            resp = requests.post(f"{BASE_URL}/auth/token", data={"username": u["email"], "password": u["password"]})
            if resp.status_code != 200:
                print(f"❌ Failed to login {u['email']}")
                continue
            
            token = resp.json()["access_token"]
            
            # 2. Create Key
            headers = {"Authorization": f"Bearer {token}"}
            resp = requests.post(f"{BASE_URL}/auth/keys", headers=headers, json={"label": f"Launch Demo {u['tier']}"})
            
            if resp.status_code == 200:
                key = resp.json()["api_key"]
                print(f"✅ Generated {u['tier']} Key")
                
                credentials += f"## {u['tier']} Tier\n"
                credentials += f"- **User**: `{u['email']}`\n"
                credentials += f"- **Limits**: {u['desc']}\n"
                credentials += f"- **API Key**:\n```text\n{key}\n```\n\n"
            else:
                print(f"❌ Failed to create key for {u['tier']}: {resp.text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(credentials)
    
    print(f"\n Credentials saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    try:
        generate_keys()
    except Exception as e:
        print(e)
