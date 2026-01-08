# Runbook - Monitoring & Observability

## 🎯 Purpose

Step-by-step procedures for common operational tasks and incident response for the monitoring infrastructure.

---

## 📋 TABLE OF CONTENTS

1. Alert Response Procedures
2. Service Recovery
3. Performance Issues
4. Data Management
5. Configuration Changes
6. Verification Procedures
7. Escalation Procedures

---

## 🚨 ALERT RESPONSE PROCEDURES

### Alert: ServiceDown (🔴 CRITICAL)
MCP Memory Server is unreachable. Respond immediately.

1) Verify alert
```bash
docker-compose ps mcp-memory-server
curl http://localhost:8080/metrics
curl http://localhost:8080/health
```
2) Check logs
```bash
docker-compose logs --tail=100 mcp-memory-server
docker-compose logs mcp-memory-server | grep -i error
dmesg | grep -i "out of memory"
```
3) Attempt recovery
```bash
docker-compose restart mcp-memory-server
sleep 30
curl http://localhost:8080/health
```
4) If still down
```bash
docker stats mcp-memory-server
df -h
netstat -tulpn | grep 8080
```
Full restart (last resort):
```bash
docker-compose down
docker-compose up -d
docker-compose ps
```
5) Escalate if unresolved after 15 minutes.

### Alert: HighSessionFailureRate (⚠️ WARNING)
More than 10% of work sessions failing; respond within 30 minutes.

1) Identify failure pattern
```bash
curl -s 'http://localhost:9090/api/v1/query?query=rate(mcp_journal_sessions_total{status="failed"}[5m])' | jq .
docker-compose logs mcp-memory-server | jq 'select(.level=="ERROR" and .event=="session_end")'
```
2) Check common causes
```bash
docker-compose exec mcp-memory-server python -c "
from src.storage.database import Database
from src.utils.config import get_settings
import asyncio
async def test():
    db = Database(get_settings()); await db.init(); print('Database OK'); await db.close()
asyncio.run(test())
"

docker-compose exec mcp-memory-server python -c "
from src.storage.vector_store import VectorMemoryStore
from src.utils.config import get_settings
import asyncio
async def test():
    vs = VectorMemoryStore(get_settings()); await vs.init(); count = await vs.count(); print(f'Vector store OK: {count}')
asyncio.run(test())
"
```
3) Analyze error patterns
```bash
docker-compose logs mcp-memory-server | jq -r 'select(.level=="ERROR") | .error_type' | sort | uniq -c | sort -rn
docker-compose logs mcp-memory-server | jq -r 'select(.level=="ERROR") | .message' | sort | uniq -c | sort -rn | head -5
```
4) Apply fix per error type (validation, DB, vector store, timeouts).
5) Monitor recovery
```bash
watch -n 5 'curl -s "http://localhost:9090/api/v1/query?query=rate(mcp_journal_sessions_total{status=\"failed\"}[5m])" | jq ".data.result[0].value[1]"'
```

### Alert: TooManyActiveSessions (⚠️ WARNING)
More than 10 active sessions detected.

1) Verify active sessions
```bash
curl -s 'http://localhost:9090/api/v1/query?query=mcp_journal_sessions_active' | jq .
```
2) Identify stuck sessions
```bash
docker-compose exec mcp-memory-server sqlite3 /app/data/memory.db "
SELECT id, task, start_time,
       CAST((julianday('now') - julianday(start_time)) * 24 AS INTEGER) as hours
FROM work_sessions
WHERE end_time IS NULL
  AND CAST((julianday('now') - julianday(start_time)) * 24 AS INTEGER) > 8
ORDER BY start_time;
"
```
3) Clean up stuck sessions (backup first)
```bash
docker-compose exec mcp-memory-server sqlite3 /app/data/memory.db "
UPDATE work_sessions
SET end_time = datetime('now')
WHERE end_time IS NULL
  AND CAST((julianday('now') - julianday(start_time)) * 24 AS INTEGER) > 8;
"
```
4) Investigate root cause (missing end_work_session, errors) and add cleanup safeguards.

### Alert: SlowReflectionGeneration (⚠️ WARNING)
Reflection generation taking more than 30 seconds.

