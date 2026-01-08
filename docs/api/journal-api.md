# Daily Journal API Reference

## MCP Tools

### `start_working_on`

Start tracking a work session.

**Signature:**

```python
async def start_working_on(task: str) -> dict[str, Any]
```

**Parameters:**

| Parameter | Type  | Required | Constraints | Description            |
| --------- | ----- | -------- | ----------- | ---------------------- |
| `task`    | `str` | Yes      | 1-500 chars | What you're working on |

**Returns:**

```python
{
    "success": bool,
    "session_id": str,        # Unique identifier
    "task": str,              # Echo of task
    "started_at": str,        # ISO 8601 timestamp
    "message": str,           # Human-readable message
    "tip": str,               # Helpful suggestion
    "error": str | None       # Error message if failed
}
```

**Success Example:**

```python
{
    "success": true,
    "session_id": "a1b2c3d4",
    "task": "Implementing user authentication",
    "started_at": "2025-01-08T10:30:00Z",
    "message": "Started working on: Implementing user authentication",
    "tip": "Use end_work_session when done to get AI reflection"
}
```

**Error Examples:**

```python
# Empty task
{
    "success": false,
    "error": "Task description is required",
    "tip": "Provide a brief description of what you're working on"
}

# Session already active
{
    "success": false,
    "error": "Session already active: Previous task",
    "tip": "Use end_work_session to complete current session first"
}

# Task too long
{
    "success": false,
    "error": "Task description too long (max 500 characters)",
    "tip": "Keep it concise - just the main focus"
}
```

**Behavior:**

- Creates new work session in today's journal
- Sets `start_time` to current UTC timestamp
- Fails if another session is already active
- Updates active context automatically

---

### `end_work_session`

End current work session with optional reflection.

**Signature:**

```python
async def end_work_session(
    what_i_learned: list[str] | None = None,
    challenges_faced: list[str] | None = None,
    quick_note: str = ""
) -> dict[str, Any]
```

**Parameters:**

| Parameter          | Type        | Required | Constraints    | Description                |
| ------------------ | ----------- | -------- | -------------- | -------------------------- |
| `what_i_learned`   | `list[str]` | No       | Max 10 items   | Key learnings from session |
| `challenges_faced` | `list[str]` | No       | Max 10 items   | Blockers or difficulties   |
| `quick_note`       | `str`       | No       | Max 2000 chars | Additional context         |

**Returns:**

```python
{
    "success": bool,
    "session_id": str,
    "task": str,
    "duration_minutes": int,
    "reflection": str,        # AI-generated (if ≥30 min)
    "message": str,
    "next": str,              # Suggestion for next action
    "error": str | None
}
```

**Success with Reflection:**

```python
{
    "success": true,
    "session_id": "a1b2c3d4",
    "task": "Implementing user authentication",
    "duration_minutes": 127,
    "reflection": "This authentication implementation builds on yesterday's security work. The OAuth2 flow implementation demonstrates solid understanding of the protocol. Consider documenting the token refresh strategy as it solves the session management challenge from last week.",
    "message": "Session ended. Reflection generated and saved.",
    "next": "Check recent reflections with: search_memory('reflection today')"
}
```

**Success without Reflection (short session):**

```python
{
    "success": true,
    "session_id": "e5f6g7h8",
    "task": "Quick bug fix",
    "duration_minutes": 15,
    "message": "Session ended.",
    "next": "Check recent reflections with: search_memory('reflection today')"
}
```

**Error Example:**

```python
{
    "success": false,
    "error": "No active work session found",
    "tip": "Use start_working_on to begin a session"
}
```

**Behavior:**

- Sets `end_time` to current UTC timestamp
- Calculates duration automatically
- Generates AI reflection if duration ≥30 minutes (configurable)
- Saves reflection to vector store for searchability
- Updates session with learnings, challenges, and notes

---

### `how_was_my_day`

Get AI-generated summary of your workday.

**Signature:**

```python
async def how_was_my_day(date: str | None = None) -> dict[str, Any]
```

**Parameters:**

