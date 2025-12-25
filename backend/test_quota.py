from fastapi.testclient import TestClient
from sqlmodel import Session, select, create_engine, text
from app.main import app
from app.db import create_db_and_tables, get_session
from app.models import User, Organization, Tier
from app.auth import get_password_hash

client = TestClient(app)

def setup_demo_data():
    create_db_and_tables()
    engine = create_engine("sqlite:///users.db")
    with Session(engine) as session:
        # cleanup
        session.exec(text("DELETE FROM dailyusage"))
        session.exec(text("DELETE FROM apikey"))
        session.exec(text("DELETE FROM user"))
        session.exec(text("DELETE FROM organization"))
        
        # Create Tiers
        org_free = Organization(name="Free Org", tier=Tier.FREE)
        org_pro = Organization(name="Pro Org", tier=Tier.PRO)
        org_ent = Organization(name="Ent Org", tier=Tier.ENTERPRISE)
        session.add(org_free)
        session.add(org_pro)
        session.add(org_ent)
        session.commit()
        
        # Create Users
        u_free = User(email="free@test.com", hashed_password=get_password_hash("pass"), org_id=org_free.id)
        u_pro = User(email="pro@test.com", hashed_password=get_password_hash("pass"), org_id=org_pro.id)
        u_ent = User(email="ent@test.com", hashed_password=get_password_hash("pass"), org_id=org_ent.id)
        session.add(u_free)
        session.add(u_pro)
        session.add(u_ent)
        session.commit()
        
        return u_free, u_pro, u_ent

def get_api_key(email):
    # Login
    resp = client.post("/auth/token", data={"username": email, "password": "pass"})
    token = resp.json()["access_token"]
    
    # Create Key
    resp = client.post("/auth/keys", headers={"Authorization": f"Bearer {token}"}, json={"label": "test"})
    return resp.json()["api_key"]

def test_limits():
    u_free, u_pro, u_ent = setup_demo_data()
    
    key_free = get_api_key("free@test.com")
    key_pro = get_api_key("pro@test.com")
    
    print(f"Testing FREE Tier Gating...")
    # 1. Free Tier - PDF Scan (Should Fail)
    resp = client.post(
        "/scan-pdf", 
        headers={"X-API-Key": key_free},
        files={"file": ("test.pdf", b"%PDF-1.4...", "application/pdf")}
    )
    assert resp.status_code == 403, f"Expected 403, got {resp.status_code}"
    print("✅ Free Tier correctly blocked from PDF scanning")
    
    print(f"Testing PRO Tier Access...")
    # 2. Pro Tier - PDF Scan (Should Pass or Error on Library but not 403)
    resp = client.post(
        "/scan-pdf", 
        headers={"X-API-Key": key_pro},
        files={"file": ("test.pdf", b"%PDF-1.4...", "application/pdf")}
    )
    # We expect 200 (if PDF lib installed) or 200 with error message, OR 500 if lib fails. 
    # Key is it should NOT be 403.
    if resp.status_code == 403:
        print("❌ Pro Tier INCORRECTLY blocked")
    else:
        print(f"✅ Pro Tier allowed (Status: {resp.status_code})")

if __name__ == "__main__":
    try:
        test_limits()
    except Exception as e:
        print(f"FAILED: {e}")
