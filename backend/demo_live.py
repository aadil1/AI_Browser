import requests

BASE_URL = "http://localhost:8000"

def demo_user(email, password, tier_name):
    print(f"\n--- Testing {tier_name} User ({email}) ---")
    
    # 1. Login
    try:
        resp = requests.post(f"{BASE_URL}/auth/token", data={"username": email, "password": password})
        if resp.status_code != 200:
            print(f"❌ Login Failed: {resp.text}")
            return
        
        token = resp.json()["access_token"]
        print("✅ Login Success")
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return

    # 2. Create API Key
    try:
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.post(f"{BASE_URL}/auth/keys", headers=headers, json={"label": "Demo Key"})
        if resp.status_code != 200:
            print(f"❌ Key Creation Failed: {resp.text}")
            return
            
        api_key = resp.json()["api_key"]
        print(f"✅ API Key Created: {api_key[:10]}...")
    except Exception as e:
        print(f"❌ Error creating key: {e}")
        return

    # 3. Test HTML Scan (Allowed for all)
    try:
        headers = {"X-API-Key": api_key}
        payload = {"url": "http://example.com", "html": "<html><body>Hello</body></html>", "query": "test"}
        resp = requests.post(f"{BASE_URL}/safe-ask", headers=headers, json=payload)
        
        if resp.status_code == 200:
            print("✅ HTML Scan (Active): Success")
        else:
            print(f"❌ HTML Scan Failed: {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"❌ Error scanning: {e}")

    # 4. Test PDF Scan (Gated)
    print(f"Testing PDF Scan (Should be {'BLOCKED' if tier_name == 'Free' else 'ALLOWED'})...")
    try:
        files = {'file': ('test.pdf', b'%PDF-1.4 empty pdf', 'application/pdf')}
        resp = requests.post(f"{BASE_URL}/scan-pdf", headers=headers, files=files)
        
        if resp.status_code == 200:
            print(f"✅ PDF Scan: Allowed (Status 200)")
        elif resp.status_code == 403:
            print(f"🛡️ PDF Scan: Blocked (Status 403) - Correct for Free Tier")
        else:
            print(f"ℹ️ PDF Scan Response: {resp.status_code} (Likely OCR missing, but not 403)")
    except Exception as e:
        print(f"❌ Error scanning PDF: {e}")

if __name__ == "__main__":
    print("🚀 Starting Live Demo...")
    demo_user("free@example.com", "password", "Free")
    demo_user("pro@example.com", "password", "Pro")
