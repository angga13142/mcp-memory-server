# Daily Work Journal - User Guide

## 🌟 What is Daily Work Journal?

Your personal "second brain" that tracks work sessions, captures learnings, and provides AI-powered insights about your productivity patterns.

### Core Features

- ⏱️ **Automatic Time Tracking** - Start/stop sessions with one command
- 🧠 **Learning Capture** - Document insights as you discover them
- 🎯 **Daily Intentions** - Set focus at start of day
- 🎉 **Win Tracking** - Celebrate achievements big and small
- 📊 **AI Insights** - Get reflections and summaries automatically
- 🔍 **Full-Text Search** - Find anything from past work

### Who Is This For?

- **Solo Developers** - Track personal productivity and learning
- **Small Teams (2-10)** - Share knowledge and coordinate work
- **Researchers** - Document discoveries and connect ideas
- **Anyone** who wants to remember what they worked on and learned

---

## 🚀 Quick Start - Your First Session

### Step 1: Start Working (10 seconds)

```python
start_working_on("Learning the Daily Journal feature")
```

✅ Returns: `{"success": true, "session_id": "abc123", "started_at": "..."}`

### Step 2: Do Your Work (however long)

The timer runs automatically. No need to do anything!

### Step 3: End Session with Notes (30 seconds)

```python
end_work_session(
    what_i_learned=["Daily journal is easy to use"],
    quick_note="Ready to use this daily"
)
```

✅ Returns: Session summary with duration

### Step 4: Get Daily Summary (10 seconds)

```python
how_was_my_day()
```

✅ Returns: AI-generated summary of your day

**That's it! You just tracked your first work session. 🎉**

---

## 📅 Complete Daily Workflow

### 🌅 Morning (2 minutes)

**1. Get Your Briefing**

```python
@mcp morning_briefing_prompt
```

Shows:

- Yesterday's summary
- Pending tasks
- Recent decisions
- What to focus on

**2. Set Your Intention**

```python
set_morning_intention("Ship authentication feature and write tests")
```

### 💼 During Work (ongoing)

**Start Focused Sessions**

```python
# Each time you start a new task
start_working_on("Implementing OAuth2 authentication")
```

**Check Your Progress Anytime**

```python
@mcp daily_progress_prompt
```

**Capture Wins As They Happen**

```python
capture_win("All tests passing! Deployed to staging")
```

**Check Active Work**

```python
@mcp active_session_prompt
```

### 🌙 Evening (2 minutes)

**End Your Last Session**

```python
end_work_session(
    what_i_learned=["Key insights from today"],
    challenges_faced=["Blockers encountered"]
)
```

**Get Daily Summary**

```python
how_was_my_day()
```

Returns: Comprehensive summary with AI insights

---

## ⚡ Pro Tips for Daily Use

**1. Be Specific with Task Names**

- ❌ Bad: `start_working_on("coding")`
- ✅ Good: `start_working_on("Implementing Redis caching layer")`

**2. Capture Learnings Immediately**
Don't wait! Write them down while fresh:

```python
end_work_session(
    what_i_learned=[
        "Redis pipelines are 3x faster than individual calls",
        "Connection pooling is critical for production"
    ]
)
```

**3. Document Challenges**
Future you will thank you:

```python
end_work_session(
    challenges_faced=[
        "Connection pooling configuration was not obvious",
        "Needed to read Redis docs carefully"
    ]
)
```

**4. Celebrate Small Wins**

```python
capture_win("Fixed annoying bug")
capture_win("Wrote clear documentation")
capture_win("Helped teammate debug issue")
```

---

## 🎯 Common Use Cases

### Use Case 1: Deep Focus Day

```python
# Morning
set_morning_intention("Deep focus on algorithm optimization")

# Long session
start_working_on("Optimizing search algorithm")
# ... work for 3 hours ...
end_work_session(
    what_i_learned=[
        "Binary search tree reduced time from O(n) to O(log n)",
        "Profiling revealed unexpected bottleneck"
    ]
)
```

### Use Case 2: Learning New Technology

