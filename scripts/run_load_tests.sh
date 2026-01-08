#!/bin/bash
#
# Run load tests for monitoring infrastructure
#

set -e

echo "🔥 LOAD TESTING - Monitoring Infrastructure"
echo "==========================================="
echo ""

# Check if services are running
export PYTHONPATH=$PYTHONPATH:.
echo "Checking if services are running..."
if ! timeout 2 curl -v http://localhost:8080/sse 2>&1 | grep -q "200 OK" && ! curl -sf http://localhost:8080/health > /dev/null; then
    echo "❌ Application not running. Please start with: docker-compose up -d"
    exit 1
fi

if ! curl -sf http://localhost:9090/-/healthy > /dev/null; then
    echo "⚠️  Prometheus not running.  Some tests may fail."
fi

echo "✅ Services are running"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -q pytest pytest-asyncio requests psutil --break-system-packages

echo ""

# Run load tests
echo "Running load tests..."
echo ""

pytest tests/load/test_metrics_performance.py \
    -v \
    -m load \
    --tb=short \
    --durations=10 \
    -s

EXIT_CODE=$?

echo ""
echo "==========================================="

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ ALL LOAD TESTS PASSED"
    echo ""
    echo "Performance Summary:"
    echo "- Metrics endpoint: <100ms at P95"
    echo "- Concurrent updates: >1000/s"
    echo "- CPU overhead: <5%"
    echo "- Success rate: >99%"
else
    echo "❌ SOME LOAD TESTS FAILED"
    echo "Review output above for details"
fi

echo "==========================================="

exit $EXIT_CODE
