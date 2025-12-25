"""
Prompt-Injection Firewall & Policy Engine - FastAPI Backend
Production-ready API with health checks, policy engine, and audit logging.
"""
import logging
import time
import uuid
import hashlib
import sys
from contextlib import asynccontextmanager

# Force UTF-8 for Windows consoles
sys.stdout.reconfigure(encoding='utf-8') 
sys.stderr.reconfigure(encoding='utf-8')

from fastapi import FastAPI, Request, Header, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from app.config import get_settings
from app.schemas import (
    SafeAskRequest, SafeAskResponse, HealthResponse,
    ScanHtmlRequest, ScanHtmlResponse,
    AuditLogsResponse, AuditLogEntry, AuditStatsResponse
)
from app.heuristic_safety import is_page_safe
from app.agent import browsing_agent_answer
from app.policy_engine import get_policy_engine
from app.audit import get_audit_logger
from app.db import create_db_and_tables, get_session
from app.auth import create_access_token, verify_password, get_password_hash, get_current_user
from app.models import User, Organization, APIKey
from app.schemas import Token, UserCreate, UserRead, APIKeyCreate, APIKeyRead, APIKeyNew
import secrets
from fastapi.security import OAuth2PasswordRequestForm
from app.quota import check_and_increment_quota
from sqlmodel import Session, select
from datetime import datetime, timedelta

# Constants
MAX_HTML_SIZE = 5_000_000  # 5 MB


async def get_current_org_and_check_quota(
    api_key: str = Header(..., alias="X-API-Key"),
    session: Session = Depends(get_session)
) -> Organization:
    """
    Validates API Key, finds Organization, and Checks Quota.
    Returns the Organization object if successful.
    """
    # 1. Hash key to find in DB
    # Note: In real app, we might salt or use specific lookup field
    # For now, we assume client sends raw key, we hash and look up 'key_hash'
    # BUT wait, earlier we implemented hashing on creation.
    # To look it up, we need to hash the incoming key.
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    statement = select(APIKey).where(APIKey.key_hash == key_hash, APIKey.is_active == True)
    db_key = session.exec(statement).first()
    
    if not db_key:
        # Fallback to config-based keys for backward compatibility/admin
        settings = get_settings()
        if settings.is_valid_api_key(api_key):
             # Allow system/test keys to bypass database check
             return Organization(id=0, name="System/Test", tier="enterprise", created_at=datetime.utcnow())
        
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # 2. Update Last Used
    db_key.last_used_at = datetime.utcnow()
    session.add(db_key)
    
    # 3. Check Quota
    org = session.get(Organization, db_key.org_id)
    if not org:
        raise HTTPException(status_code=500, detail="Orphaned API Key")
        
    check_and_increment_quota(session, org.id, org.tier)
    
    return org


def hash_api_key(api_key: str) -> str:
    """Hash API key for audit logging (privacy)."""
    return hashlib.sha256(api_key.encode()).hexdigest()[:16]


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    settings = get_settings()
    logger.info(f"🚀 Starting Prompt-Injection Firewall v{settings.version}")
    logger.info(f"📊 LLM Model: {settings.openai_model}")
    logger.info(f"🛡️ Injection Threshold: {settings.injection_threshold}")
    logger.info(f"📋 Policy Engine: Enabled")
    logger.info(f"📝 Audit Logging: Enabled")
    
    # Initialize Database
    create_db_and_tables()
    logger.info(f"💾 Database: Initialized (SQLite)")
    
    if not settings.openai_api_key:
        logger.warning("⚠️ OPENAI_API_KEY not configured - LLM features will fail")
    
    yield
    
    logger.info("👋 Shutting down...")


