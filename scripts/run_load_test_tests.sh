#!/bin/bash
#
# Run tests for the load testing framework itself
#

set -e

echo "🧪 Testing Load Testing Framework"
echo "================================="
echo ""

# Unit tests
echo "Running unit tests for load testing framework..."
pytest tests/unit/test_load_testing_framework.py -v

echo ""

# Integration tests
# Ensure dependencies are installed for integration tests
pip install -q requests pytest-asyncio --break-system-packages

echo "Running integration tests for load testing..."
pytest tests/integration/test_load_testing_integration.py -v

echo ""

# Coverage
echo "Generating coverage report..."
pytest tests/unit/test_load_testing_framework.py \
       tests/integration/test_load_testing_integration.py \
       --cov=tests.load.test_metrics_performance \
       --cov-report=term-missing \
       --cov-report=html

echo ""
echo "================================="
echo "✅ All load testing tests passed!"
echo "Coverage report:  htmlcov/index.html"
