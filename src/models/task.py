"""Task and memory entry data models."""

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)


def generate_id() -> str:
    """Generate a unique ID."""
    return str(uuid4())[:8]


TaskStatus = Literal["done", "doing", "next", "blocked"]
TaskPriority = Literal["high", "medium", "low"]


class Task(BaseModel):
    """Task for progress tracking.

    Tracks work items with status and priority.
    """

    id: str = Field(default_factory=generate_id, description="Task unique identifier")
    title: str = Field(..., description="Task title")
    description: str = Field(default="", description="Task description")
    status: TaskStatus = Field(default="next", description="Task status")
    priority: TaskPriority = Field(default="medium", description="Task priority")
    tags: list[str] = Field(default_factory=list, description="Categorization tags")
    parent_id: str | None = Field(default=None, description="Parent task ID for subtasks")
    created_at: datetime = Field(default_factory=utc_now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=utc_now, description="Last update timestamp")
    completed_at: datetime | None = Field(default=None, description="Completion timestamp")
    blocked_reason: str | None = Field(default=None, description="Reason if blocked")

    model_config = {"extra": "forbid"}

    def update_status(
        self, status: TaskStatus, blocked_reason: str | None = None
    ) -> "Task":
        """Update task status."""
        self.status = status
        self.updated_at = utc_now()

        if status == "done":
            self.completed_at = utc_now()
            self.blocked_reason = None
        elif status == "blocked":
            self.blocked_reason = blocked_reason
            self.completed_at = None
        else:
            self.blocked_reason = None
            self.completed_at = None

        return self

    def is_active(self) -> bool:
        """Check if task is currently active."""
        return self.status in ("doing", "next")


class ProgressTracker(BaseModel):
    """Task collection with progress tracking."""

    tasks: list[Task] = Field(default_factory=list)

    def add(self, task: Task) -> Task:
        """Add a task."""
        self.tasks.append(task)
        return task

    def get(self, task_id: str) -> Task | None:
        """Get a task by ID."""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def by_status(self, status: TaskStatus) -> list[Task]:
        """Get tasks by status."""
        return [t for t in self.tasks if t.status == status]

    def by_priority(self, priority: TaskPriority) -> list[Task]:
        """Get tasks by priority."""
        return [t for t in self.tasks if t.priority == priority]

    def grouped_by_status(self) -> dict[str, list[Task]]:
        """Get tasks grouped by status."""
        return {
            "done": self.by_status("done"),
            "doing": self.by_status("doing"),
            "next": self.by_status("next"),
            "blocked": self.by_status("blocked"),
        }

    def active_count(self) -> int:
        """Count active tasks."""
        return len([t for t in self.tasks if t.is_active()])


class MemoryEntry(BaseModel):
    """Generic memory entry for vector search.

    Used for storing arbitrary content with embeddings for semantic search.
    """

    id: str = Field(default_factory=generate_id, description="Entry unique identifier")
    content: str = Field(..., description="Text content to embed and search")
    content_type: str = Field(
        default="note", description="Type of content (note, decision, context, etc.)"
    )
    source_id: str | None = Field(
        default=None, description="ID of source object (decision_id, task_id, etc.)"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    tags: list[str] = Field(default_factory=list, description="Categorization tags")
    embedding: list[float] | None = Field(
        default=None, description="Vector embedding (populated by vector store)"
    )
    created_at: datetime = Field(default_factory=utc_now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=utc_now, description="Last update timestamp")

    model_config = {"extra": "forbid"}

    def update_content(self, content: str) -> None:
        """Update content and clear embedding (needs re-embedding)."""
        self.content = content
        self.embedding = None
        self.updated_at = utc_now()

    def to_search_metadata(self) -> dict[str, Any]:
        """Get metadata for vector search indexing."""
        return {
            "id": self.id,
            "content_type": self.content_type,
            "source_id": self.source_id or "",
            "tags": ",".join(self.tags),
            "created_at": self.created_at.isoformat(),
            **{k: str(v) for k, v in self.metadata.items()},
        }
