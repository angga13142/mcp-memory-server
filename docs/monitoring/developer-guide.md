# Developer Guide - Monitoring & Observability

For developers adding or modifying metrics, logging, and health checks.

## Where to Add Metrics

# Developer Guide - Monitoring & Observability

## 🎯 Purpose

This guide is for developers who need to add monitoring and observability to their code, create new metrics, or extend the existing monitoring infrastructure.

---

## 🚀 QUICK START FOR DEVELOPERS

### Adding Metrics to Your Code

#### 1. Import Metrics

```python
from src.monitoring.metrics import journal_metrics
```

#### 2. Increment Counters

```python
# In your service method
async def my_service_method(self):
    try:
        result = await some_operation()
        journal_metrics.increment_session('success')
        return result
    except Exception:
        journal_metrics.increment_session('failed')
        raise
```

#### 3. Observe Durations

```python
import time

async def timed_operation(self):
    start_time = time.time()
    try:
        result = await heavy_operation()
        return result
    finally:
        duration = time.time() - start_time
        journal_metrics.session_duration.observe(duration)
```

#### 4. Use Decorators (Recommended)

```python
from src.monitoring.decorators import track_operation
from src.monitoring.metrics import journal_metrics
import logging

logger = logging.getLogger(__name__)

@track_operation(
    counter=journal_metrics.sessions_total,
    histogram=journal_metrics.session_duration,
    logger=logger
)
async def my_tracked_operation(self):
    return {"success": True}
```

---

## 📊 CREATING NEW METRICS

### Step-by-Step Guide

#### Step 1: Define Metric Class

**File:** src/monitoring/metrics/my_feature_metrics.py

```python
"""Metrics for my new feature."""

from prometheus_client import Counter, Gauge, Histogram
from .base import MetricCollector
from typing import Dict


class MyFeatureMetrics(MetricCollector):
    """Metrics for my awesome feature."""

    def __init__(self):
        self.operations_total: Counter | None = None
        self.active_operations: Gauge | None = None
        self.operation_duration: Histogram | None = None

    def register(self) -> None:
        self.operations_total = Counter(
            'mcp_myfeature_operations_total',
            'Total operations performed',
            ['status', 'operation_type'],
        )
        self.active_operations = Gauge(
            'mcp_myfeature_operations_active',
            'Currently active operations',
        )
        self.operation_duration = Histogram(
            'mcp_myfeature_operation_duration_seconds',
            'Operation duration in seconds',
            ['operation_type'],
            buckets=[0.1, 0.5, 1, 2, 5, 10, 30],
        )

    def collect(self) -> Dict[str, float]:
        return {
            'active_operations': self._require(self.active_operations, 'active_operations')._value.get(),
        }

    def increment_operation(self, status: str, operation_type: str) -> None:
        self._require(self.operations_total, 'operations_total').labels(
            status=status,
            operation_type=operation_type,
        ).inc()

    def observe_duration(self, duration: float, operation_type: str) -> None:
        self._require(self.operation_duration, 'operation_duration').labels(
            operation_type=operation_type,
        ).observe(duration)

    def _require(self, metric, name: str):
        if metric is None:
            raise RuntimeError(f"Metric '{name}' not registered")
        return metric


my_feature_metrics = MyFeatureMetrics()
```

#### Step 2: Register Metrics

