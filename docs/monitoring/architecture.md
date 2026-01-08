# Architecture Documentation - Monitoring & Observability

## 🎯 Purpose

This document describes the architecture, design decisions, and technical implementation of the monitoring and observability infrastructure for MCP Memory Server.

---

## 📐 HIGH-LEVEL ARCHITECTURE

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        External Users                           │
│                    (Developers, Operators)                      │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Visualization Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Grafana    │  │ Alertmanager │  │  Prometheus  │          │
│  │  Dashboards  │  │     UI       │  │      UI      │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼──────────────────┼──────────────────┼─────────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Aggregation Layer                            │
│  ┌──────────────────────────────────────────────────────┐       │
│  │               Prometheus TSDB                        │       │
│  │  - Scrapes metrics every 15s                         │       │
│  │  - Stores time series data                           │       │
│  │  - Evaluates alert rules                             │       │
│  │  - 30-day retention                                  │       │
│  └──────────────────────────────────────────────────────┘       │
│                            │                                     │
│  ┌──────────────────────────────────────────────────────┐       │
│  │            Alertmanager                               │       │
│  │  - Receives alerts from Prometheus                    │       │
│  │  - Groups and deduplicates alerts                     │       │
│  │  - Routes to notification channels                    │       │
│  └──────────────────────────────────────────────────────┘       │
└─────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Collection Layer                              │
│  ┌──────────────────────────────────────────────────────┐       │
│  │           MCP Memory Server                          │       │
│  │                                                      │       │
│  │  ┌──────────────────────────────────────────────┐    │       │
│  │  │    Metrics Instrumentation                    │    │       │
│  │  │  - Journal metrics                            │    │       │
│  │  │  - Database metrics                           │    │       │
│  │  │  - Vector store metrics                       │    │       │
│  │  │  - System metrics                             │    │       │
│  │  └──────────────────────────────────────────────┘    │       │
│  │                                                      │       │
│  │  ┌──────────────────────────────────────────────┐    │       │
│  │  │    Structured Logging                        │    │       │
│  │  │  - JSON format                               │    │       │
│  │  │  - Correlation IDs                           │    │       │
│  │  │  - Context propagation                       │    │       │
│  │  └──────────────────────────────────────────────┘    │       │
│  │                                                      │       │
│  │  ┌──────────────────────────────────────────────┐    │       │
│  │  │    /metrics Endpoint                         │    │       │
│  │  │  - Prometheus format                         │    │       │
│  │  │  - 30s cache TTL                             │    │       │
│  │  └──────────────────────────────────────────────┘    │       │
│  └──────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧩 COMPONENT ARCHITECTURE

### 1. Metrics Collection Layer

#### 1.1 Metric Types

```python
from prometheus_client import Counter, Gauge, Histogram

# Counter - Monotonically increasing
sessions_total = Counter(
    'mcp_journal_sessions_total',
    'Total work sessions',
    ['status']
)

# Gauge - Can go up or down
sessions_active = Gauge(
    'mcp_journal_sessions_active',
    'Active work sessions'
)

# Histogram - Distribution of values
session_duration = Histogram(
    'mcp_journal_session_duration_minutes',
    'Session duration',
    buckets=[5, 15, 30, 60, 120, 240, 480]
)
```

**Design Decision:** Use Prometheus client library directly for performance and simplicity.

**Trade-offs:**
- ✅ Pros: Low overhead, native Prometheus support, widely adopted
- ❌ Cons: Vendor lock-in to Prometheus format

---

#### 1.2 Metrics Organization

```
src/monitoring/metrics/
├── __init__.py
├── base.py                 # Base classes and registry
├── journal_metrics.py      # Journal-specific metrics
├── database_metrics.py     # Database metrics
├── vector_store_metrics.py # Vector store metrics
├── system_metrics.py       # System resource metrics
└── collectors.py           # Metric collection logic
```

**Design Pattern:** Modular metrics organized by domain

**Rationale:**
- Separation of Concerns: Each module handles one domain
- Testability: Easy to test metrics in isolation
- Extensibility: New metric modules can be added without touching existing code

---

#### 1.3 Metrics Registration

