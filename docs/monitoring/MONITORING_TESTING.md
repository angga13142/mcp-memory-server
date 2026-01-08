# Monitoring Testing Guide

## Overview

Comprehensive test suite for monitoring and observability components.

## Test Structure

```
tests/
├── unit/                          # Unit tests
│   ├── test_metrics.py           # Metrics functionality
│   └── test_logging.py           # Logging functionality
├── integration/                   # Integration tests
│   ├── test_prometheus_integration.py
│   └── test_grafana_integration.py
├── load/                          # Performance tests
│   └── test_metrics_performance.py
└── alerts/                        # Alert tests
    └── test_alert_scenarios.py
```

## Quick Start

```bash
# Run all tests
chmod +x scripts/run_monitoring_tests.sh
./scripts/run_monitoring_tests.sh

# Run specific test suite
pytest tests/unit/test_metrics.py -v
pytest tests/integration/ -v
pytest tests/load/ -v
```

## Test Categories

### Unit Tests

**Metrics Tests** (`test_metrics.py`):

- Counter increments
- Gauge operations
- Histogram observations
- Metric decorators
- Export format

**Logging Tests** (`test_logging.py`):

- JSON formatting
- Required fields
- Correlation IDs
- Exception handling
- Log levels

Run unit tests:

```bash
pytest tests/unit/ -v
```

### Integration Tests

**Prometheus Integration** (`test_prometheus_integration.py`):

- Target scraping
- Metric queries
- Range queries
- Alert rules

**Grafana Integration** (`test_grafana_integration.py`):

- Datasource configuration
- Dashboard loading
- Panel queries
- Health checks

Run integration tests:

```bash
# Requires Prometheus and Grafana running
pytest tests/integration/ -v -s
```

### Performance Tests

**Metrics Performance** (`test_metrics_performance.py`):

- Collection overhead
- Concurrent updates
- Export performance
- Memory usage

Run performance tests:

```bash
pytest tests/load/ -v -s
```

### Alert Tests

**Alert Scenarios** (`test_alert_scenarios.py`):

- Alert triggering
- Alert annotations
- Alert recovery

Run alert tests:

```bash
# Quick tests (skip slow ones)
pytest tests/alerts/ -v -s -m 'not slow'

# Full tests (includes 16-minute alert test)
pytest tests/alerts/ -v -s
```

## Prerequisites

### Required Services

```bash
# Start main services
docker-compose up -d

# Start monitoring stack (optional for integration tests)
docker-compose -f docker-compose.monitoring.yml up -d
```

### Required Packages

```bash
pip install pytest pytest-asyncio pytest-cov requests psutil
```

## Running Tests

### All Tests

```bash
./scripts/run_monitoring_tests.sh
```

### By Category

```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v -s

# Performance tests only
pytest tests/load/ -v -s
```

### By File

```bash
pytest tests/unit/test_metrics.py -v
pytest tests/unit/test_logging.py -v
pytest tests/integration/test_prometheus_integration.py -v -s
```

### Specific Test

```bash
pytest tests/unit/test_metrics.py::TestMetricsCounters::test_sessions_total_increment -v
```

## Coverage

### Generate Coverage Report

```bash
pytest tests/unit/ tests/integration/ \
    --cov=src.utils.metrics \
    --cov=src.utils.structured_logging \
    --cov-report=html \
    --cov-report=term-missing
```

### View HTML Report

```bash
open htmlcov/index.html
```

### Coverage Requirements

- **Metrics**: ≥90%
- **Logging**: ≥85%
- **Overall**: ≥85%

## Test Markers

```bash
# Slow tests (e.g., alert triggering)
pytest -m slow

# Skip slow tests
pytest -m "not slow"
```

## Troubleshooting

### Tests Skip Due to Service Not Available

**Issue**: Tests skip with "Prometheus/Grafana not available"

**Solution**:

```bash
# Start monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# Wait for services
sleep 30

# Verify services
curl http://localhost:9090/-/healthy
curl http://localhost:3000/api/health
```

### Import Errors

**Issue**: `ModuleNotFoundError`

**Solution**:

```bash
# Ensure you're in project root
cd /home/racoon/AgentMemorh/mcp-memory-server

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Test Failures

**Issue**: Metrics tests fail

**Solution**:

```bash
# Reset metrics (restart server)
docker-compose restart memory-server

# Clear test data
rm -rf data/test_*

# Run tests again
pytest tests/unit/test_metrics.py -v
```

## Continuous Integration

Tests are automatically run in CI/CD pipeline:

```yaml
# .github/workflows/ci-cd.yml
jobs:
  test:
    - name: Run unit tests
      run: pytest tests/unit/ -v

    - name: Run integration tests
      run: pytest tests/integration/ -v -s

    - name: Generate coverage
      run: pytest --cov --cov-report=xml
```

## Best Practices

1. **Isolation**: Each test should be independent
2. **Cleanup**: Clean up test data in teardown
3. **Timeouts**: Use appropriate timeouts for async tests
4. **Markers**: Mark slow tests with `@pytest.mark.slow`
5. **Fixtures**: Reuse fixtures for common setup

## Example Test Run

```bash
$ ./scripts/run_monitoring_tests.sh

🧪 Running Monitoring & Observability Tests
============================================

📦 Ensuring monitoring stack is running...

🔬 UNIT TESTS
-------------
Running Metrics Unit Tests...
✅ Metrics Unit Tests PASSED

Running Logging Unit Tests...
✅ Logging Unit Tests PASSED

🔗 INTEGRATION TESTS
--------------------
Running Prometheus Integration...
✅ Prometheus Integration PASSED

Running Grafana Integration...
✅ Grafana Integration PASSED

⚡ PERFORMANCE TESTS
--------------------
Running Metrics Performance...
✅ Metrics Performance PASSED

🚨 ALERT TESTS (Quick)
----------------------
Running Alert Configuration...
✅ Alert Configuration PASSED

============================================
TEST SUMMARY
============================================
Passed: 6
Failed: 0

🎉 ALL TESTS PASSED!
✅ Monitoring system tested and ready
```

## Test Completion Checklist

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Performance tests meet thresholds
- [ ] Alert tests verify configuration
- [ ] Code coverage ≥85%
- [ ] No flaky tests
- [ ] All tests documented
- [ ] CI/CD pipeline includes tests
