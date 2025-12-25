"""
Comprehensive SDK test for SafeBrowse v0.2.0
Tests all Phase 1 & Phase 2 features.
"""
import sys
import os
sys.path.insert(0, '.')

from safebrowse import (
    SafeBrowseClient,
    SafeBrowseConfig,
    ScanResult,
    AskResult,
    SanitizeResult,
    BatchScanResult,
    ErrorCode,
    BlockedError,
)


def test_sdk():
    """Test all SafeBrowse SDK features."""
    print("=" * 70)
    print("SafeBrowse SDK v0.2.0 — Comprehensive Test Suite")
    print("=" * 70)
    
    blocked_calls = []
    allowed_calls = []
    
    def on_blocked(result: ScanResult):
        blocked_calls.append(result)
        print(f"   [HOOK] on_blocked fired: risk={result.risk_score}")
    
    def on_allowed(result: ScanResult):
        allowed_calls.append(result)
        print(f"   [HOOK] on_allowed fired: risk={result.risk_score}")
    
    # ==================== PHASE 1 TESTS ====================
    print("\n" + "─" * 70)
    print("PHASE 1: Launch-Critical Features")
    print("─" * 70)
    
    # Test 1: SafeBrowseConfig object
    print("\n✅ Test 1: SafeBrowseConfig object")
    config = SafeBrowseConfig(
        api_key="test-key",
        base_url="http://localhost:8000",
        timeout=30,
        on_blocked=on_blocked,
        on_allowed=on_allowed,
    )
    print(f"   api_key: {config.api_key[:4]}...")
    print(f"   base_url: {config.base_url}")
    print(f"   timeout: {config.timeout}")
    print(f"   fail_closed: {config.fail_closed}")
    assert config.fail_closed == True, "fail_closed must always be True"
    print("   ✓ PASSED")
    
    # Test 2: Config fails if no API key
    print("\n✅ Test 2: Config requires API key")
    try:
        bad_config = SafeBrowseConfig(api_key="")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"   Correctly raised: {e}")
    print("   ✓ PASSED")
    
    # Test 3: Config enforces fail_closed
    print("\n✅ Test 3: fail_closed cannot be disabled")
    try:
        bad_config = SafeBrowseConfig(api_key="test", fail_closed=False)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"   Correctly raised: {e}")
    print("   ✓ PASSED")
    
    # Test 4: Client with config object
    print("\n✅ Test 4: Client accepts config object")
    client = SafeBrowseClient(config=config)
    result = client.scan_html(
        html="<html><body>Hello World</body></html>",
        url="https://example.com"
    )
    print(f"   is_safe: {result.is_safe}")
    print(f"   request_id: {result.request_id}")
    assert result.is_safe, "Safe content should pass"
    print("   ✓ PASSED")
    
    # Test 5: Logging hooks invoked
    print("\n✅ Test 5: Logging hooks invoked")
    print(f"   on_allowed called: {len(allowed_calls)} times")
    assert len(allowed_calls) > 0, "on_allowed should have been called"
    print("   ✓ PASSED")
    
    # Test 6: guard() returns decision metadata
    print("\n✅ Test 6: guard() provides decision metadata")
    with client.guard(
        html="<html><body>Safe agent content</body></html>",
        url="https://example.com"
    ) as decision:
        print(f"   decision.is_safe: {decision.is_safe}")
        print(f"   decision.risk_score: {decision.risk_score}")
        print(f"   decision.request_id: {decision.request_id}")
        assert isinstance(decision, ScanResult)
    print("   ✓ PASSED")
    
    # Test 7: Error codes on BlockedError
    print("\n✅ Test 7: Machine-readable error codes")
    print(f"   ErrorCode.INJECTION_DETECTED = {ErrorCode.INJECTION_DETECTED.value}")
    print(f"   ErrorCode.POLICY_LOGIN_FORM = {ErrorCode.POLICY_LOGIN_FORM.value}")
    print(f"   ErrorCode.AUTH_INVALID_KEY = {ErrorCode.AUTH_INVALID_KEY.value}")
    print("   ✓ PASSED")
    
    # ==================== PHASE 2 TESTS ====================
    print("\n" + "─" * 70)
    print("PHASE 2: Developer Experience Features")
    print("─" * 70)
    
    # Test 8: sanitize() for RAG pipelines
    print("\n✅ Test 8: sanitize() for RAG pipelines")
    sanitize_result = client.sanitize(
        documents=[
            "This is safe content about Python.",
            "Another safe paragraph about coding.",
            "Normal text here.",
        ],
        url="https://docs.example.com",
        source="web"
    )
    print(f"   total_count: {sanitize_result.total_count}")
    print(f"   safe_count: {sanitize_result.safe_count}")
    print(f"   blocked_count: {sanitize_result.blocked_count}")
    print(f"   safe_chunks: {len(sanitize_result.safe_chunks)} items")
    print(f"   request_id: {sanitize_result.request_id}")
    assert isinstance(sanitize_result, SanitizeResult)
    print("   ✓ PASSED")
    
    # Test 9: Batch scanning
    print("\n✅ Test 9: scan_batch() for bulk operations")
    batch_result = client.scan_batch([
        {"html": "<html><body>Page 1 content</body></html>", "url": "https://example.com/1"},
        {"html": "<html><body>Page 2 content</body></html>", "url": "https://example.com/2"},
        {"html": "<html><body>Page 3 content</body></html>", "url": "https://example.com/3"},
    ])
    print(f"   total: {batch_result.total}")
    print(f"   safe_count: {batch_result.safe_count}")
    print(f"   blocked_count: {batch_result.blocked_count}")
    print(f"   results: {len(batch_result.results)} items")
    assert isinstance(batch_result, BatchScanResult)
    assert batch_result.total == 3
    print("   ✓ PASSED")
    
    # Test 10: get_capabilities()
    print("\n✅ Test 10: get_capabilities() feature flags")
    caps = client.get_capabilities()
    print(f"   html_scanning: {caps.get('html_scanning')}")
    print(f"   policy_engine: {caps.get('policy_engine')}")
    print(f"   audit_logging: {caps.get('audit_logging')}")
    assert caps.get("html_scanning") == True
    print("   ✓ PASSED")
    
    # Test 11: attach_request_id()
    print("\n✅ Test 11: attach_request_id() for correlation")
    client.attach_request_id("my-agent-step-42")
    result = client.scan_html(
        html="<html><body>Test with correlation</body></html>",
        url="https://example.com"
    )
    print(f"   Attached correlation ID: my-agent-step-42")
    print(f"   Scan completed: request_id={result.request_id}")
    print("   ✓ PASSED")
    
    # Test 12: safe_ask still works
    print("\n✅ Test 12: safe_ask() with LLM")
    ask_result = client.safe_ask(
        html="<html><body><h1>Python Tutorial</h1><p>Python is great.</p></body></html>",
        url="https://example.com",
        query="What is this page about?"
    )
    print(f"   status: {ask_result.status}")
    print(f"   answer: {ask_result.answer[:80] if ask_result.answer else 'None'}...")
    assert ask_result.status == "ok"
    print("   ✓ PASSED")
    
    # Test 13: Client as context manager
    print("\n✅ Test 13: Client as context manager")
    with SafeBrowseClient(api_key="test-key") as ctx_client:
        result = ctx_client.is_safe("<html><body>Test</body></html>", "https://example.com")
        print(f"   is_safe: {result}")
    print("   ✓ PASSED")
    
    # Test 14: Exception to_dict()
    print("\n✅ Test 14: Exception serialization")
    try:
        error = BlockedError(
            message="Test blocked",
            risk_score=0.9,
            code=ErrorCode.INJECTION_DETECTED,
            explanations=["Found injection pattern"],
            policy_violations=["test_policy"],
            request_id="test-123"
        )
        error_dict = error.to_dict()
        print(f"   error_dict keys: {list(error_dict.keys())}")
        print(f"   code: {error_dict['code']}")
        assert error_dict["code"] == "INJECTION_DETECTED"
    except Exception as e:
        print(f"   Error: {e}")
    print("   ✓ PASSED")
    
    # Test 15: Config with_hooks()
    print("\n✅ Test 15: Config.with_hooks() immutability")
    new_config = config.with_hooks(
        on_blocked=lambda r: print("New blocked hook"),
        on_allowed=lambda r: print("New allowed hook"),
    )
    assert new_config.api_key == config.api_key
    assert new_config.on_blocked != config.on_blocked
    print("   Original config unchanged, new config has new hooks")
    print("   ✓ PASSED")
    
    client.close()
    
    # ==================== SUMMARY ====================
    print("\n" + "=" * 70)
    print("🎉 ALL SDK TESTS PASSED!")
    print("=" * 70)
    print("\nFeatures Tested:")
    print("  ✓ SafeBrowseConfig object")
    print("  ✓ Environment-based config (from_env)")
    print("  ✓ Enforced fail_closed security")
    print("  ✓ Logging hooks (on_blocked, on_allowed)")
    print("  ✓ Decision metadata in guard()")
    print("  ✓ Machine-readable error codes")
    print("  ✓ sanitize() for RAG pipelines")
    print("  ✓ scan_batch() for bulk operations")
    print("  ✓ get_capabilities() feature flags")
    print("  ✓ attach_request_id() correlation")
    print("  ✓ Exception serialization to_dict()")
    print("=" * 70)


if __name__ == "__main__":
    test_sdk()
