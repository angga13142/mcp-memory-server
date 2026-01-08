# Daily Journal - Examples & Recipes

## Copy-Paste Examples for Common Scenarios

### Recipe 1: Simple Daily Workflow

```python
# ===== MORNING =====
set_morning_intention("Complete authentication feature")

# ===== START WORK =====
start_working_on("Implementing OAuth2 authentication")

# ... do your work ...

# ===== END SESSION =====
end_work_session(
    what_i_learned=["OAuth2 requires careful state management"],
    quick_note="Feature ready for review"
)

# ===== EVENING =====
summary = how_was_my_day()
print(f"Worked {summary['stats']['total_hours']} hours today")
```

---

### Recipe 2: Deep Focus Day (Multiple Sessions)

```python
# Morning intention
set_morning_intention("Deep focus on performance optimization")

# Session 1: Profiling
start_working_on("Profiling application bottlenecks")
# ... work 90 minutes ...
end_work_session(
    what_i_learned=[
        "Database queries are main bottleneck",
        "N+1 query problem in user endpoint"
    ]
)

# Session 2: Optimization
start_working_on("Optimizing database queries")
# ... work 120 minutes ...
end_work_session(
    what_i_learned=[
        "Added indexes reduced query time by 90%",
        "Batch loading eliminates N+1 problem"
    ]
)

# Session 3: Testing
start_working_on("Performance testing optimizations")
# ... work 60 minutes ...
end_work_session(
    what_i_learned=["Load testing shows 5x improvement"],
    quick_note="Ready for production deployment"
)

# Capture wins
capture_win("Identified performance bottleneck")
capture_win("Achieved 5x performance improvement")
capture_win("All performance tests passing")

# Review day
summary = how_was_my_day()
print(f"📊 Stats:")
print(f"  Sessions: {summary['stats']['sessions']}")
print(f"  Learnings: {summary['stats']['learnings_captured']}")
print(f"  Total time: {summary['stats']['total_hours']}h")
```

---

### Recipe 3: Learning New Technology

```python
# Set learning goal
set_morning_intention("Deep dive into GraphQL - learn fundamentals")

# Structured learning sessions
learning_topics = [
    {
        "topic": "GraphQL schema design basics",
        "duration_min": 30,
        "learnings": [
            "Schema-first design provides clear contracts",
            "Types are the foundation of GraphQL",
            "Query, Mutation, Subscription are root types"
        ]
    },
    {
        "topic": "Implementing resolvers",
        "duration_min": 45,
        "learnings": [
            "Resolvers are just functions that return data",
            "DataLoader pattern prevents N+1 queries",
            "Context object shares data across resolvers"
        ]
    },
    {
        "topic": "GraphQL best practices",
        "duration_min": 30,
        "learnings": [
            "Use cursor-based pagination for scalability",
            "Implement proper error handling",
            "Consider schema design for backwards compatibility"
        ]
    }
]

# Execute learning sessions
for session in learning_topics:
    start_working_on(f"Learning: {session['topic']}")

    # Study, practice, take notes...
    # (work for session['duration_min'] minutes)

    end_work_session(what_i_learned=session['learnings'])
    capture_win(f"Completed: {session['topic']}")

# Review learning progress
summary = how_was_my_day()
print(f"📚 Learnings captured: {summary['stats']['learnings_captured']}")
print(f"🎓 Topics covered: {summary['stats']['tasks_worked_on']}")
```

---

### Recipe 4: Bug Fixing Template

```python
def fix_bug(bug_title, learnings, challenges, notes):
    """Template for systematic bug fixing."""

    # Start tracking
    start_working_on(f"Debug: {bug_title}")

    # ... investigate and fix ...

    # Document
    end_work_session(
        what_i_learned=learnings,
        challenges_faced=challenges,
        quick_note=notes
    )

    # Celebrate
    capture_win(f"Fixed: {bug_title}")

# Example usage
fix_bug(
    bug_title="Memory leak in session handler",
    learnings=["Always clean up event listeners", "WeakMap prevents leaks"],
    challenges=["Leak only visible after hours of runtime"],
    notes="Added cleanup in componentWillUnmount"
)

fix_bug(
    bug_title="Race condition in payment processing",
    learnings=["Use pessimistic locking for critical sections"],
    challenges=["Only happened under high concurrent load"],
    notes="Implemented row-level locking"
)

# Review bug-fixing session
summary = how_was_my_day()
print(f"🐛 Bugs fixed: {summary['stats']['sessions']}")
print(f"💡 Lessons learned: {summary['stats']['learnings_captured']}")
```

---

### Recipe 5: Pomodoro-Style Sessions

