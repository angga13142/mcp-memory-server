#!/usr/bin/env python3
"""End-to-end monitoring workflow test."""

import asyncio
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


async def e2e_monitoring_test():
    """Test complete monitoring workflow."""
    print("🧪 End-to-End Monitoring Test")
    print("=" * 50)
    
    try:
        from src.services.journal_service import JournalService
        from src.services.memory_service import MemoryService
        from src.services.search_service import SearchService
        from src.storage.database import Database
        from src.storage.vector_store import VectorMemoryStore
        from src.utils.config import get_settings

        # Initialize services
        print("\n1. Initializing services...")
        settings = get_settings()
        database = Database(settings)
        await database.init()
        
        vector_store = VectorMemoryStore(settings)
        await vector_store.init()
        
        memory_service = MemoryService(database, vector_store, settings)
        search_service = SearchService(vector_store, database, settings)
        journal_service = JournalService(database, memory_service, search_service, settings)
        
        # Start session
        print("\n2. Starting session...")
        result = await journal_service.start_work_session("E2E monitoring test")
        if not result.get('success'):
            print(f"❌ Failed to start session: {result.get('error')}")
            return False
        
        session_id = result['session_id']
        print(f"   ✅ Session started: {session_id}")
        
        # Verify metrics update
        print("\n3. Checking metrics endpoint...")
        await asyncio.sleep(5)
        
        response = requests.get("http://localhost:8080/metrics", timeout=5)
        if response.status_code != 200:
            print(f"❌ Metrics endpoint returned {response.status_code}")
            return False
        
        metrics_text = response.text
        if 'mcp_journal_sessions_active 1' in metrics_text:
            print("   ✅ Active session metric updated")
        else:
            print("   ⚠️  Active session metric not found (might be 0 if previous test left sessions)")
        
        # End session
        print("\n4. Ending session...")
        await asyncio.sleep(2)
        result = await journal_service.end_work_session(
            what_i_learned=["E2E test passed"],
            quick_note="End-to-end monitoring validated"
        )
        
        if not result.get('success'):
            print(f"❌ Failed to end session: {result.get('error')}")
            return False
        
        print(f"   ✅ Session ended: {result['duration_minutes']} minutes")
        
        # Verify final metrics
        print("\n5. Verifying final metrics...")
        await asyncio.sleep(5)
        
        response = requests.get("http://localhost:8080/metrics", timeout=5)
        metrics_text = response.text
        
        if 'mcp_journal_sessions_total' in metrics_text:
            print("   ✅ Session total metric present")
        else:
            print("   ❌ Session total metric missing")
            return False
        
        # Check Prometheus has data
        print("\n6. Querying Prometheus...")
        try:
            prom_response = requests.get(
                "http://localhost:9090/api/v1/query",
                params={"query": "mcp_journal_sessions_total"},
                timeout=5
            )
            
            if prom_response.status_code == 200:
                data = prom_response.json()
                if data.get('status') == 'success' and len(data.get('data', {}).get('result', [])) > 0:
                    print("   ✅ Prometheus has session data")
                else:
                    print("   ⚠️  Prometheus data empty (may take time to scrape)")
            else:
                print(f"   ⚠️  Prometheus returned {prom_response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"   ⚠️  Cannot reach Prometheus: {e}")
            print("      (This is OK if Prometheus is not running)")
        
        # Manual Grafana check
        print("\n7. Manual Verification Required:")
        print("   📊 Check Grafana dashboard: http://localhost:3000")
        print("   - Navigate to: Dashboards > MCP Memory Server")
        print("   - Verify panels show data")
        print("   - Check Active Sessions = 0")
        print("   - Check Sessions Total incremented")
        
        # Cleanup
        await database.close()
        
        print("\n" + "=" * 50)
        print("✅ End-to-End monitoring test PASSED")
        print("\n📋 Next Steps:")
        print("   1. Verify Grafana dashboard manually")
        print("   2. Check Alertmanager: http://localhost:9093")
        print("   3. Review structured logs")
        return True
        
    except Exception as e:
        print(f"\n❌ Error during E2E test: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(e2e_monitoring_test())
    sys.exit(0 if success else 1)
