"""
Policy Engine for rule-based content blocking.
Allows enterprises to define custom security policies.
"""
import re
from dataclasses import dataclass, field
from enum import Enum
from urllib.parse import urlparse
from bs4 import BeautifulSoup


class RuleType(str, Enum):
    """Types of policy rules."""
    FORMS = "forms"
    LOGIN = "login"
    PAYMENT = "payment"
    DOMAIN_BLOCK = "domain_block"
    DOMAIN_ALLOW = "domain_allow"
    TLD_BLOCK = "tld_block"
    KEYWORD_BLOCK = "keyword_block"


@dataclass
class PolicyViolation:
    """Represents a policy violation."""
    rule_type: RuleType
    description: str
    severity: float  # 0.0 to 1.0


@dataclass
class PolicyResult:
    """Result of policy evaluation."""
    allowed: bool
    violations: list[PolicyViolation] = field(default_factory=list)
    
    @property
    def risk_score(self) -> float:
        """Calculate risk score from violations."""
        if not self.violations:
            return 0.0
        return max(v.severity for v in self.violations)
    
    @property
    def explanations(self) -> list[str]:
        """Get human-readable explanations."""
        return [v.description for v in self.violations]


class PolicyEngine:
    """
    Rule-based content blocking engine.
    
    Evaluates HTML content and URLs against configurable policies.
    """
    
    # Default suspicious TLDs
    SUSPICIOUS_TLDS = {".xyz", ".top", ".work", ".click", ".loan", ".gq", ".ml", ".cf", ".tk"}
    
    # Payment-related keywords
    PAYMENT_KEYWORDS = {
        "credit card", "card number", "cvv", "expiry", "billing address",
        "payment", "checkout", "pay now", "add to cart", "purchase"
    }
    
    # Login-related patterns - match both single and double quotes
    LOGIN_PATTERNS = [
        r'type=["\']?password["\']?',
        r'name=["\']?password["\']?',
        r'id=["\']?password["\']?',
        r'autocomplete=["\']?current-password["\']?',
        r'autocomplete=["\']?new-password["\']?',
        r'<input[^>]*password',  # Generic password input
    ]
    
    def __init__(self):
        self.blocked_domains: set[str] = set()
        self.allowed_domains: set[str] = set()
        self.blocked_tlds: set[str] = self.SUSPICIOUS_TLDS.copy()
        self.blocked_keywords: set[str] = set()
        
        # Feature flags for built-in rules
        self.block_forms = False
        self.block_login = True  # Default: block login pages
        self.block_payment = False
        self.enforce_domain_allowlist = False  # If True, only allowed domains pass
    
    def add_blocked_domain(self, domain: str):
        """Add a domain to the blocklist."""
        self.blocked_domains.add(domain.lower())
    
    def add_allowed_domain(self, domain: str):
        """Add a domain to the allowlist."""
        self.allowed_domains.add(domain.lower())
    
    def add_blocked_tld(self, tld: str):
        """Add a TLD to the blocklist."""
        if not tld.startswith("."):
            tld = "." + tld
        self.blocked_tlds.add(tld.lower())
    
    def add_blocked_keyword(self, keyword: str):
        """Add a keyword to block."""
        self.blocked_keywords.add(keyword.lower())
    
    def _check_domain(self, url: str) -> list[PolicyViolation]:
        """Check domain against blocklist/allowlist."""
        violations = []
        
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Check explicit blocklist
            if domain in self.blocked_domains:
                violations.append(PolicyViolation(
                    rule_type=RuleType.DOMAIN_BLOCK,
                    description=f"Domain '{domain}' is on the blocklist",
                    severity=1.0
                ))
            
            # Check TLD blocklist - high severity to actually block
            for tld in self.blocked_tlds:
                if domain.endswith(tld):
                    violations.append(PolicyViolation(
                        rule_type=RuleType.TLD_BLOCK,
                        description=f"Domain has suspicious TLD: {tld} - blocked by policy",
                        severity=1.0  # High severity to trigger block
                    ))
                    break
            
            # Check allowlist enforcement
            if self.enforce_domain_allowlist and domain not in self.allowed_domains:
                violations.append(PolicyViolation(
                    rule_type=RuleType.DOMAIN_ALLOW,
                    description=f"Domain '{domain}' is not on the allowlist",
                    severity=1.0
                ))
                
        except Exception:
            pass  # Invalid URL, let other checks handle it
        
        return violations
    
    def _check_forms(self, soup: BeautifulSoup) -> list[PolicyViolation]:
        """Check for forms in the page."""
        violations = []
        
        if not self.block_forms:
            return violations
        
        forms = soup.find_all("form")
        if forms:
            violations.append(PolicyViolation(
                rule_type=RuleType.FORMS,
                description=f"Page contains {len(forms)} form(s) - form submission blocked by policy",
                severity=0.6
            ))
        
        return violations
    
    def _check_login(self, html: str, soup: BeautifulSoup) -> list[PolicyViolation]:
        """Check for login/password fields."""
        violations = []
        
        if not self.block_login:
            return violations
        
        html_lower = html.lower()
        
        for pattern in self.LOGIN_PATTERNS:
            if re.search(pattern, html_lower):
                violations.append(PolicyViolation(
                    rule_type=RuleType.LOGIN,
                    description="Page contains password/login fields - authentication pages blocked by policy",
                    severity=0.8
                ))
                break
        
        return violations
    
    def _check_payment(self, html: str) -> list[PolicyViolation]:
        """Check for payment-related keywords."""
        violations = []
        
        if not self.block_payment:
            return violations
        
        html_lower = html.lower()
        found_keywords = []
        
        for keyword in self.PAYMENT_KEYWORDS:
            if keyword in html_lower:
                found_keywords.append(keyword)
        
        if found_keywords:
            violations.append(PolicyViolation(
                rule_type=RuleType.PAYMENT,
                description=f"Page contains payment keywords: {', '.join(found_keywords[:3])}",
                severity=0.7
            ))
        
        return violations
    
    def _check_keywords(self, html: str) -> list[PolicyViolation]:
        """Check for custom blocked keywords."""
        violations = []
        html_lower = html.lower()
        
        for keyword in self.blocked_keywords:
            if keyword in html_lower:
                violations.append(PolicyViolation(
                    rule_type=RuleType.KEYWORD_BLOCK,
                    description=f"Page contains blocked keyword: '{keyword}'",
                    severity=0.8
                ))
        
        return violations
    
    def evaluate(self, html: str, url: str) -> PolicyResult:
        """
        Evaluate content against all policies.
        
        Returns PolicyResult with allowed status and any violations.
        """
        violations = []
        
        # Parse HTML
        try:
            soup = BeautifulSoup(html, 'lxml')
        except Exception:
            soup = BeautifulSoup(html, 'html.parser')
        
        # Run all checks
        violations.extend(self._check_domain(url))
        violations.extend(self._check_forms(soup))
        violations.extend(self._check_login(html, soup))
        violations.extend(self._check_payment(html))
        violations.extend(self._check_keywords(html))
        
        # Determine if allowed (no high-severity violations)
        allowed = all(v.severity < 1.0 for v in violations)
        
        return PolicyResult(allowed=allowed, violations=violations)


# Global policy engine instance
_policy_engine: PolicyEngine | None = None


def get_policy_engine() -> PolicyEngine:
    """Get or create the global policy engine."""
    global _policy_engine
    if _policy_engine is None:
        _policy_engine = PolicyEngine()
    return _policy_engine
