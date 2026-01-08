"""Integration tests with real database."""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta, date
from pathlib import Path

from src.storage.database import Database
from src.storage.repositories import JournalRepository
from src.models.journal import DailyJournal, WorkSession, SessionReflection
from src.utils.config import get_settings


@pytest.fixture(scope="module")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
async def test_database():
    """Create test database."""
    settings = get_settings()
    
    # Use test database
    test_db_path = Path("data/test_memory.db")
    settings.storage.sqlite.database_url = f"sqlite+aiosqlite:///{test_db_path}"
    
    # Clean up old test database
    if test_db_path.exists():
        test_db_path.unlink()
    
    # Initialize database
    database = Database(settings)
    await database.init()
    
    yield database
    
    # Cleanup
    await database.close()
    if test_db_path.exists():
        test_db_path.unlink()


@pytest.mark.asyncio
class TestJournalDatabaseIntegration:
    """Integration tests with real database."""
    
    async def test_create_and_retrieve_journal(self, test_database):
        """Test creating and retrieving journal."""
        async with test_database.session() as session:
            repo = JournalRepository(session)
            
            # Create journal
            journal = await repo.get_or_create_today()
            
            assert journal is not None
            assert journal.id is not None
            assert journal.date == datetime.now(timezone.utc).date()
            
            # Retrieve same journal
            journal_id = journal.id
        
        async with test_database.session() as session:
            repo = JournalRepository(session)
            retrieved = await repo.get_or_create_today()
            
            assert retrieved.id == journal_id
    
    async def test_add_and_retrieve_session(self, test_database):
        """Test adding and retrieving work session."""
        async with test_database.session() as session:
            repo = JournalRepository(session)
            
            # Get journal
            journal = await repo.get_or_create_today()
            
            # Add session
            work_session = WorkSession(
                task="Integration test task",
                start_time=datetime.now(timezone.utc),
                notes="Test notes for integration"
            )
            
            await repo.add_session(journal.id, work_session)
            session_id = work_session.id
        
        # Retrieve in new transaction
        async with test_database.session() as session:
            repo = JournalRepository(session)
            sessions = await repo.get_sessions_by_date(datetime.now(timezone.utc).date())
            
            assert len(sessions) > 0
            found = next((s for s in sessions if s.id == session_id), None)
            assert found is not None
            assert found.task == "Integration test task"
            assert found.notes == "Test notes for integration"
    
    async def test_update_session(self, test_database):
        """Test updating work session."""
        async with test_database.session() as session:
            repo = JournalRepository(session)
            
            journal = await repo.get_or_create_today()
            
            # Add session
            work_session = WorkSession(
                task="Session to update",
                start_time=datetime.now(timezone.utc) - timedelta(minutes=30)
            )
            await repo.add_session(journal.id, work_session)
            session_id = work_session.id
        
        # Update session
        async with test_database.session() as session:
            repo = JournalRepository(session)
            
            # Update it
            work_session.end_time = datetime.now(timezone.utc)
            work_session.learnings = ["Integration test learning"]
            work_session.challenges = ["Integration test challenge"]
            work_session.files_touched = ["test.py", "integration.py"]
            
            await repo.update_session(work_session)
        
        # Verify updates
        async with test_database.session() as session:
            repo = JournalRepository(session)
            sessions = await repo.get_sessions_by_date(datetime.now(timezone.utc).date())
            
            updated = next((s for s in sessions if s.id == session_id), None)
            assert updated is not None
            assert updated.end_time is not None
            assert len(updated.learnings) == 1
            assert updated.learnings[0] == "Integration test learning"
            assert len(updated.files_touched) == 2
    
    async def test_save_and_retrieve_reflection(self, test_database):
        """Test saving and retrieving reflection."""
        async with test_database.session() as session:
            repo = JournalRepository(session)
            
            journal = await repo.get_or_create_today()
            
            # Add session
            work_session = WorkSession(
                task="Session with reflection",
                start_time=datetime.now(timezone.utc) - timedelta(minutes=45),
                end_time=datetime.now(timezone.utc)
            )
            await repo.add_session(journal.id, work_session)
            
            # Add reflection
            reflection = SessionReflection(
                session_id=work_session.id,
                task=work_session.task,
                duration_minutes=work_session.duration_minutes,
                reflection_text="This was a productive integration test session.",
                key_insights=["Insight 1", "Insight 2"],
                related_memories=["mem1", "mem2", "mem3"]
            )
            
            await repo.save_reflection(reflection)
        
        # Verify reflection was saved (check via raw query)
        async with test_database.session() as session:
            from sqlalchemy import select, text
            result = await session.execute(
                text("SELECT * FROM session_reflections WHERE session_id = :sid"),
                {"sid": work_session.id}
            )
            row = result.fetchone()
            
            assert row is not None
            assert "productive integration test" in row.reflection_text.lower()
    
    async def test_update_journal_fields(self, test_database):
        """Test updating journal fields."""
        async with test_database.session() as session:
            repo = JournalRepository(session)
            
            journal = await repo.get_or_create_today()
            journal.morning_intention = "Complete all integration tests"
            journal.energy_level = 5
            journal.mood = "energized"
            journal.wins = ["Win 1", "Win 2"]
            
            await repo.save(journal)
            journal_id = journal.id
        
        # Verify updates
        async with test_database.session() as session:
            repo = JournalRepository(session)
            retrieved = await repo.get_by_date(journal.date)
            
            assert retrieved is not None
            assert retrieved.id == journal_id
            assert retrieved.morning_intention == "Complete all integration tests"
            assert retrieved.energy_level == 5
            assert retrieved.mood == "energized"
            assert len(retrieved.wins) == 2
    
    async def test_get_recent_journals(self, test_database):
        """Test getting recent journals."""
        # Create journals for multiple days
        dates_to_create = [
            date.today(),
            date.today() - timedelta(days=1),
            date.today() - timedelta(days=2),
            date.today() - timedelta(days=3)
        ]
        
        for test_date in dates_to_create:
            async with test_database.session() as session:
                repo = JournalRepository(session)
                
                # Create journal for specific date
                journal = DailyJournal(date=test_date)
                await repo.save(journal)
        
        # Retrieve recent journals
        async with test_database.session() as session:
            repo = JournalRepository(session)
            recent = await repo.get_recent_journals(days=7)
            
            assert len(recent) >= 4
            # Should be sorted by date descending
            assert recent[0].date >= recent[-1].date
    
    async def test_multiple_sessions_same_day(self, test_database):
        """Test multiple work sessions in same day."""
        # Use a specific date to avoid interference from other tests
        test_date = date.today() - timedelta(days=365)
        
        async with test_database.session() as session:
            repo = JournalRepository(session)
            
            # Create journal for specific date/ID needs to be saved first
            journal = DailyJournal(date=test_date)
            await repo.save(journal)
            
            # Add multiple sessions
            sessions_data = [
                ("Morning coding", 60),
                ("Afternoon review", 45),
                ("Evening documentation", 90)
            ]
            
            for task, minutes in sessions_data:
                work_session = WorkSession(
                    task=task,
                    start_time=datetime.now(timezone.utc) - timedelta(minutes=minutes),
                    end_time=datetime.now(timezone.utc)
                )
                await repo.add_session(journal.id, work_session)
        
        # Verify all sessions retrieved
        async with test_database.session() as session:
            repo = JournalRepository(session)
            retrieved = await repo.get_by_date(test_date)
            
            assert len(retrieved.work_sessions) == 3
            assert retrieved.total_work_minutes >= 190  # ~195 minutes total
            assert retrieved.tasks_worked_on == 3
    
    async def test_transaction_rollback(self, test_database):
        """Test that failed transactions rollback properly."""
        try:
            async with test_database.session() as session:
                repo = JournalRepository(session)
                
                journal = await repo.get_or_create_today()
                
                # Add valid session
                work_session = WorkSession(
                    task="Will be rolled back",
                    start_time=datetime.now(timezone.utc)
                )
                await repo.add_session(journal.id, work_session)
                
                # Force an error
                raise Exception("Simulated error")
        except Exception: 
            pass  # Expected
        
        # Verify session was NOT saved due to rollback
        async with test_database.session() as session:
            repo = JournalRepository(session)
            sessions = await repo.get_sessions_by_date(datetime.now(timezone.utc).date())
            
            # Should not find the rolled-back session
            found = any(s.task == "Will be rolled back" for s in sessions)
            assert not found


