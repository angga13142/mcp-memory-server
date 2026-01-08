# Monitoring Validation Guide

## Overview

This guide provides step-by-step validation procedures for the monitoring and observability stack.

## Quick Start

```bash
# Ensure services are running
docker-compose up -d

# Run full validation suite
chmod +x scripts/validation/run_monitoring_validation.sh
./scripts/validation/run_monitoring_validation.sh
```

## Manual Validation Checklist

### 1. Metrics Endpoint

**Check metrics are exposed:**

```bash
curl http://localhost:8080/metrics
```

**Expected output:**

- Prometheus format text
- Multiple `mcp_*` metrics
- HTTP 200 status

**Verify key metrics present:**

```bash
curl -s http://localhost:8080/metrics | grep -E "mcp_journal_sessions|mcp_db_queries|mcp_vector"
```

### 2. Prometheus Scraping

**Access Prometheus UI:**

```bash
open http://localhost:9090
```

**Check targets (Status → Targets):**

- ✅ mcp-memory-server: UP
- ✅ redis: UP (if enabled)
- ✅ node-exporter: UP (if monitoring stack enabled)

**Run test queries:**

```promql
# Check active sessions
mcp_journal_sessions_active

# Check session rate
rate(mcp_journal_sessions_total[5m])

# Check p95 duration
histogram_quantile(0.95, rate(mcp_journal_session_duration_minutes_bucket[5m]))
```

### 3. Grafana Dashboards

**Access Grafana:**

```bash
open http://localhost:3000
# Login: admin / admin
```

**Verify dashboard:**

1. Navigate to Dashboards
2. Find "MCP Memory Server - Daily Journal"
3. Check all panels load
4. Verify data is displayed
5. Test auto-refresh (5s interval)

**Generate test data:**

```bash
python3 scripts/validation/generate_test_data.py
```

**Wait 30 seconds and verify:**

- Session counters updated
- Graphs show activity
- No "No Data" panels

### 4. Alert Rules

**Check alerts loaded (Prometheus → Alerts):**

- HighSessionFailureRate
- ReflectionGenerationFailing
- SlowReflectionGeneration
- TooManyActiveSessions
- SlowDatabaseQueries
- VectorStoreEmbeddingFailures
- HighMemoryUsage
- ServiceDown

**All should show:**

- State: Inactive (green)
- No syntax errors

**Test alert (optional):**

```python
# Start many sessions to trigger alert
for i in range(12):
    await start_working_on(f"Test {i}")
```

Wait 15 minutes and check if `TooManyActiveSessions` fires.

### 5. Structured Logging

**Check log format:**

```bash
docker-compose logs memory-server | tail -20
```

**Should see JSON logs with:**

- `@timestamp`
- `level`
- `logger`
- `message`
- `module`

**Validate JSON:**

```bash
docker-compose logs memory-server | grep -o '{.*}' | head -1 | jq .
```

Should parse without errors.

### 6. Alertmanager (Optional)

**Access UI:**

```bash
open http://localhost:9093
```

**Verify:**

- UI loads
- No errors
- Silence functionality works

**Test Slack integration:**

```bash
# Set webhook in .env
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# Restart alertmanager
docker-compose restart alertmanager

# Trigger test alert and verify Slack notification
```

## Automated Validation Scripts

### Session Metrics Test

```bash
python3 scripts/validation/validate_session_metrics.py
```

**Verifies:**

- Metrics endpoint accessible
- Session counters increment
- All session metrics present

### Generate Test Data

```bash
python3 scripts/validation/generate_test_data.py
```

**Creates:**

- 5 work sessions
- Learnings and challenges
- Wins
- Daily summary

### End-to-End Test

```bash
python3 scripts/validation/e2e_monitoring_test.py
```

**Tests:**

- Full workflow from session to metrics
- Prometheus data collection
- Metric propagation

## Performance Validation

### Metrics Overhead

**Measure impact:**

```bash
# Run with metrics
time python3 -c "
import asyncio
from scripts.validation.generate_test_data import generate_test_data
asyncio.run(generate_test_data())
"
```

**Expected:**

- Overhead < 10%
- Memory increase < 50MB
- No noticeable latency

### Cardinality Check

```bash
# Count unique metrics
curl -s http://localhost:9090/api/v1/label/__name__/values | jq '.data | length'
```

**Expected:**

- Total metrics < 1000
- No high-cardinality labels

## Troubleshooting

### Metrics Not Showing

**Debug steps:**

1. Check endpoint: `curl http://localhost:8080/metrics`
2. Check Prometheus logs: `docker-compose logs prometheus`
3. Verify network: `docker network inspect mcp-network`
4. Check targets: http://localhost:9090/targets

### Dashboard Empty

**Debug steps:**

1. Verify Prometheus has data:
   ```bash
   curl "http://localhost:9090/api/v1/query?query=up"
   ```
2. Check Grafana datasource connection
3. Adjust time range (Last 1 hour)
4. Generate test data

### Alerts Not Firing

**Debug steps:**

1. Check rule syntax:
   ```bash
   docker-compose exec prometheus promtool check rules /etc/prometheus/alerts/*.yml
   ```
2. Verify alert query returns data
3. Check Alertmanager logs:
   ```bash
   docker-compose logs alertmanager
   ```

### Logs Not JSON

**Debug steps:**

1. Check environment variable:
   ```bash
   docker-compose exec memory-server env | grep LOG_FORMAT
   ```
2. Should be: `MEMORY_SERVER__SERVER__LOG_FORMAT=json`
3. Restart container if needed

## Acceptance Criteria

✅ Monitoring validated when:

- [ ] Metrics endpoint returns 200 with valid data
- [ ] Prometheus scrapes all targets successfully
- [ ] All Grafana panels display data
- [ ] Alert rules load without errors
- [ ] Structured logging produces valid JSON
- [ ] Metrics overhead < 10%
- [ ] E2E test passes
- [ ] Validation report generated

## Report Generation

After validation, generate report:

```bash
./scripts/validation/run_monitoring_validation.sh
```

Report saved to: `monitoring_validation_report.md`

## Next Steps

After successful validation:

1. ✅ Review validation report
2. 📊 Customize Grafana dashboards
3. 🔔 Configure Slack/PagerDuty alerts
4. 📝 Document custom metrics
5. 🚀 Deploy to production
