#!/bin/bash
#
# Run system metrics tests
#

set -e

echo "🧪 Running System Metrics Tests"
echo "==============================="
echo ""

# Unit tests
echo "Running unit tests..."
export PYTHONPATH=$PYTHONPATH:.
pytest tests/unit/test_system_metrics.py -v
pytest tests/unit/test_system_collector.py -v

echo ""

# Integration tests
echo "Running integration tests..."
pytest tests/integration/test_system_metrics_integration.py -v

echo ""

# Coverage report
echo "Generating coverage report..."
pytest tests/unit/test_system_metrics.py \
       tests/unit/test_system_collector.py \
       --cov=src.monitoring.metrics.system_metrics \
       --cov=src.monitoring.collectors \
       --cov-report=term-missing \
       --cov-report=html

echo ""
echo "==============================="
echo "✅ All tests passed!"
echo "Coverage report: htmlcov/index.html"
