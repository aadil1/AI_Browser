from sqlmodel import Session, create_engine, select
from app.db import create_db_and_tables, engine
from app.models import User, Organization, Tier
from app.auth import get_password_hash

def seed_data():
    print("🗑️  Cleaning up old data...")
    create_db_and_tables()
    
    with Session(engine) as session:
        # Check if data exists
        existing_org = session.exec(select(Organization)).first()
        if existing_org:
            print("⚠️  Data already exists. Skipping seed.")
            return

        print("🌱 Seeding tiers and users...")
        
        # 1. Organizations
        org_free = Organization(name="Startup Inc", tier=Tier.FREE)
        org_pro = Organization(name="ScaleUp Ltd", tier=Tier.PRO)
        org_ent = Organization(name="BigCorp Global", tier=Tier.ENTERPRISE, sso_enabled=True)
        
        session.add(org_free)
        session.add(org_pro)
        session.add(org_ent)
        session.commit()
        
        # 2. Users (Password: 'password')
        pwd_hash = get_password_hash("password")
        
        u_free = User(email="free@example.com", hashed_password=pwd_hash, org_id=org_free.id)
        u_pro = User(email="pro@example.com", hashed_password=pwd_hash, org_id=org_pro.id)
        u_ent = User(email="admin@bigcorp.com", hashed_password=pwd_hash, org_id=org_ent.id, is_superuser=True)
        
        session.add(u_free)
        session.add(u_pro)
        session.add(u_ent)
        session.commit()
        
        print("\n✅ Seed Complete!")
        print("------------------------------------------------")
        print(f"👤 Free User: free@example.com  (Org: {org_free.name})")
        print(f"👤 Pro User:  pro@example.com   (Org: {org_pro.name})")
        print(f"👤 Ent User:  admin@bigcorp.com (Org: {org_ent.name})")
        print("🔑 Password for all: 'password'")
        print("------------------------------------------------")

if __name__ == "__main__":
    seed_data()
