# Monitoring & Observability

Comprehensive monitoring and observability stack for MCP Memory Server with focus on the daily journal flow.

## Overview

- Metrics collection with Prometheus for journal, database, vector store, system resources
- Structured JSON logging with correlation/user/request context
- Dashboards for Grafana
- Alerting via Prometheus/Alertmanager
- Health checks for liveness/readiness

## Quick Start

1. Start application and monitoring stack:

```bash
docker-compose up -d
docker-compose -f docker-compose.monitoring.yml up -d
docker-compose ps
```

2. Access UIs:

- Grafana: http://localhost:3000 (admin / admin)
- Prometheus: http://localhost:9090
- Alertmanager: http://localhost:9093
- Metrics endpoint: http://localhost:8080/metrics

3. View structured logs:

```bash
docker-compose logs -f mcp-memory-server | jq .
```

Filter examples:

```bash
docker-compose logs mcp-memory-server | jq 'select(.level=="ERROR")'
docker-compose logs mcp-memory-server | jq 'select(.correlation_id=="abc-123")'
```

## Key Metrics

### Journal

- mcp_journal_sessions_total (counter)
- mcp_journal_sessions_active (gauge)
- mcp_journal_session_duration_minutes (histogram)
- mcp_journal_reflections_generated_total (counter)
- mcp_journal_reflection_generation_seconds (histogram)
- mcp_journal_daily_summaries_total (counter)
- mcp_journal_daily_summary_seconds (histogram)
- mcp_journal_learnings_captured_total (counter)
- mcp_journal_challenges_noted_total (counter)
- mcp_journal_wins_captured_total (counter)

### Database

- mcp_db_connections_active (gauge)
- mcp_db_query_duration_seconds (histogram)
- mcp_db_queries_total (counter)

### Vector Store

- mcp_vector_embeddings_generated_total (counter)
- mcp_vector_embedding_seconds (histogram)
- mcp_vector_searches_total (counter)
- mcp_vector_search_seconds (histogram)
- mcp_vector_store_size_bytes (gauge)
- mcp_vector_memory_count (gauge)

### System

- mcp_system_memory_usage_bytes (gauge)
- mcp_system_cpu_usage_percent (gauge)

## Active Alerts (examples)

- ServiceDown (critical)
- VectorStoreEmbeddingFailures (critical)
- HighSessionFailureRate (warning)
- SlowReflectionGeneration (warning)
- TooManyActiveSessions (warning)
- SlowDatabaseQueries (warning)
- HighMemoryUsage (warning)

## Dashboards

- Journal overview: active sessions, rates, duration distribution, learnings/wins
- Performance: API latency (p50/p95/p99), DB queries, vector store times, system usage
- Error tracking: error rate, breakdown by type, failed operations, alert status

## Configuration

Environment examples:

```bash
METRICS_ENABLED=true
METRICS_PORT=8080
METRICS_CACHE_TTL=30
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=/app/logs/server.log
ALERTMANAGER_URL=http://alertmanager:9093
```

YAML snippet (config.yaml):

```yaml
monitoring:
  metrics:
    enabled: true
    port: 8080
    cache_ttl: 30
  logging:
    level: INFO
    format: json
    sanitize: true
  alerts:
    enabled: true
    prometheus_url: http://prometheus:9090
```

## Health Checks

- Liveness: `curl http://localhost:8080/health`
- Readiness: `python scripts/health_check.py`
  Checks include DB, vector store, embeddings, filesystem.

## Links

- Operator Guide: operator-guide.md
- Developer Guide: developer-guide.md
- Runbook: runbook.md
- Troubleshooting: troubleshooting.md
- API Reference: api-reference.md
- Architecture: architecture.md