```python
import asyncio

async def pomodoro_session(task, duration_minutes=25):
    """Run a Pomodoro-style focused session."""

    # Start
    start_working_on(task)
    print(f"🍅 Pomodoro: {task}")
    print(f"⏰ Focus for {duration_minutes} minutes")

    # Work
    await asyncio.sleep(duration_minutes * 60)

    # End
    print("⏰ Time's up! Quick break...")
    result = end_work_session(quick_note=f"Pomodoro ({duration_minutes}min)")

    return result

# Run Pomodoro workday
async def pomodoro_workday():
    # Morning pomodoros
    await pomodoro_session("Design database schema", 25)
    await asyncio.sleep(5 * 60)  # 5-min break

    await pomodoro_session("Implement user model", 25)
    await asyncio.sleep(5 * 60)

    await pomodoro_session("Write model tests", 25)
    await asyncio.sleep(15 * 60)  # Longer break

    # Afternoon pomodoros
    await pomodoro_session("API endpoint implementation", 25)
    await asyncio.sleep(5 * 60)

    await pomodoro_session("Integration testing", 25)

    # Review
    summary = how_was_my_day()
    print(f"🍅 Pomodoros completed: {summary['stats']['sessions']}")

# Run it
asyncio.run(pomodoro_workday())
```

---

### Recipe 6: Context Switching Recovery

```python
# When interrupted mid-work

# End current work with detailed notes
end_work_session(
    quick_note="""
    Current progress:
    - Completed steps 1-3 of algorithm
    - Working on step 4: optimize inner loop
    - Next: Test with large dataset
    - File: algorithms/optimizer.py, line 247
    - Docs: docs/optimization-guide.md
    """
)

# Handle interruption
start_working_on("Urgent: Production issue")
# ... handle issue ...
end_work_session(
    what_i_learned=["Root cause was config mismatch"],
    quick_note="Issue resolved, config updated"
)

# Resume original work using notes
progress = how_was_my_day()
# Look at notes from previous session
previous_note = progress['sessions'][0]['notes']
print(f"Resuming: {previous_note}")

start_working_on("Continue: Algorithm optimization")
# You know exactly where you left off!
```

---

### Recipe 7: Weekly Review

```python
from datetime import date, timedelta

async def weekly_review():
    """Generate comprehensive weekly review."""

    print("📊 Weekly Review")
    print("=" * 50)

    # Get each day's data
    today = date.today()
    weekly_data = []

    for i in range(7):
        day = today - timedelta(days=i)
        summary = await how_was_my_day(day.isoformat())

        if summary['success']:
            weekly_data.append({
                'date': day,
                'stats': summary['stats'],
                'summary': summary['summary']
            })

    # Calculate totals
    total_hours = sum(d['stats']['total_hours'] for d in weekly_data)
    total_sessions = sum(d['stats']['sessions'] for d in weekly_data)
    total_learnings = sum(d['stats']['learnings_captured'] for d in weekly_data)
    days_worked = len([d for d in weekly_data if d['stats']['sessions'] > 0])

    print(f"\n📈 Weekly Stats:")
    print(f"  Total work: {total_hours:.1f} hours")
    print(f"  Days worked: {days_worked}/7")
    print(f"  Sessions: {total_sessions}")
    print(f"  Learnings: {total_learnings}")
    print(f"  Avg hours/day: {total_hours/days_worked:.1f}")

    # Show daily breakdown
    print(f"\n📅 Daily Breakdown:")
    for d in reversed(weekly_data):
        print(f"\n{d['date'].strftime('%A, %b %d')}")
        stats = d['stats']
        print(f"  ⏱️  {stats['total_hours']}h | 📝 {stats['sessions']} sessions")
        if stats['sessions'] > 0:
            print(f"  {d['summary'][:100]}...")

# Run weekly review
await weekly_review()
```

---

### Recipe 8: Export to Markdown

```python
async def export_journal_to_markdown(output_file="journal_export.md"):
    """Export journal to markdown file."""

    journals = await get_resource("memory://journal/recent")

    with open(output_file, 'w') as f:
        f.write("# Work Journal Export\n\n")

        for journal in reversed(journals):
            date = journal['date']
            f.write(f"## {date}\n\n")

            if journal.get('morning_intention'):
                f.write(f"**Intention:** {journal['morning_intention']}\n\n")

            # Sessions
            f.write(f"### Sessions ({len(journal['work_sessions'])})\n\n")
            for session in journal['work_sessions']:
                f.write(f"#### {session['task']} ({session['duration_minutes']}min)\n\n")

                if session.get('learnings'):
                    f.write("**Learnings:**\n")
                    for learning in session['learnings']:
                        f.write(f"- {learning}\n")
                    f.write("\n")

                if session.get('notes'):
                    f.write(f"**Notes:** {session['notes']}\n\n")

            # Wins
            if journal.get('wins'):
                f.write("### Wins 🎉\n\n")
                for win in journal['wins']:
                    f.write(f"- {win}\n")
                f.write("\n")

            # Summary
            if journal.get('end_of_day_reflection'):
                f.write("### Summary\n\n")
                f.write(f"{journal['end_of_day_reflection']}\n\n")

            f.write("---\n\n")

    print(f"✅ Exported to {output_file}")

await export_journal_to_markdown("my_journal.md")
```