```python
from prometheus_client import REGISTRY

class MetricRegistry:
    def __init__(self):
        self._collectors = []
    
    def register_collector(self, collector):
        self._collectors.append(collector)
        collector.register()

metric_registry = MetricRegistry()

metric_registry.register_collector(journal_metrics)
metric_registry.register_collector(database_metrics)
```

**Design Decision:** Centralized registration with singleton registry

**Benefits:**
- Single source of truth for all metrics
- Easy to list all registered metrics
- Prevents duplicate registrations

---

### 2. Logging Architecture

#### 2.1 Structured Logging Flow

```
Application Code
     │
     ▼
┌─────────────────────┐
│  log_event()        │ ← Helper function
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  LogContext         │ ← Add correlation ID
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Python Logger       │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ StructuredFormatter │ ← Convert to JSON
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Log Handler         │ ← File/Console
└─────────────────────┘
```

**Design Decision:** Structured JSON logging with correlation tracking

**Implementation:**

```python
class StructuredFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            '@timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'correlation_id': get_correlation_id(),
        }
        return json.dumps(log_data)
```

**Rationale:**
- Queryability: JSON logs easy to parse and query
- Context: Correlation IDs enable request tracing
- Standardization: Consistent log format across services

---

#### 2.2 Context Propagation

```python
from contextvars import ContextVar

correlation_id_var: ContextVar[str] = ContextVar('correlation_id')

async def request_handler():
    with LogContext(correlation_id="abc-123"):
        logger.info("Processing request")
        await process_data()
        logger.info("Request complete")
```

**Design Decision:** Use contextvars for async-safe context

**Benefits:**
- Async-safe: Works with asyncio and threads
- Automatic: Context propagates through call stack
- Clean: No need to pass context explicitly

---

### 3. Prometheus Integration

#### 3.1 Scraping Architecture

```
Prometheus Server
     │
     │ HTTP GET /metrics (every 15s)
     │
     ▼
┌─────────────────────────────┐
│  MCP Memory Server          │
│                             │
│  GET /metrics               │
│       │                     │
│       ▼                     │
│  ┌─────────────────────┐   │
│  │ get_metrics()       │   │
│  │ - Check cache (30s) │   │
│  │ - Collect if stale  │   │
│  │ - Return text       │   │
│  └─────────────────────┘   │
└─────────────────────────────┘
```

**Design Decision:** 30-second metric caching

**Rationale:**
- Performance: Avoid expensive collection on every scrape
- Consistency: Same values returned within cache window
- Resource Usage: Reduced CPU overhead

**Implementation:**

```python
class OptimizedMetricCollector:
    def __init__(self, ttl_seconds=30):
        self._cache = MetricCache(ttl_seconds=ttl_seconds)
    
    async def collect_with_cache(self):
        if not self._cache.is_expired():
            return self._cache.get()
        metrics = await self._collect_metrics()
        self._cache.update(metrics)
        return metrics
```

---

#### 3.2 Time Series Storage

```
┌─────────────────────────────────────┐
│   Prometheus TSDB                   │
│                                     │
│  Blocks (2-hour chunks):            │
│  ┌────────┐ ┌────────┐ ┌────────┐ │
│  │ Block  │ │ Block  │ │ Block  │ │
│  │  01    │ │  02    │ │  03    │ │
│  │ 00-02h │ │ 02-04h │ │ 04-06h │ │
│  └────────┘ └────────┘ └────────┘ │
│                                     │
│  Retention: 30 days                 │
│  Compression: ~1-2 bytes/sample     │
└─────────────────────────────────────┘
```

**Storage Characteristics:**
- Block Size: 2 hours of data per block
- Retention: 30 days (configurable)
- Compression: Highly efficient
- Disk Usage: ~500MB per day for typical metrics

---

### 4. Alerting Architecture

#### 4.1 Alert Evaluation Flow

