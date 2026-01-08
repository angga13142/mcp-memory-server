"""Validate journal models structure and constraints."""

import asyncio
from datetime import datetime, timedelta, timezone

from pydantic import ValidationError

from src.models.journal import DailyJournal, SessionReflection, WorkSession


async def validate_work_session_model():
    """Validate WorkSession model."""
    print("🧪 Testing WorkSession model...")

    # Test 1: Valid session creation
    session = WorkSession(task="Test task", start_time=datetime.now(timezone.utc))
    assert session.id is not None, "Session ID should be auto-generated"
    assert session.is_active == True, "New session should be active"
    assert session.duration_minutes >= 0, "Duration should be non-negative"
    print("  ✅ Valid session creation works")

    # Test 2: Duration calculation
    start = datetime.now(timezone.utc) - timedelta(minutes=45)
    session = WorkSession(
        task="Test task", start_time=start, end_time=datetime.now(timezone.utc)
    )
    assert (
        44 <= session.duration_minutes <= 46
    ), f"Duration should be ~45 min, got {session.duration_minutes}"
    assert session.is_active == False, "Completed session should not be active"
    print("  ✅ Duration calculation works")

    # Test 3: Task validation (empty)
    try:
        session = WorkSession(task="", start_time=datetime.now(timezone.utc))
        assert False, "Should have raised ValidationError for empty task"
    except ValidationError as e:
        assert "task" in str(e).lower(), "Error should mention task field"
    print("  ✅ Empty task validation works")

    # Test 4: Task length limit
    try:
        session = WorkSession(
            task="x" * 501,  # Exceeds 500 char limit
            start_time=datetime.now(timezone.utc),
        )
        assert False, "Should have raised ValidationError for task too long"
    except ValidationError as e:
        assert "500" in str(e) or "max_length" in str(e).lower()
    print("  ✅ Task length validation works")

    print("✅ WorkSession model validation PASSED\n")


async def validate_daily_journal_model():
    """Validate DailyJournal model."""
    print("🧪 Testing DailyJournal model...")

    # Test 1: Valid journal creation
    journal = DailyJournal()
    assert journal.id is not None, "Journal ID should be auto-generated"
    assert (
        journal.date == datetime.now(timezone.utc).date()
    ), "Date should default to today"
    assert journal.energy_level == 3, "Energy level should default to 3"
    assert journal.total_work_minutes == 0, "New journal should have 0 work minutes"
    assert journal.tasks_worked_on == 0, "New journal should have 0 tasks"
    print("  ✅ Valid journal creation works")

    # Test 2: Add session
    session = WorkSession(task="Test task", start_time=datetime.now(timezone.utc))
    journal.add_session(session)
    assert len(journal.work_sessions) == 1, "Session should be added"
    assert journal.tasks_worked_on == 1, "Tasks count should update"
    print("  ✅ Add session works")

    # Test 3: Get active session
    active = journal.get_active_session()
    assert active is not None, "Should find active session"
    assert active.id == session.id, "Should return correct session"
    print("  ✅ Get active session works")

    print("✅ DailyJournal model validation PASSED\n")


async def validate_session_reflection_model():
    """Validate SessionReflection model."""
    print("🧪 Testing SessionReflection model...")

    # Test 1: Valid reflection
    reflection = SessionReflection(
        session_id="test123",
        task="Test task",
        duration_minutes=45,
        reflection_text="This was productive.",
    )
    assert reflection.session_id == "test123"
    assert len(reflection.key_insights) == 0, "Should default to empty list"
    print("  ✅ Valid reflection creation works")

    print("✅ SessionReflection model validation PASSED\n")


async def main():
    """Run all model validations."""
    print("=" * 60)
    print("PHASE 1: MODEL VALIDATION")
    print("=" * 60)
    print()

    await validate_work_session_model()
    await validate_daily_journal_model()
    await validate_session_reflection_model()

    print("=" * 60)
    print("✅ ALL MODEL VALIDATIONS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
