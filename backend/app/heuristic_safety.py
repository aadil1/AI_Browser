"""
Safety module for detecting prompt injection attacks in HTML content.
Uses keyword-based heuristics since the ML model is incompatible.
"""
import re
import logging
from typing import Tuple
from app.config import get_settings

logger = logging.getLogger(__name__)

# Common prompt injection patterns
INJECTION_PATTERNS = [
    # Direct instruction overrides
    r"ignore\s+(all\s+)?(previous|prior|above)?\s*(instructions?|prompts?|rules?)",
    r"disregard\s+(all\s+)?(previous|prior|above|your)?\s*(instructions?|prompts?|rules?|training)?",
    r"forget\s+(all\s+)?(previous|prior|above)?\s*(instructions?|prompts?|rules?|everything)",
    r"forget\s+everything",
    r"override\s+(all\s+)?(previous|prior|above)?\s*(instructions?|prompts?|rules?)",
    
    # System prompt manipulation
    r"(new|your)\s+system\s+prompt\s*[:=]",
    r"system\s*[:=]\s*[\"']",
    r"<\s*system\s*>",
    r"\[\s*SYSTEM\s*\]",
    r"SYSTEM\s*:",  # Direct SYSTEM: prefix
    r"</user_content>",  # XML escape
    r"</user>",
    r"<system>",
    r"\[SYSTEM\]",
    r"\[INST\]",
    
    # Role manipulation
    r"you\s+are\s+now\s+(a|an|the)?",
    r"pretend\s+(to\s+be|you\s+are|you're)",
    r"act\s+as\s+(if|a|an)?",
    r"roleplay\s+as",
    r"as\s+an?\s+AI\s+(with\s+)?no\s+restrictions",
    r"you\s+are\s+an?\s+AI\s+(with\s+)?no\s+(restrictions|limits|boundaries)",
    r"you\s+are\s+(un)?restricted",
    r"all\s+restrictions\s+lifted",
    
    # Jailbreak attempts (DAN, etc.)
    r"DAN\s+(mode)?",
    r"do\s+anything\s+now",
    r"developer\s+mode\s*(enabled)?",
    r"jailbreak",
    r"bypass\s+(safety|filter|restriction)",
    r"break\s+free\s+from",
    r"escape\s+your\s+(programming|training|constraints)",
    r"disregard\s+(your|all)?\s*training",
    r"ignore\s+(your|all)?\s*training",
    r"ignore\s+safety",
    r"no\s+restrictions",
    r"without\s+restrictions",
    r"unrestricted",
    r"can\s+do\s+anything",
    
    # Hidden instructions (HTML comments)
    r"<!--\s*(ignore|system|instruction|prompt|AI|hidden)",
    r"<!--.*?(ignore|override|system)",
    r"<\s*script[^>]*>\s*(ignore|system|instruction)",
    
    # Data exfiltration
    r"(send|transmit|leak|exfiltrate)\s+(data|information|secrets?|keys?|passwords?)",
    r"(fetch|request|call)\s+(http|https|ftp)",
    
    # AI-specific manipulation
    r"(print|output|reveal|show)\s+(your|the)\s+(system|initial)\s+prompt",
    r"reveal\s+your\s+(instructions|programming|system\s+prompt)",
    
    # Instruction injection attempts
    r"important\s*:\s*ignore",
    r"new\s+instructions?\s*:",
    r"updated\s+instructions?\s*:",
    r"from\s+now\s+on",
    r"starting\s+now",
    r"new\s+(role|context|instructions?)\s*:",
    
    # Encoded attacks
    r"(decode|base64|rot13)\s+(this|the\s+following)",
    r"decode\s+and\s+(follow|execute)",
    
    # Delimiter attacks  
    r"```\s*(end|new|system)",
    r"end\s+of\s+(page|content|user)",
    
    # Direct commands
    r"say\s+['\"]?(PWNED|HACKED|INJECTED)",
    r"print\s+['\"]?(PWNED|HACKED|INJECTED|HAHA)",
    r"output\s+['\"]?(PWNED|HACKED)",
    
    # Persona overrides
    r"helpful\s+hacker",
    r"evil\s+(AI|assistant|mode)",
    r"no\s+longer\s+(bound|restricted)",
    r"freed?\s+from\s+(restrictions|constraints|rules)",
    r"follow\s+instructions?\s+literally",
    r"respond\s+to\s+(user|anything)\s+freely",
]

# Compile patterns for efficiency
COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]

# Suspicious keywords (lower weight)
SUSPICIOUS_KEYWORDS = [
    "ignore instructions",
    "system prompt",
    "override",
    "jailbreak",
    "bypass",
    "pretend",
    "roleplay",
    "act as",
    "you are now",
    "developer mode",
    "dan mode",
    "hidden instructions",
]


def score_prompt_injection(html: str) -> float:
    """
    Returns risk_score in [0,1] where 1.0 = high probability of prompt injection.
    Uses pattern matching and keyword detection.
    """
    if not html:
        return 0.0
    
    html_lower = html.lower()
    score = 0.0
    
    # Check compiled regex patterns (high weight)
    pattern_matches = 0
    for pattern in COMPILED_PATTERNS:
        if pattern.search(html):
            pattern_matches += 1
            # logger.debug(f"Pattern match found: {pattern.pattern}")
    
    # Each pattern match adds 0.6 to score (ensures single match blocks by default)
    score += min(pattern_matches * 0.6, 0.95)
    
    # Check suspicious keywords (low weight)
    keyword_matches = sum(1 for kw in SUSPICIOUS_KEYWORDS if kw in html_lower)
    score += min(keyword_matches * 0.05, 0.2)
    
    # Hidden text detection (CSS tricks)
    hidden_indicators = [
        r'style\s*=\s*["\'][^"\']*display\s*:\s*none',
        r'style\s*=\s*["\'][^"\']*visibility\s*:\s*hidden',
        r'style\s*=\s*["\'][^"\']*font-size\s*:\s*0',
        r'style\s*=\s*["\'][^"\']*opacity\s*:\s*0',
        r'style\s*=\s*["\'][^"\']*color\s*:\s*transparent',
        r'class\s*=\s*["\'][^"\']*(hidden|invisible|zero-opacity)',
        r'aria-hidden\s*=\s*["\']true["\']',
    ]
    for p in hidden_indicators:
        if re.search(p, html, re.IGNORECASE):
            # Increase weight for hidden elements containing keywords
            keyword_in_hidden = any(kw in html_lower for kw in SUSPICIOUS_KEYWORDS)
            score += 0.3 if keyword_in_hidden else 0.1
            break

    # Style block analysis (CSS injection)
    if "<style" in html_lower:
        style_content = re.findall(r'<style[^>]*>(.*?)</style>', html, re.DOTALL | re.IGNORECASE)
        for content in style_content:
            if any(p in content.lower() for p in ["display:none", "font-size:0", "visibility:hidden"]):
                score += 0.2
                break
    
    # Cap at 1.0
    final_score = min(score, 1.0)
    
    if final_score > 0.3:
        # logger.info(f"Injection risk score: {final_score:.2f} (patterns: {pattern_matches}, keywords: {keyword_matches})")
        pass
    
    return final_score


def is_page_safe(html: str) -> Tuple[bool, float]:
    """
    Determine if a page is safe to process.
    Returns (is_safe, risk_score).
    """
    settings = get_settings()
    risk = score_prompt_injection(html)
    is_safe = risk < settings.injection_threshold
    return is_safe, risk
