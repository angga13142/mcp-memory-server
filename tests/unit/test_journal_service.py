"""Unit tests for journal service."""

import pytest
from datetime import datetime, timezone, timedelta, date
from unittest.mock import AsyncMock, MagicMock, patch

from src.services.journal_service import JournalService
from src.models.journal import DailyJournal, WorkSession


@pytest.mark.asyncio
class TestJournalService: 
    """Test JournalService."""
    
    @pytest.fixture
    def mock_database(self):
        """Mock database."""
        db = AsyncMock()
        mock_session_cm = AsyncMock()
        mock_session_cm.__aenter__.return_value = mock_session_cm
        mock_session_cm.__aexit__.return_value = None
        
        # session() method should return context manager
        db.session = MagicMock(return_value=mock_session_cm)
        return db
    
    @pytest.fixture
    def mock_vector_store(self):
        """Mock vector store."""
        vs = AsyncMock()
        vs.add_memory = AsyncMock()
        return vs
    
    @pytest.fixture
    def mock_search_service(self):
        """Mock search service."""
        ss = AsyncMock()
        ss.search = AsyncMock(return_value=[])
        return ss
    
    @pytest.fixture
    def service(self, mock_database, mock_vector_store, mock_search_service):
        """Create journal service with mocks."""
        return JournalService(
            database=mock_database,
            vector_store=mock_vector_store,
            search_service=mock_search_service,
            sampling_service=None
        )
    
    async def test_start_work_session_success(self, service):
        """Test starting work session successfully."""
        task = "Test task for unit test"
        
        # Mock repository
        mock_repo = AsyncMock()
        mock_journal = DailyJournal()
        mock_repo.get_or_create_today.return_value = mock_journal
        mock_repo.add_session = AsyncMock()
        
        with patch('src.services.journal_service.JournalRepository', return_value=mock_repo):
            result = await service.start_work_session(task)
            
            assert result["success"] is True
            assert result["task"] == task
            assert "session_id" in result
            assert "started_at" in result
            assert mock_repo.add_session.called
    
    async def test_start_work_session_already_active(self, service):
        """Test starting session when one is already active."""
        # Mock journal with active session
        mock_journal = DailyJournal()
        active_session = WorkSession(
            task="Existing task",
            start_time=datetime.now(timezone.utc)
        )
        mock_journal.add_session(active_session)
        
        mock_repo = AsyncMock()
        mock_repo.get_or_create_today.return_value = mock_journal
        
        with patch('src.services.journal_service.JournalRepository', return_value=mock_repo):
            result = await service.start_work_session("New task")
            
            assert result["success"] is False
            assert "already active" in result["error"].lower()
    
    async def test_end_work_session_success(self, service, mock_vector_store):
        """Test ending work session successfully."""
        # Mock journal with active session
        mock_journal = DailyJournal()
        start_time = datetime.now(timezone.utc) - timedelta(minutes=45)
        active_session = WorkSession(
            task="Test task",
            start_time=start_time
        )
        mock_journal.add_session(active_session)
        
        mock_repo = AsyncMock()
        mock_repo.get_or_create_today.return_value = mock_journal
        mock_repo.update_session = AsyncMock()
        mock_repo.save_reflection = AsyncMock()
        
        with patch('src.services.journal_service.JournalRepository', return_value=mock_repo):
            result = await service.end_work_session(
                learnings=["Test learning"],
                challenges=["Test challenge"],
                quick_note="Test note"
            )
            
            assert result["success"] is True
            assert result["duration_minutes"] >= 44
            assert mock_repo.update_session.called
            
            # Should generate reflection for sessions >= 30 min
            assert mock_repo.save_reflection.called
            assert mock_vector_store.add_memory.called
    
    async def test_end_work_session_no_active(self, service):
        """Test ending session when none is active."""
        # Mock journal with no active sessions
        mock_journal = DailyJournal()
        
        mock_repo = AsyncMock()
        mock_repo.get_or_create_today.return_value = mock_journal
        
        with patch('src.services.journal_service.JournalRepository', return_value=mock_repo):
            result = await service.end_work_session()
            
            assert result["success"] is False
            assert "no active" in result["error"].lower()
    
    async def test_end_work_session_short_no_reflection(self, service):
        """Test that short sessions don't generate reflection."""
        # Mock journal with short active session (< 30 min)
        mock_journal = DailyJournal()
        start_time = datetime.now(timezone.utc) - timedelta(minutes=15)
        active_session = WorkSession(
            task="Short task",
            start_time=start_time
        )
        mock_journal.add_session(active_session)
        
        mock_repo = AsyncMock()
        mock_repo.get_or_create_today.return_value = mock_journal
        mock_repo.update_session = AsyncMock()
        mock_repo.save_reflection = AsyncMock()
        
        with patch('src.services.journal_service.JournalRepository', return_value=mock_repo):
            result = await service.end_work_session()
            
            assert result["success"] is True
            # Should NOT save reflection for short sessions
            assert not mock_repo.save_reflection.called
    
    async def test_generate_daily_summary_success(self, service, mock_vector_store):
        """Test generating daily summary successfully."""
        # Mock journal with sessions
        mock_journal = DailyJournal()
        session = WorkSession(
            task="Test task",
            start_time=datetime.now(timezone.utc) - timedelta(hours=2),
            end_time=datetime.now(timezone.utc) - timedelta(hours=1),
            learnings=["Learning 1"],
            challenges=["Challenge 1"]
        )
        mock_journal.add_session(session)
        
        mock_repo = AsyncMock()
        mock_repo.get_by_date.return_value = mock_journal
        mock_repo.save = AsyncMock()
        
        with patch('src.services.journal_service.JournalRepository', return_value=mock_repo):
            result = await service.generate_daily_summary()
            
            assert result["success"] is True
            assert "summary" in result
            assert "stats" in result
            assert result["stats"]["total_hours"] > 0
            assert result["stats"]["sessions"] == 1
            assert mock_repo.save.called
            assert mock_vector_store.add_memory.called
    
    async def test_generate_daily_summary_no_sessions(self, service):
        """Test generating summary when no sessions exist."""
        mock_repo = AsyncMock()
        mock_repo.get_by_date.return_value = None
        
        with patch('src.services.journal_service.JournalRepository', return_value=mock_repo):
            result = await service.generate_daily_summary()
            
            assert result["success"] is False
            assert "no work sessions" in result["message"].lower()
    
    async def test_generate_session_reflection(self, service, mock_search_service):
        """Test generating session reflection."""
        session = WorkSession(
            task="Test task",
            start_time=datetime.now(timezone.utc) - timedelta(minutes=45),
            end_time=datetime.now(timezone.utc),
            learnings=["Learning 1", "Learning 2"],
            challenges=["Challenge 1"],
            notes="Test notes"
        )
        
        # Mock search results
        item1 = MagicMock()
        item1.id = "mem1"
        item1.content = "Related memory 1"
        item1.score = 0.8
        
        item2 = MagicMock()
        item2.id = "mem2"
        item2.content = "Related memory 2"
        item2.score = 0.7
        
        mock_search_service.search.return_value = [item1, item2]
        
        reflection = await service._generate_session_reflection(session)
        
        assert reflection.session_id == session.id
        assert reflection.task == session.task
        assert reflection.duration_minutes == session.duration_minutes
        assert len(reflection.reflection_text) > 0
        assert len(reflection.related_memories) == 2
        assert len(reflection.key_insights) > 0
    
    async def test_get_morning_briefing(self, service):
        """Test getting morning briefing."""
        # Mock yesterday's journal
        yesterday_journal = DailyJournal(
            date=date.today() - timedelta(days=1),
            end_of_day_reflection="Yesterday was productive!"
        )
        
        mock_repo = AsyncMock()
        mock_repo.get_by_date.return_value = yesterday_journal
        
        with patch('src.services.journal_service.JournalRepository', return_value=mock_repo):
            briefing = await service.get_morning_briefing()
            
            assert len(briefing) > 0
            assert "morning briefing" in briefing.lower() or "briefing" in briefing.lower()
            assert "yesterday" in briefing.lower()
    
    async def test_error_handling(self, service):
        """Test that errors are handled gracefully."""
        # Force an error by making repository raise exception
        mock_repo = AsyncMock()
        mock_repo.get_or_create_today.side_effect = Exception("Database error")
        
        with patch('src.services.journal_service.JournalRepository', return_value=mock_repo):
            result = await service.start_work_session("Test task")
            
            assert result["success"] is False
            assert "error" in result
            assert len(result["error"]) > 0
