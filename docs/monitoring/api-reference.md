# API Reference - Monitoring & Observability

## 🎯 Purpose

Complete reference for all metrics, endpoints, alert rules, and configuration options.

---

## 📊 METRICS REFERENCE

### Journal Metrics

#### `mcp_journal_sessions_total`
- Type: Counter
- Description: Total number of work sessions started
- Labels: `status` (success, failed)

Examples:
```promql
mcp_journal_sessions_total{status="success"}
rate(mcp_journal_sessions_total[5m])
(rate(mcp_journal_sessions_total{status="success"}[5m]) / rate(mcp_journal_sessions_total[5m])) * 100
```

#### `mcp_journal_sessions_active`
- Type: Gauge
- Description: Number of currently active work sessions
- Labels: none

Examples:
```promql
mcp_journal_sessions_active
mcp_journal_sessions_active > 10
```

#### `mcp_journal_session_duration_minutes`
- Type: Histogram
- Description: Distribution of work session durations (minutes)
- Labels: none
- Buckets: [5, 15, 30, 60, 120, 240, 480]

Examples:
```promql
histogram_quantile(0.5, rate(mcp_journal_session_duration_minutes_bucket[5m]))
histogram_quantile(0.95, rate(mcp_journal_session_duration_minutes_bucket[5m]))
rate(mcp_journal_session_duration_minutes_sum[5m]) / rate(mcp_journal_session_duration_minutes_count[5m])
```

#### `mcp_journal_reflections_generated_total`
- Type: Counter
- Description: Total AI reflections generated
- Labels: `status` (success, failed, skipped)

Examples:
```promql
mcp_journal_reflections_generated_total{status="success"}
rate(mcp_journal_reflections_generated_total[5m])
rate(mcp_journal_reflections_generated_total{status="failed"}[5m])
```

#### `mcp_journal_reflection_generation_seconds`
- Type: Histogram
- Description: Time to generate AI reflections (seconds)
- Labels: none
- Buckets: [0.5, 1, 2, 5, 10, 30]

Examples:
```promql
histogram_quantile(0.95, rate(mcp_journal_reflection_generation_seconds_bucket[5m]))
rate(mcp_journal_reflection_generation_seconds_sum[5m]) / rate(mcp_journal_reflection_generation_seconds_count[5m])
```

#### `mcp_journal_learnings_captured_total`
- Type: Counter
- Description: Total learnings captured

Examples:
```promql
mcp_journal_learnings_captured_total
increase(mcp_journal_learnings_captured_total[1d])
```

#### `mcp_journal_challenges_noted_total`
- Type: Counter
- Description: Total challenges noted

Examples:
```promql
mcp_journal_challenges_noted_total
rate(mcp_journal_challenges_noted_total[5m])
```

#### `mcp_journal_wins_captured_total`
- Type: Counter
- Description: Total wins captured

Examples:
```promql
mcp_journal_wins_captured_total
rate(mcp_journal_wins_captured_total[1h]) * 3600
```

---

### Database Metrics

#### `mcp_db_connections_active`
- Type: Gauge
- Description: Active database connections

Examples:
```promql
mcp_db_connections_active
mcp_db_connections_active > 50
```

#### `mcp_db_query_duration_seconds`
- Type: Histogram
- Description: Query execution time (seconds)
- Labels: `operation` (select, insert, update, delete)
- Buckets: [0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0]

Examples:
```promql
histogram_quantile(0.95, rate(mcp_db_query_duration_seconds_bucket[5m])) by (operation)
histogram_quantile(0.95, rate(mcp_db_query_duration_seconds_bucket[5m])) > 1
```

#### `mcp_db_queries_total`
- Type: Counter
- Description: Total queries executed
- Labels: `operation` (select, insert, update, delete), `status` (success, failed)

Examples:
```promql
rate(mcp_db_queries_total[5m]) by (operation)
rate(mcp_db_queries_total{status="failed"}[5m])
```

---

### Vector Store Metrics

#### `mcp_vector_embeddings_generated_total`
- Type: Counter
- Description: Total embeddings generated
- Labels: `status` (success, failed)