```
┌─────────────────────────────────────────────────┐
│          Prometheus                             │
│                                                 │
│  1. Evaluate rules (every 30s)                  │
│     ┌─────────────────────────────────────┐    │
│     │ mcp_journal_sessions_active > 10    │    │
│     │ for: 15m                            │    │
│     └─────────────┬───────────────────────┘    │
│                   │                             │
│  2. Alert state   ▼                             │
│     ┌─────────┐ ┌─────────┐ ┌─────────┐        │
│     │ Inactive│→│ Pending │→│ Firing  │        │
│     └─────────┘ └─────────┘ └────┬────┘        │
└───────────────────────────────────┼────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────┐
│          Alertmanager                           │
│                                                 │
│  3. Group alerts                                │
│  4. Deduplicate                                 │
│  5. Route to receivers                          │
│                                                 │
│  Receivers:                                     │
│    Critical → Slack                             │
│    Warning  → Email                             │
│    Default  → Slack                             │
└─────────────────────────────────────────────────┘
```

**Design Decisions:**
- Evaluation interval: 30s for responsiveness without excess load
- Alert states: Inactive → Pending → Firing with `for` durations to reduce flapping
- Grouping/deduplication to prevent alert spam

---

#### 4.2 Alert Rule Design

```yaml
groups:
  - name: journal_alerts
    interval: 30s
    rules:
      - alert: HighSessionFailureRate
        expr: |
          (
            rate(mcp_journal_sessions_total{status="failed"}[5m])
            /
            rate(mcp_journal_sessions_total[5m])
          ) > 0.1
        for: 5m
        labels:
          severity: warning
          component: journal
        annotations:
          summary: "High session failure rate"
          description: "{{ $value | humanizePercentage }} of sessions failing"
```

Key components: `expr` (PromQL), `for` (duration), `labels` (routing metadata), `annotations` (human-readable context).

---

### 5. Grafana Integration

#### 5.1 Dashboard Architecture

```
┌─────────────────────────────────────────────────┐
│            Grafana Dashboard                    │
│                                                 │
│  Row: Overview                                  │
│    - Active Sessions (Stat)                     │
│    - Success Rate (Gauge)                       │
│    - Total Sessions (Stat)                      │
│                                                 │
│  Row: Performance                               │
│    - Session Duration (Histogram p50/p95/p99)   │
│    - Learnings & Challenges (Graph)             │
│                                                 │
│  Row: System Resources                          │
│    - Memory Usage (Graph)                       │
│    - CPU Usage (Graph)                          │
└─────────────────────────────────────────────────┘
```

**Panel Types:** Stat, Gauge, Graph, Heatmap (for distributions).

#### 5.2 Query Examples

- Active Sessions (Stat):
```promql
mcp_journal_sessions_active
```

- Success Rate (Gauge):
```promql
(
  rate(mcp_journal_sessions_total{status="success"}[5m])
  /
  rate(mcp_journal_sessions_total[5m])
) * 100
```

- Session Duration p95 (Graph):
```promql
histogram_quantile(0.95, rate(mcp_journal_session_duration_minutes_bucket[5m]))
```

---

## 🔐 SECURITY ARCHITECTURE

### 1. Data Sanitization

```python
class DataSanitizer:
    SENSITIVE_PATTERNS = [
        re.compile(r'password["\s:=]+["\']?([^"\'\s]+)', re.I),
        re.compile(r'api[_-]?key["\s:=]+["\']?([^"\'\s]+)', re.I),
        re.compile(r'token["\s:=]+["\']?([^"\'\s]+)', re.I),
    ]
    @classmethod
    def sanitize_string(cls, text):
        for pattern in cls.SENSITIVE_PATTERNS:
            text = pattern.sub('***REDACTED***', text)
        return text
```

Applied at log messages (formatter), metric labels (manual review), and error messages (formatter).

---

### 2. Rate Limiting

```python
class RateLimiter:
    def __init__(self, max_requests=100, window_seconds=60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests = defaultdict(list)
    
    def is_allowed(self, client_id):
        now = time.time()
        cutoff = now - self.window_seconds
        self._requests[client_id] = [t for t in self._requests[client_id] if t > cutoff]
        if len(self._requests[client_id]) >= self.max_requests:
            return False
        self._requests[client_id].append(now)
        return True
```

Applied to `/metrics` (100 requests/min/IP). `/health` is unrestricted.

---

## 📊 DATA FLOW

### End-to-End Data Flow

```
1. Application event (e.g., session started)
2. Metric update: journal_metrics.sessions_total.labels(status='success').inc()
3. In-memory storage by Prometheus client
4. Scrape every 15s: Prometheus GET /metrics
5. Time series storage: Prometheus TSDB block write
6. Query & visualization: Grafana queries Prometheus and renders panels
```

