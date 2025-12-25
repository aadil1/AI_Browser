"""
Centralized configuration using Pydantic Settings.
All environment variables are loaded and validated here.
"""
import os
import hashlib
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import Set


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    openai_api_key: str = Field(default="", description="API key for LLM provider")
    openai_base_url: str | None = Field(default=None, description="Custom base URL for OpenAI-compatible APIs")
    openai_model: str = Field(default="gpt-4o-mini", description="Model name to use")
    
    # SafeBrowse API Keys (comma-separated for multiple keys)
    safebrowse_api_keys: str = Field(
        default="test-key",
        description="Comma-separated list of valid API keys"
    )

    # Auth Configuration
    secret_key: str = Field(default="dev-secret-key-change-in-prod", description="JWT Secret Key")
    algorithm: str = Field(default="HS256", description="JWT Algorithm")
    access_token_expire_minutes: int = Field(default=30, description="Token expiration time")
    
    # Safety Configuration
    injection_threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="Risk threshold for blocking pages")
    safety_model_enabled: bool = Field(default=False, description="Whether to use the ML safety model (requires torch)")
    
    # Server Configuration
    cors_origins: list[str] = Field(default=["*"], description="Allowed CORS origins")
    debug: bool = Field(default=False, description="Enable debug mode")
    
    # Version
    version: str = Field(default="1.0.0", description="API version")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [origin.strip() for origin in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    def get_valid_api_keys(self) -> Set[str]:
        """Parse and return the set of valid API keys."""
        keys = set()
        for key in self.safebrowse_api_keys.split(","):
            key = key.strip()
            if key:
                keys.add(key)
        return keys
    
    def is_valid_api_key(self, key: str) -> bool:
        """Check if an API key is valid using constant-time comparison."""
        if not key:
            return False
        
        valid_keys = self.get_valid_api_keys()
        
        # Use hash comparison for timing-attack resistance
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        for valid_key in valid_keys:
            valid_hash = hashlib.sha256(valid_key.encode()).hexdigest()
            if key_hash == valid_hash:
                return True
        
        return False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
