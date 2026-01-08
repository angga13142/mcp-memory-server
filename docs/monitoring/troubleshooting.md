# Troubleshooting Guide - Monitoring & Observability

## 🎯 Purpose

Common issues, their symptoms, causes, and solutions for the monitoring infrastructure.

---

## 📋 QUICK DIAGNOSTICS

### Run Quick Health Check

```bash
curl -s http://localhost:8080/health && \
curl -s http://localhost:9090/-/healthy && \
curl -s http://localhost:3000/api/health && \
echo "✅ All services healthy"
```

### Check All Services Status

```bash
docker-compose ps
```

### View Recent Errors

```bash
docker-compose logs --tail=50 mcp-memory-server | jq 'select(.level=="ERROR")'
```

---

## 🔴 CRITICAL ISSUES

### Issue: Metrics Endpoint Returns 404

**Symptoms:**
```bash
$ curl http://localhost:8080/metrics
404 Not Found
```

**Possible Causes:**
1) Metrics endpoint not configured
2) Wrong port
3) Service not started

**Solutions:**

- Verify service is running
```bash
docker-compose ps mcp-memory-server
docker-compose port mcp-memory-server 8080
docker-compose up -d mcp-memory-server
```

- Verify configuration
```bash
docker-compose exec mcp-memory-server python -c "
from src.utils.config import get_settings
s = get_settings()
print(f'Metrics enabled: {s.monitoring.metrics.enabled}')
print(f'Metrics port: {s.monitoring.metrics.port}')
"
```

- Check route registration (FastAPI example)
```bash
docker-compose exec mcp-memory-server python -c "
from src.server import app
for route in app.routes:
    print(f'{route.methods} {route.path}')
" | grep metrics
```

### Issue: Prometheus Not Scraping Targets

**Symptoms:**
- Prometheus UI shows targets as DOWN
- No metrics appearing

**Diagnosis:**
```bash
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health, error: .lastError}'
```

**Solutions:**

- Network connectivity
```bash
docker-compose exec prometheus wget -O- http://mcp-memory-server:8080/metrics
```

- Validate configuration
```bash
docker-compose exec prometheus promtool check config /etc/prometheus/prometheus.yml
docker-compose exec prometheus cat /etc/prometheus/prometheus.yml
```

- Reload Prometheus
```bash
curl -X POST http://localhost:9090/-/reload
# or restart
 docker-compose restart prometheus
```

### Issue: Grafana Dashboards Show "No Data"

**Symptoms:** panels empty

**Diagnosis:**
```bash
curl -s http://admin:admin@localhost:3000/api/datasources | jq '.[ ] | {name: .name, type: .type, url: .url}'
DATASOURCE_ID=$(curl -s http://admin:admin@localhost:3000/api/datasources | jq '.[0].id')
curl -s http://admin:admin@localhost:3000/api/datasources/$DATASOURCE_ID/health | jq .
```

**Solutions:**

- Fix datasource configuration
```bash
curl -X PUT http://admin:admin@localhost:3000/api/datasources/1 \
  -H "Content-Type: application/json" \
  -d '{"name":"Prometheus","type":"prometheus","url":"http://prometheus:9090","access":"proxy","isDefault":true}'
```

- Check time range / data availability
```bash
curl -s 'http://localhost:9090/api/v1/query?query=mcp_journal_sessions_total'
```

- Verify queries
```bash
curl -s 'http://localhost:9090/api/v1/query?query=mcp_journal_sessions_active' | jq .
curl http://localhost:8080/metrics | grep mcp_journal
```

---

## ⚠️ WARNING ISSUES

### Issue: High Memory Usage Alert Firing

**Diagnosis:**
```bash
docker stats mcp-memory-server --no-stream
docker-compose exec mcp-memory-server python -c "import psutil, os; p=psutil.Process(os.getpid()); mem=p.memory_info(); print(f'RSS: {mem.rss/1024/1024:.2f} MB'); print(f'VMS: {mem.vms/1024/1024:.2f} MB'); print(f'Percent: {p.memory_percent():.2f}%')"
```

**Solutions:**
- Restart quickly: `docker-compose restart mcp-memory-server`
- Reduce caches in config and restart
- Increase container memory limit if needed

### Issue: Slow Metric Collection

**Diagnosis:**
```bash
time curl http://localhost:8080/metrics > /dev/null
curl -s http://localhost:8080/metrics | grep "^mcp_" | wc -l
```

**Solutions:**
- Reduce label cardinality (avoid user/session ids)
- Use OptimizedMetricCollector with caching TTL
- Disable unused collectors

### Issue: Alerts Not Firing