| Parameter | Type  | Required | Format     | Description                           |
| --------- | ----- | -------- | ---------- | ------------------------------------- |
| `date`    | `str` | No       | YYYY-MM-DD | Date to summarize (defaults to today) |

**Returns:**

```python
{
    "success": bool,
    "date": str,
    "summary": str,           # AI-generated narrative
    "stats": {
        "total_hours": float,
        "tasks_worked_on": int,
        "sessions": int,
        "learnings_captured": int,
        "challenges_noted": int
    },
    "message": str | None,
    "error": str | None
}
```

**Success Example:**

```python
{
    "success": true,
    "date": "2025-01-08",
    "summary": "Today was a deep-work day! You spent 6.2 hours in focused sessions, primarily on caching infrastructure. The Redis implementation you completed addresses the performance bottleneck identified in Monday's load testing. Your learnings about pipelines and connection pooling will be valuable for future optimizations. Tomorrow, consider sharing these insights with the team and tackling that API documentation you've been postponing. Great progress!",
    "stats": {
        "total_hours": 6.2,
        "tasks_worked_on": 3,
        "sessions": 4,
        "learnings_captured": 8,
        "challenges_noted": 2
    }
}
```

**Error Examples:**

```python
# No sessions recorded
{
    "success": false,
    "message": "No work sessions recorded for 2025-01-08",
    "date": "2025-01-08"
}

# Invalid date format
{
    "success": false,
    "error": "Invalid date format. Use YYYY-MM-DD (e.g., 2025-01-08)"
}
```

**Behavior:**

- Aggregates all sessions for the specified date
- Calculates statistics (time, tasks, learnings, challenges)
- Generates AI summary connecting to past work
- Provides suggestions for next day
- Saves summary to journal and vector store

---

### `set_morning_intention`

Set your intention or goal for the day.

**Signature:**

```python
async def set_morning_intention(intention: str) -> dict[str, Any]
```

**Parameters:**

| Parameter   | Type  | Required | Constraints  | Description         |
| ----------- | ----- | -------- | ------------ | ------------------- |
| `intention` | `str` | Yes      | 1-1000 chars | Daily focus or goal |

**Returns:**

```python
{
    "success": bool,
    "message": str,
    "intention": str,
    "tip": str,
    "error": str | None
}
```

**Example:**

```python
{
    "success": true,
    "message": "Morning intention set! 🌅",
    "intention": "Ship authentication feature and write comprehensive tests",
    "tip": "Use start_working_on when you begin your first task"
}
```

---

### `capture_win`

Capture a win or achievement for today.

**Signature:**

```python
async def capture_win(win: str) -> dict[str, Any]
```

**Parameters:**

| Parameter | Type  | Required | Constraints | Description             |
| --------- | ----- | -------- | ----------- | ----------------------- |
| `win`     | `str` | Yes      | 1-500 chars | Achievement description |

**Returns:**

```python
{
    "success": bool,
    "message": str,
    "win": str,
    "total_wins_today": int,
    "tip": str,
    "error": str | None
}
```

**Example:**

```python
{
    "success": true,
    "message": "Win captured! 🎉",
    "win": "All tests passing! 100% coverage achieved",
    "total_wins_today": 3,
    "tip": "Keep celebrating your progress!"
}
```

---

## MCP Prompts

### `morning_briefing_prompt`

Generate morning briefing with context.

**Returns:** Formatted markdown string

**Content Includes:**

- Yesterday's summary
- Pending tasks
- Recent decisions
- Suggested focus areas

**Example Output:**

```markdown
# Morning Briefing - Wednesday, January 8

## Yesterday's Recap

You had a productive day focused on authentication.
Completed 3 tasks and made solid progress on OAuth2 implementation.

## Today's Focus Areas

**Pending Tasks:**

- [DOING] Write integration tests
- [NEXT] Deploy to staging
- [NEXT] Update documentation

**Recent Decisions to Remember:**

- Use JWT for session management
- Implement refresh token rotation

---

_What's your intention for today?_
```

---

### `active_session_prompt`

Get status of current work session.

**Returns:** Formatted markdown string

