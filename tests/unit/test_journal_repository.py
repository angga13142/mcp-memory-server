"""Unit tests for journal repository."""

from datetime import UTC, date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.models.journal import DailyJournal, SessionReflection, WorkSession
from src.storage.repositories import JournalRepository


@pytest.mark.asyncio
class TestJournalRepository:
    """Test JournalRepository."""

    @pytest.fixture
    def mock_session(self):
        """Mock database session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.flush = AsyncMock()
        session.add = MagicMock()
        return session

    @pytest.fixture
    def repository(self, mock_session):
        """Create repository with mocked session."""
        return JournalRepository(mock_session)

    async def test_get_or_create_today_creates_new(self, repository, mock_session):
        """Test get_or_create_today creates new journal."""
        # Mock no existing journal
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Should create new journal
        with patch.object(repository, "_to_model", return_value=DailyJournal()):
            journal = await repository.get_or_create_today()

            assert journal is not None
            assert mock_session.add.called
            assert mock_session.flush.called

    async def test_get_or_create_today_returns_existing(self, repository, mock_session):
        """Test get_or_create_today returns existing journal."""
        # Mock existing journal
        mock_db_journal = MagicMock()
        mock_db_journal.id = "existing123"
        mock_db_journal.date = datetime.now(UTC).date()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_db_journal
        mock_session.execute.return_value = mock_result

        with patch.object(
            repository, "_to_model", return_value=DailyJournal(id="existing123")
        ):
            journal = await repository.get_or_create_today()

            assert journal.id == "existing123"
            # Should not add new journal
            assert not mock_session.add.called

    async def test_get_by_date_found(self, repository, mock_session):
        """Test get_by_date when journal exists."""
        target_date = date(2025, 1, 15)

        mock_db_journal = MagicMock()
        mock_db_journal.id = "test123"
        mock_db_journal.date = target_date

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_db_journal
        mock_session.execute.return_value = mock_result

        with patch.object(
            repository, "_to_model", return_value=DailyJournal(date=target_date)
        ):
            journal = await repository.get_by_date(target_date)

            assert journal is not None
            assert journal.date == target_date

    async def test_get_by_date_not_found(self, repository, mock_session):
        """Test get_by_date when journal doesn't exist."""
        target_date = date(2025, 1, 15)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        journal = await repository.get_by_date(target_date)

        assert journal is None

    async def test_add_session(self, repository, mock_session):
        """Test adding work session."""
        journal_id = "journal123"
        session = WorkSession(task="Test task", start_time=datetime.now(UTC))

        result = await repository.add_session(journal_id, session)

        assert result.id == session.id
        assert mock_session.add.called
        assert mock_session.flush.called

        # Verify session was added with correct journal_id
        added_session = mock_session.add.call_args[0][0]
        assert added_session.journal_id == journal_id

    async def test_update_session(self, repository, mock_session):
        """Test updating work session."""
        session = WorkSession(
            id="session123",
            task="Test task",
            start_time=datetime.now(UTC) - timedelta(minutes=30),
            end_time=datetime.now(UTC),
            learnings=["New learning"],
            notes="Updated notes",
        )

        # Mock finding existing session
        mock_db_session = MagicMock()
        mock_db_session.id = "session123"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_db_session
        mock_session.execute.return_value = mock_result

        result = await repository.update_session(session)

        assert result.id == session.id
        # Verify session was updated
        assert mock_db_session.end_time == session.end_time
        assert mock_db_session.learnings == session.learnings
        assert mock_db_session.notes == session.notes

    async def test_save_reflection(self, repository, mock_session):
        """Test saving session reflection."""
        reflection = SessionReflection(
            session_id="session123",
            task="Test task",
            duration_minutes=45,
            reflection_text="Great progress today",
            key_insights=["Insight 1", "Insight 2"],
        )

        result = await repository.save_reflection(reflection)

        assert result.session_id == reflection.session_id
        assert mock_session.add.called
        assert mock_session.flush.called

    async def test_get_sessions_by_date(self, repository, mock_session):
        """Test getting sessions for a specific date."""
        target_date = date(2025, 1, 15)

        # Mock sessions
        mock_db_session1 = MagicMock()
        mock_db_session1.id = "session1"
        mock_db_session1.task = "Task 1"

        mock_db_session2 = MagicMock()
        mock_db_session2.id = "session2"
        mock_db_session2.task = "Task 2"

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_db_session1, mock_db_session2]
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        with patch.object(
            repository,
            "_session_to_model",
            side_effect=lambda s: WorkSession(
                task=s.task, start_time=datetime.now(UTC)
            ),
        ):
            sessions = await repository.get_sessions_by_date(target_date)

            assert len(sessions) == 2
            assert sessions[0].task == "Task 1"
            assert sessions[1].task == "Task 2"

    async def test_get_recent_journals(self, repository, mock_session):
        """Test getting recent journals."""
        # Mock journals
        mock_db_journals = [
            MagicMock(id="journal1", date=date.today()),
            MagicMock(id="journal2", date=date.today() - timedelta(days=1)),
            MagicMock(id="journal3", date=date.today() - timedelta(days=2)),
        ]

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_db_journals
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        with patch.object(
            repository,
            "_to_model",
            side_effect=lambda j: DailyJournal(id=j.id, date=j.date),
        ):
            journals = await repository.get_recent_journals(days=7)

            assert len(journals) == 3
            assert journals[0].id == "journal1"

    async def test_session_to_model_conversion(self, mock_session):
        """Test converting DB session to model."""
        repository = JournalRepository(mock_session)
        # Mock DB session
        mock_db_session = MagicMock()
        mock_db_session.id = "session123"
        mock_db_session.task = "Test task"
        mock_db_session.start_time = datetime.now(UTC)
        mock_db_session.end_time = None
        mock_db_session.files_touched = ["file1.py", "file2.py"]
        mock_db_session.decisions_made = ["Decision 1"]
        mock_db_session.notes = "Test notes"
        mock_db_session.learnings = ["Learning 1"]
        mock_db_session.challenges = ["Challenge 1"]

        session = repository._session_to_model(mock_db_session)

        assert session.id == "session123"
        assert session.task == "Test task"
        assert len(session.files_touched) == 2
        assert len(session.learnings) == 1
        assert session.notes == "Test notes"
