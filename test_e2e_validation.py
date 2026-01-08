"""End-to-end validation of journal feature."""

import asyncio
from pathlib import Path
from src.utils.config import get_settings
from src.storage.database import Database
from src.storage.vector_store import VectorMemoryStore
from src.services.search_service import SearchService
from src.services.journal_service import JournalService


async def run_e2e_validation():
    """Run end-to-end validation."""
    print("=" * 60)
    print("PHASE 3-6: END-TO-END VALIDATION")
    print("=" * 60)
    print()
    
    # Initialize services
    settings = get_settings()
    database = Database(settings)
    await database.init()
    
    vector_store = VectorMemoryStore(settings)
    await vector_store.init()
    
    search_service = SearchService(vector_store)
    journal_service = JournalService(
        database=database,
        vector_store=vector_store,
        search_service=search_service,
        sampling_service=None
    )
    
    print("☀️ MORNING ROUTINE")
    print("-" * 40)
    
    # Get morning briefing
    print("\n1. Getting morning briefing...")
    briefing = await journal_service.get_morning_briefing()
    assert len(briefing) > 0
    print(f"   ✅ Briefing received ({len(briefing)} chars)")
    
    # Set morning intention
    print("\n2. Setting morning intention...")
    async with database.session() as session:
        from src.storage.repositories import JournalRepository
        repo = JournalRepository(session)
        today_journal = await repo.get_or_create_today()
        today_journal.morning_intention = "Complete validation testing"
        await repo.save(today_journal)
    print("   ✅ Intention set")
    
    print("\n\n💼 WORK SESSION 1")
    print("-" * 40)
    
    # Start work session
    print("\n3. Starting work session...")
    result = await journal_service.start_work_session("Validation testing phase 1")
    assert result["success"] == True
    print(f"   ✅ Session started: {result['task']}")
    session_id = result["session_id"]
    
    # Try to start another (should fail)
    print("\n4. Testing duplicate prevention...")
    result2 = await journal_service.start_work_session("Another task")
    assert result2["success"] == False
    assert "already active" in result2["error"].lower()
    print("   ✅ Duplicate prevention works")
    
    # Wait for duration
    await asyncio.sleep(2)
    
    # End session
    print("\n5. Ending work session...")
    result = await journal_service.end_work_session(
        learnings=["Models validated", "Database schema correct"],
        challenges=["Setup async testing"],
        quick_note="Good progress"
    )
    assert result["success"] == True
    assert result["duration_minutes"] >= 0
    print(f"   ✅ Session ended ({result['duration_minutes']}min)")
    
    print("\n\n💼 WORK SESSION 2")
    print("-" * 40)
    
    # Start second session
    print("\n6. Starting second session...")
    result = await journal_service.start_work_session("Integration testing")
    assert result["success"] == True
    print(f"   ✅ Session started: {result['task']}")
    
    await asyncio.sleep(1)
    
    # End second session
    print("\n7. Ending second session...")
    result = await journal_service.end_work_session(
        learnings=["E2E flow validated"],
        quick_note="All systems operational"
    )
    assert result["success"] == True
    print(f"   ✅ Session ended ({result['duration_minutes']}min)")
    
    print("\n\n�� EVENING ROUTINE")
    print("-" * 40)
    
    # Generate daily summary
    print("\n8. Generating daily summary...")
    result = await journal_service.generate_daily_summary()
    assert result["success"] == True
    assert "summary" in result
    assert "stats" in result
    print(f"   ✅ Summary generated:")
    print(f"      Sessions: {result['stats']['sessions']}")
    print(f"      Total hours: {result['stats']['total_hours']:.2f}")
    print(f"      Learnings: {result['stats']['learnings_captured']}")
    
    # Test end without active session
    print("\n9. Testing end without active session...")
    result = await journal_service.end_work_session()
    assert result["success"] == False
    assert "no active" in result["error"].lower()
    print("   ✅ Validation works")
    
    await database.close()
    
    print("\n\n" + "=" * 60)
    print("✅ ALL E2E VALIDATIONS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_e2e_validation())
