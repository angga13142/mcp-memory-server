#!/usr/bin/env python3
"""Validate session metrics collection."""

import asyncio
import requests
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


async def test_session_metrics():
    """Test that session metrics are properly collected."""
    print("🧪 Testing Session Metrics Collection")
    print("=" * 50)
    
    try:
        # Get baseline metrics
        print("\n1. Getting baseline metrics...")
        response = requests.get("http://localhost:8080/metrics", timeout=5)
        if response.status_code != 200:
            print(f"❌ Metrics endpoint returned {response.status_code}")
            return False
        
        baseline = response.text
        
        # Extract current count
        match = re.search(r'mcp_journal_sessions_total\{status="success"\} (\d+)', baseline)
        baseline_count = int(match.group(1)) if match else 0
        print(f"   Baseline sessions: {baseline_count}")
        
        # Import after baseline to avoid initialization issues
        from src.services.journal_service import JournalService
        from src.storage.database import Database
        from src.storage.vector_store import VectorMemoryStore
        from src.services.search_service import SearchService
        from src.services.memory_service import MemoryService
        from src.utils.config import get_settings
        
        # Initialize services
        print("\n2. Initializing services...")
        settings = get_settings()
        database = Database(settings)
        await database.init()
        
        vector_store = VectorMemoryStore(settings)
        await vector_store.init()
        
        memory_service = MemoryService(database, vector_store, settings)
        search_service = SearchService(vector_store, database, settings)
        journal_service = JournalService(database, memory_service, search_service, settings)
        
        # Start and end session
        print("\n3. Starting test session...")
        result = await journal_service.start_work_session("Validation test session")
        if not result.get('success'):
            print(f"❌ Failed to start session: {result.get('error')}")
            return False
        
        print(f"   Session started: {result['session_id']}")
        
        await asyncio.sleep(2)
        
        print("\n4. Ending test session...")
        result = await journal_service.end_work_session(
            what_i_learned=["Testing metrics"],
            quick_note="Validation"
        )
        
        if not result.get('success'):
            print(f"❌ Failed to end session: {result.get('error')}")
            return False
        
        print(f"   Session ended: {result['duration_minutes']} minutes")
        
        # Wait for metrics update
        print("\n5. Waiting for metrics update...")
        await asyncio.sleep(5)
        
        # Check metrics updated
        response = requests.get("http://localhost:8080/metrics", timeout=5)
        updated = response.text
        
        match = re.search(r'mcp_journal_sessions_total\{status="success"\} (\d+)', updated)
        updated_count = int(match.group(1)) if match else 0
        
        print(f"   Updated sessions: {updated_count}")
        
        # Verify increment
        if updated_count != baseline_count + 1:
            print(f"❌ Expected {baseline_count + 1}, got {updated_count}")
            return False
        
        # Check for other metrics
        print("\n6. Verifying other metrics...")
        required_metrics = [
            'mcp_journal_sessions_active',
            'mcp_journal_session_duration_minutes',
            'mcp_journal_learnings_captured_total',
        ]
        
        for metric in required_metrics:
            if metric in updated:
                print(f"   ✅ {metric}")
            else:
                print(f"   ❌ Missing: {metric}")
                return False
        
        # Cleanup
        await database.close()
        
        print("\n" + "=" * 50)
        print("✅ Session metrics validation PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Error during validation: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_session_metrics())
    sys.exit(0 if success else 1)