**Diagnosis:**
```bash
curl -s http://localhost:9090/api/v1/rules | jq '.data.groups[].name'
docker-compose exec prometheus promtool check rules /etc/prometheus/alerts/*.yml
curl -s 'http://localhost:9090/api/v1/query?query=mcp_journal_sessions_active' | jq '.data.result[0].value[1]'
```

**Solutions:**
- Fix rule syntax and reload Prometheus
- Adjust thresholds/for clauses for testing
- Confirm Alertmanager is receiving alerts: `curl -s http://localhost:9093/api/v1/alerts`

---

## 🔵 INFO ISSUES

### Issue: Logs Not Showing Up

**Diagnosis:**
```bash
docker-compose ps mcp-memory-server
docker inspect mcp-memory-server | jq '.[0].HostConfig.LogConfig'
docker-compose exec mcp-memory-server ls -lh /app/logs/
```

**Solutions:**
- Verify logging config via get_settings()
- Fix permissions: `docker-compose exec mcp-memory-server chown -R appuser:appuser /app/logs/`
- Temporarily set LOG_LEVEL=DEBUG and restart

### Issue: Dashboard Not Loading

**Solutions:**
- Validate JSON: `jq . monitoring/grafana/dashboards/journal_dashboard.json`
- Reimport dashboard via Grafana API (delete existing then POST dashboard JSON)

---

## 🛠️ DEBUGGING TOOLS

### Enable Debug Logging

```bash
export LOG_LEVEL=DEBUG
export MEMORY_SERVER__SERVER__LOG_LEVEL=DEBUG
docker-compose restart mcp-memory-server
docker-compose logs -f mcp-memory-server
```

### Inspect Metric Values

```bash
docker-compose exec mcp-memory-server python -c "
from src.monitoring.metrics import journal_metrics
print(journal_metrics.sessions_active._value.get())
print(journal_metrics.sessions_total.labels(status='success')._value.get())
"
```

### Query Prometheus Directly

```bash
docker-compose exec prometheus /bin/promtool query instant http://localhost:9090 'mcp_journal_sessions_active'
docker-compose exec prometheus /bin/promtool query range --start=-1h --end=now 'rate(mcp_journal_sessions_total[5m])'
```

---

## 📚 COMMON ERROR MESSAGES

- "context deadline exceeded": increase timeout, check network, optimize slow ops.
- "connection refused": ensure service is running, ports mapped, network healthy.
- "out of memory": increase limits, reduce caches, check for leaks.
- "no such metric": verify name and export, reload Prometheus config.

---

## 🆘 GETTING FURTHER HELP

### Collect Diagnostic Information

```bash
#!/bin/bash
# collect_diagnostics.sh

DIAG_DIR="diagnostics_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$DIAG_DIR"

echo "🔍 Collecting diagnostic information..."

docker-compose ps > "$DIAG_DIR/service_status.txt"

docker-compose logs --tail=500 mcp-memory-server > "$DIAG_DIR/app_logs.txt"
docker-compose logs --tail=500 prometheus > "$DIAG_DIR/prometheus_logs.txt"
docker-compose logs --tail=500 grafana > "$DIAG_DIR/grafana_logs.txt"

cp config.yaml "$DIAG_DIR/" || true
cp monitoring/prometheus.yml "$DIAG_DIR/" || true
cp docker-compose.yml "$DIAG_DIR/" || true

curl -s http://localhost:8080/metrics > "$DIAG_DIR/metrics_snapshot.txt"
curl -s http://localhost:9090/api/v1/targets > "$DIAG_DIR/prometheus_targets.json"

docker stats --no-stream > "$DIAG_DIR/docker_stats.txt"
df -h > "$DIAG_DIR/disk_usage.txt"

tar -czf "$DIAG_DIR.tar.gz" "$DIAG_DIR"
rm -rf "$DIAG_DIR"

echo "✅ Diagnostics collected: $DIAG_DIR.tar.gz"
```

### Report Issue Template

```markdown
**Issue Description:**
[Brief description of the problem]

**Steps to Reproduce:**
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Expected Behavior:**
[What should happen]

**Actual Behavior:**
[What actually happens]

**Environment:**
- OS: [e.g., Ubuntu 22.04]
- Docker version: [e.g., 24.0.7]
- MCP Memory Server version: [e.g., 1.0.0]

**Logs:**
```
[Paste relevant log excerpts]
```

**Screenshots:**
[If applicable]

**Diagnostic Archive:**
[Attach diagnostics_*.tar.gz]
```

---

**Last Updated:** 2025-01-08  
**Version:** 1.0
