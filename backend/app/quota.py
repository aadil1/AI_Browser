from datetime import datetime
from fastapi import HTTPException
from sqlmodel import Session, select
from app.models import Organization, DailyUsage, Tier

# Limits per tier
TIER_LIMITS = {
    Tier.FREE: 100,
    Tier.PRO: 1000,
    Tier.ENTERPRISE: 1000000 # Effectively unlimited
}

def check_and_increment_quota(session: Session, org_id: int, tier: Tier):
    """
    Check if the organization has remaining quota for the day.
    If yes, increment and return True.
    If no, raise HTTPException(429).
    """
    today = datetime.utcnow().strftime("%Y-%m-%d")
    limit = TIER_LIMITS.get(tier, 100)
    
    # Get or create usage record
    statement = select(DailyUsage).where(
        DailyUsage.org_id == org_id,
        DailyUsage.date == today
    )
    usage = session.exec(statement).first()
    
    if not usage:
        usage = DailyUsage(org_id=org_id, date=today, request_count=0)
        session.add(usage)
    
    if usage.request_count >= limit:
        raise HTTPException(
            status_code=429,
            detail=f"Daily quota exceeded for {tier.value} tier ({limit} requests/day). Upgrade to increase limits."
        )
    
    usage.request_count += 1
    session.add(usage)
    session.commit()
    
    return True
