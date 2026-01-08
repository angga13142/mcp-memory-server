"""Integration flow test - simulate real MCP tool usage."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.storage.database import Database
from src.storage.vector_store import VectorMemoryStore
from src.services.search_service import SearchService
from src.services.journal_service import JournalService
from src.services.service_manager import ServiceManager
from src.utils.config import get_settings


async def test_mcp_integration():
    """Test MCP tool integration."""
    print("=" * 60)
    print("MCP TOOLS INTEGRATION TEST")
    print("=" * 60)
    print()
    
    # Initialize service manager
    settings = get_settings()
    service_manager = ServiceManager()
    await service_manager.initialize(settings)
    memory_service, search_service, journal_service = service_manager.get_services()
    
    print("✅ Services initialized")
    print()
    
    # Test 1: start_working_on
    print("1. Testing start_working_on tool...")
    result = await journal_service.start_work_session("Test MCP integration")
    
    if result["success"]:
        print(f"   ✅ SUCCESS")
        print(f"      Session ID: {result['session_id']}")
        print(f"      Task: {result['task']}")
    else:
        print(f"   ❌ FAILED: {result.get('error')}")
    
    # Test duplicate start
    print("\n2. Testing duplicate start (should fail)...")
    result2 = await journal_service.start_work_session("Another task")
    
    if not result2["success"] and "already active" in result2["error"].lower():
        print("   ✅ Duplicate prevention works")
    else:
        print("   ❌ Should have failed with 'already active'")
    
    # Wait for duration
    await asyncio.sleep(1)
    
    # Test 2: end_work_session
    print("\n3. Testing end_work_session tool...")
    result = await journal_service.end_work_session(
        learnings=["MCP integration works", "Tools validated"],
        challenges=["Async setup"],
        quick_note="Good test"
    )
    
    if result["success"]:
        print(f"   ✅ SUCCESS")
        print(f"      Duration: {result['duration_minutes']}min")
        if result.get("reflection"):
            print(f"      Reflection: {result['reflection'][:60]}...")
    else:
        print(f"   ❌ FAILED: {result.get('error')}")
    
    # Test 3: how_was_my_day
    print("\n4. Testing how_was_my_day tool...")
    result = await journal_service.generate_daily_summary()
    
    if result["success"]:
        print(f"   ✅ SUCCESS")
        print(f"      Sessions: {result['stats']['sessions']}")
        print(f"      Total hours: {result['stats']['total_hours']:.2f}")
        print(f"      Summary: {result['summary'][:80]}...")
    else:
        print(f"   ❌ FAILED: {result.get('error')}")
    
    # Test 4: morning_briefing
    print("\n5. Testing morning_briefing...")
    briefing = await journal_service.get_morning_briefing()
    
    if len(briefing) > 0:
        print(f"   ✅ SUCCESS")
        print(f"      Length: {len(briefing)} chars")
        print(f"      Preview: {briefing[:80]}...")
    else:
        print("   ❌ FAILED: Empty briefing")
    
    # Test 5: End without active session (should fail)
    print("\n6. Testing end_work_session without active session...")
    result = await journal_service.end_work_session()
    
    if not result["success"] and "no active" in result["error"].lower():
        print("   ✅ Validation works correctly")
    else:
        print("   ❌ Should have failed with 'no active session'")
    
    await service_manager.cleanup()
    
    print("\n" + "=" * 60)
    print("✅ MCP INTEGRATION TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_mcp_integration())