1) Measure current performance
```bash
curl -s 'http://localhost:9090/api/v1/query?query=histogram_quantile(0.95, rate(mcp_journal_reflection_generation_seconds_bucket[5m]))' | jq .
docker-compose logs mcp-memory-server | jq 'select(.event=="reflection_generated") | .generation_time_seconds' | tail -10
```
2) Check resources
```bash
docker stats mcp-memory-server --no-stream
docker-compose exec mcp-memory-server free -h
```
3) Check model load/inference time
```bash
docker-compose exec mcp-memory-server python -c "
import time
from sentence_transformers import SentenceTransformer
start = time.time(); model = SentenceTransformer('all-MiniLM-L6-v2'); load_time = time.time() - start
start = time.time(); _ = model.encode('test'); infer_time = time.time() - start
print(f'Load: {load_time:.2f}s, Inference: {infer_time:.2f}s')
"
```
4) Check vector store search
```bash
docker-compose exec mcp-memory-server python -c "
import time, asyncio
from src.storage.vector_store import VectorMemoryStore
from src.utils.config import get_settings
async def test():
    vs = VectorMemoryStore(get_settings()); await vs.init(); start = time.time(); _ = await vs.search('test query', limit=5); print(f'Search time: {time.time()-start:.2f}s')
asyncio.run(test())
"
```
5) Mitigations: restart to reload model, rebuild index after backup, adjust thresholds, consider faster model or caching.

---

## 🔄 SERVICE RECOVERY

### Complete Service Restart

```bash
#!/bin/bash
echo "🔄 Starting complete service restart..."
docker-compose exec mcp-memory-server cp /app/data/memory.db /app/data/memory.db.backup.$(date +%Y%m%d_%H%M%S)
docker-compose down
docker-compose up -d
sleep 30
docker-compose ps
curl http://localhost:8080/health
curl http://localhost:8080/metrics | head -20
curl -s http://localhost:9090/-/healthy
echo "✅ Restart complete!"
```

---

## 📊 PERFORMANCE ISSUES

### High CPU Usage
1) Diagnose
```bash
docker-compose exec mcp-memory-server top -bn1 | head -20
```
Optional profiling:
```bash
docker-compose exec mcp-memory-server python -m cProfile -o profile.stats -m src.server

docker-compose exec mcp-memory-server python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative').print_stats(20)"
```
2) Resolve: optimize hot paths, add caching, or scale horizontally.

### High Memory Usage
1) Diagnose
```bash
docker-compose exec mcp-memory-server python -c "import psutil, os; p = psutil.Process(os.getpid()); mem = p.memory_info(); print(f'RSS: {mem.rss/1024/1024:.2f} MB'); print(f'VMS: {mem.vms/1024/1024:.2f} MB')"
```
2) Resolve: restart service, investigate leaks, reduce caches, adjust container limits.

---

## 🗄️ DATA MANAGEMENT

### Backup Prometheus Data

```bash
#!/bin/bash
# backup_prometheus.sh

BACKUP_DIR="/var/backups/mcp-prometheus"
DATE=$(date +%Y%m%d_%H%M%S)

echo "📦 Creating Prometheus backup..."

mkdir -p "$BACKUP_DIR"

curl -X POST http://localhost:9090/api/v1/admin/tsdb/snapshot
SNAPSHOT=$(curl -s http://localhost:9090/api/v1/admin/tsdb/snapshot | jq -r '.data.name')

docker cp prometheus:/prometheus/snapshots/$SNAPSHOT "$BACKUP_DIR/snapshot_$DATE"

tar -czf "$BACKUP_DIR/snapshot_$DATE.tar.gz" -C "$BACKUP_DIR" "snapshot_$DATE"
rm -rf "$BACKUP_DIR/snapshot_$DATE"

ls -t "$BACKUP_DIR"/snapshot_*.tar.gz | tail -n +8 | xargs -r rm -f

echo "✅ Backup created: $BACKUP_DIR/snapshot_$DATE.tar.gz"
```

### Restore Prometheus Data

```bash
#!/bin/bash
# restore_prometheus.sh

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: ./restore_prometheus.sh <backup_file.tar.gz>"
    exit 1
fi

echo "🔄 Restoring Prometheus data from $BACKUP_FILE..."

docker-compose stop prometheus

TEMP_DIR=$(mktemp -d)
tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR"

docker exec prometheus mv /prometheus /prometheus.backup.$(date +%Y%m%d_%H%M%S)

docker cp "$TEMP_DIR"/snapshot_* prometheus:/prometheus

docker-compose start prometheus
sleep 10
curl -s http://localhost:9090/-/healthy

echo "✅ Restore complete!"
```