**Latency Breakdown:**

| Stage | Latency | Notes |
|-------|---------|-------|
| Event → Metric Update | <1ms | In-memory |
| Metric Update → Scrape | 0-15s | Depends on scrape timing |
| Scrape → Storage | <100ms | Network + write |
| Query → Display | <500ms | Depends on query complexity |
| Total (worst case) | ~16s | Event to dashboard visibility |

---

## 🎯 DESIGN DECISIONS

### Decision 1: Pull vs Push Metrics
- Decision: Pull (Prometheus scraping)
- Rationale: Service discovery, reliability, direct `/metrics` debugging; acceptable 15s latency.

### Decision 2: JSON vs Text Logs
- Decision: JSON structured logs
- Rationale: Queryable, consistent key/value semantics, human-readable enough; slight size overhead acceptable.

### Decision 3: Metric Cardinality Limits
- Decision: Bound label values (max ~100 combinations per metric)
- Rationale: Prevents memory/CPU blowups; keeps queries fast.

### Decision 4: 30-Day Retention
- Decision: 30-day Prometheus retention
- Rationale: Fits debugging/trend needs with manageable storage; longer-term data can be downsampled or archived.

---

## 🔄 FAILURE MODES & RECOVERY

### Failure Mode 1: Prometheus Down
- Impact: No metrics collection; alerts stop; dashboards stale.
- Recovery: `docker-compose restart prometheus`; data preserved via persistent volume; container restart policy `always`.

### Failure Mode 2: Metrics Endpoint Overload
- Impact: Slow `/metrics`, scrape timeouts, missing datapoints.
- Recovery: Metric caching (30s TTL) already in place; if persistent, increase scrape interval, reduce cardinality, or scale app.

### Failure Mode 3: Disk Full
- Impact: Prometheus cannot write; potential crash.
- Recovery: Free space (delete old blocks), reduce retention (`--storage.tsdb.retention.time=15d`), add disk, or rotate backups.

---

## 📈 PERFORMANCE CHARACTERISTICS

### Metrics Collection Overhead

| Operation | Latency | Memory | Notes |
|-----------|---------|--------|-------|
| Counter increment | <1µs | 8 bytes | Atomic |
| Gauge set | <1µs | 8 bytes | Direct write |
| Histogram observe | <5µs | 64 bytes | Multiple buckets |
| Export all metrics | <10ms | - | With caching |

### Prometheus Query Performance

| Query Type | P50 | P95 | P99 | Notes |
|------------|-----|-----|-----|-------|
| Instant query | 20ms | 100ms | 500ms | Single timestamp |
| Range query (1h) | 100ms | 500ms | 2s | ~240 points |
| Range query (24h) | 500ms | 2s | 10s | ~5,760 points |
| Aggregation | 200ms | 1s | 5s | Depends on cardinality |

Optimization tips: use recording rules for expensive queries, limit time ranges, reduce cardinality.

---

## 🔗 INTEGRATION POINTS

### Application Code → Metrics

```python
from src.monitoring.metrics import journal_metrics
from src.monitoring.decorators import track_operation

@track_operation(counter=journal_metrics.sessions_total, histogram=journal_metrics.session_duration)
async def start_work_session(self, task):
    return {"success": True}
```

### Prometheus → Alertmanager

```yaml
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - 'alertmanager:9093'
```

### Alertmanager → Slack

```yaml
receivers:
  - name: 'slack'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/...'
        channel: '#alerts'
        title: 'Alert: {{ .CommonLabels.alertname }}'
```

---

## 📚 REFERENCES

### External Documentation
- https://prometheus.io/docs/
- https://grafana.com/docs/
- https://prometheus.io/docs/practices/naming/
- https://prometheus.io/docs/alerting/latest/configuration/

### Internal Documentation
- Operator Guide: operator-guide.md
- Developer Guide: developer-guide.md
- Runbook: runbook.md
- Troubleshooting Guide: troubleshooting.md

---

## 📝 REVISION HISTORY

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-01-08 | DevOps Team | Initial architecture documentation |

Document Status: ✅ Complete  
Last Updated: 2025-01-08  
Review Date: 2025-04-08 (Quarterly review)