Examples:
```promql
rate(mcp_vector_embeddings_generated_total[5m])
rate(mcp_vector_embeddings_generated_total{status="failed"}[5m])
```

#### `mcp_vector_embedding_seconds`
- Type: Histogram
- Description: Embedding generation time (seconds)
- Labels: none
- Buckets: [0.1, 0.5, 1, 2, 5, 10]

Examples:
```promql
histogram_quantile(0.95, rate(mcp_vector_embedding_seconds_bucket[5m]))
```

#### `mcp_vector_searches_total`
- Type: Counter
- Description: Total vector searches
- Labels: `status` (success, failed)

Examples:
```promql
rate(mcp_vector_searches_total[5m])
```

#### `mcp_vector_memory_count`
- Type: Gauge
- Description: Total memories in vector store

Examples:
```promql
mcp_vector_memory_count
deriv(mcp_vector_memory_count[1h])
```

---

### System Metrics

#### `mcp_system_memory_usage_bytes`
- Type: Gauge
- Description: Memory usage (bytes)

Examples:
```promql
mcp_system_memory_usage_bytes / 1024 / 1024
(mcp_system_memory_usage_bytes / mcp_system_memory_total_bytes) * 100
```

#### `mcp_system_cpu_usage_percent`
- Type: Gauge
- Description: CPU usage percent (0-100)

Examples:
```promql
mcp_system_cpu_usage_percent
avg_over_time(mcp_system_cpu_usage_percent[5m])
```

---

## 🌐 HTTP ENDPOINTS

### GET `/metrics`
- Description: Prometheus metrics endpoint
- Response: Prometheus text format

Example:
```bash
curl http://localhost:8080/metrics
```

### GET `/health`
- Description: Health check endpoint
- Response: JSON

Example:
```bash
curl http://localhost:8080/health
```

Sample response:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-08T10:30:00Z",
  "checks": {
    "database": "ok",
    "vector_store": "ok",
    "embedding_model": "ok"
  }
}
```

---

## 🚨 ALERT RULES REFERENCE

### Critical Alerts

#### ServiceDown
```yaml
alert: ServiceDown
expr: up{job="mcp-memory-server"} == 0
for: 2m
labels:
  severity: critical
annotations:
  summary: "MCP Memory Server is down"
  description: "Service has been down for 2 minutes"
```
- Action: immediate investigation and restart

#### VectorStoreEmbeddingFailures
```yaml
alert: VectorStoreEmbeddingFailures
expr: rate(mcp_vector_embeddings_generated_total{status="failed"}[10m]) > 0.1
for: 5m
labels:
  severity: critical
annotations:
  summary: "Vector store embedding failures"
  description: "Embedding generation failing at {{ $value }}/s"
```
- Action: check vector store health, restart if needed

### Warning Alerts

#### HighSessionFailureRate
```yaml
alert: HighSessionFailureRate
expr: |
  (
    rate(mcp_journal_sessions_total{status="failed"}[5m])
    /
    rate(mcp_journal_sessions_total[5m])
  ) > 0.1
for: 5m
labels:
  severity: warning
annotations:
  summary: "High session failure rate"
  description: "More than 10% sessions failing (current: {{ $value | humanizePercentage }})"
```
- Action: investigate recent changes and logs

---

## 📝 CONFIGURATION REFERENCE

### Environment Variables

```bash
METRICS_ENABLED=true
METRICS_PORT=8080
METRICS_CACHE_TTL=30
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=/app/logs/server.log
PROMETHEUS_URL=http://prometheus:9090
ALERTMANAGER_URL=http://alertmanager:9093
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK
```

### Configuration File (config.yaml)

```yaml
monitoring:
  metrics:
    enabled: true
    port: 8080
    path: "/metrics"
    cache_ttl: 30
  logging:
    level: "INFO"
    format: "json"
    file: "/app/logs/server.log"
    structured: true
    sanitize: true
  alerts:
    enabled: true
    prometheus_url: "http://prometheus:9090"
    alertmanager_url: "http://alertmanager:9093"
```

---

**Last Updated:** 2025-01-08  
**Version:** 1.0