### Clean Up Old Metrics

```bash
#!/bin/bash
# cleanup_old_metrics.sh

echo "🧹 Cleaning up old Prometheus data..."

docker-compose exec prometheus promtool tsdb list /prometheus | \
  grep -E "^01" | \
  while read -r block; do
    timestamp=$(echo "$block" | cut -d' ' -f1)
    age_days=$(( ( $(date +%s) - $(date -d "@$((timestamp/1000))" +%s) ) / 86400 ))
    if [ "$age_days" -gt 30 ]; then
      echo "Deleting block $block (age: $age_days days)"
      docker-compose exec prometheus rm -rf /prometheus/$block
    fi
  done

echo "✅ Cleanup complete!"
```

### Backup Grafana Dashboards

```bash
#!/bin/bash
# backup_grafana.sh

BACKUP_DIR="/var/backups/mcp-grafana"
DATE=$(date +%Y%m%d_%H%M%S)

echo "📦 Backing up Grafana dashboards..."

mkdir -p "$BACKUP_DIR"

UIDS=$(curl -s http://admin:admin@localhost:3000/api/search?type=dash-db | jq -r '.[].uid')
for uid in $UIDS; do
  echo "Backing up dashboard: $uid"
  curl -s http://admin:admin@localhost:3000/api/dashboards/uid/$uid > "$BACKUP_DIR/dashboard_${uid}_${DATE}.json"
done

curl -s http://admin:admin@localhost:3000/api/datasources > "$BACKUP_DIR/datasources_${DATE}.json"

tar -czf "$BACKUP_DIR/grafana_backup_${DATE}.tar.gz" -C "$BACKUP_DIR" dashboard_*_${DATE}.json datasources_${DATE}.json
rm -f "$BACKUP_DIR"/dashboard_*_${DATE}.json "$BACKUP_DIR"/datasources_${DATE}.json

ls -t "$BACKUP_DIR"/grafana_backup_*.tar.gz | tail -n +8 | xargs -r rm -f

echo "✅ Backup created: $BACKUP_DIR/grafana_backup_${DATE}.tar.gz"
```

---

## ⚙️ CONFIGURATION CHANGES

### Update Prometheus Scrape Interval

```bash
#!/bin/bash
# update_scrape_interval.sh

NEW_INTERVAL=$1

if [ -z "$NEW_INTERVAL" ]; then
    echo "Usage: ./update_scrape_interval.sh <interval> (e.g., 15s, 30s)"
    exit 1
fi

echo "🔧 Updating Prometheus scrape interval to $NEW_INTERVAL..."

cp monitoring/prometheus.yml monitoring/prometheus.yml.backup

sed -i "s/scrape_interval: [0-9]*s/scrape_interval: $NEW_INTERVAL/" monitoring/prometheus.yml

if docker-compose exec prometheus promtool check config /etc/prometheus/prometheus.yml; then
    echo "✅ Configuration valid"
    curl -X POST http://localhost:9090/-/reload
    echo "✅ Prometheus reloaded with new configuration"
else
    echo "❌ Configuration invalid, restoring backup"
    mv monitoring/prometheus.yml.backup monitoring/prometheus.yml
    exit 1
fi
```

### Add New Alert Rule

```bash
#!/bin/bash
# add_alert_rule.sh

ALERT_NAME=$1
ALERT_FILE=$2

if [ -z "$ALERT_NAME" ] || [ -z "$ALERT_FILE" ]; then
    echo "Usage: ./add_alert_rule.sh <alert_name> <alert_file.yml>"
    exit 1
fi

echo "🚨 Adding new alert rule: $ALERT_NAME..."

cp "$ALERT_FILE" monitoring/alerts/

if docker-compose exec prometheus promtool check rules /etc/prometheus/alerts/*.yml; then
    echo "✅ Alert rules valid"
    curl -X POST http://localhost:9090/-/reload
    echo "✅ Alert rule added: $ALERT_NAME"
else
    echo "❌ Alert rules invalid"
    rm monitoring/alerts/$(basename "$ALERT_FILE")
    exit 1
fi
```

### Update Grafana Dashboard