**Example Output (Active Session):**

```markdown
# Active Work Session

**Task:** Implementing Redis caching layer

**Duration:** 1h 23m

**Started:** 09:15 AM

---

_Keep up the focus! Use end_work_session() when ready._
```

**Example Output (No Session):**

```markdown
# No Active Session

You're not currently tracking a work session.

Use `start_working_on("task description")` to begin.
```

---

### `daily_progress_prompt`

Get snapshot of today's progress.

**Returns:** Formatted markdown string

**Example Output:**

```markdown
# Today's Progress - Wednesday, January 8

## Work Sessions

- **Completed:** 3 sessions
- **Total Time:** 5h 45m
- **Tasks:** 3

**Currently Working:** Writing documentation (45m)

## Wins Today 🎉

- All tests passing
- Feature deployed to staging
- Documentation complete

---

✨ **Great focus today!** You're in the zone.
```

---

## MCP Resources

### `memory://journal/today`

Get today's complete journal.

**Returns:** JSON object of `DailyJournal` model

**Example:**

```json
{
  "id": "journal123",
  "date": "2025-01-08",
  "morning_intention": "Ship authentication feature",
  "work_sessions": [
    {
      "id": "session1",
      "task": "Implementing OAuth2",
      "start_time": "2025-01-08T09:00:00Z",
      "end_time": "2025-01-08T11:00:00Z",
      "duration_minutes": 120,
      "learnings": ["OAuth2 flow requires state management"],
      "challenges": ["CORS configuration was tricky"],
      "notes": "Feature complete, needs testing"
    }
  ],
  "wins": ["Feature deployed to staging"],
  "energy_level": 4,
  "mood": "focused",
  "end_of_day_reflection": "Productive day focused on authentication...",
  "total_work_minutes": 360,
  "tasks_worked_on": 3
}
```

---

### `memory://journal/{date}`

Get journal for specific date.

**Path Parameters:**

- `date`: Date in YYYY-MM-DD format

**Example:** `memory://journal/2025-01-07`

**Returns:** JSON object of `DailyJournal` or error

---

### `memory://journal/recent`

Get journals for past 7 days.

**Returns:** Array of `DailyJournal` objects (most recent first)

---

### `memory://journal/stats/weekly`

Get work statistics for past week.

**Returns:**

```json
{
  "period": "Last 7 days",
  "total_hours": 42.5,
  "days_worked": 6,
  "total_sessions": 23,
  "total_tasks": 15,
  "total_wins": 12,
  "averages": {
    "hours_per_day": 7.1,
    "sessions_per_day": 3.8
  }
}
```

---

## Data Models

### WorkSession

```python
class WorkSession(BaseModel):
    id: str                           # Auto-generated (8 chars)
    start_time: datetime              # UTC timezone-aware
    end_time: datetime | None         # None if active
    task: str                         # 1-500 characters
    files_touched: list[str]          # Max 50 items
    decisions_made: list[str]         # Max 20 items
    notes: str                        # Max 2000 characters
    learnings: list[str]              # Max 10 items
    challenges: list[str]             # Max 10 items

    # Computed properties (read-only)
    duration_minutes: int
    is_active: bool
```

### DailyJournal

```python
class DailyJournal(BaseModel):
    id: str                           # Auto-generated
    date: date                        # Defaults to today
    morning_intention: str            # Max 1000 characters
    work_sessions: list[WorkSession]
    end_of_day_reflection: str        # AI-generated, max 2000 chars
    energy_level: int                 # 1-5 scale
    mood: str                         # Max 50 characters
    wins: list[str]                   # Max 10 items, 500 chars each
    created_at: datetime
    updated_at: datetime

    # Computed properties (read-only)
    total_work_minutes: int
    tasks_worked_on: int              # Unique tasks count
```

### SessionReflection

```python
class SessionReflection(BaseModel):
    session_id: str
    task: str
    duration_minutes: int
    reflection_text: str              # Max 1000 characters
    key_insights: list[str]           # Max 5 items
    related_memories: list[str]       # Max 5 memory IDs
    created_at: datetime
```