**File:** src/monitoring/metrics/**init**.py

```python
from .my_feature_metrics import MyFeatureMetrics, my_feature_metrics

metric_registry.register_collector(my_feature_metrics)

__all__ += [
    'MyFeatureMetrics',
    'my_feature_metrics',
]
```

#### Step 3: Use in Your Code

```python
from src.monitoring.metrics import my_feature_metrics
import time

async def my_operation(operation_type: str):
    my_feature_metrics.active_operations.inc()
    start = time.time()
    try:
        result = await do_something()
        duration = time.time() - start
        my_feature_metrics.increment_operation('success', operation_type)
        my_feature_metrics.observe_duration(duration, operation_type)
        return result
    except Exception:
        duration = time.time() - start
        my_feature_metrics.increment_operation('failed', operation_type)
        my_feature_metrics.observe_duration(duration, operation_type)
        raise
    finally:
        my_feature_metrics.active_operations.dec()
```

#### Step 4: Test Your Metrics

```python
import pytest
from src.monitoring.metrics import my_feature_metrics, get_metrics


def test_increment_operation():
    initial = my_feature_metrics.operations_total.labels(status='success', operation_type='test')._value.get()
    my_feature_metrics.increment_operation('success', 'test')
    final = my_feature_metrics.operations_total.labels(status='success', operation_type='test')._value.get()
    assert final == initial + 1


def test_observe_duration():
    my_feature_metrics.observe_duration(1.5, 'test')
    metrics = get_metrics().decode('utf-8')
    assert 'mcp_myfeature_operation_duration_seconds' in metrics
```

---

## 📝 ADDING STRUCTURED LOGGING

### Basic Logging

```python
import logging
from src.monitoring.logging import log_event

logger = logging.getLogger(__name__)

def my_function():
    log_event(
        logger,
        'INFO',
        'my_event',
        'Operation completed successfully',
        user_id='user123',
        operation='create_widget',
        duration_ms=150,
    )
```

### Using Context

```python
from src.monitoring.logging import LogContext

async def handle_request(request):
    with LogContext(user_id=request.user_id):
        logger.info("Processing request")
        result = await process(request)
        logger.info("Request completed")
        return result
```

### Custom Log Events

```python
from src.monitoring.logging import log_event

log_event(
    logger,
    'INFO',
    'widget_created',
    'Widget created successfully',
    widget_id='widget-123',
    user_id='user-456',
    duration_ms=250,
)

log_event(
    logger,
    'ERROR',
    'widget_creation_failed',
    'Failed to create widget',
    widget_type='premium',
    error='ValidationError',
    error_message='Invalid widget configuration',
)
```

---

## 🎨 BEST PRACTICES

### Metric Design

- Use clear, descriptive names with units and low-cardinality labels.
- Prefer Counter for monotonic counts, Gauge for up/down, Histogram for latency/size distributions.
- Avoid unbounded label values (user_id, session_id, request_id).
- Reuse metrics with labels instead of many separate metrics.

### Histogram Buckets

- Match buckets to expected ranges (API latency in seconds, sessions in minutes, sizes in bytes).

### Logging

- Choose appropriate log levels.
- Include context fields (ids, durations, status).
- Do not log secrets; sanitize with DataSanitizer or SanitizingFormatter.

---

## 🔧 TESTING MONITORING CODE

### Testing Metrics

```python
import pytest
from src.monitoring.metrics import journal_metrics
from src.monitoring.decorators import track_operation


class TestJournalMetrics:
    @pytest.fixture(autouse=True)
    def reset_metrics(self):
        yield

    def test_session_counter_increments(self):
        initial = journal_metrics.sessions_total.labels(status='success')._value.get()
        journal_metrics.increment_session('success')
        current = journal_metrics.sessions_total.labels(status='success')._value.get()
        assert current == initial + 1

    @pytest.mark.asyncio
    async def test_decorator_tracks_metrics(self):
        @track_operation(counter=journal_metrics.sessions_total, logger=None)
        async def test_func():
            return {"success": True}

        initial = journal_metrics.sessions_total.labels(status='success')._value.get()
        await test_func()
        current = journal_metrics.sessions_total.labels(status='success')._value.get()
        assert current == initial + 1
```

### Testing Logging

```python
import logging
from src.monitoring.logging import log_event


def test_log_event_includes_context(caplog):
    logger = logging.getLogger('test')
    with caplog.at_level(logging.INFO):
        log_event(
            logger,
            'INFO',
            'test_event',
            'Test message',
            user_id='user123',
            count=42,
        )
    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert record.levelname == 'INFO'
    assert hasattr(record, 'extra_data')
    assert record.extra_data['user_id'] == 'user123'
    assert record.extra_data['count'] == 42
```

---

## 🎯 COMMON PATTERNS

### Pattern 1: Tracking Function Execution

```python
from src.monitoring.decorators import track_with_context
import logging

logger = logging.getLogger(__name__)

@track_with_context(
    metric_name='data_processing',
    operation_type='process_batch',
    logger=logger,
)
async def process_batch(items: list):
    results = []
    for item in items:
        results.append(await process_item(item))
    return results
```

### Pattern 2: Retry with Metrics

```python
from src.monitoring.decorators import retry_on_error
from src.monitoring.metrics import database_metrics
import logging

logger = logging.getLogger(__name__)

@retry_on_error(max_retries=3, delay=1.0, logger=logger)
async def save_to_database(data):
    try:
        await db.insert(data)
        database_metrics.queries_total.labels(operation='insert', status='success').inc()
    except Exception:
        database_metrics.queries_total.labels(operation='insert', status='failed').inc()
        raise
```

### Pattern 3: Background Metric Collection

```python
import asyncio
import logging
from src.monitoring.metrics import system_metrics

logger = logging.getLogger(__name__)

async def collect_system_metrics_periodically():
    while True:
        try:
            await system_metrics.update()
        except Exception as exc:
            logger.error("Failed to collect system metrics: %s", exc)
        await asyncio.sleep(15)

asyncio.create_task(collect_system_metrics_periodically())
```

---

## 📚 API REFERENCE

### Metrics Module

```python
from src.monitoring.metrics import (
    journal_metrics,
    database_metrics,
    vector_store_metrics,
    metric_registry,
)
```

### Decorators Module

```python
from src.monitoring.decorators import (
    track_operation,
    track_with_context,
    retry_on_error,
)
```

### Logging Module

```python
from src.monitoring.logging import (
    LogContext,
    log_event,
    log_error,
    set_correlation_id,
    get_correlation_id,
)
```

---

## 🆘 TROUBLESHOOTING

### Metrics Not Appearing

- Ensure the collector is registered in metrics/**init**.py.
- Check logs for registration errors.
- Confirm the metric is incremented in code paths.

### High Cardinality Warning

- Review labels and remove unbounded identifiers.
- Prefer operation/status enums instead of user/session IDs.

---

## 📝 CHECKLIST FOR NEW METRICS

- Descriptive name with units
- Appropriate type (Counter/Gauge/Histogram)
- Low-cardinality labels
- Suitable histogram buckets
- Registered in global registry
- Unit tests added
- Documentation updated
- Dashboard update considered
- Local verification and Prometheus check

---

## 🔗 USEFUL LINKS

- https://prometheus.io/docs/practices/naming/
- https://github.com/prometheus/client_python
- https://grafana.com/docs/grafana/latest/dashboards/
- https://www.structlog.org/

---

**Next:** runbook.md for operational procedures

- Unit: `PYTHONPATH=. pytest tests/unit/test_metrics.py` (and related logging tests when added).
- Lint/type: `ruff check src/monitoring`, `mypy src/monitoring`.

## Troubleshooting Instrumentation

- Missing metrics: ensure collector registered in `metrics/__init__.py` and process imports occur early.
- Duplicate metric errors: ensure single registration; avoid re-import side effects in tests (reset registry if needed).
- High cardinality: avoid unbounded label values; prefer bounded enums.