```python
# Set learning goal
set_morning_intention("Learn GraphQL fundamentals")

# Multiple short sessions
start_working_on("Learning: GraphQL schemas")
# ... 30 min ...
end_work_session(what_i_learned=["Schema-first design is powerful"])

start_working_on("Learning: GraphQL resolvers")
# ... 45 min ...
end_work_session(what_i_learned=["Resolvers are just functions"])

# Review learning
how_was_my_day()  # See all learnings aggregated
```

### Use Case 3: Bug Fixing Marathon

```python
# For each bug
start_working_on("Debug: Memory leak in session handler")
# ... investigate and fix ...
end_work_session(
    what_i_learned=["Always clean up event listeners"],
    challenges_faced=["Hard to reproduce locally"]
)
capture_win("Fixed memory leak!")

# Track all bugs
how_was_my_day()  # Shows: 5 bugs fixed, patterns identified
```

### Use Case 4: Interrupted Workday

```python
# Start work
start_working_on("Complex algorithm implementation")

# Get interrupted
end_work_session(quick_note="At step 3, need to resume after meeting")

# After interruption, recover context
@mcp daily_progress_prompt  # Shows what you were doing

# Resume
start_working_on("Continue: Algorithm implementation")
```

---

## 📊 Understanding Your Insights

### Session Reflections (for sessions ≥30 min)

**What You Get:**

```
"This caching implementation builds on yesterday's performance work.
The Redis pipeline discovery will be valuable for future optimizations.
Consider documenting the connection pooling solution as it solves
the scaling issue mentioned last week."
```

**What It Tells You:**

- ✅ What you accomplished
- 🔗 How it connects to past work
- 💡 Patterns or insights discovered
- 📝 Suggestions for next steps

### Daily Summaries

**What You Get:**

```
"Today was a deep-work day! You spent 6.2 hours in focused sessions,
primarily on caching infrastructure. The Redis implementation addresses
the performance bottleneck from Monday. Your learnings about pipelines
will be valuable for the team. Tomorrow, consider sharing these insights
and tackling that API documentation."
```

**What It Tells You:**

- 📊 Productivity metrics (time, sessions, tasks)
- 🎯 Main theme/focus of the day
- ✅ Key accomplishments
- 🔗 Context from previous days
- 💡 Suggestions for tomorrow

### Adjusting Insight Generation

**Change Reflection Threshold:**

```yaml
# config.yaml
personal:
  journal:
    min_session_minutes: 45 # Only sessions ≥45 min
```

**Disable Reflections Temporarily:**

```yaml
personal:
  journal:
    auto_reflection: false
```

---

## 🔍 Finding Past Work

### Basic Search

```python
search_memory("authentication implementation")
```

Returns: All work sessions, learnings, notes mentioning "authentication"

### View Specific Date

```python
how_was_my_day("2025-01-15")
```

### Get Recent History

```python
@mcp memory://journal/recent
```

Returns: Last 7 days of journals

### Search Tips

**1. Use Multiple Keywords**

```python
search_memory("Redis caching performance")  # More specific
```

**2. Search by Date**

```python
search_memory("authentication", date_from="2025-01-01")
```

**3. Search Learnings Only**

```python
search_memory("OAuth2", content_types=["session_reflection"])
```

---

## 📝 Quick Reference Card

```
🌅 MORNING
━━━━━━━━━━━━━━━━━━━━━━━━━━
set_morning_intention("...")     Set daily focus
@mcp morning_briefing_prompt     Get briefing

💼 DURING WORK
━━━━━━━━━━━━━━━━━━━━━━━━━━
start_working_on("...")          Start session
@mcp active_session_prompt       Check status
capture_win("...")               Log achievement
@mcp daily_progress_prompt       See progress

🌙 END OF DAY
━━━━━━━━━━━━━━━━━━━━━━━━━━
end_work_session(...)            End session
how_was_my_day()                 Get summary

🔍 ANYTIME
━━━━━━━━━━━━━━━━━━━━━━━━━━
search_memory("...")             Find past work
how_was_my_day("2025-01-15")    View date
@mcp memory://journal/recent     Last 7 days
```
