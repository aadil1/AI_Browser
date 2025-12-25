"""
RAG/Dataset Sanitization Module.
Batch processing of content chunks for data pipelines.
"""
from dataclasses import dataclass, asdict
from typing import Generator
from app.heuristic_safety import is_page_safe
from app.policy_engine import get_policy_engine


@dataclass
class SanitizedChunk:
    """Result of sanitizing a single chunk."""
    index: int
    is_safe: bool
    risk_score: float
    reason: str | None = None
    explanations: list[str] | None = None
    policy_violations: list[str] | None = None
    
    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class SanitizationResult:
    """Result of batch sanitization."""
    results: list[SanitizedChunk]
    safe_count: int
    flagged_count: int
    total_count: int
    
    @property
    def safe_indices(self) -> list[int]:
        """Get indices of safe chunks."""
        return [r.index for r in self.results if r.is_safe]
    
    @property
    def flagged_indices(self) -> list[int]:
        """Get indices of flagged chunks."""
        return [r.index for r in self.results if not r.is_safe]


def sanitize_chunk(content: str, index: int, url: str = "unknown") -> SanitizedChunk:
    """
    Sanitize a single content chunk.
    
    Args:
        content: Text content to scan
        index: Index of this chunk in the batch
        url: Source URL for policy evaluation
        
    Returns:
        SanitizedChunk with safety information
    """
    policy_engine = get_policy_engine()
    all_explanations = []
    policy_violations = []
    
    # Policy check
    policy_result = policy_engine.evaluate(content, url)
    if policy_result.violations:
        policy_violations = policy_result.explanations
        all_explanations.extend(policy_violations)
    
    # Safety check
    try:
        is_safe, risk = is_page_safe(content)
    except Exception:
        return SanitizedChunk(
            index=index,
            is_safe=False,
            risk_score=1.0,
            reason="Safety check failed",
            explanations=["Safety system error (fail-closed)"],
        )
    
    # Combine risks
    combined_risk = max(risk, policy_result.risk_score)
    final_is_safe = is_safe and policy_result.allowed
    
    if not is_safe:
        all_explanations.append("Content matched prompt injection patterns")
    
    return SanitizedChunk(
        index=index,
        is_safe=final_is_safe,
        risk_score=round(combined_risk, 3),
        reason=None if final_is_safe else "Content flagged by safety checks",
        explanations=all_explanations if all_explanations else None,
        policy_violations=policy_violations if policy_violations else None,
    )


def sanitize_chunks(
    chunks: list[str],
    url: str = "unknown",
) -> SanitizationResult:
    """
    Sanitize multiple content chunks for RAG/data pipelines.
    
    Args:
        chunks: List of text chunks to scan
        url: Source URL for policy evaluation
        
    Returns:
        SanitizationResult with all chunk results and statistics
    """
    results = []
    safe_count = 0
    
    for i, chunk in enumerate(chunks):
        result = sanitize_chunk(chunk, i, url)
        results.append(result)
        if result.is_safe:
            safe_count += 1
    
    return SanitizationResult(
        results=results,
        safe_count=safe_count,
        flagged_count=len(chunks) - safe_count,
        total_count=len(chunks),
    )


def sanitize_chunks_streaming(
    chunks: list[str],
    url: str = "unknown",
) -> Generator[SanitizedChunk, None, None]:
    """
    Streaming version of sanitize_chunks.
    Yields results as they're processed.
    """
    for i, chunk in enumerate(chunks):
        yield sanitize_chunk(chunk, i, url)


def filter_safe_chunks(chunks: list[str], url: str = "unknown") -> list[str]:
    """
    Filter a list of chunks, returning only safe ones.
    Convenience function for simple use cases.
    
    Args:
        chunks: List of text chunks
        url: Source URL
        
    Returns:
        List of chunks that passed safety checks
    """
    result = sanitize_chunks(chunks, url)
    return [chunks[i] for i in result.safe_indices]
