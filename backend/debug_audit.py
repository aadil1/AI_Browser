from app.audit import get_audit_logger
import uuid

try:
    print("Initializing Audit Logger...")
    logger = get_audit_logger()
    print("Logger initialized.")
    
    logger.log_request(
        request_id=str(uuid.uuid4()),
        url="http://test.com",
        status="ok",
        risk_score=0.1,
        reasons=[],
        policy_violations=[]
    )
    print("Log written successfully.")
except Exception as e:
    print(f"❌ Error: {e}")
