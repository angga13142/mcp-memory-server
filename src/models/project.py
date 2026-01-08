"""Project-level data models."""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field, field_validator


def utc_now() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)


class ProjectBrief(BaseModel):
    """Immutable project overview.

    This represents the high-level project information that rarely changes.
    """

    name: str = Field(..., max_length=255, description="Project name")
    description: str = Field(..., max_length=5000, description="Project description")
    goals: list[str] = Field(
        default_factory=list, max_length=100, description="Project goals"
    )
    created_at: datetime = Field(
        default_factory=utc_now, description="Creation timestamp"
    )
    version: str = Field(default="1.0.0", max_length=50, description="Project version")

    model_config = {"extra": "forbid"}

    @field_validator("goals")
    @classmethod
    def validate_goal_length(cls, v: list[str]) -> list[str]:
        """Validate that goals don't exceed max length."""
        for goal in v:
            if len(goal) > 500:
                raise ValueError("Goals must be <= 500 characters")
        return v


class TechStackItem(BaseModel):
    """Individual technology stack item."""

    name: str = Field(..., max_length=100, description="Technology name")
    version: str = Field(
        default="", max_length=50, description="Version (if applicable)"
    )
    category: str = Field(
        default="general",
        max_length=50,
        description="Category (language, framework, tool)",
    )


class TechStack(BaseModel):
    """Technology stack configuration.

    Semi-stable list of technologies used in the project.
    """

    languages: list[str] = Field(
        default_factory=list, max_length=50, description="Programming languages"
    )
    frameworks: list[TechStackItem] = Field(
        default_factory=list, max_length=100, description="Frameworks with versions"
    )
    tools: list[str] = Field(
        default_factory=list, max_length=100, description="Development tools"
    )
    last_updated: datetime = Field(
        default_factory=utc_now, description="Last update timestamp"
    )

    model_config = {"extra": "forbid"}

    @field_validator("languages", "tools")
    @classmethod
    def validate_string_list_items(cls, v: list[str]) -> list[str]:
        """Validate that list items don't exceed max length."""
        for item in v:
            if len(item) > 100:
                raise ValueError("List items must be <= 100 characters")
        return v

    def add_framework(self, name: str, version: str = "") -> None:
        """Add a framework to the stack."""
        self.frameworks.append(
            TechStackItem(name=name, version=version, category="framework")
        )
        self.last_updated = utc_now()


class SystemPattern(BaseModel):
    """Architectural pattern or convention."""

    id: str = Field(..., description="Pattern unique identifier")
    name: str = Field(..., description="Pattern name")
    description: str = Field(..., description="Pattern description")
    example: str = Field(default="", description="Usage example")
    tags: list[str] = Field(default_factory=list, description="Categorization tags")
    created_at: datetime = Field(default_factory=utc_now)

    model_config = {"extra": "forbid"}


class SystemPatterns(BaseModel):
    """Collection of system patterns and conventions."""

    patterns: list[SystemPattern] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=utc_now)

    def add_pattern(
        self,
        id: str,
        name: str,
        description: str,
        example: str = "",
        tags: list[str] | None = None,
    ) -> SystemPattern:
        """Add a new pattern."""
        pattern = SystemPattern(
            id=id,
            name=name,
            description=description,
            example=example,
            tags=tags or [],
        )
        self.patterns.append(pattern)
        self.last_updated = utc_now()
        return pattern

    def get_pattern(self, pattern_id: str) -> SystemPattern | None:
        """Get a pattern by ID."""
        for pattern in self.patterns:
            if pattern.id == pattern_id:
                return pattern
        return None
