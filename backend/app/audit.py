"""
Audit logging system for compliance and debugging.
Supports SOC2, ISO 27001, and internal audits.
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from contextlib import contextmanager
from typing import Generator


# Database path
DB_PATH = Path(__file__).parent.parent / "audit.db"


@dataclass
class AuditEntry:
    """Single audit log entry."""
    request_id: str
    timestamp: str
    url: str
    status: str  # ok, blocked, error
    risk_score: float
    reasons: list[str]
    policy_violations: list[str]
    user_agent: str | None = None
    api_key_hash: str | None = None  # Hashed for privacy


@dataclass
class AuditStats:
    """Aggregated audit statistics."""
    total_requests: int
    blocked_requests: int
    allowed_requests: int
    avg_risk_score: float
    top_blocked_domains: list[dict]
    requests_by_hour: list[dict]


class AuditLogger:
    """
    SQLite-backed audit logging for compliance.
    
    Logs every request with:
    - Request ID
    - Timestamp
    - URL
    - Status (ok/blocked)
    - Risk score
    - Blocking reasons
    - Policy violations
    """
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize the database schema."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id TEXT UNIQUE NOT NULL,
                    timestamp TEXT NOT NULL,
                    url TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    status TEXT NOT NULL,
                    risk_score REAL NOT NULL,
                    reasons TEXT NOT NULL,
                    policy_violations TEXT NOT NULL,
                    user_agent TEXT,
                    api_key_hash TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Index for common queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_timestamp 
                ON audit_logs(timestamp)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_status 
                ON audit_logs(status)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_domain 
                ON audit_logs(domain)
            """)
            
            conn.commit()
    
    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Get database connection with context management."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc
        except Exception:
            return "unknown"
    
    def log_request(
        self,
        request_id: str,
        url: str,
        status: str,
        risk_score: float,
        reasons: list[str] | None = None,
        policy_violations: list[str] | None = None,
        user_agent: str | None = None,
        api_key_hash: str | None = None,
    ):
        """Log a request to the audit database."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO audit_logs 
                (request_id, timestamp, url, domain, status, risk_score, 
                 reasons, policy_violations, user_agent, api_key_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                request_id,
                datetime.utcnow().isoformat(),
                url,
                self._extract_domain(url),
                status,
                risk_score,
                json.dumps(reasons or []),
                json.dumps(policy_violations or []),
                user_agent,
                api_key_hash,
            ))
            conn.commit()
    
    def get_logs(
        self,
        limit: int = 100,
        offset: int = 0,
        status: str | None = None,
        domain: str | None = None,
    ) -> list[AuditEntry]:
        """Get paginated audit logs with optional filters."""
        query = "SELECT * FROM audit_logs WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        if domain:
            query += " AND domain LIKE ?"
            params.append(f"%{domain}%")
        
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            
            return [
                AuditEntry(
                    request_id=row["request_id"],
                    timestamp=row["timestamp"],
                    url=row["url"],
                    status=row["status"],
                    risk_score=row["risk_score"],
                    reasons=json.loads(row["reasons"]),
                    policy_violations=json.loads(row["policy_violations"]),
                    user_agent=row["user_agent"],
                    api_key_hash=row["api_key_hash"],
                )
                for row in rows
            ]
    
    def get_total_count(self, status: str | None = None, domain: str | None = None) -> int:
        """Get total count of audit logs with optional filters."""
        query = "SELECT COUNT(*) FROM audit_logs WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        if domain:
            query += " AND domain LIKE ?"
            params.append(f"%{domain}%")
        
        with self._get_connection() as conn:
            return conn.execute(query, params).fetchone()[0]
    
    def get_stats(self, hours: int = 24) -> AuditStats:
        """Get aggregated statistics for the last N hours."""
        with self._get_connection() as conn:
            # Total counts
            total = conn.execute(
                "SELECT COUNT(*) FROM audit_logs"
            ).fetchone()[0]
            
            blocked = conn.execute(
                "SELECT COUNT(*) FROM audit_logs WHERE status = 'blocked'"
            ).fetchone()[0]
            
            allowed = conn.execute(
                "SELECT COUNT(*) FROM audit_logs WHERE status = 'ok'"
            ).fetchone()[0]
            
            # Average risk score
            avg_risk = conn.execute(
                "SELECT AVG(risk_score) FROM audit_logs"
            ).fetchone()[0] or 0.0
            
            # Top blocked domains
            top_domains = conn.execute("""
                SELECT domain, COUNT(*) as count 
                FROM audit_logs 
                WHERE status = 'blocked'
                GROUP BY domain 
                ORDER BY count DESC 
                LIMIT 10
            """).fetchall()
            
            # Requests by hour (last 24 hours)
            hourly = conn.execute("""
                SELECT 
                    strftime('%Y-%m-%d %H:00', timestamp) as hour,
                    COUNT(*) as count,
                    SUM(CASE WHEN status = 'blocked' THEN 1 ELSE 0 END) as blocked
                FROM audit_logs
                GROUP BY hour
                ORDER BY hour DESC
                LIMIT ?
            """, (hours,)).fetchall()
            
            return AuditStats(
                total_requests=total,
                blocked_requests=blocked,
                allowed_requests=allowed,
                avg_risk_score=round(avg_risk, 3),
                top_blocked_domains=[
                    {"domain": row["domain"], "count": row["count"]}
                    for row in top_domains
                ],
                requests_by_hour=[
                    {"hour": row["hour"], "total": row["count"], "blocked": row["blocked"]}
                    for row in hourly
                ],
            )


# Global audit logger instance
_audit_logger: AuditLogger | None = None


def get_audit_logger() -> AuditLogger:
    """Get or create the global audit logger."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger
