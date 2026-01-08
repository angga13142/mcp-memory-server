"""Unit tests for journal models."""

from datetime import UTC, date, datetime, timedelta

import pytest
from pydantic import ValidationError

from src.models.journal import DailyJournal, SessionReflection, WorkSession


class TestWorkSession:
    """Test WorkSession model."""

    def test_create_valid_session(self):
        """Test creating a valid work session."""
        session = WorkSession(task="Test task", start_time=datetime.now(UTC))

        assert session.id is not None
        assert session.task == "Test task"
        assert session.is_active is True
        assert session.end_time is None
        assert session.duration_minutes >= 0

    def test_session_with_end_time(self):
        """Test session with end time."""
        start = datetime.now(UTC) - timedelta(minutes=30)
        end = datetime.now(UTC)

        session = WorkSession(task="Test task", start_time=start, end_time=end)

        assert session.is_active is False
        assert 29 <= session.duration_minutes <= 31  # ~30 minutes

    def test_duration_calculation_active_session(self):
        """Test duration calculation for active session."""
        start = datetime.now(UTC) - timedelta(minutes=15)
        session = WorkSession(task="Test", start_time=start)

        # Active session calculates from start to now
        assert session.duration_minutes >= 14
        assert session.duration_minutes <= 16

    def test_task_validation_empty(self):
        """Test that empty task is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            WorkSession(task="", start_time=datetime.now(UTC))

        assert "task" in str(exc_info.value).lower()

    def test_task_validation_too_long(self):
        """Test that task exceeding max length is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            WorkSession(
                task="x" * 501,  # Exceeds 500 limit
                start_time=datetime.now(UTC),
            )

        error_str = str(exc_info.value)
        assert "500" in error_str or "max_length" in error_str.lower()

    def test_files_touched_validation(self):
        """Test files_touched list validation."""
        # Valid list
        session = WorkSession(
            task="Test",
            start_time=datetime.now(UTC),
            files_touched=["file1.py", "file2.py"],
        )
        assert len(session.files_touched) == 2

        # Too many items
        with pytest.raises(ValidationError) as exc_info:
            WorkSession(
                task="Test",
                start_time=datetime.now(UTC),
                files_touched=["file.py"] * 51,  # Exceeds 50
            )
        assert "50" in str(exc_info.value) or "max_items" in str(exc_info.value).lower()

    def test_learnings_validation(self):
        """Test learnings list validation."""
        # Valid
        session = WorkSession(
            task="Test",
            start_time=datetime.now(UTC),
            learnings=["Learning 1", "Learning 2"],
        )
        assert len(session.learnings) == 2

        # Too many
        with pytest.raises(ValidationError):
            WorkSession(
                task="Test",
                start_time=datetime.now(UTC),
                learnings=["item"] * 11,  # Exceeds 10
            )

    def test_challenges_validation(self):
        """Test challenges list validation."""
        # Valid
        session = WorkSession(
            task="Test",
            start_time=datetime.now(UTC),
            challenges=["Challenge 1"],
        )
        assert len(session.challenges) == 1

        # Too many
        with pytest.raises(ValidationError):
            WorkSession(
                task="Test",
                start_time=datetime.now(UTC),
                challenges=["item"] * 11,  # Exceeds 10
            )

    def test_notes_validation(self):
        """Test notes field validation."""
        # Valid
        session = WorkSession(
            task="Test",
            start_time=datetime.now(UTC),
            notes="These are some notes",
        )
        assert session.notes == "These are some notes"

        # Too long
        with pytest.raises(ValidationError) as exc_info:
            WorkSession(
                task="Test",
                start_time=datetime.now(UTC),
                notes="x" * 2001,  # Exceeds 2000
            )
        assert "2000" in str(exc_info.value)

    def test_session_serialization(self):
        """Test model serialization to dict."""
        session = WorkSession(
            task="Test task",
            start_time=datetime.now(UTC),
            learnings=["Test learning"],
            files_touched=["test.py"],
        )

        data = session.model_dump()

        assert data["task"] == "Test task"
        assert "id" in data
        assert "duration_minutes" in data
        assert data["learnings"] == ["Test learning"]
        assert data["files_touched"] == ["test.py"]


class TestDailyJournal:
    """Test DailyJournal model."""

    def test_create_journal(self):
        """Test creating a daily journal."""
        journal = DailyJournal()

        assert journal.id is not None
        assert journal.date == datetime.now(UTC).date()
        assert journal.energy_level == 3
        assert len(journal.work_sessions) == 0
        assert journal.total_work_minutes == 0
        assert journal.tasks_worked_on == 0

    def test_journal_with_custom_date(self):
        """Test journal with specific date."""
        custom_date = date(2025, 1, 15)
        journal = DailyJournal(date=custom_date)

        assert journal.date == custom_date

    def test_add_session(self):
        """Test adding work session to journal."""
        journal = DailyJournal()
        session = WorkSession(task="Test task", start_time=datetime.now(UTC))

        journal.add_session(session)

        assert len(journal.work_sessions) == 1
        assert journal.work_sessions[0].id == session.id
        assert journal.tasks_worked_on == 1

    def test_get_active_session(self):
        """Test getting active session."""
        journal = DailyJournal()

        # No active session
        assert journal.get_active_session() is None

        # Add active session
        session1 = WorkSession(task="Task 1", start_time=datetime.now(UTC))
        journal.add_session(session1)

        active = journal.get_active_session()
        assert active is not None
        assert active.id == session1.id

        # End session and add another
        session1.end_time = datetime.now(UTC)
        session2 = WorkSession(task="Task 2", start_time=datetime.now(UTC))
        journal.add_session(session2)

        active = journal.get_active_session()
        assert active.id == session2.id

    def test_total_work_minutes_calculation(self):
        """Test total work time calculation."""
        journal = DailyJournal()

        # Add completed sessions
        start1 = datetime.now(UTC) - timedelta(minutes=60)
        session1 = WorkSession(
            task="Task 1", start_time=start1, end_time=start1 + timedelta(minutes=30)
        )

        start2 = datetime.now(UTC) - timedelta(minutes=30)
        session2 = WorkSession(
            task="Task 2", start_time=start2, end_time=datetime.now(UTC)
        )

        journal.add_session(session1)
        journal.add_session(session2)

        # Should be ~60 minutes total
        assert journal.total_work_minutes >= 58
        assert journal.total_work_minutes <= 62

    def test_tasks_worked_on_count(self):
        """Test unique tasks count."""
        journal = DailyJournal()

        # Same task multiple times
        session1 = WorkSession(task="Same Task", start_time=datetime.now(UTC))
        session2 = WorkSession(task="Same Task", start_time=datetime.now(UTC))
        session3 = WorkSession(task="Different Task", start_time=datetime.now(UTC))

        journal.add_session(session1)
        journal.add_session(session2)
        journal.add_session(session3)

        assert journal.tasks_worked_on == 2  # Only 2 unique tasks

    def test_morning_intention_validation(self):
        """Test morning intention field validation."""
        # Valid
        journal = DailyJournal(morning_intention="Focus on testing today")
        assert journal.morning_intention == "Focus on testing today"

        # Too long
        with pytest.raises(ValidationError) as exc_info:
            DailyJournal(morning_intention="x" * 1001)
        assert "1000" in str(exc_info.value)

    def test_energy_level_validation(self):
        """Test energy level constraints."""
        # Valid values (1-5)
        for level in range(1, 6):
            journal = DailyJournal(energy_level=level)
            assert journal.energy_level == level

        # Too high
        with pytest.raises(ValidationError):
            DailyJournal(energy_level=6)

        # Too low
        with pytest.raises(ValidationError):
            DailyJournal(energy_level=0)

    def test_wins_list(self):
        """Test wins list."""
        journal = DailyJournal(wins=["Win 1", "Win 2", "Win 3"])
        assert len(journal.wins) == 3

        # Too many wins
        with pytest.raises(ValidationError):
            DailyJournal(wins=["win"] * 11)  # Exceeds 10

    def test_mood_validation(self):
        """Test mood field."""
        journal = DailyJournal(mood="focused")
        assert journal.mood == "focused"

        # Too long
        with pytest.raises(ValidationError):
            DailyJournal(mood="x" * 51)  # Exceeds 50


