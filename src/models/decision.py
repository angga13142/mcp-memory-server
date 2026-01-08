"""Decision logging data models."""

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


def utc_now() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)


def generate_id() -> str:
    """Generate a unique ID."""
    return str(uuid4())[:8]


class Decision(BaseModel):
    """Architectural decision record (ADR).

    Captures important decisions with context and rationale.
    """

    id: str = Field(default_factory=generate_id, description="Decision unique identifier")
    title: str = Field(..., max_length=500, description="Decision title/summary")
    decision: str = Field(..., max_length=5000, description="The decision that was made")
    rationale: str = Field(..., max_length=5000, description="Why this decision was made")
    alternatives_considered: list[str] = Field(
        default_factory=list, max_length=50, description="Other options that were considered"
    )
    consequences: list[str] = Field(
        default_factory=list, max_length=50, description="Expected consequences of this decision"
    )
    tags: list[str] = Field(default_factory=list, max_length=50, description="Categorization tags")
    status: Literal["proposed", "accepted", "deprecated", "superseded"] = Field(
        default="accepted", description="Decision status"
    )
    created_at: datetime = Field(default_factory=utc_now, description="Creation timestamp")
    created_by: str = Field(default="user", max_length=100, description="Who made this decision")
    superseded_by: str | None = Field(
        default=None, description="ID of decision that supersedes this one"
    )

    model_config = {"extra": "forbid"}

    @field_validator('tags', 'alternatives_considered', 'consequences')
    @classmethod
    def validate_string_list_items(cls, v: list[str]) -> list[str]:
        """Validate that list items don't exceed max length."""
        for item in v:
            if len(item) > 500:
                raise ValueError("List items must be <= 500 characters")
        return v

    def deprecate(self, superseded_by: str | None = None) -> None:
        """Mark this decision as deprecated."""
        self.status = "superseded" if superseded_by else "deprecated"
        self.superseded_by = superseded_by


class DecisionLog(BaseModel):
    """Collection of decisions with query capabilities."""

    decisions: list[Decision] = Field(default_factory=list)

    def add(self, decision: Decision) -> Decision:
        """Add a new decision to the log."""
        self.decisions.append(decision)
        return decision

    def get(self, decision_id: str) -> Decision | None:
        """Get a decision by ID."""
        for decision in self.decisions:
            if decision.id == decision_id:
                return decision
        return None

    def filter_by_tag(self, tag: str) -> list[Decision]:
        """Get decisions with a specific tag."""
        return [d for d in self.decisions if tag in d.tags]

    def filter_by_status(
        self, status: Literal["proposed", "accepted", "deprecated", "superseded"]
    ) -> list[Decision]:
        """Get decisions with a specific status."""
        return [d for d in self.decisions if d.status == status]

    def recent(self, limit: int = 5) -> list[Decision]:
        """Get the most recent decisions."""
        sorted_decisions = sorted(self.decisions, key=lambda d: d.created_at, reverse=True)
        return sorted_decisions[:limit]
