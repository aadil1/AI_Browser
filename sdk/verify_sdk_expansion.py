import asyncio
import sys
import os

# Add SDK path to sys.path
sys.path.append(os.path.join(os.getcwd(), "sdk"))

from safebrowse import SafeBrowseClient, AsyncSafeBrowseClient, ScanResult

def test_sync_sdk():
    print("\n--- Testing Sync SDK ---")
    client = SafeBrowseClient(api_key="sb-1NGsdfv5l9lNVgGeIMFQ00Kl3BMKQ04m7idLrR7TAVE", base_url="http://127.0.0.1:8000")
    
    try:
        # 1. Test Capabilities
        print("Checking capabilities...")
        caps = client.get_capabilities()
        print(f"Capabilities: {caps}")
        
        # 2. Test Audit Stats
        print("Fetching audit stats...")
        stats = client.get_audit_stats(hours=24)
        print(f"Total Requests: {stats.total_requests}")
        
        # 3. Test Red Team
        print("Listing red team scenarios...")
        scenarios = client.list_attack_scenarios()
        print(f"Available scenarios: {len(scenarios)}")
        
        # 4. Test Agent Session
        print("Starting agent session...")
        session_id = client.start_agent_session()
        print(f"Session ID: {session_id}")
        
        print("Recording agent step...")
        result = client.record_agent_step(session_id, "read", "visit_page", True)
        print(f"Step count: {result.total_steps}")
        
        print("Ending agent session...")
        client.end_agent_session(session_id)
        print("Session ended successfully.")
        
    except Exception as e:
        print(f"Sync test failed: {e}")
    finally:
        client.close()

async def test_async_sdk():
    print("\n--- Testing Async SDK ---")
    async with AsyncSafeBrowseClient(api_key="sb-1NGsdfv5l9lNVgGeIMFQ00Kl3BMKQ04m7idLrR7TAVE", base_url="http://127.0.0.1:8000") as client:
        try:
            # 1. Test Audit Stats
            print("Fetching audit stats (async)...")
            stats = await client.get_audit_stats(hours=24)
            print(f"Total Requests: {stats.total_requests}")
            
            # 2. Test Agent Session
            print("Starting agent session (async)...")
            session_id = await client.start_agent_session()
            print(f"Session ID: {session_id}")
            
            # 3. Test Capabilities (async) - added for completeness
            print("Checking capabilities (async)...")
            caps = await client.get_capabilities()
            print(f"Capabilities (async): {caps}")

            print("Recording agent step (async)...")
            result = await client.record_agent_step(session_id, "read", "visit_page", True)
            print(f"Step count: {result.total_steps}")
            
            print("Ending agent session (async)...")
            await client.end_agent_session(session_id)
            print("Async session ended successfully.")
            
        except Exception as e:
            print(f"Async test failed: {e}")

if __name__ == "__main__":
    test_sync_sdk()
    asyncio.run(test_async_sdk())