@pytest.mark.asyncio
class TestJournalConcurrency:
    """Test concurrent operations."""
    
    async def test_concurrent_session_updates(self, test_database):
        """Test concurrent updates to different sessions."""
        # Create initial sessions
        session_ids = []
        async with test_database.session() as session:
            repo = JournalRepository(session)
            journal = await repo.get_or_create_today()
            
            for i in range(3):
                work_session = WorkSession(
                    task=f"Concurrent task {i}",
                    start_time=datetime.now(timezone.utc)
                )
                await repo.add_session(journal.id, work_session)
                session_ids.append(work_session.id)
        
        # Update sessions concurrently
        async def update_session(session_id, note):
            async with test_database.session() as session:
                repo = JournalRepository(session)
                sessions = await repo.get_sessions_by_date(datetime.now(timezone.utc).date())
                work_session = next(s for s in sessions if s.id == session_id)
                work_session.notes = note
                work_session.end_time = datetime.now(timezone.utc)
                await repo.update_session(work_session)
        
        # Run concurrent updates
        await asyncio.gather(
            update_session(session_ids[0], "Updated by coroutine 1"),
            update_session(session_ids[1], "Updated by coroutine 2"),
            update_session(session_ids[2], "Updated by coroutine 3")
        )
        
        # Verify all updates succeeded
        async with test_database.session() as session:
            repo = JournalRepository(session)
            sessions = await repo.get_sessions_by_date(datetime.now(timezone.utc).date())
            
            for i, session_id in enumerate(session_ids):
                found = next(s for s in sessions if s.id == session_id)
                assert found.notes == f"Updated by coroutine {i+1}"