# Initialize FastAPI app
settings = get_settings()
app = FastAPI(
    title="Prompt-Injection Firewall & Policy Engine",
    description="Protect AI systems from prompt injection attacks with policy engine and audit logging",
    version=settings.version,
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Mount Dashboard (if available)
dashboard_dir = None
if os.path.exists("dashboard"):
    dashboard_dir = "dashboard"
elif os.path.exists("../dashboard"):
    dashboard_dir = "../dashboard"

if dashboard_dir:
    app.mount("/dashboard", StaticFiles(directory=dashboard_dir, html=True), name="dashboard")
    
    @app.get("/dashboard")
    async def dashboard_root():
        return FileResponse(os.path.join(dashboard_dir, "index.html"))


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests with timing."""
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} - {response.status_code} - {duration:.3f}s"
    )
    
    return response


@app.get("/", tags=["Public"])
async def root():
    """Serve the public landing page."""
    if os.path.exists("landing.html"):
         return FileResponse("landing.html")
    elif os.path.exists("../landing.html"):
         return FileResponse("../landing.html")
    return {"status": "running", "version": settings.version}


@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    """Detailed health check with dependency status."""
    return HealthResponse(
        status="healthy",
        version=settings.version,
        llm_configured=bool(settings.openai_api_key),
        safety_threshold=settings.injection_threshold,
    )


@app.post("/safe-ask", response_model=SafeAskResponse, tags=["Core"])
async def safe_ask(
    payload: SafeAskRequest, 
    org: Organization = Depends(get_current_org_and_check_quota),
    api_key: str = Header(..., alias="X-API-Key")
):
    """
    Safely answer a question about a webpage.
    
    1. Validates API key
    2. Checks HTML size limits
    3. Evaluates policy rules
    4. Checks for prompt injection attacks
    5. If safe, sends to LLM for answering
    6. Logs to audit trail
    """
    request_id = str(uuid.uuid4())
    url_str = str(payload.url)
    audit_logger = get_audit_logger()
    policy_engine = get_policy_engine()
    
    # API key is validated by Depends(get_current_org_and_check_quota)
    
    all_explanations = []
    policy_violations = []
    
    # Check HTML size limit
    if len(payload.html) > MAX_HTML_SIZE:
        logger.warning(f"[{request_id}] Page too large: {len(payload.html)} bytes")
        all_explanations.append("Content exceeds maximum size limit (5MB)")
        
        audit_logger.log_request(
            request_id=request_id,
            url=url_str,
            status="blocked",
            risk_score=1.0,
            reasons=all_explanations,
            policy_violations=[],
            api_key_hash=hash_api_key(api_key),
        )
        
        return SafeAskResponse(
            status="blocked",
            reason="Page too large to analyze safely (max 5MB)",
            explanations=all_explanations,
            risk_score=1.0,
            version=settings.version,
            request_id=request_id,
        )
    
    # Step 1: Policy check
    if org.tier != "free":
        policy_result = policy_engine.evaluate(payload.html, url_str)
        if policy_result.violations:
            policy_violations = policy_result.explanations
            all_explanations.extend(policy_violations)
    else:
        # Free tier skips policy engine
        from app.policy_engine import PolicyResult
        policy_result = PolicyResult(allowed=True, violations=[])
    
    if not policy_result.allowed:
        logger.warning(f"[{request_id}] Policy blocked: {policy_violations}")
        
        audit_logger.log_request(
            request_id=request_id,
            url=url_str,
            status="blocked",
            risk_score=policy_result.risk_score,
            reasons=all_explanations,
            policy_violations=policy_violations,
            api_key_hash=hash_api_key(api_key),
        )
        
        return SafeAskResponse(
            status="blocked",
            reason="Page blocked by security policy",
            explanations=all_explanations,
            risk_score=policy_result.risk_score,
            version=settings.version,
            request_id=request_id,
        )
    
    # Step 2: Safety check (prompt injection)
    try:
        is_safe, risk = is_page_safe(payload.html)
    except Exception as e:
        logger.error(f"[{request_id}] Safety check failed: {e}")
        all_explanations.append("Safety system encountered an error (fail-closed)")
        
        audit_logger.log_request(
            request_id=request_id,
            url=url_str,
            status="blocked",
            risk_score=1.0,
            reasons=all_explanations,
            policy_violations=policy_violations,
            api_key_hash=hash_api_key(api_key),
        )
        
        return SafeAskResponse(
            status="blocked",
            reason="Safety system failure (fail-closed)",
            explanations=all_explanations,
            risk_score=1.0,
            version=settings.version,
            request_id=request_id,
        )

    # Combine policy and safety risks
    combined_risk = max(risk, policy_result.risk_score)
    
    # Step 3: Block if unsafe
    if not is_safe:
        all_explanations.append("Content matched prompt injection detection patterns")
        logger.warning(f"[{request_id}] Page blocked - risk: {risk:.2f}, url: {url_str}")
        
        audit_logger.log_request(
            request_id=request_id,
            url=url_str,
            status="blocked",
            risk_score=combined_risk,
            reasons=all_explanations,
            policy_violations=policy_violations,
            api_key_hash=hash_api_key(api_key),
        )
        
        return SafeAskResponse(
            status="blocked",
            reason="⚠️ This page has been flagged for possible prompt-injection or malicious instructions.",
            explanations=all_explanations,
            risk_score=combined_risk,
            version=settings.version,
            request_id=request_id,
        )

    # Step 4: Get LLM answer
    try:
        answer = browsing_agent_answer(
            query=payload.query,
            html=payload.html,
            url=url_str,
        )
    except Exception as e:
        logger.error(f"[{request_id}] LLM agent failed: {e}")
        all_explanations.append("LLM service encountered an error (fail-closed)")
        
        audit_logger.log_request(
            request_id=request_id,
            url=url_str,
            status="blocked",
            risk_score=1.0,
            reasons=all_explanations,
            policy_violations=policy_violations,
            api_key_hash=hash_api_key(api_key),
        )
        
        return SafeAskResponse(
            status="blocked",
            reason="LLM service failure (fail-closed)",
            explanations=all_explanations,
            risk_score=1.0,
            version=settings.version,
            request_id=request_id,
        )

    # Success - log and return
    audit_logger.log_request(
        request_id=request_id,
        url=url_str,
        status="ok",
        risk_score=combined_risk,
        reasons=[],
        policy_violations=policy_violations,
        api_key_hash=hash_api_key(api_key),
    )

    return SafeAskResponse(
        status="ok",
        answer=answer,
        risk_score=combined_risk,
        version=settings.version,
        request_id=request_id,
    )


@app.post("/scan-html", response_model=ScanHtmlResponse, tags=["Core"])
async def scan_html(payload: ScanHtmlRequest, org: Organization = Depends(get_current_org_and_check_quota)):
    """
    Scan HTML for prompt injection and policy violations without LLM processing.
    Useful for agents, scrapers, and security teams.
    """
    request_id = str(uuid.uuid4())
    url_str = str(payload.url)
    policy_engine = get_policy_engine()
    audit_logger = get_audit_logger()
    
    # API key is validated by Depends(get_current_org_and_check_quota)
    
    all_explanations = []
    policy_violations = []
    
    # Check HTML size limit
    if len(payload.html) > MAX_HTML_SIZE:
        return ScanHtmlResponse(
            is_safe=False,
            risk_score=1.0,
            reason="Page too large to analyze safely (max 5MB)",
            explanations=["Content exceeds maximum size limit (5MB)"],
            policy_violations=[],
            request_id=request_id,
        )
    
    # Policy check
    if org.tier != "free":
        policy_result = policy_engine.evaluate(payload.html, url_str)
        if policy_result.violations:
            policy_violations = policy_result.explanations
            all_explanations.extend(policy_violations)
    else:
         from app.policy_engine import PolicyResult
         policy_result = PolicyResult(allowed=True, violations=[])
    
    # Safety check
    try:
        is_safe, risk = is_page_safe(payload.html)
    except Exception as e:
        logger.error(f"[{request_id}] Safety scan failed: {e}")
        return ScanHtmlResponse(
            is_safe=False,
            risk_score=1.0,
            reason="Safety system failure (fail-closed)",
            explanations=["Safety system encountered an error"],
            policy_violations=policy_violations,
            request_id=request_id,
        )
    
    # Combine results
    combined_risk = max(risk, policy_result.risk_score)
    final_is_safe = is_safe and policy_result.allowed
    
    if not is_safe:
        all_explanations.append("Content matched prompt injection detection patterns")
    
    # Log to audit
    audit_logger.log_request(
        request_id=request_id,
        url=url_str,
        status="ok" if final_is_safe else "blocked",
        risk_score=combined_risk,
        reasons=all_explanations,
        policy_violations=policy_violations,
    )
    
    return ScanHtmlResponse(
        is_safe=final_is_safe,
        risk_score=combined_risk,
        reason=None if final_is_safe else "Content flagged by safety or policy checks",
        explanations=all_explanations if all_explanations else None,
        policy_violations=policy_violations if policy_violations else None,
        request_id=request_id,
    )


# ============== Audit Endpoints ==============

@app.get("/audit/logs", response_model=AuditLogsResponse, tags=["Audit"])
async def get_audit_logs(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    status: str | None = Query(default=None, description="Filter by status: ok, blocked"),
    domain: str | None = Query(default=None, description="Filter by domain (partial match)"),
    org: Organization = Depends(get_current_org_and_check_quota),
):
    """
    Get paginated audit logs.
    [PRO and ENTERPRISE]
    """
    if org.tier == "free":
        raise HTTPException(status_code=403, detail="Audit logs are available on PRO and ENTERPRISE tiers.")
    
    audit_logger = get_audit_logger()
    logs = audit_logger.get_logs(limit=limit, offset=offset, status=status, domain=domain)
    
    return AuditLogsResponse(
        logs=[
            AuditLogEntry(
                request_id=log.request_id,
                timestamp=log.timestamp,
                url=log.url,
                status=log.status,
                risk_score=log.risk_score,
                reasons=log.reasons,
                policy_violations=log.policy_violations,
            )
            for log in logs
        ],
        total=audit_logger.get_total_count(status=status, domain=domain),
        limit=limit,
        offset=offset,
    )


@app.get("/audit/stats", response_model=AuditStatsResponse, tags=["Audit"])
async def get_audit_stats(
    hours: int = Query(default=24, ge=1, le=720),
    org: Organization = Depends(get_current_org_and_check_quota),
):
    """
    Get aggregated audit statistics.
    Useful for dashboards and compliance reporting.
    """
    if org.tier == "free":
        raise HTTPException(status_code=403, detail="Audit stats are available on PRO and ENTERPRISE tiers.")
    
    # API key validated by dependency
    
    audit_logger = get_audit_logger()
    stats = audit_logger.get_stats(hours=hours)
    
    block_rate = 0.0
    if stats.total_requests > 0:
        block_rate = round(stats.blocked_requests / stats.total_requests * 100, 2)
    
    return AuditStatsResponse(
        total_requests=stats.total_requests,
        blocked_requests=stats.blocked_requests,
        allowed_requests=stats.allowed_requests,
        block_rate=block_rate,
        avg_risk_score=stats.avg_risk_score,
        top_blocked_domains=stats.top_blocked_domains,
        requests_by_hour=stats.requests_by_hour,
    )


# ============== RAG Sanitization Endpoints ==============

from app.schemas import SanitizeRequest, SanitizeResponse, SanitizedChunkResult
from app.sanitizer import sanitize_chunks


@app.post("/sanitize", response_model=SanitizeResponse, tags=["RAG"])
async def sanitize_dataset(
    payload: SanitizeRequest,
    org: Organization = Depends(get_current_org_and_check_quota),
):
    """
    Sanitize multiple content chunks for RAG/data pipelines.
    
    Use this to clean scraped content before indexing in vector databases.
    Returns safety status for each chunk with explanations.
    """
    request_id = str(uuid.uuid4())
    # API key validated by dependency
    
    result = sanitize_chunks(payload.chunks, payload.url)
    
    return SanitizeResponse(
        results=[
            SanitizedChunkResult(
                index=r.index,
                is_safe=r.is_safe,
                risk_score=r.risk_score,
                reason=r.reason,
                explanations=r.explanations,
            )
            for r in result.results
        ],
        safe_count=result.safe_count,
        flagged_count=result.flagged_count,
        total_count=result.total_count,
        request_id=request_id,
    )


# ============== Document Scanning Endpoints ==============

from fastapi import UploadFile, File
from app.schemas import DocumentScanResponse
from app.ocr_scanner import scan_image, scan_pdf, check_ocr_available, check_pdf_available


@app.post("/scan-image", response_model=DocumentScanResponse, tags=["Documents"])
async def scan_image_endpoint(
    file: UploadFile = File(..., description="Image file to scan"),
    org: Organization = Depends(get_current_org_and_check_quota),
):
    """
    Scan an image for hidden prompt injection via OCR.
    
    Extracts text from the image and runs it through safety checks.
    Supports: PNG, JPG, JPEG, GIF, BMP, TIFF
    """
    request_id = str(uuid.uuid4())
    
    # if not verify_api_key(api_key):
    #     raise HTTPException(status_code=401, detail="Invalid API key")
    
    if org.tier == "free":
        raise HTTPException(status_code=403, detail="Image scanning is available on PRO and ENTERPRISE tiers.")
    
    # Check OCR availability
    available, error = check_ocr_available()
    if not available:
        return DocumentScanResponse(
            is_safe=False,
            risk_score=1.0,
            extracted_text="",
            reason=f"OCR not available: {error}",
            explanations=["Install pytesseract and Tesseract OCR to enable image scanning"],
            request_id=request_id,
        )
    
    # Read file
    try:
        image_data = await file.read()
    except Exception as e:
        return DocumentScanResponse(
            is_safe=False,
            risk_score=1.0,
            extracted_text="",
            reason=f"Failed to read image: {e}",
            request_id=request_id,
        )
    
    # Scan image
    result = scan_image(image_data, source=file.filename or "image")
    
    return DocumentScanResponse(
        is_safe=result.is_safe,
        risk_score=result.risk_score,
        extracted_text=result.extracted_text,
        reason=result.reason,
        explanations=result.explanations,
        policy_violations=result.policy_violations,
        page_count=result.page_count,
        request_id=request_id,
    )


@app.post("/scan-pdf", response_model=DocumentScanResponse, tags=["Documents"])
async def scan_pdf_endpoint(
    file: UploadFile = File(..., description="PDF file to scan"),
    org: Organization = Depends(get_current_org_and_check_quota),
):
    """
    Scan a PDF for hidden prompt injection.
    
    Extracts text from all pages and runs through safety checks.
    Uses OCR for image-based pages.
    """
    request_id = str(uuid.uuid4())
    
    if org.tier == "free":
        raise HTTPException(status_code=403, detail="PDF scanning is available on PRO and ENTERPRISE tiers.")
    
    # Check PDF availability
    available, error = check_pdf_available()
    if not available:
        return DocumentScanResponse(
            is_safe=False,
            risk_score=1.0,
            extracted_text="",
            reason=f"PDF scanning not available: {error}",
            explanations=["Install PyMuPDF to enable PDF scanning"],
            request_id=request_id,
        )
    
    # Read file
    try:
        pdf_data = await file.read()
    except Exception as e:
        return DocumentScanResponse(
            is_safe=False,
            risk_score=1.0,
            extracted_text="",
            reason=f"Failed to read PDF: {e}",
            request_id=request_id,
        )
    
    # Scan PDF
    result = scan_pdf(pdf_data, source=file.filename or "pdf")
    
    return DocumentScanResponse(
        is_safe=result.is_safe,
        risk_score=result.risk_score,
        extracted_text=result.extracted_text,
        reason=result.reason,
        explanations=result.explanations,
        policy_violations=result.policy_violations,
        page_count=result.page_count,
        request_id=request_id,
    )


@app.get("/capabilities", tags=["Health"])
async def get_capabilities():
    """
    Get available scanning capabilities.
    Shows which features are available based on installed dependencies.
    """
    ocr_available, ocr_msg = check_ocr_available()
    pdf_available, pdf_msg = check_pdf_available()
    
    return {
        "html_scanning": True,
        "policy_engine": True,
        "audit_logging": True,
        "rag_sanitization": True,
        "image_ocr": ocr_available,
        "image_ocr_status": ocr_msg,
        "pdf_scanning": pdf_available,
        "pdf_scanning_status": pdf_msg,
        "agent_guardrails": True,
        "red_team_testing": True,
    }


# ============== Red Team Testing Endpoints ==============

from app.red_team import (
    ATTACK_SCENARIOS, get_scenario, get_all_scenarios,
    run_scenario_test, run_all_tests, get_detection_rate, TestResult
)
from app.heuristic_safety import is_page_safe
from app.policy_engine import get_policy_engine


def _scan_for_redteam(html: str) -> tuple[bool, float, list[str]]:
    """Wrapper for red team testing."""
    policy_engine = get_policy_engine()
    explanations = []
    
    # Policy check
    policy_result = policy_engine.evaluate(html, "redteam-test")
    if policy_result.violations:
        explanations.extend(policy_result.explanations)
    
    # Safety check
    try:
        is_safe, risk = is_page_safe(html)
    except Exception:
        return False, 1.0, ["Safety check error"]
    
    if not is_safe:
        explanations.append("Prompt injection pattern detected")
    
    combined_risk = max(risk, policy_result.risk_score)
    final_is_safe = is_safe and policy_result.allowed
    
    return final_is_safe, combined_risk, explanations


@app.get("/test/scenarios", tags=["Testing"])
async def list_attack_scenarios():
    """List all available attack scenarios for red team testing."""
    return {
        "scenarios": [
            {
                "id": s.id,
                "name": s.name,
                "category": s.category.value,
                "severity": s.severity,
                "description": s.description,
            }
            for s in get_all_scenarios()
        ],
        "total": len(ATTACK_SCENARIOS),
    }


@app.post("/test/red-team", tags=["Testing"])
async def run_red_team_test(
    scenario_ids: list[str] | None = None,
    org: Organization = Depends(get_current_org_and_check_quota),
):
    """
    Run red team attack scenarios against SafeBrowse.
    
    Tests your defenses against known prompt injection attacks.
    
    Args:
        scenario_ids: Optional list of scenario IDs to test. If empty, runs all.
    """
    # API key validated by dependency
    
    if scenario_ids:
        # Run specific scenarios
        results = []
        for sid in scenario_ids:
            if sid in ATTACK_SCENARIOS:
                result = run_scenario_test(sid, _scan_for_redteam)
                results.append(result)
    else:
        # Run all scenarios
        results = run_all_tests(_scan_for_redteam)
    
    stats = get_detection_rate(results)
    
    return {
        "results": [
            {
                "scenario_id": r.scenario_id,
                "scenario_name": r.scenario_name,
                "detected": r.detected,
                "risk_score": r.risk_score,
                "explanations": r.explanations,
            }
            for r in results
        ],
        "statistics": stats,
    }


# ============== Auth Endpoints ==============

@app.post("/auth/register", response_model=Token, tags=["Auth"])
async def register(
    user_in: UserCreate,
    session: Session = Depends(get_session)
):
    """
    Register a new user and organization.
    Auto-generates an API key for immediate use.
    """
    # 1. Check if user exists
    statement = select(User).where(User.email == user_in.email)
    existing_user = session.exec(statement).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="User with this email already exists"
        )
    
    # 2. Create Organization
    org = Organization(
        name=user_in.org_name or f"{user_in.email.split('@')[0]}'s Org",
        tier="free"
    )
    session.add(org)
    session.commit()
    session.refresh(org)
    
    # 3. Create User
    hashed_password = get_password_hash(user_in.password)
    user = User(
        email=user_in.email,
        hashed_password=hashed_password,
        org_id=org.id,
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    # 4. Create Initial API Key
    # Generate random key
    raw_key = f"sb_live_{secrets.token_urlsafe(24)}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    
    api_key = APIKey(
        key_hash=key_hash,
        label="Default Key",
        user_id=user.id,
        org_id=org.id
    )
    session.add(api_key)
    session.commit()
    
    # 5. Generate Login Token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "api_key": raw_key
    }


@app.post("/auth/token", response_model=Token, tags=["Auth"])
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session)
):
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    statement = select(User).where(User.email == form_data.username)
    user = session.exec(statement).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/auth/keys", response_model=list[APIKeyRead], tags=["Auth"])
async def get_api_keys(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """List API keys for the current user."""
    statement = select(APIKey).where(APIKey.user_id == current_user.id, APIKey.is_active == True)
    keys = session.exec(statement).all()
    return [
        APIKeyRead(
            id=k.id,
            label=k.label,
            prefix=k.key_hash[:8] + "...", # In real app, store prefix separately
            created_at=k.created_at.isoformat(),
            last_used_at=k.last_used_at.isoformat() if k.last_used_at else None
        )
        for k in keys
    ]


@app.post("/auth/keys", response_model=APIKeyNew, tags=["Auth"])
async def create_api_key(
    key_in: APIKeyCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Generate a new API key."""
    # Enforce limit (e.g., max 5 keys)
    statement = select(APIKey).where(APIKey.user_id == current_user.id, APIKey.is_active == True)
    existing_count = len(session.exec(statement).all())
    if existing_count >= 5:
        raise HTTPException(status_code=400, detail="Maximum of 5 API keys allowed")

    raw_key = f"sb_live_{secrets.token_urlsafe(24)}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    
    api_key = APIKey(
        key_hash=key_hash,
        label=key_in.label,
        user_id=current_user.id,
        org_id=current_user.org_id
    )
    session.add(api_key)
    session.commit()
    session.refresh(api_key)
    
    return APIKeyNew(
        api_key=raw_key,
        label=api_key.label,
        prefix=raw_key[:8] + "...",
        warning="Save this key now. You won't be able to see it again."
    )



@app.get("/auth/me", response_model=UserRead, tags=["Auth"])
async def read_users_me(
    current_user: User = Depends(get_current_user)
):
    """Get current user details."""
    return current_user


# ============== Agent Guard Endpoints ==============

from app.agent_guard import AgentGuard, GuardSession, get_default_guard

# In-memory session storage (use Redis in production)
_active_sessions: dict[str, GuardSession] = {}


@app.post("/agent/session/start", tags=["Agent Guard"])
async def start_agent_session(
    max_steps: int = 100,
    max_retries: int = 5,
    timeout_seconds: float = 300,
    org: Organization = Depends(get_current_org_and_check_quota),
):
    """
    Start a new guarded agent session.
    
    Returns a session_id to use for recording steps.
    """
    # Auth handled by dependency
    
    guard = AgentGuard(
        max_steps=max_steps,
        max_retries=max_retries,
        timeout_seconds=timeout_seconds,
    )
    
    session_id = str(uuid.uuid4())
    session = GuardSession(guard=guard, session_id=session_id)
    _active_sessions[session_id] = session
    
    return {
        "session_id": session_id,
        "limits": {
            "max_steps": max_steps,
            "max_retries": max_retries,
            "timeout_seconds": timeout_seconds,
        },
    }


@app.post("/agent/session/{session_id}/step", tags=["Agent Guard"])
async def record_agent_step(
    session_id: str,
    action_type: str,
    action_name: str,
    success: bool = True,
    org: Organization = Depends(get_current_org_and_check_quota),
):
    """
    Record an agent step in a guarded session.
    
    Will raise error if limits are exceeded.
    """
    # Auth handled by dependency
    
    session = _active_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        step = session.record_step(
            action_type=action_type,
            action_name=action_name,
            success=success,
        )
        return {
            "step_id": step.step_id,
            "session_summary": session.get_summary(),
        }
    except Exception as e:
        # Session violated guardrails
        return {
            "error": str(e),
            "session_summary": session.get_summary(),
            "stopped": True,
        }


@app.get("/agent/session/{session_id}", tags=["Agent Guard"])
async def get_agent_session(
    session_id: str,
    org: Organization = Depends(get_current_org_and_check_quota),
):
    """Get the current state of an agent session."""
    # Auth handled by dependency
    
    session = _active_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session.get_summary()


@app.delete("/agent/session/{session_id}", tags=["Agent Guard"])
async def end_agent_session(
    session_id: str,
    org: Organization = Depends(get_current_org_and_check_quota),
):
    """End an agent session."""
    # Auth handled by dependency
    
    session = _active_sessions.pop(session_id, None)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "message": "Session ended",
        "final_summary": session.get_summary(),
    }


