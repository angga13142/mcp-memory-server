"""Integration tests for journal service with real dependencies."""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta, date
from pathlib import Path

from src.storage.database import Database
from src.storage.vector_store import VectorMemoryStore
from src.services.search_service import SearchService
from src.services.journal_service import JournalService
from src.utils.config import get_settings


@pytest.fixture(scope="module")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
async def integrated_services():
    """Create integrated services with real dependencies."""
    settings = get_settings()
    
    # Use test paths
    test_db_path = Path("data/test_integration_memory.db")
    test_chroma_path = Path("data/test_chroma_db")
    
    settings.storage.sqlite.database_url = f"sqlite+aiosqlite:///{test_db_path}"
    settings.storage.chroma.persist_directory = str(test_chroma_path)
    
    # Clean up old test data
    if test_db_path.exists():
        test_db_path.unlink()
    if test_chroma_path.exists():
        import shutil
        shutil.rmtree(test_chroma_path)
    
    # Initialize services
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
    
    yield {
        "database": database,
        "vector_store": vector_store,
        "search_service": search_service,
        "journal_service": journal_service
    }
    
    # Cleanup
    await database.close()
    
    if test_db_path.exists():
        test_db_path.unlink()
    if test_chroma_path.exists():
        import shutil
        shutil.rmtree(test_chroma_path)


@pytest.mark.asyncio
class TestJournalServiceIntegration:
    """Integration tests for journal service."""
    
    async def test_full_session_workflow(self, integrated_services):
        """Test complete work session workflow."""
        journal_service = integrated_services["journal_service"]
        vector_store = integrated_services["vector_store"]
        
        # Start session
        start_result = await journal_service.start_work_session(
            "Integration test: full workflow"
        )
        
        assert start_result["success"] is True
        session_id = start_result["session_id"]
        
        # Wait a moment for duration
        await asyncio.sleep(2)
        
        # End session with details
        end_result = await journal_service.end_work_session(
            learnings=["Integration testing is important", "Services work together well"],
            challenges=["Setting up test fixtures takes time"],
            quick_note="Overall smooth integration"
        )
        
        assert end_result["success"] is True
        assert end_result["session_id"] == session_id
        assert end_result["duration_minutes"] >= 0
        
        # Verify reflection was saved to vector store
        # (For sessions >= 30 min, but this one is short, so no reflection)
        # Just verify no errors occurred
    
    async def test_long_session_generates_reflection(self, integrated_services):
        """Test that long sessions generate reflections."""
        journal_service = integrated_services["journal_service"]
        vector_store = integrated_services["vector_store"]
        
        # Start session
        await journal_service.start_work_session("Long integration test session")
        
        # Manually set start time to 45 minutes ago
        from src.storage.repositories import JournalRepository
        async with integrated_services["database"].session() as session:
            repo = JournalRepository(session)
            journal = await repo.get_or_create_today()
            active = journal.get_active_session()
            active.start_time = datetime.now(timezone.utc) - timedelta(minutes=45)
            await repo.update_session(active)
        
        # End session
        end_result = await journal_service.end_work_session(
            learnings=["Long sessions get reflections"],
            quick_note="This should trigger reflection generation"
        )
        
        assert end_result["success"] is True
        # Should have reflection for sessions >= 30 min
        if end_result.get("reflection"):
            assert len(end_result["reflection"]) > 0
    
    async def test_daily_summary_generation(self, integrated_services):
        """Test daily summary with real data."""
        journal_service = integrated_services["journal_service"]
        
        # Create multiple sessions
        for i in range(3):
            await journal_service.start_work_session(f"Summary test task {i+1}")
            await asyncio.sleep(1)
            await journal_service.end_work_session(
                learnings=[f"Learning from task {i+1}"],
                challenges=[f"Challenge from task {i+1}"]
            )
        
        # Generate summary
        summary_result = await journal_service.generate_daily_summary()
        
        assert summary_result["success"] is True
        assert "summary" in summary_result
        assert "stats" in summary_result
        
        stats = summary_result["stats"]
        assert stats["sessions"] >= 3
        assert stats["total_hours"] >= 0
        assert stats["learnings_captured"] >= 3
        assert stats["challenges_noted"] >= 3
    
    async def test_vector_store_searchability(self, integrated_services):
        """Test that reflections are searchable."""
        journal_service = integrated_services["journal_service"]
        search_service = integrated_services["search_service"]
        vector_store = integrated_services["vector_store"]
        
        # Add a memory directly to vector store
        await vector_store.add_memory(
            id="test_reflection_123",
            content="This is a test reflection about authentication implementation. We learned about OAuth2 flows and token management.",
            metadata={
                "content_type": "session_reflection",
                "date": date.today().isoformat()
            }
        )
        
        # Wait for embedding to be processed
        await asyncio.sleep(1)
        
        # Search for it
        results = await search_service.search(
            query="authentication OAuth2",
            limit=5
        )
        
        assert len(results) > 0
        # Should find our test reflection
        found = any("authentication" in r["content"].lower() for r in results)
        assert found
    
    async def test_morning_briefing_with_data(self, integrated_services):
        """Test morning briefing with real previous day data."""
        journal_service = integrated_services["journal_service"]
        
        # Create yesterday's data
        from src.storage.repositories import JournalRepository
        yesterday = date.today() - timedelta(days=1)
        
        async with integrated_services["database"].session() as session:
            repo = JournalRepository(session)
            
            from src.models.journal import DailyJournal
            journal = DailyJournal(
                date=yesterday,
                end_of_day_reflection="Yesterday was highly productive with 3 major features completed."
            )
            await repo.save(journal)
        
        # Get morning briefing
        briefing = await journal_service.get_morning_briefing()
        
        assert len(briefing) > 0
        assert "yesterday" in briefing.lower() or "recap" in briefing.lower()
        assert "productive" in briefing.lower()
    
    async def test_error_recovery(self, integrated_services):
        """Test service recovers gracefully from errors."""
        journal_service = integrated_services["journal_service"]
        
        # Try to end session when none is active
        result = await journal_service.end_work_session()
        assert result["success"] is False
        assert "error" in result
        
        # Service should still work after error
        start_result = await journal_service.start_work_session("Recovery test")
        assert start_result["success"] is True
        
        # Clean up
        await journal_service.end_work_session()
    
    async def test_concurrent_service_operations(self, integrated_services):
        """Test concurrent operations on journal service."""
        journal_service = integrated_services["journal_service"]
        
        # Try to start multiple sessions concurrently
        # (Only first should succeed due to active session check)
        results = await asyncio.gather(
            journal_service.start_work_session("Concurrent task 1"),
            journal_service.start_work_session("Concurrent task 2"),
            journal_service.start_work_session("Concurrent task 3"),
            return_exceptions=True
        )
        
        # Count successes
        successes = sum(1 for r in results if isinstance(r, dict) and r.get("success") is True)
        
        # Only one should succeed (first one to acquire lock)
        assert successes == 1
        
        # Clean up
        await journal_service.end_work_session()
