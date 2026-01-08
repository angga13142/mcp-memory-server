# Daily Journal - Troubleshooting Guide

## Common Issues & Solutions

### Issue 1: "No active work session found"

**Problem:** Trying to end a session when none is active.

**Solution:**

```python
# Check status first
@mcp active_session_prompt

# If no session, start one
start_working_on("Your task")
```

---

### Issue 2: "Session already active"

**Problem:** Trying to start when one is already running.

**Solution:**

```python
# Option A: End current session first
end_work_session()
start_working_on("New task")

# Option B: Check what's running
@mcp active_session_prompt
```

---

### Issue 3: Session duration is 0 minutes

**Cause:** Ended immediately after starting.

**Solution:** This is expected! Duration is calculated from start to end time.

```python
start_working_on("Task")
# Actually work for some time
await asyncio.sleep(1800)  # 30 minutes
end_work_session()  # Now duration ≈ 30
```

---

### Issue 4: No reflection generated

**Cause:** Session was shorter than 30 minutes (default threshold).

**Solutions:**

**A. Work longer sessions:**

```python
# Aim for 30+ minute focused blocks
```

**B. Adjust threshold:**

```yaml
# config.yaml
personal:
  journal:
    min_session_minutes: 15 # Lower threshold
```

---

### Issue 5: Search not finding memories

**Causes & Solutions:**

**A. Query too specific:**

```python
# Too specific
search_memory("OAuth2 RFC 6749 section 4.1.2")

# Better
search_memory("OAuth2 authentication")
```

**B. Semantic mismatch:**

```python
# Stored as
end_work_session(what_i_learned=["Implemented login flow"])

# Search won't match well
search_memory("authentication")

# Better search
search_memory("login flow")
search_memory("user authentication login")
```

**C. Wait for indexing:**

```python
# After ending session, wait briefly
await asyncio.sleep(2)
results = search_memory("your query")
```

---

### Issue 6: Configuration not loading

**Solutions:**

**A. Restart server:**

```bash
# Config loads at startup
# Stop and restart server
```

**B. Check environment override:**

```bash
# Override via environment
export MEMORY_SERVER__PERSONAL__JOURNAL__MIN_SESSION_MINUTES=45
```

**C. Validate YAML:**

```bash
python -c "import yaml; yaml.safe_load(open('config.yaml'))"
```

---

### Issue 7: Database locked error

**Cause:** SQLite lock from concurrent access.

**Solutions:**

**A. Wait and retry:**

```python
# Automatically retried by repository layer
```

**B. Check for stuck processes:**

```bash
# Check running processes
ps aux | grep memory-server

# Kill if needed
kill <pid>
```

**C. Clean database:**

```bash
# Last resort - backup first
cp data/memory.db data/memory.db.backup
rm data/memory.db
# Server will create new on restart
```

---

### Issue 8: Missing or incomplete summaries

**Cause:** No sessions recorded for the day.

**Solution:**

```python
# Check sessions first
@mcp daily_progress_prompt

# If no sessions, verify you're using start_working_on
start_working_on("Your task")
# ... work ...
end_work_session()

# Now summary will work
how_was_my_day()
```

---

### Issue 9: Timestamps showing wrong timezone

**Cause:** Timestamps stored in UTC, displayed in local time.

**Solution:** This is by design for consistency.

```python
# All timestamps are UTC internally
# Convert for display if needed
from datetime import datetime, timezone

utc_time = datetime.fromisoformat(timestamp)
local_time = utc_time.astimezone()
print(local_time.strftime("%I:%M %p"))
```

---

### Issue 10: Vector store not initializing

**Cause:** ChromaDB directory permissions or corruption.

**Solutions:**

**A. Check permissions:**

```bash
ls -la data/chroma_db
chmod -R 755 data/chroma_db
```

**B. Recreate vector store:**

```bash
# Backup first
mv data/chroma_db data/chroma_db.backup

# Server will recreate on startup
```

**C. Check disk space:**

```bash
df -h
```

---

## Debugging Tips

### Enable Debug Logging

```yaml
# config.yaml
server:
  log_level: "DEBUG"
```

**View logs:**

```bash
# If using systemd
journalctl -u memory-server -f

# If using Docker
docker logs -f memory-server

# If running directly
# Logs will appear in terminal
```

---

### Check Database

```bash
sqlite3 data/memory.db

# Check journal count
SELECT COUNT(*) FROM daily_journals;

# Check recent sessions
SELECT task, start_time, end_time
FROM work_sessions
ORDER BY start_time DESC
LIMIT 5;

# Check today's journal
SELECT * FROM daily_journals
WHERE date = date('now');

# Exit
.exit
```

---

### Verify Vector Store

```python
# Check ChromaDB collection
from src.storage.vector_store import VectorMemoryStore
from src.utils.config import get_settings

settings = get_settings()
vector_store = VectorMemoryStore(settings)
await vector_store.init()

# Count memories
count = await vector_store.count()
print(f"Total memories: {count}")

# Test search
results = await vector_store.search("test")
print(f"Search results: {len(results)}")
```

---

### Health Check

```python
# Run health check
from src.health_check import check_health

health = await check_health()
print(health)
```

Expected output:

```json
{
  "status": "healthy",
  "database": "connected",
  "vector_store": "initialized",
  "journal_service": "ready"
}
```

---

### Test MCP Tools

```python
# Test each tool manually
result = await start_working_on("Test session")
print(f"Start: {result}")

result = await end_work_session()
print(f"End: {result}")

result = await how_was_my_day()
print(f"Summary: {result}")
```

---

## Performance Issues

### Slow reflection generation

**Cause:** LLM API slow or rate-limited.

**Solutions:**

**A. Check LLM API status:**

```bash
# Test API endpoint
curl https://api.openai.com/v1/models
```

**B. Reduce reflection length:**

```yaml
# config.yaml
personal:
  journal:
    reflection_length: 100 # Shorter = faster
```

**C. Disable temporarily:**

```yaml
personal:
  journal:
    auto_reflection: false
```

---

### Slow searches

**Cause:** Large vector store or inefficient queries.

**Solutions:**

**A. Limit results:**

```python
search_memory("query", limit=5)  # Instead of default 10
```

**B. Be more specific:**

```python
# More specific = fewer results to rank
search_memory("OAuth2 implementation Python")
```

**C. Check vector store size:**

```python
count = await vector_store.count()
# If > 10,000, consider archiving old memories
```

---

## Error Messages Reference

| Error                                | Cause                      | Solution                    |
| ------------------------------------ | -------------------------- | --------------------------- |
| `Task description is required`       | Empty task string          | Provide non-empty task      |
| `Session already active`             | Previous session not ended | End current session first   |
| `No active work session found`       | No session started         | Start a session             |
| `Invalid date format`                | Wrong date string          | Use YYYY-MM-DD format       |
| `Database connection failed`         | DB file locked/missing     | Check file permissions      |
| `Vector store initialization failed` | ChromaDB error             | Check directory permissions |
| `Reflection generation failed`       | LLM API error              | Check API key/connectivity  |

---

## Getting Help

### Check Logs

```bash
# View recent errors
tail -100 logs/memory-server.log | grep ERROR

# Watch logs live
tail -f logs/memory-server.log
```

### Run Diagnostics

```bash
# Run full diagnostic
python scripts/diagnose.py
```

### Report Issue

When reporting issues, include:

1. Error message (full text)
2. Steps to reproduce
3. Relevant config settings
4. Log excerpts
5. System info (OS, Python version)

```bash
# Gather system info
python --version
uname -a
df -h
```
