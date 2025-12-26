"""
Pydantic schemas for API request/response validation.
"""
import re
from pydantic import BaseModel, HttpUrl, Field, field_validator


class SafeAskRequest(BaseModel):
    """Request body for /safe-ask endpoint."""
    url: HttpUrl = Field(..., description="URL of the page being analyzed")
    html: str = Field(..., description="Raw HTML content of the page")
    query: str = Field(..., min_length=1, max_length=2000, description="User's question about the page")


class SafeAskResponse(BaseModel):
    """Response body for /safe-ask endpoint."""
    status: str = Field(..., description="Response status: 'ok', 'blocked', or 'error'")
    answer: str | None = Field(default=None, description="LLM-generated answer (when status is 'ok')")
    risk_score: float | None = Field(default=None, ge=0.0, le=1.0, description="Injection risk score (0-1)")
    reason: str | None = Field(default=None, description="Reason for blocking or error message")
    explanations: list[str] | None = Field(default=None, description="Detailed human-readable explanations")
    version: str = Field(default="0.2.0", description="API version")
    request_id: str | None = Field(default=None, description="Unique request ID for debugging")


class HealthResponse(BaseModel):
    """Response body for /health endpoint."""
    status: str = Field(..., description="Overall health status")
    version: str = Field(..., description="API version")
    llm_configured: bool = Field(..., description="Whether LLM API key is configured")
    safety_threshold: float = Field(..., description="Current injection threshold")


class ScanHtmlRequest(BaseModel):
    """Request body for /scan-html endpoint (safety-only scanning)."""
    url: HttpUrl = Field(..., description="URL of the page being scanned")
    html: str = Field(..., description="Raw HTML content of the page")


class ScanHtmlResponse(BaseModel):
    """Response body for /scan-html endpoint."""
    is_safe: bool = Field(..., description="Whether the page passed safety checks")
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Injection risk score (0-1)")
    reason: str | None = Field(default=None, description="Reason if unsafe")
    explanations: list[str] | None = Field(default=None, description="Detailed human-readable explanations")
    policy_violations: list[str] | None = Field(default=None, description="Policy rule violations")
    request_id: str = Field(..., description="Unique request ID for debugging")


# Audit schemas
class AuditLogEntry(BaseModel):
    """Single audit log entry."""
    request_id: str
    timestamp: str
    url: str
    status: str
    risk_score: float
    reasons: list[str]
    policy_violations: list[str]


class AuditLogsResponse(BaseModel):
    """Response for /audit/logs endpoint."""
    logs: list[AuditLogEntry]
    total: int
    limit: int
    offset: int


class AuditStatsResponse(BaseModel):
    """Response for /audit/stats endpoint."""
    total_requests: int
    blocked_requests: int
    allowed_requests: int
    block_rate: float
    avg_risk_score: float
    top_blocked_domains: list[dict]
    requests_by_hour: list[dict]


# Sanitization schemas
class SanitizeRequest(BaseModel):
    """Request body for /sanitize endpoint."""
    chunks: list[str] = Field(..., min_length=1, max_length=1000, description="Text chunks to sanitize")
    url: str = Field(default="unknown", description="Source URL for policy evaluation")


class SanitizedChunkResult(BaseModel):
    """Result for a single sanitized chunk."""
    index: int
    is_safe: bool
    risk_score: float
    reason: str | None = None
    explanations: list[str] | None = None


class SanitizeResponse(BaseModel):
    """Response for /sanitize endpoint."""
    results: list[SanitizedChunkResult]
    safe_count: int
    flagged_count: int
    total_count: int
    request_id: str


# Document scanning schemas
class DocumentScanResponse(BaseModel):
    """Response for /scan-image and /scan-pdf endpoints."""
    is_safe: bool
    risk_score: float
    extracted_text: str = Field(default="", description="Extracted text (truncated)")
    reason: str | None = None
    explanations: list[str] | None = None
    policy_violations: list[str] | None = None
    page_count: int = 1
    request_id: str


# Auth Schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    api_key: str | None = None

class TokenData(BaseModel):
    email: str | None = None

class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    password: str
    org_name: str | None = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be 8 characters or more")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        return v

class UserRead(UserBase):
    id: int
    is_active: bool
    org_id: int | None = None


class APIKeyCreate(BaseModel):
    label: str = "My API Key"

class APIKeyRead(BaseModel):
    id: int
    label: str
    prefix: str
    created_at: str
    last_used_at: str | None = None

class APIKeyNew(BaseModel):
    """Response when creating a key - includes the raw secret."""
    api_key: str
    label: str
    prefix: str
    warning: str = "Save this key now. You won't be able to see it again."


class PasswordResetRequest(BaseModel):
    email: str

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        # Reuse logic from UserCreate (or better, refactor to shared validator)
        if len(v) < 8:
            raise ValueError("Password must be 8 characters or more")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        return v
