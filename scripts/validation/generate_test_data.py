#!/usr/bin/env python3
"""Generate test data for monitoring dashboards."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


async def generate_test_data():
    """Generate test data for Grafana dashboards."""
    print("🎨 Generating Test Data for Dashboards")
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
        journal_service = JournalService(
            database, memory_service, search_service, settings
        )

        # Generate sessions
        print("\n2. Creating 5 test sessions...")
        for i in range(5):
            print(f"   Session {i+1}/5...")

            # Start session
            result = await journal_service.start_work_session(f"Test session {i+1}")
            if not result.get("success"):
                print(f"   ❌ Failed: {result.get('error')}")
                continue

            await asyncio.sleep(2)

            # End session
            result = await journal_service.end_work_session(
                what_i_learned=[f"Learning {i+1}: Important insight"],
                challenges_faced=[f"Challenge {i+1}: Overcame difficulty"],
                quick_note=f"Test session {i+1} completed",
            )

            if not result.get("success"):
                print(f"   ❌ Failed: {result.get('error')}")
                continue

            # Capture win
            await journal_service.capture_win(f"Win {i+1}: Achieved milestone")

            print(f"   ✅ Session {i+1} completed")

        # Generate daily summary
        print("\n3. Generating daily summary...")
        result = await journal_service.generate_daily_summary()
        if result.get("success"):
            print("   ✅ Daily summary generated")
        else:
            print(f"   ⚠️  Summary generation skipped: {result.get('message')}")

        # Cleanup
        await database.close()

        print("\n" + "=" * 50)
        print("✅ Test data generation completed")
        print("\nYou can now view the data in:")
        print("  - Prometheus: http://localhost:9090")
        print("  - Grafana: http://localhost:3000")
        return True

    except Exception as e:
        print(f"\n❌ Error generating test data: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(generate_test_data())
    sys.exit(0 if success else 1)
