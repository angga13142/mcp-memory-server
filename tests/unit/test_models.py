"""Unit tests for Pydantic models."""

from datetime import datetime

from src.models.context import ActiveContext
from src.models.decision import Decision, DecisionLog
from src.models.project import ProjectBrief, TechStack, TechStackItem
from src.models.task import MemoryEntry, ProgressTracker, Task


class TestProjectBrief:
    """Tests for ProjectBrief model."""

    def test_create_basic(self):
        """Test basic project brief creation."""
        brief = ProjectBrief(
            name="Test Project",
            description="A test project",
            goals=["Goal 1", "Goal 2"],
        )
        assert brief.name == "Test Project"
        assert brief.description == "A test project"
        assert len(brief.goals) == 2
        assert brief.version == "1.0.0"
        assert isinstance(brief.created_at, datetime)

    def test_serialize(self):
        """Test model serialization."""
        brief = ProjectBrief(
            name="Test",
            description="Test desc",
        )
        data = brief.model_dump()
        assert data["name"] == "Test"
        assert "created_at" in data


class TestTechStack:
    """Tests for TechStack model."""

    def test_add_framework(self):
        """Test adding a framework."""
        stack = TechStack()
        stack.add_framework("FastAPI", "0.100.0")
        assert len(stack.frameworks) == 1
        assert stack.frameworks[0].name == "FastAPI"
        assert stack.frameworks[0].version == "0.100.0"

    def test_full_stack(self):
        """Test full tech stack."""
        stack = TechStack(
            languages=["Python", "TypeScript"],
            frameworks=[TechStackItem(name="FastMCP", version="2.14.0")],
            tools=["Docker", "Git"],
        )
        assert len(stack.languages) == 2
        assert len(stack.frameworks) == 1
        assert len(stack.tools) == 2


class TestDecision:
    """Tests for Decision model."""

    def test_create_decision(self):
        """Test decision creation."""
        decision = Decision(
            title="Use SQLite",
            decision="We will use SQLite for storage",
            rationale="Simple and portable",
        )
        assert decision.title == "Use SQLite"
        assert decision.status == "accepted"
        assert len(decision.id) == 8

    def test_deprecate(self):
        """Test deprecating a decision."""
        decision = Decision(
            title="Old Decision",
            decision="Something",
            rationale="Reason",
        )
        decision.deprecate("new-id")
        assert decision.status == "superseded"
        assert decision.superseded_by == "new-id"


class TestDecisionLog:
    """Tests for DecisionLog model."""

    def test_add_and_get(self):
        """Test adding and retrieving decisions."""
        log = DecisionLog()
        decision = Decision(
            title="Test",
            decision="Test decision",
            rationale="Test rationale",
        )
        log.add(decision)

        retrieved = log.get(decision.id)
        assert retrieved is not None
        assert retrieved.title == "Test"

    def test_filter_by_tag(self):
        """Test filtering by tag."""
        log = DecisionLog()
        log.add(
            Decision(
                title="Tagged",
                decision="D",
                rationale="R",
                tags=["important"],
            )
        )
        log.add(
            Decision(
                title="Not Tagged",
                decision="D",
                rationale="R",
            )
        )

        filtered = log.filter_by_tag("important")
        assert len(filtered) == 1
        assert filtered[0].title == "Tagged"


class TestActiveContext:
    """Tests for ActiveContext model."""

    def test_update(self):
        """Test context update."""
        context = ActiveContext()
        context.update(
            current_task="Implement feature",
            related_files=["file.py"],
        )
        assert context.current_task == "Implement feature"
        assert "file.py" in context.related_files

    def test_add_file(self):
        """Test adding a file."""
        context = ActiveContext()
        context.add_file("test.py")
        context.add_file("test.py")  # Duplicate
        assert len(context.related_files) == 1

    def test_to_prompt(self):
        """Test prompt generation."""
        context = ActiveContext(
            current_task="Testing",
            notes="Some notes",
        )
        prompt = context.to_prompt()
        assert "Testing" in prompt
        assert "Some notes" in prompt


class TestTask:
    """Tests for Task model."""

    def test_create_task(self):
        """Test task creation."""
        task = Task(title="Test Task")
        assert task.title == "Test Task"
        assert task.status == "next"
        assert task.priority == "medium"

    def test_update_status(self):
        """Test status update."""
        task = Task(title="Test")
        task.update_status("done")
        assert task.status == "done"
        assert task.completed_at is not None

    def test_blocked_with_reason(self):
        """Test blocking a task."""
        task = Task(title="Test")
        task.update_status("blocked", "Waiting for review")
        assert task.status == "blocked"
        assert task.blocked_reason == "Waiting for review"


class TestProgressTracker:
    """Tests for ProgressTracker model."""

    def test_grouped_by_status(self):
        """Test grouping tasks by status."""
        tracker = ProgressTracker()
        tracker.add(Task(title="Done", status="done"))
        tracker.add(Task(title="Doing", status="doing"))
        tracker.add(Task(title="Next 1", status="next"))
        tracker.add(Task(title="Next 2", status="next"))

        grouped = tracker.grouped_by_status()
        assert len(grouped["done"]) == 1
        assert len(grouped["doing"]) == 1
        assert len(grouped["next"]) == 2
        assert len(grouped["blocked"]) == 0


class TestMemoryEntry:
    """Tests for MemoryEntry model."""

    def test_create_entry(self):
        """Test memory entry creation."""
        entry = MemoryEntry(content="Test content")
        assert entry.content == "Test content"
        assert entry.content_type == "note"
        assert len(entry.id) == 8

    def test_search_metadata(self):
        """Test search metadata generation."""
        entry = MemoryEntry(
            content="Test",
            content_type="decision",
            tags=["tag1", "tag2"],
        )
        metadata = entry.to_search_metadata()
        assert metadata["content_type"] == "decision"
        assert "tag1,tag2" in metadata["tags"]