```bash
#!/bin/bash
# update_dashboard.sh

DASHBOARD_FILE=$1

if [ -z "$DASHBOARD_FILE" ]; then
    echo "Usage: ./update_dashboard.sh <dashboard.json>"
    exit 1
fi

echo "📈 Updating Grafana dashboard..."

curl -X POST http://admin:admin@localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @"$DASHBOARD_FILE"

if [ $? -eq 0 ]; then
    echo "✅ Dashboard updated successfully"
else
    echo "❌ Failed to update dashboard"
    exit 1
fi
```

---

## 🔍 VERIFICATION PROCEDURES

### Post-Deployment Verification

```bash
#!/bin/bash
# verify_deployment.sh

echo "🔍 Running post-deployment verification..."

FAILED=0

echo "Test 1: Checking service health..."
if curl -f http://localhost:8080/health > /dev/null 2>&1; then
    echo "  ✅ Service is healthy"
else
    echo "  ❌ Service health check failed"
    FAILED=1
fi

echo "Test 2: Checking metrics endpoint..."
if curl -f http://localhost:8080/metrics | grep -q "mcp_journal_sessions_total"; then
    echo "  ✅ Metrics endpoint working"
else
    echo "  ❌ Metrics endpoint failed"
    FAILED=1
fi

echo "Test 3: Checking Prometheus targets..."
TARGETS_UP=$(curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets | map(select(.health=="up")) | length')
TARGETS_TOTAL=$(curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets | length')
if [ "$TARGETS_UP" -eq "$TARGETS_TOTAL" ]; then
    echo "  ✅ All Prometheus targets up ($TARGETS_UP/$TARGETS_TOTAL)"
else
    echo "  ⚠️  Some targets down ($TARGETS_UP/$TARGETS_TOTAL)"
    FAILED=1
fi

echo "Test 4: Checking Grafana..."
if curl -f http://localhost:3000/api/health > /dev/null 2>&1; then
    echo "  ✅ Grafana is healthy"
else
    echo "  ❌ Grafana health check failed"
    FAILED=1
fi

echo "Test 5: Checking Alertmanager..."
if curl -f http://localhost:9093/-/healthy > /dev/null 2>&1; then
    echo "  ✅ Alertmanager is healthy"
else
    echo "  ❌ Alertmanager health check failed"
    FAILED=1
fi

echo "Test 6: Checking alert rules..."
RULES_COUNT=$(curl -s http://localhost:9090/api/v1/rules | jq '.data.groups | map(.rules | length) | add')
if [ "$RULES_COUNT" -gt 0 ]; then
    echo "  ✅ Alert rules loaded ($RULES_COUNT rules)"
else
    echo "  ❌ No alert rules loaded"
    FAILED=1
fi

if [ $FAILED -eq 0 ]; then
    echo "✅ All verification tests passed!"
    exit 0
else
    echo "❌ Some verification tests failed"
    exit 1
fi
```

---

## 📞 ESCALATION PROCEDURES

### When to Escalate

| Situation | Time to Escalate | Contact |
|-----------|------------------|---------|
| Service down >15 minutes | Immediately | On-call Engineer |
| Critical alert firing >30 minutes | Immediately | Senior SRE |
| Data loss detected | Immediately | Senior SRE + Dev Lead |
| Security incident | Immediately | Security Team |
| Repeated alerts (>5 in 1 hour) | Within 1 hour | Development Team |
| Performance degradation >50% | Within 2 hours | DevOps Team |

### Escalation Template

```markdown
**ESCALATION ALERT**

**Severity:** [CRITICAL/HIGH/MEDIUM]

**Issue:** [Brief description]

**Time Started:** [YYYY-MM-DD HH:MM UTC]

**Duration:** [X hours/minutes]

**Impact:** [User-facing impact description]

**Actions Taken:**
1. [Action 1]
2. [Action 2]
3. [Action 3]

**Current Status:** [Status description]

**Need:** [What help is needed]

**Incident Commander:** [Your name]
```

---

## 🔗 RELATED PROCEDURES

- Deployment Runbook: ../deployment/runbook.md
- Security Incident Response: ../security/incident-response.md
- Database Operations: ../database/runbook.md

---

**Last Updated:** 2025-01-08  
**Version:** 1.0  
**Owner:** DevOps Team
