from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.main import app, get_session
from app.db import create_db_and_tables

# Setup Test DB
client = TestClient(app)

def test_auth_flow():
    # 1. Register User
    response = client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password123", "org_name": "TestCorp"}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    
    token = data["access_token"]
    print(f"[SUCCESS] Registered and got token: {token[:10]}...")

    # 2. Login User
    response = client.post(
        "/auth/token",
        data={"username": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 200, response.text
    login_data = response.json()
    assert "access_token" in login_data
    print("[SUCCESS] Logged in successfully")
    
    # 3. Fail Login
    response = client.post(
        "/auth/token",
        data={"username": "test@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    print("[SUCCESS] Failed login blocked correctly")

if __name__ == "__main__":
    # Create tables (using the main DB settings for now, or could use test fixture)
    print("Initializing DB...")
    create_db_and_tables()
    print("Running Auth Flow Test...")
    try:
        test_auth_flow()
        print("\nALL TESTS PASSED ✨")
    except AssertionError as e:
        print(f"\nTEST FAILED ❌: {e}")
    except Exception as e:
        print(f"\nERROR 💥: {e}")