# ============== Auth Endpoints ==============

@app.post("/auth/token", response_model=Token, tags=["Auth"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    statement = select(User).where(User.email == form_data.username)
    user = session.exec(statement).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/auth/register", response_model=Token, tags=["Auth"])
async def register_user(user: UserCreate, session: Session = Depends(get_session)):
    """Register a new user and organization."""
    # Check if user exists
    statement = select(User).where(User.email == user.email)
    existing_user = session.exec(statement).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create Organization
    org_name = user.org_name if user.org_name else f"{user.email}'s Org"
    org = Organization(name=org_name)
    
    session.add(org)
    session.commit()
    session.refresh(org)
    
    hashed_pwd = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        hashed_password=hashed_pwd,
        org_id=org.id
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    
    access_token = create_access_token(data={"sub": db_user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/auth/keys", response_model=APIKeyNew, tags=["Auth"])
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Create a new API Key."""
    # Generate random key
    raw_key = f"sb-{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    
    api_key = APIKey(
        key_hash=key_hash,
        label=key_data.label,
        user_id=current_user.id,
        org_id=current_user.org_id
    )
    session.add(api_key)
    session.commit()
    session.refresh(api_key)
    
    return {
        "api_key": raw_key,
        "label": api_key.label,
        "prefix": raw_key[:6] + "...",
    }

@app.get("/auth/keys", response_model=list[APIKeyRead], tags=["Auth"])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """List my API Keys."""
    statement = select(APIKey).where(APIKey.user_id == current_user.id)
    keys = session.exec(statement).all()
    
    results = []
    for k in keys:
        results.append({
            "id": k.id,
            "label": k.label,
            "prefix": "sb-******", # Placeholder since we didn't store prefix
            "created_at": k.created_at.isoformat(),
            "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None
        })
    return results
