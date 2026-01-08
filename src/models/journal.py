"""Daily work journal models."""

from datetime import datetime, timezone, timedelta, date as dt_date
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field, computed_field


def utc_now() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)


def generate_id() -> str:
    """Generate a unique ID."""
    return str(uuid4())[:8]


class WorkSession(BaseModel):
    """Individual work session within a day."""
    
    id: str = Field(default_factory=generate_id, description="Session ID")
    start_time: datetime = Field(default_factory=utc_now, description="Session start")
    end_time: datetime | None = Field(default=None, description="Session end")
    task: str = Field(..., min_length=1, max_length=500, description="What you're working on")
    files_touched: list[str] = Field(default_factory=list, max_length=50, description="Files modified")
    decisions_made: list[str] = Field(default_factory=list, max_length=20, description="Decisions during session")
    notes: str = Field(default="", max_length=2000, description="Session notes")
    learnings: list[str] = Field(default_factory=list, max_length=10, description="What you learned")
    challenges: list[str] = Field(default_factory=list, max_length=10, description="Challenges faced")
    
    model_config = {"extra": "forbid"}
    
    @computed_field
    @property
    def duration_minutes(self) -> int:
        """Calculate session duration in minutes."""
        if not self.end_time:
            # Session still active - calculate current duration
            return int((datetime.now(timezone.utc) - self.start_time).total_seconds() / 60)
        return int((self.end_time - self.start_time).total_seconds() / 60)
    
    @computed_field
    @property
    def is_active(self) -> bool:
        """Check if session is currently active."""
        return self.end_time is None


class DailyJournal(BaseModel):
    """Daily work journal entry."""
    
    id: str = Field(default_factory=generate_id, description="Journal entry ID")
    date: dt_date = Field(
        default_factory=lambda: datetime.now(timezone.utc).date(),
        description="Journal date"
    )
    morning_intention: str = Field(
        default="",
        max_length=1000,
        description="What you plan to work on today"
    )
    work_sessions: list[WorkSession] = Field(
        default_factory=list,
        description="Work sessions for the day"
    )
    end_of_day_reflection: str = Field(
        default="",
        max_length=2000,
        description="AI-generated daily reflection"
    )
    energy_level: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Energy level (1=drained, 5=energized)"
    )
    mood: str = Field(
        default="",
        max_length=50,
        description="Mood descriptor (focused, creative, struggling, etc.)"
    )
    wins: list[str] = Field(
        default_factory=list,
        max_length=10,
        description="Wins for the day"
    )
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    
    model_config = {"extra": "forbid"}
    
    @computed_field
    @property
    def total_work_minutes(self) -> int:
        """Calculate total work time for the day."""
        return sum(session.duration_minutes for session in self.work_sessions)
    
    @computed_field
    @property
    def tasks_worked_on(self) -> int:
        """Count unique tasks worked on."""
        return len(set(session.task for session in self.work_sessions))
    
    def add_session(self, session: WorkSession) -> None:
        """Add a work session to the journal."""
        self.work_sessions.append(session)
        self.updated_at = utc_now()
    
    def get_active_session(self) -> WorkSession | None:
        """Get currently active session if any."""
        for session in self.work_sessions:
            if session.is_active:
                return session
        return None


class SessionReflection(BaseModel):
    """AI-generated reflection for a work session."""
    
    session_id: str
    task: str
    duration_minutes: int
    reflection_text: str = Field(max_length=1000)
    key_insights: list[str] = Field(default_factory=list, max_length=5)
    related_memories: list[str] = Field(default_factory=list, max_length=5)
    created_at: datetime = Field(default_factory=utc_now)
