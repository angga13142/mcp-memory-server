"""Active context data models."""

from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_validator


def utc_now() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)


class ActiveContext(BaseModel):
    """Current working focus.

    Tracks what the user/AI is currently working on. This is frequently updated
    and provides immediate context for the current session.
    """

    current_task: str = Field(default="", max_length=1000, description="Current task being worked on")
    related_files: list[str] = Field(
        default_factory=list, max_length=100, description="Files relevant to current work"
    )
    relevant_decisions: list[str] = Field(
        default_factory=list, max_length=100, description="IDs of relevant decisions"
    )
    notes: str = Field(default="", max_length=10000, description="Free-form notes about current context")
    working_branch: str = Field(default="", max_length=255, description="Git branch being worked on")
    session_id: str = Field(default="", max_length=100, description="Current session identifier")
    last_updated: datetime = Field(default_factory=utc_now, description="Last update timestamp")

    model_config = {"extra": "forbid"}

    @field_validator('related_files')
    @classmethod
    def validate_file_path_length(cls, v: list[str]) -> list[str]:
        """Validate that file paths don't exceed max length."""
        for path in v:
            if len(path) > 500:
                raise ValueError("File paths must be <= 500 characters")
        return v

    def update(
        self,
        current_task: str | None = None,
        related_files: list[str] | None = None,
        relevant_decisions: list[str] | None = None,
        notes: str | None = None,
        working_branch: str | None = None,
    ) -> "ActiveContext":
        """Update context fields and timestamp."""
        if current_task is not None:
            self.current_task = current_task
        if related_files is not None:
            self.related_files = related_files
        if relevant_decisions is not None:
            self.relevant_decisions = relevant_decisions
        if notes is not None:
            self.notes = notes
        if working_branch is not None:
            self.working_branch = working_branch
        self.last_updated = utc_now()
        return self

    def add_file(self, file_path: str) -> None:
        """Add a file to related files if not already present."""
        if file_path not in self.related_files:
            self.related_files.append(file_path)
            self.last_updated = utc_now()

    def remove_file(self, file_path: str) -> None:
        """Remove a file from related files."""
        if file_path in self.related_files:
            self.related_files.remove(file_path)
            self.last_updated = utc_now()

    def clear(self) -> "ActiveContext":
        """Reset context to empty state."""
        self.current_task = ""
        self.related_files = []
        self.relevant_decisions = []
        self.notes = ""
        self.working_branch = ""
        self.last_updated = utc_now()
        return self

    def to_prompt(self) -> str:
        """Convert context to a prompt-friendly string."""
        lines = []
        if self.current_task:
            lines.append(f"Current Task: {self.current_task}")
        if self.related_files:
            lines.append(f"Related Files: {', '.join(self.related_files)}")
        if self.notes:
            lines.append(f"Notes: {self.notes}")
        if self.working_branch:
            lines.append(f"Branch: {self.working_branch}")
        return "\n".join(lines) if lines else "No active context set."