class TestSessionReflection:
    """Test SessionReflection model."""

    def test_create_reflection(self):
        """Test creating a session reflection."""
        reflection = SessionReflection(
            session_id="test123",
            task="Test task",
            duration_minutes=45,
            reflection_text="This was a productive session.",
        )

        assert reflection.session_id == "test123"
        assert reflection.task == "Test task"
        assert reflection.duration_minutes == 45
        assert reflection.reflection_text == "This was a productive session."
        assert len(reflection.key_insights) == 0
        assert len(reflection.related_memories) == 0

    def test_reflection_with_insights(self):
        """Test reflection with key insights."""
        reflection = SessionReflection(
            session_id="test",
            task="Test",
            duration_minutes=30,
            reflection_text="Good progress",
            key_insights=["Insight 1", "Insight 2", "Insight 3"],
        )

        assert len(reflection.key_insights) == 3

    def test_reflection_text_validation(self):
        """Test reflection text length validation."""
        # Valid
        reflection = SessionReflection(
            session_id="test",
            task="Test",
            duration_minutes=30,
            reflection_text="x" * 1000,  # Max length
        )
        assert len(reflection.reflection_text) == 1000

        # Too long
        with pytest.raises(ValidationError) as exc_info:
            SessionReflection(
                session_id="test",
                task="Test",
                duration_minutes=30,
                reflection_text="x" * 1001,
            )
        assert "1000" in str(exc_info.value)

    def test_key_insights_validation(self):
        """Test key insights list validation."""
        # Valid - up to 5 items
        reflection = SessionReflection(
            session_id="test",
            task="Test",
            duration_minutes=30,
            reflection_text="Test",
            key_insights=["1", "2", "3", "4", "5"],
        )
        assert len(reflection.key_insights) == 5

        # Too many
        with pytest.raises(ValidationError):
            SessionReflection(
                session_id="test",
                task="Test",
                duration_minutes=30,
                reflection_text="Test",
                key_insights=["1", "2", "3", "4", "5", "6"],  # 6 exceeds limit
            )

    def test_related_memories_validation(self):
        """Test related memories list validation."""
        # Valid
        reflection = SessionReflection(
            session_id="test",
            task="Test",
            duration_minutes=30,
            reflection_text="Test",
            related_memories=["mem1", "mem2", "mem3"],
        )
        assert len(reflection.related_memories) == 3

        # Too many
        with pytest.raises(ValidationError):
            SessionReflection(
                session_id="test",
                task="Test",
                duration_minutes=30,
                reflection_text="Test",
                related_memories=["mem"] * 6,  # Exceeds 5
            )


# Pytest configuration
@pytest.fixture
def sample_session():
    """Fixture providing a sample work session."""
    return WorkSession(
        task="Sample task for testing",
        start_time=datetime.now(UTC) - timedelta(minutes=30),
        end_time=datetime.now(UTC),
        learnings=["Test learning"],
        challenges=["Test challenge"],
        notes="Sample notes",
    )


@pytest.fixture
def sample_journal():
    """Fixture providing a sample daily journal."""
    journal = DailyJournal(
        morning_intention="Test all features", energy_level=4, mood="focused"
    )

    # Add some sessions
    session1 = WorkSession(
        task="Task 1",
        start_time=datetime.now(UTC) - timedelta(hours=2),
        end_time=datetime.now(UTC) - timedelta(hours=1),
    )
    session2 = WorkSession(
        task="Task 2",
        start_time=datetime.now(UTC) - timedelta(minutes=30),
        end_time=datetime.now(UTC),
    )

    journal.add_session(session1)
    journal.add_session(session2)
    journal.wins = ["Completed testing"]

    return journal


def test_fixtures(sample_session, sample_journal):
    """Test that fixtures work correctly."""
    assert sample_session is not None
    assert sample_session.task == "Sample task for testing"

    assert sample_journal is not None
    assert len(sample_journal.work_sessions) == 2
    assert len(sample_journal.wins) == 1
