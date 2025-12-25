from datetime import datetime
from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from enum import Enum

class Tier(str, Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class Organization(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    tier: Tier = Field(default=Tier.FREE)
    sso_enabled: bool = Field(default=False)
    # Stripe or Billing ID could go here
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    users: List["User"] = Relationship(back_populates="organization")
    api_keys: List["APIKey"] = Relationship(back_populates="organization")

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    org_id: Optional[int] = Field(default=None, foreign_key="organization.id")
    organization: Optional[Organization] = Relationship(back_populates="users")
    
    api_keys: List["APIKey"] = Relationship(back_populates="owner")

class APIKey(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    key_hash: str = Field(index=True, unique=True)
    # The actual key is never stored, only the hash
    label: str = Field(default="My API Key")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used_at: Optional[datetime] = None
    
    user_id: int = Field(foreign_key="user.id")
    owner: User = Relationship(back_populates="api_keys")
    
    org_id: int = Field(foreign_key="organization.id")
    organization: Organization = Relationship(back_populates="api_keys")

class DailyUsage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    date: str = Field(index=True) # YYYY-MM-DD
    request_count: int = Field(default=0)
    
    org_id: int = Field(foreign_key="organization.id")
    # organization: Organization = Relationship(back_populates="daily_usage") # explicit backref if needed
