#!/bin/bash
#
# Automated Load Test Validation
#

set -e

echo "🔍 Validating Load Testing Implementation"
echo "========================================="
echo ""

FAILED=0

# Test 1: Test discovery
echo "Test 1: Test Discovery"
export PYTHONPATH=$PYTHONPATH:.
TEST_COUNT=$(pytest tests/load/ --collect-only -q | grep "test session starts" | wc -l)
if [ "$TEST_COUNT" -gt 0 ]; then
    echo "✅ Tests discovered"
else
    echo "❌ No tests found"
    ((FAILED++))
fi
echo ""

# Test 2: Dependencies
echo "Test 2: Dependencies"
if python3 -c "import pytest, requests, psutil" 2>/dev/null; then
    echo "✅ All dependencies installed"
else
    echo "❌ Missing dependencies"
    ((FAILED++))
fi
echo ""

# Test 3: Services running
echo "Test 3: Services Running"
if timeout 2 curl -v http://localhost:8080/sse 2>&1 | grep -q "200 OK" || curl -sf http://localhost:8080/health > /dev/null; then
    echo "✅ Application is running"
else
    echo "❌ Application not running"
    ((FAILED++))
fi
echo ""

# Test 4: Run quick load test
echo "Test 4: Quick Load Test"
if pytest tests/load/test_metrics_performance.py::TestMetricsEndpointLoad::test_metrics_endpoint_concurrent_requests \
    -v --tb=line -q -s > /tmp/load_test.log 2>&1; then
    echo "✅ Load test passes"
    
    # Check metrics
    if grep -q "P95:" /tmp/load_test.log; then
        P95=$(grep "P95:" /tmp/load_test.log | awk '{print $2}')
        echo "  P95 response time: $P95"
    fi
    
    if grep -q "Success Rate:" /tmp/load_test.log; then
        SUCCESS_RATE=$(grep "Success Rate:" /tmp/load_test.log | awk '{print $3}')
        echo "  Success rate: $SUCCESS_RATE"
    fi
else
    echo "❌ Load test failed"
    cat /tmp/load_test.log
    ((FAILED++))
fi
echo ""

# Test 5: Performance targets
echo "Test 5: Performance Targets"
if [ -f /tmp/load_test.log ]; then
    P95=$(grep "P95:" /tmp/load_test.log | awk '{print $2}' | tr -d 'ms')
    SUCCESS_RATE=$(grep "Success Rate:" /tmp/load_test.log | awk '{print $3}' | tr -d '%')
    
    if (( $(echo "$P95 < 100" | bc -l) )); then
        echo "✅ P95 response time target met ($P95 ms < 100ms)"
    else
        echo "❌ P95 response time too high:  $P95 ms"
        ((FAILED++))
    fi
    
    if (( $(echo "$SUCCESS_RATE > 99" | bc -l) )); then
        echo "✅ Success rate target met ($SUCCESS_RATE% > 99%)"
    else
        echo "❌ Success rate too low: $SUCCESS_RATE%"
        ((FAILED++))
    fi
fi
echo ""

# Test 6: Scripts executable
echo "Test 6: Scripts Executable"
if [ -x scripts/run_load_tests.sh ]; then
    echo "✅ run_load_tests.sh is executable"
else
    echo "❌ run_load_tests. sh not executable"
    ((FAILED++))
fi
echo ""

echo "========================================="

if [ $FAILED -eq 0 ]; then
    echo "✅ ALL VALIDATIONS PASSED"
    exit 0
else
    echo "❌ $FAILED VALIDATIONS FAILED"
    exit 1
fi
