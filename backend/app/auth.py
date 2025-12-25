from datetime import datetime, timedelta
from typing import Optional
import hashlib
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt.exceptions import PyJWTError
from passlib.context import CryptContext
from sqlmodel import Session, select

from app.config import get_settings
from app.db import get_session
from app.models import User, Organization, APIKey

# Password Hashing
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
# Allow optional login (to checking API key if token missing)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    settings = get_settings()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    api_key_header: Optional[str] = Header(None, alias="X-API-Key"),
    session: Session = Depends(get_session)
):
    settings = get_settings()
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 1. Try JWT
    if token:
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            email: str = payload.get("sub")
            if email is None:
                raise credentials_exception
            
            statement = select(User).where(User.email == email)
            user = session.exec(statement).first()
            if user:
                return user
        except PyJWTError:
            pass # Fall through to API Key check

    # 2. Try API Key
    if api_key_header:
        # Replicate hash logic from main.py (FULL hash for auth, sliced for logs)
        key_hash = hashlib.sha256(api_key_header.encode()).hexdigest()
        statement = select(APIKey).where(APIKey.key_hash == key_hash)
        api_key_obj = session.exec(statement).first()
        
        if api_key_obj and api_key_obj.owner:
            return api_key_obj.owner

    # 3. Failed
    raise credentials_exception

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_superuser(current_user: User = Depends(get_current_user)):
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return current_user
